"""Route-constrained Kalman filter (D51, step 4 of estimator_plan.md): distance, speed, forward offset.

Phone-only. The same information as ``route_imu`` (GPS + IMU alignment stage, route map, map grade,
portal freeze), but the fixed 5 s speed blend and the unquestioned calibration are replaced by a
filter with the state

    x = [d, v, b]    d: distance along the route [m], v: speed [m/s], b: forward offset [m/s^2]

* Prediction, every IMU sample: the grade-compensated forward specific force a, minus b, is integrated
  (d += v·dt + ½(a − b)·dt², v += (a − b)·dt). The offset b is what the calibration left in the forward
  channel (pitch residual, bias, drift): a random walk.
* Updates, every GPS fix: the fix projected onto the route (d) and the GPS speed (v), each weighted by the
  accuracy the phone reports (solution 1c). Position jumps beyond 4σ are rejected (multipath), at most 3
  fixes in a row. The speed is not gated: a gate there rejected exactly the updates that should correct a
  wrong offset, and the offset never converged (found in validation). b is observed
  through how the speed measurements diverge from the integrated IMU, over all fixes: the offset is fitted
  over the approach, not set by its last fix (solution 1e).
* Portal freeze zone (D46): no speed updates; position updates continue (gated).
* After a GPS outage the first fix resets d and v (as ``route_imu``); b and its uncertainty are kept.
* The v ≥ 0 clamp stays (no standstill information in the phone-only solution, P5).
* ``position_std_m`` is the filter's 1σ along-route uncertainty (for uncertainty-aware announcements).

Tuning (PD6: nominal values of the estimator, never read from the scenario configuration):
* accelerometer noise 180 µg/√Hz (a typical phone MEMS datasheet value; the simulator's preset happens to
  use the same order) plus a model-error term for what the forward channel gets wrong while driving (yaw
  residual × lateral acceleration, map grade errors): together 0.005 m/s²/√Hz;
* offset random walk 0.05 mg/√s (bias instability of ~0.5 mg over minutes);
* initial offset uncertainty 1 mg (what a GPS-levelled calibration typically leaves).
"""

from __future__ import annotations

import math

from throughtunnel.observations import GnssFix, RouteMap
from throughtunnel.positioning.alignment import VehicleImu
from throughtunnel.positioning.base import StateEstimate
from throughtunnel.positioning.route_constrained import (
    GNSS_TIMEOUT_S,
    SEARCH_AHEAD_M,
    SEARCH_BACK_M,
    RouteImuDeadReckoning,
)

G = 9.80665
ACCEL_PSD = 0.005**2  # [(m/s^2)^2/Hz]: sensor noise (180 µg/√Hz) + model error while driving
OFFSET_PSD = (0.05e-3 * G) ** 2  # [(m/s^2)^2/s]: random walk of the forward offset
OFFSET_SIGMA0 = 1e-3 * G  # [m/s^2]: initial offset uncertainty
YAW_SIGMA = math.radians(0.5)  # nominal yaw residual of the calibration: lateral acceleration leaks in
GATE_SIGMA = 4.0  # position jumps beyond this many σ are rejected (multipath) ...
MAX_REJECTED_IN_ROW = 3  # ... but never more than this many fixes in a row (no lock-out)
MIN_POSITION_SIGMA_M = 1.0
MIN_SPEED_SIGMA_MPS = 0.05


