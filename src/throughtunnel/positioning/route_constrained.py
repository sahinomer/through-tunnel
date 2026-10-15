"""Route-constrained estimators: the vehicle is assumed to stay on the navigation route.

The state is one-dimensional: the distance d travelled along the route map, plus speed. Position and
heading come from the map. This removes cross-track error and heading drift entirely: what remains is
along-track error (speed error integrated over time) and the map's own deviation from the road.

* ``RouteImuDeadReckoning``: speed is integrated from the forward specific force of the GPS + IMU
  alignment stage (D40), the same stage as the calibrated vehicle dead reckoning. While GPS is
  available the speed is blended towards the GPS speed (complementary filter, 5 s), as in
  ``dr_filtered``.
* ``RouteSpeedHold``: the naive reference. Keep the last GPS speed. Uses no IMU (no alignment stage).
  Inertial methods must beat this.

If the route map provides the road grade (D39), ``RouteImuDeadReckoning`` subtracts the gravity
leakage predicted from it at the estimated distance d (``map_grade.GradeCompensation``).

While GPS is available, d is the projection of each fix onto the route (searched near the previous
value, so a fix cannot snap to a far-away part of the route).
"""

from __future__ import annotations

import math

from throughtunnel.observations import GnssFix, RouteMap
from throughtunnel.positioning.alignment import VehicleImu
from throughtunnel.positioning.base import Estimator, StateEstimate
from throughtunnel.positioning.map_grade import grade_compensation

GNSS_TIMEOUT_S = 1.5
BLEND_SPEED_TAU_S = 5.0
SEARCH_BACK_M = 50.0
SEARCH_AHEAD_M = 200.0


class RouteConstrained(Estimator):
    name = "route"
    label = "Route-constrained"
    use_imu_speed = True

    def __init__(self, route: RouteMap) -> None:
        super().__init__(route)
        self._aligned = False  # the last IMU sample came with an orientation
        self._t: float | None = None
        self._last_fix_t = -math.inf
        self._d: float | None = None
        self._v = 0.0
        self._grade = grade_compensation(route) if self.use_imu_speed else None

    def on_gnss(self, fix: GnssFix) -> None:
        e, n = self.fix_enu(fix)
        if self._d is None:
            self._d = self.route.project_enu(e, n)[0]
        else:
            self._d = self.route.project_enu(
                e, n, lo_m=self._d - SEARCH_BACK_M, hi_m=self._d + SEARCH_AHEAD_M
            )[0]
        blending = self.use_imu_speed and self._aligned and fix.t - self._last_fix_t <= GNSS_TIMEOUT_S
        if blending:
            self._v += min(1.0, (fix.t - self._last_fix_t) / BLEND_SPEED_TAU_S) * (fix.speed_mps - self._v)
        else:
            self._v = fix.speed_mps
        self._last_fix_t = fix.t
        self._t = fix.t

    def on_imu(self, t: float, imu: VehicleImu | None) -> None:
        self._aligned = imu is not None
        if self._d is None:
            return
        dt = t - self._t if self._t is not None else 0.0
        self._t = t
        if dt <= 0.0:
            return
        v_new = self._v
        if self.use_imu_speed and imu is not None:
            a_fwd = imu.accel[0]
            if self._grade is not None:
                a_fwd -= self._grade.forward_gravity(self._d, imu.calibration_grade_angle)
            v_new = max(self._v + a_fwd * dt, 0.0)
        self._d = min(self._d + 0.5 * (self._v + v_new) * dt, self.route.length_m)
        self._v = v_new

    def state(self) -> StateEstimate | None:
        if self._d is None or self._t is None:
            return None
        e, n = self.route.enu_at(self._d)
        return StateEstimate(
            t=self._t,
            east=e,
            north=n,
            speed=self._v,
            heading=self.route.heading_at(self._d),
            mode="gnss" if self._t - self._last_fix_t <= GNSS_TIMEOUT_S else "dead_reckoning",
            route_distance=self._d,
        )


class RouteImuDeadReckoning(RouteConstrained):
    name = "route_imu"
    label = "Route + filtered IMU speed"
    use_imu_speed = True


class RouteSpeedHold(RouteConstrained):
    name = "route_hold"
    label = "Route + last GPS speed (naive)"
    use_imu_speed = False
    alignment = None
