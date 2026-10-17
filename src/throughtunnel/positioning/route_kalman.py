"""Route-constrained Kalman filters (estimator_plan.md): ``route_kf`` (D51, step 4) and ``route_kf_yaw`` (D52,
step 4.1), two estimators on one implementation.

Phone-only. The same information as ``route_imu`` (GPS + IMU alignment stage, route map, map grade,
portal freeze), but the fixed 5 s speed blend and the unquestioned calibration are replaced by a
filter with the state

    x = [d, v, b, ψ]    d: distance along the route [m], v: speed [m/s], b: forward offset [m/s^2],
                        ψ: yaw residual of the calibrated axes [rad] (``route_kf_yaw`` only)

* Prediction, every IMU sample: the grade-compensated forward specific force a, minus b and minus the
  yaw leak ψ·f_lat (f_lat: the measured lateral channel), is integrated (d += v·dt + ½·â·dt²,
  v += â·dt, â = a − b − ψ·f_lat). The offset b is what the calibration left in the forward channel
  (pitch residual, bias, drift): a random walk.
* ``route_kf`` keeps ψ at 0. A yaw residual leaks lateral acceleration into the forward channel in turns
  (P6); this filter cannot separate it from b and widens the process noise in turns instead (nominal
  0.5° yaw residual). With a calibration yaw error, b absorbs the leak of the approach curves
  (yaw_study.md).
* ``route_kf_yaw`` estimates ψ: observable where f_lat varies, i.e. on curves with GPS speed; a slow
  random walk (the phone may shift in its holder), carried into the tunnel. Robust to a calibration yaw
  error, but no better with realistic sensors (it learns from the same GPS data as the calibration's yaw
  fit; route_kalman_yaw.md).
* Updates, every GPS fix: the fix projected onto the route (d) and the GPS speed (v), each weighted by the
  accuracy the phone reports (solution 1c). Position jumps beyond 4σ are rejected (multipath), at most 3
  fixes in a row. The speed is not gated: a gate there rejected exactly the updates that should correct a
  wrong offset, and the offset never converged (found in validation). b is observed
  through how the speed measurements diverge from the integrated IMU, over all fixes: the offset is fitted
  over the approach, not set by its last fix (solution 1e).
* Portal freeze zone (D46): no speed updates; position updates continue (gated).
* After a GPS outage the first fix resets d and v (as ``route_imu``); b, ψ and their uncertainty are kept.
* Each re-solve of the calibration moves its axes; the stage reports by how much (``offset_shift``,
  ``yaw_shift``), and b and ψ move with it: they describe the residual of the axes in use.
* The v ≥ 0 clamp stays (no standstill information in the phone-only solution, P5).
* ``position_std_m`` is the filter's 1σ along-route uncertainty (for uncertainty-aware announcements).

Tuning (PD6: nominal values of the estimator, never read from the scenario configuration):
* accelerometer noise 180 µg/√Hz (a typical phone MEMS datasheet value; the simulator's preset happens to
  use the same order) plus a model-error term for what the forward channel gets wrong while driving (map
  grade errors and the like): together 0.005 m/s²/√Hz;
* offset random walk 0.05 mg/√s (bias instability of ~0.5 mg over minutes);
* initial offset uncertainty 10 mg and yaw uncertainty 10° (D54): the filter starts when the calibration is
  *first* solved, and a first solution from a short, weakly excited approach is far from converged
  (Eisenhower: up to 37 mg / 26° off; calibration_start_study.md). D51/D52 used 1 mg / 3°, which describe a
  converged calibration; ``offset_sigma0`` / ``yaw_sigma0`` reproduce them;
* yaw random walk 0.01°/√s (a phone settling in its holder: ~0.1° over a 2 min tunnel).
"""

from __future__ import annotations

import math

from throughtunnel.geodesy import STANDARD_GRAVITY
from throughtunnel.observations import GnssFix, RouteMap
from throughtunnel.positioning.alignment import VehicleImu
from throughtunnel.positioning.base import StateEstimate
from throughtunnel.positioning.route_constrained import (
    GNSS_TIMEOUT_S,
    SEARCH_AHEAD_M,
    SEARCH_BACK_M,
    RouteImuDeadReckoning,
)

ACCEL_PSD = 0.005**2  # [(m/s^2)^2/Hz]: sensor noise (180 µg/√Hz) + model error while driving
OFFSET_PSD = (0.05e-3 * STANDARD_GRAVITY) ** 2  # [(m/s^2)^2/s]: random walk of the forward offset
OFFSET_SIGMA0 = 10e-3 * STANDARD_GRAVITY  # [m/s^2]: initial offset uncertainty (fresh calibration, D54)
YAW_SIGMA0 = math.radians(10.0)  # [rad]: initial yaw uncertainty (fresh calibration, D54)
YAW_PSD = math.radians(0.01) ** 2  # [rad^2/s]: random walk of the yaw residual
YAW_SIGMA = math.radians(0.5)  # nominal yaw residual behind ``route_kf``'s turn noise
GATE_SIGMA = 4.0  # position jumps beyond this many σ are rejected (multipath) ...
MAX_REJECTED_IN_ROW = 3  # ... but never more than this many fixes in a row (no lock-out)
MIN_POSITION_SIGMA_M = 1.0
MIN_SPEED_SIGMA_MPS = 0.05