class RouteKalman(RouteImuDeadReckoning):
    name = "route_kf"
    label = "Route + IMU Kalman filter (distance, speed, offset)"
    turn_noise = 1.0  # 0: no turn-dependent process noise (comparison)

    def __init__(self, route: RouteMap) -> None:
        super().__init__(route)
        self._b = 0.0
        # covariance of (d, v, b), symmetric: dd, dv, db, vv, vb, bb
        self._p = [0.0] * 6
        self._p[5] = OFFSET_SIGMA0**2
        self.rejected = 0  # gated position fixes (diagnostics)
        self._rejected_in_row = 0

    @property
    def offset(self) -> float:
        """Current estimate of the forward offset b [m/s^2] (diagnostics)."""
        return self._b

    # ------------------------------------------------------------------ GPS
    def on_gnss(self, fix: GnssFix) -> None:
        e, n = self.fix_enu(fix)
        sigma_d = max(fix.horizontal_accuracy_m, MIN_POSITION_SIGMA_M)
        sigma_v = max(fix.speed_accuracy_mps, MIN_SPEED_SIGMA_MPS)
        tracking = self._d is not None and self._aligned and fix.t - self._last_fix_t <= GNSS_TIMEOUT_S
        if not tracking:  # start, before the alignment, or the first fix after an outage: reset d and v
            if self._d is None:
                self._d = self.route.project_enu(e, n)[0]
            else:
                lo = self._d - SEARCH_BACK_M
                self._d = self.route.project_enu(e, n, lo_m=lo, hi_m=self._d + SEARCH_AHEAD_M)[0]
            self._v = fix.speed_mps
            pbb = self._p[5]
            self._p = [sigma_d**2, 0.0, 0.0, sigma_v**2, 0.0, pbb]
        else:
            z_d = self.route.project_enu(e, n, lo_m=self._d - SEARCH_BACK_M, hi_m=self._d + SEARCH_AHEAD_M)[0]
            self._reset_distance(z_d, sigma_d)
            if not (self._freeze is not None and self._freeze.active(self._d)):
                self._update(1, fix.speed_mps - self._v, sigma_v**2)
            self._v = max(self._v, 0.0)
        self._last_fix_t = fix.t
        self._t = fix.t

    def _reset_distance(self, z_d: float, sigma_d: float) -> None:
        """The fix's route distance replaces d (gated): position informs d only, never v or b.

        Phone GPS position errors are correlated over tens of seconds (simulator: 2.5 m, τ 30 s). A
        slowly wandering position error looks like acceleration (~0.3 mg) and, as a normal measurement,
        corrupted the offset estimate in a first version (wrong sign in half the realistic runs). The
        speed (Doppler) errors are white, so v and b are estimated from the speed alone."""
        dd = self._p[0]
        if (z_d - self._d) ** 2 > GATE_SIGMA**2 * (
            dd + sigma_d**2
        ) and self._rejected_in_row < MAX_REJECTED_IN_ROW:
            self.rejected += 1
            self._rejected_in_row += 1
            return
        self._rejected_in_row = 0
        self._d = z_d
        _, _, _, vv, vb, bb = self._p
        self._p = [sigma_d**2, 0.0, 0.0, vv, vb, bb]

    def _update(self, i: int, innovation: float, r: float) -> None:
        """Scalar measurement of state component i (0: d, 1: v)."""
        dd, dv, db, vv, vb, bb = self._p
        col = (dd, dv, db) if i == 0 else (dv, vv, vb)  # P[:, i]
        s = col[i] + r
        k = (col[0] / s, col[1] / s, col[2] / s)
        self._d += k[0] * innovation
        self._v += k[1] * innovation
        self._b += k[2] * innovation
        # P -= K · P[i, :]
        self._p = [
            dd - k[0] * col[0],
            dv - k[0] * col[1],
            db - k[0] * col[2],
            vv - k[1] * col[1],
            vb - k[1] * col[2],
            bb - k[2] * col[2],
        ]

    # ------------------------------------------------------------------ IMU
    def on_imu(self, t: float, imu: VehicleImu | None) -> None:
        self._aligned = imu is not None
        if self._d is None:
            return
        dt = t - self._t if self._t is not None else 0.0
        self._t = t
        if dt <= 0.0:
            return
        if imu is None:  # no orientation yet: coast
            self._d = min(self._d + self._v * dt, self.route.length_m)
            return
        self._b += imu.offset_shift  # the calibration re-solved: same offset, new frame
        a = self._forward_accel(imu) - self._b
        v_new = self._v + a * dt
        self._d = min(self._d + 0.5 * (self._v + max(v_new, 0.0)) * dt, self.route.length_m)
        self._v = max(v_new, 0.0)
        # While turning, the yaw residual leaks lateral acceleration (v·ω) into the forward channel; the
        # filter cannot separate it from b, so it widens the process noise instead of blaming the offset.
        leak = self.turn_noise * YAW_SIGMA * self._v * imu.gyro[2]
        self._predict_covariance(dt, leak * leak * dt)

    def _predict_covariance(self, dt: float, extra_q: float = 0.0) -> None:
        """P = F P Fᵀ + Q with F = [[1, dt, −dt²/2], [0, 1, −dt], [0, 0, 1]]."""
        dd, dv, db, vv, vb, bb = self._p
        h = 0.5 * dt * dt
        r1 = (dd + dt * dv - h * db, dv + dt * vv - h * vb, db + dt * vb - h * bb)
        r2 = (dv - dt * db, vv - dt * vb, vb - dt * bb)
        q = ACCEL_PSD + extra_q / dt  # extra_q: variance added to v over this step
        self._p = [
            r1[0] + dt * r1[1] - h * r1[2] + q * dt**3 / 3.0,
            r1[1] - dt * r1[2] + q * dt * dt / 2.0,
            r1[2],
            r2[1] - dt * r2[2] + q * dt,
            r2[2],
            bb + OFFSET_PSD * dt,
        ]

    def state(self) -> StateEstimate | None:
        est = super().state()
        if est is None:
            return None
        return StateEstimate(
            t=est.t,
            east=est.east,
            north=est.north,
            speed=est.speed,
            heading=est.heading,
            mode=est.mode,
            route_distance=est.route_distance,
            position_std_m=math.sqrt(max(self._p[0], 0.0)),
        )
