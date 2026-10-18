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

Portal freeze (D46): inside [B − 200 m, C] ``RouteImuDeadReckoning`` does not blend the speed towards the
fixes; the IMU carries it, so it hands over the last speed it trusted. d still follows the fixes.
``RouteSpeedHold`` (the naive reference) keeps the last GPS speed as before.

While GPS is available, d is the projection of each fix onto the route (searched near the previous
value, so a fix cannot snap to a far-away part of the route).
"""

from __future__ import annotations

import math

from throughtunnel.observations import GnssFix, RouteMap
from throughtunnel.positioning.alignment import VehicleImu
from throughtunnel.positioning.base import Estimator, StateEstimate
from throughtunnel.positioning.map_grade import grade_compensation
from throughtunnel.positioning.portal import portal_freeze

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
        self._freeze = portal_freeze(route) if self.use_imu_speed else None

    def on_gnss(self, fix: GnssFix) -> None:
        e, n = self.fix_enu(fix)
        if self._d is None:
            self._d = self.route.project_enu(e, n)[0]
        else:
            self._d = self.route.project_enu(
                e, n, lo_m=self._d - SEARCH_BACK_M, hi_m=self._d + SEARCH_AHEAD_M
            )[0]
        blending = self.use_imu_speed and self._aligned and fix.t - self._last_fix_t <= GNSS_TIMEOUT_S
        if blending and self._freeze is not None and self._freeze.active(self._d):
            pass  # portal freeze zone: the IMU carries the speed (D46)
        elif blending:
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
            v_new = max(self._v + self._forward_accel(imu) * dt, 0.0)
        self._d = min(self._d + 0.5 * (self._v + v_new) * dt, self.route.length_m)
        self._v = v_new

    def _forward_accel(self, imu: VehicleImu) -> float:
        """Forward specific force with the map-grade gravity removed (if the map has the grade)."""
        a_fwd = imu.accel[0]
        if self._grade is not None:
            a_fwd -= self._grade.forward_gravity(self._d, imu.calibration_grade_angle)
        return a_fwd

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
    description = (
        "Assumes the car stays on the route. Its speed comes from the calibrated forward accelerometer, "
        "averaged with GPS speed before the tunnel."
    )
    pipeline = "GPS fixes + IMU → calibration → forward speed → distance on the route → position"
    use_imu_speed = True


MIN_STOP_SAMPLES = 200  # ~1 s at 200 Hz: shorter stops do not re-measure the offset


class RouteImuStandstill(RouteImuDeadReckoning):
    """Oracle estimator (D49): route + IMU with standstill given by the oracle. **Not phone-only**: the
    standstill comes from the true motion, to measure what knowing it is worth (not a validated detector).

    While the car stands: speed exactly 0 and the route distance held, in both directions. The phone-only
    estimators only have the v ≥ 0 clamp, which resets a negative speed error at a stop but lets a
    positive one creep through it (P5). With ``measure_offset`` (variant b, zero-velocity update) the
    standing car also measures the forward offset: the mean grade-compensated forward specific force over
    the stop, which is then subtracted until the next stop (calibration pitch residual and bias drift,
    solutions 3a/4a).
    """

    name = "route_imu_stop"
    label = "Route + IMU + standstill oracle: speed reset ‡"
    description = (
        "The route + IMU estimator with speed set to 0 at each true stop. It shows what knowing when the "
        "car stands still would be worth."
    )
    pipeline = "GPS fixes + IMU + true standstill → speed reset at stops → distance on the route → position"
    uses_standstill = True
    measure_offset = False

    def __init__(self, route: RouteMap) -> None:
        super().__init__(route)
        self._standing = False
        self._offset = 0.0  # forward offset measured at the last stop [m/s^2]
        self._stop_sum = 0.0
        self._stop_n = 0

    def on_standstill(self, t: float, standing: bool) -> None:
        if standing:
            self._v = 0.0
            self._stop_sum, self._stop_n = 0.0, 0
        elif self.measure_offset and self._stop_n >= MIN_STOP_SAMPLES:
            self._offset += self._stop_sum / self._stop_n
        self._standing = standing

    def on_imu(self, t: float, imu: VehicleImu | None) -> None:
        if not self._standing:
            super().on_imu(t, imu)
            return
        self._aligned = imu is not None
        if self._d is None:
            return
        self._t = t
        self._v = 0.0
        if imu is not None:
            self._stop_sum += self._forward_accel(imu)  # what is left after the current correction
            self._stop_n += 1

    def _forward_accel(self, imu: VehicleImu) -> float:
        return super()._forward_accel(imu) - self._offset


class RouteImuZeroVelocity(RouteImuStandstill):
    name = "route_imu_zupt"
    label = "Route + IMU + standstill oracle: speed reset + offset ‡"
    description = (
        "Like the speed reset, plus the accelerometer offset is measured at each stop and removed until the "
        "next."
    )
    pipeline = (
        "GPS fixes + IMU + true standstill → speed and offset reset at stops → "
        "distance on the route → position"
    )
    measure_offset = True


class RouteSpeedHold(RouteConstrained):
    name = "route_hold"
    label = "Route + last GPS speed (naive)"
    description = (
        "Keeps the last GPS speed through the tunnel and uses no IMU. It's the baseline every inertial "
        "method must beat."
    )
    pipeline = "last GPS speed → distance on the route → position"
    use_imu_speed = False
    alignment = None


MIN_CALIBRATION_SPEED = 5.0  # [m/s] GPS and reading must both exceed this for a calibration pair
MIN_CALIBRATION_PAIRS = 10


class RouteVehicleSpeed(RouteConstrained):
    """Reference estimator (D41): route + the car's own speed reading; no IMU, no phone sensor at all.

    Not part of the phone-only solution (D20): the only estimator that declares ``uses_vehicle_speed``.
    The distance along the route advances with the speed reading, times a scale factor calibrated on
    the approach: the least-squares ratio of GPS speed to the reading over moving GPS fixes (the reading
    interpolated to the fix time). That removes most of the sensor's fixed scale error; what remains
    comes from GPS speed noise and degradation. With map grade, the along-road reading is converted to
    horizontal speed (÷ √(1 + grade²)) before calibration and use. ``calibrate_scale = False`` (set on an
    instance) uses the reading as it is, for sensitivity runs.
    """

    name = "route_vspeed"
    label = "Route + vehicle speed (reference)"
    description = (
        "Uses the car's own speed reading, with its scale calibrated against GPS on the approach. It's the "
        "ceiling."
    )
    pipeline = "GPS fixes + car speed → distance on the route → position"
    alignment = None
    use_imu_speed = False
    uses_vehicle_speed = True
    calibrate_scale = True

    def __init__(self, route: RouteMap) -> None:
        super().__init__(route)
        self._reading: tuple[float, float] | None = None  # (t, horizontal speed) of the last reading
        self._pending: tuple[float, float] | None = None  # (t, GPS speed) of a fix not yet paired
        self._num = self._den = 0.0
        self._pairs = 0

    @property
    def scale(self) -> float:
        """Factor applied to the reading (1 until enough calibration pairs)."""
        if not self.calibrate_scale or self._pairs < MIN_CALIBRATION_PAIRS:
            return 1.0
        return self._num / self._den

    def on_gnss(self, fix: GnssFix) -> None:
        super().on_gnss(fix)  # route distance from the fix, timing
        self._pending = (fix.t, fix.speed_mps)
        if self._reading is not None:
            self._v = self.scale * self._reading[1]  # the car's speed, not the GPS speed

    def on_vehicle_speed(self, t: float, speed_mps: float) -> None:
        v = speed_mps
        if self.route.has_grade and self._d is not None:
            v /= math.sqrt(1.0 + self.route.grade_at(self._d) ** 2)
        if self._pending is not None and self._reading is not None and t >= self._pending[0]:
            t_fix, v_gps = self._pending
            t0, v0 = self._reading
            r = v0 + (v - v0) * (t_fix - t0) / (t - t0) if t > t0 else v
            if v_gps > MIN_CALIBRATION_SPEED and r > MIN_CALIBRATION_SPEED:
                self._num += v_gps * r
                self._den += r * r
                self._pairs += 1
            self._pending = None
        self._reading = (t, v)
        self._v = self.scale * v
