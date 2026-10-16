"""Baseline B0: GPS-initialised 2-D vehicle dead reckoning (positioning_design.md §4).

While GPS fixes arrive, the state is reset to each fix (position, speed, bearing). Between fixes, and
after GPS is lost, it is propagated with the vehicle-axis IMU from the alignment stage (D40):

    a_fwd = forward specific force   (flat road -> no gravity if levelled)
    w_up  = yaw rate                 (gyro bias already removed by the stage)
    v    += a_fwd dt,  psi += w_up dt,  (E, N) += v (cos psi, sin psi) dt

The vehicle is assumed not to move sideways (non-holonomic), so the lateral accelerometer channel is
not integrated. The estimators differ in their alignment stage and GPS blending:

* ``dr_raw``: declared alignment (phone axes taken as vehicle axes, no calibration). The "raw physics"
  baseline; valid only for an aligned mount (an explicit assumption, not knowledge of the mounting).
* ``dr_calibrated``: GPS + IMU alignment (axes and gyro bias from approach GPS). The levelling absorbs
  the horizontal accelerometer bias.
* ``dr_filtered``: as ``dr_calibrated``, plus GPS blending.

Until the stage has an orientation, the estimate coasts with the last GPS velocity.

Optional GPS blending (``blend_speed_tau_s`` / ``blend_heading_tau_s``): once the IMU is aligned,
speed and heading are not reset to each (noisy) fix but pulled towards it with a first-order,
causal complementary filter, x += (dt_fix / tau) * (x_gps - x). Between fixes the calibrated IMU
carries them. This averages GPS speed/bearing noise over ~tau seconds, so the state handed over to
pure dead reckoning at the tunnel entrance is better than a single fix. Position is still reset to
each fix: GPS position errors are time-correlated, so averaging them gains little.

Map grade (D39): if the route map provides the road grade, the gravity leakage predicted from it is
subtracted from the forward channel (``map_grade.GradeCompensation``). The grade is looked up at an
along-route distance the estimator keeps for this purpose only: each fix projected onto the route
(searched near the previous value), advanced by the estimated speed in between. Without map grade
nothing changes.

Portal freeze (D46): with GPS blending (``dr_filtered``), inside [B − 200 m, C] speed and heading are not
pulled towards the fixes; the IMU carries them, so the state handed over is the last one trusted.
Position still resets to each fix. The zone is looked up at the same projected along-route distance.
``dr_calibrated`` resets to every fix by design and keeps doing so (its calibration still freezes).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from throughtunnel.observations import GnssFix, RouteMap
from throughtunnel.positioning.alignment import VehicleImu
from throughtunnel.positioning.base import Estimator, StateEstimate
from throughtunnel.positioning.map_grade import grade_compensation
from throughtunnel.positioning.portal import portal_freeze

SEARCH_BACK_M = 50.0  # window for projecting a fix onto the route near the previous distance
SEARCH_AHEAD_M = 200.0


@dataclass(frozen=True)
class DeadReckoningConfig:
    gnss_timeout_s: float = 1.5  # no fix for this long -> dead-reckoning mode
    blend_speed_tau_s: float | None = None  # None: reset speed to every fix
    blend_heading_tau_s: float | None = None  # None: reset heading to every fix
    min_speed_for_bearing: float = 5.0  # GPS bearing is ignored below this speed when blending


class VehicleDeadReckoning(Estimator):
    name = "dr"
    label = "Dead reckoning"

    def __init__(self, route: RouteMap, config: DeadReckoningConfig | None = None) -> None:
        super().__init__(route)
        self.config = config or DeadReckoningConfig()
        self._aligned = False  # the last IMU sample came with an orientation
        self._t: float | None = None
        self._last_fix_t = -math.inf
        self._e = self._n = self._v = self._psi = 0.0
        self._initialised = False
        self._grade = grade_compensation(route)
        blends = self.config.blend_speed_tau_s or self.config.blend_heading_tau_s
        self._freeze = portal_freeze(route) if blends else None
        self._d: float | None = None  # along-route distance: map-grade lookup and freeze zone only

    # ------------------------------------------------------------------ observations
    def on_gnss(self, fix: GnssFix) -> None:
        cfg = self.config
        blending = self._initialised and self._aligned and fix.t - self._last_fix_t <= cfg.gnss_timeout_s
        self._e, self._n = self.fix_enu(fix)
        if self._grade is not None or self._freeze is not None:
            if self._d is None:
                self._d = self.route.project_enu(self._e, self._n)[0]
            else:
                lo, hi = self._d - SEARCH_BACK_M, self._d + SEARCH_AHEAD_M
                self._d = self.route.project_enu(self._e, self._n, lo_m=lo, hi_m=hi)[0]
        # Portal freeze zone: the IMU carries speed and heading (D46).
        hold = blending and self._freeze is not None and self._freeze.active(self._d)
        yaw_gps = self.bearing_to_yaw(fix.bearing_deg)
        if hold:
            pass
        elif blending and cfg.blend_speed_tau_s:
            self._v += min(1.0, (fix.t - self._last_fix_t) / cfg.blend_speed_tau_s) * (
                fix.speed_mps - self._v
            )
        else:
            self._v = fix.speed_mps
        if hold:
            pass
        elif blending and cfg.blend_heading_tau_s:
            if fix.speed_mps >= cfg.min_speed_for_bearing:
                gain = min(1.0, (fix.t - self._last_fix_t) / cfg.blend_heading_tau_s)
                self._psi += gain * math.remainder(yaw_gps - self._psi, 2.0 * math.pi)
        else:
            self._psi = yaw_gps
        self._last_fix_t = fix.t
        self._t = fix.t
        self._initialised = True

    def on_imu(self, t: float, imu: VehicleImu | None) -> None:
        self._aligned = imu is not None
        if not self._initialised:
            return
        dt = t - self._t if self._t is not None else 0.0
        self._t = t
        if dt <= 0.0:
            return
        if imu is None:  # no orientation yet: coast with the last GPS velocity
            self._e += self._v * math.cos(self._psi) * dt
            self._n += self._v * math.sin(self._psi) * dt
            self._advance_route_distance(self._v * dt)
            return
        a_fwd = imu.accel[0]
        if self._grade is not None and self._d is not None:
            a_fwd -= self._grade.forward_gravity(self._d, imu.calibration_grade_angle)
        w_up = imu.gyro[2]
        v_new = max(self._v + a_fwd * dt, 0.0)
        psi_new = self._psi + w_up * dt
        v_mid, psi_mid = 0.5 * (self._v + v_new), 0.5 * (self._psi + psi_new)  # midpoint integration
        self._e += v_mid * math.cos(psi_mid) * dt
        self._n += v_mid * math.sin(psi_mid) * dt
        self._v, self._psi = v_new, psi_new
        self._advance_route_distance(v_mid * dt)

    def _advance_route_distance(self, ds: float) -> None:
        if self._d is not None:
            self._d = min(self._d + ds, self.route.length_m)

    def state(self) -> StateEstimate | None:
        if not self._initialised or self._t is None:
            return None
        gnss = self._t - self._last_fix_t <= self.config.gnss_timeout_s
        return StateEstimate(
            t=self._t,
            east=self._e,
            north=self._n,
            speed=self._v,
            heading=self._psi,
            mode="gnss" if gnss else "dead_reckoning",
        )


class RawDeadReckoning(VehicleDeadReckoning):
    name = "dr_raw"
    label = "DR raw IMU (assumed aligned mount)"
    alignment = "declared"

    def __init__(self, route: RouteMap) -> None:
        super().__init__(route, DeadReckoningConfig())


class CalibratedDeadReckoning(VehicleDeadReckoning):
    name = "dr_calibrated"
    label = "DR GPS-calibrated IMU"

    def __init__(self, route: RouteMap) -> None:
        super().__init__(route, DeadReckoningConfig())


class FilteredDeadReckoning(VehicleDeadReckoning):
    name = "dr_filtered"
    label = "DR calibrated + GPS-blended speed/heading"

    def __init__(self, route: RouteMap) -> None:
        super().__init__(route, DeadReckoningConfig(blend_speed_tau_s=5.0, blend_heading_tau_s=10.0))