class RouteKalman(RouteImuDeadReckoning):
    name = "route_kf"
    label = "Route + IMU Kalman filter (distance, speed, offset)"
    # Turn noise: process noise from lateral acceleration × a nominal 0.5° yaw residual (1), or none (0)
    turn_noise = 1.0
    # False: ψ fixed at 0 (no prior, no random walk, re-solve yaw shifts ignored)
    yaw_state = False
    # Initial uncertainties of b and ψ (D54); 1 mg / 3° reproduce the first versions (D51, D52; comparison)
    offset_sigma0 = OFFSET_SIGMA0
    yaw_sigma0 = YAW_SIGMA0

    def __init__(self, route: RouteMap) -> None:
        super().__init__(route)
        self._b = 0.0
        self._psi = 0.0
        # covariance of (d, v, b, ψ), full 4 × 4, symmetric
        self._p = [[0.0] * 4 for _ in range(4)]
        self._p[2][2] = self.offset_sigma0**2
        self._p[3][3] = self.yaw_sigma0**2 if self.yaw_state else 0.0
        self.rejected = 0  # gated position fixes (diagnostics)
        self._rejected_in_row = 0

    @property
    def offset(self) -> float:
        """Current estimate of the forward offset b [m/s^2] (diagnostics)."""
        return self._b

    @property
    def yaw(self) -> float:
        """Current estimate of the yaw residual ψ [rad] (diagnostics)."""
        return self._psi

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
            p = self._p
            for i in range(4):  # d and v restart, uncorrelated; the (b, ψ) block is kept
                for j in range(4):
                    if i < 2 or j < 2:
                        p[i][j] = 0.0
            p[0][0], p[1][1] = sigma_d**2, sigma_v**2
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
        p = self._p
        if (z_d - self._d) ** 2 > GATE_SIGMA**2 * (
            p[0][0] + sigma_d**2
        ) and self._rejected_in_row < MAX_REJECTED_IN_ROW:
            self.rejected += 1
            self._rejected_in_row += 1
            return
        self._rejected_in_row = 0
        self._d = z_d
        for j in range(1, 4):
            p[0][j] = p[j][0] = 0.0
        p[0][0] = sigma_d**2

    def _update(self, i: int, innovation: float, r: float) -> None:
        """Scalar measurement of state component i (0: d, 1: v)."""
        p = self._p
        col = [p[j][i] for j in range(4)]  # P[:, i]
        s = col[i] + r
        k = [c / s for c in col]
        self._d += k[0] * innovation
        self._v += k[1] * innovation
        self._b += k[2] * innovation
        self._psi += k[3] * innovation
        # P -= K · P[i, :]
        self._p = [[p[a][c] - k[a] * col[c] for c in range(4)] for a in range(4)]

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
        self._b += imu.offset_shift  # the calibration re-solved: same residuals, new frame
        if self.yaw_state:
            self._psi += imu.yaw_shift
        f_lat = imu.accel[1]
        a = self._forward_accel(imu) - self._b - self._psi * f_lat
        v_new = self._v + a * dt
        self._d = min(self._d + 0.5 * (self._v + max(v_new, 0.0)) * dt, self.route.length_m)
        self._v = max(v_new, 0.0)
        # While turning, a yaw residual leaks lateral acceleration (v·ω) into the forward channel. Without a
        # yaw state the filter cannot separate it from b, so it widens the process noise instead of blaming b.
        leak = self.turn_noise * YAW_SIGMA * self._v * imu.gyro[2]
        self._predict_covariance(dt, f_lat, leak * leak * dt)

    def _predict_covariance(self, dt: float, f_lat: float, extra_q: float = 0.0) -> None:
        """P = F P Fᵀ + Q, F = I + [[0, dt, −h, −h·f_lat], [0, 0, −dt, −dt·f_lat], [0]*4, [0]*4], h = dt²/2.

        b and ψ act only through the effective offset b + ψ·f_lat (w below)."""
        p = self._p
        h = 0.5 * dt * dt
        w = [p[2][j] + f_lat * p[3][j] for j in range(4)]
        rows = (  # F P
            [p[0][j] + dt * p[1][j] - h * w[j] for j in range(4)],
            [p[1][j] - dt * w[j] for j in range(4)],
            p[2],
            p[3],
        )
        out = []  # (F P) Fᵀ
        for r in rows:
            wr = r[2] + f_lat * r[3]
            out.append([r[0] + dt * r[1] - h * wr, r[1] - dt * wr, r[2], r[3]])
        q = ACCEL_PSD + extra_q / dt  # extra_q: variance added to v over this step
        out[0][0] += q * dt**3 / 3.0
        out[0][1] += q * dt * dt / 2.0
        out[1][0] += q * dt * dt / 2.0
        out[1][1] += q * dt
        out[2][2] += OFFSET_PSD * dt
        if self.yaw_state:
            out[3][3] += YAW_PSD * dt
        self._p = out

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
            position_std_m=math.sqrt(max(self._p[0][0], 0.0)),
        )


class RouteKalmanYaw(RouteKalman):
    """``route_kf`` + the yaw residual ψ as a 4th state (D52, step 4.1). The yaw state carries the turn
    uncertainty, so there is no separate turn noise."""

    name = "route_kf_yaw"
    label = "Route + IMU Kalman filter + yaw (distance, speed, offset, yaw)"
    turn_noise = 0.0
    yaw_state = True
