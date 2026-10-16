"""Mount estimation: phone-to-vehicle orientation and gyro bias from data available while GPS works
(PD5). A reusable alignment *method* (D40): the GPS + IMU alignment stage (``alignment.py``) feeds it
IMU samples and GPS fixes; it returns the vehicle axes expressed in phone coordinates, plus a gyro bias
estimate. It uses only past observations, so it is causal.

Method (per GPS interval of ~1 s, using the mean phone specific force f̄ and angular rate ω̄):

1. Up axis: direction of the mean specific force (gravity dominates), refined by first subtracting the
   vehicle acceleration predicted from GPS (step 3). On a level road this also absorbs the horizontal
   accelerometer bias: a bias tilts the estimated up axis so the forward specific force is unbiased,
   to first order. With road grade this cancellation breaks (roadmap R1): the levelling calibrates in
   the mean approach grade. If the map provides the grade (D39), the stage passes the grade angle at
   each fix and the result reports the mean over the intervals it used (``calibration_grade_angle``),
   so the estimators can remove the grade *change* later.
2. Forward axis: in the horizontal plane, find the rotation θ that best maps the vehicle acceleration
   predicted from GPS and gyro, (a_long = Δv_GPS/Δt, a_lat = v·ω_up), onto the phone's horizontal
   specific force (2-D Procrustes, means removed). ω_up = up·ω does not depend on θ. θ is observable
   only if the approach contains speed changes or turns ("excitation"); otherwise ``ready`` stays False.
3. Gyro bias about up: within each contiguous stretch of fast-enough GPS intervals, the accumulated
   difference "integrated gyro heading - GPS bearing" grows as b·t plus the bearing noise of the latest
   fix. b is the weighted least-squares slope (weights = 1 / reported bearing accuracy², one free offset
   per stretch). An earlier version used only the end points of the approach: on routes with a slow
   turn, where the bearing is noisy, it left up to 0.08 °/s of bias, i.e. hundreds of metres of
   cross-track error after 150 s.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from throughtunnel.observations import GnssFix
from throughtunnel.positioning.map_grade import GRAVITY

MIN_INTERVALS = 20  # ~20 s of GPS
MIN_EXCITATION = 0.05  # rms predicted vehicle acceleration [m/s^2] needed to observe the yaw angle
MIN_CORRELATION = 0.6  # agreement between predicted and measured horizontal acceleration
MIN_SPEED_FOR_BEARING = 5.0  # [m/s]; GPS bearing noise grows as 1/speed
MAX_SAMPLE_SPACING_S = 0.1  # IMU samples further apart than this are a gap, not the sample spacing


@dataclass(frozen=True)
class Alignment:
    up: NDArray[np.float64]  # vehicle up axis in phone coordinates (unit)
    forward: NDArray[np.float64]  # vehicle forward axis in phone coordinates (unit)
    left: NDArray[np.float64]
    gyro_bias_up: float  # rad/s, to subtract from up · gyro
    ready: bool  # enough excitation for a trustworthy forward axis
    intervals: int
    excitation: float  # rms of predicted horizontal vehicle acceleration [m/s^2]
    correlation: float  # cosine similarity predicted vs measured horizontal acceleration
    calibration_grade_angle: float = 0.0  # mean map grade angle over the intervals used [rad] (D39)


ALIGNED = Alignment(
    up=np.array([0.0, 0.0, 1.0]),
    forward=np.array([1.0, 0.0, 0.0]),
    left=np.array([0.0, 1.0, 0.0]),
    gyro_bias_up=0.0,
    ready=True,
    intervals=0,
    excitation=math.nan,
    correlation=math.nan,
)


class MountAlignmentEstimator:
    """Accumulates per-GPS-interval IMU means and solves for the vehicle axes on request."""

    def __init__(self, max_gap_s: float = 1.6) -> None:
        self._max_gap = max_gap_s
        self._sum_f = np.zeros(3)
        self._sum_w = np.zeros(3)
        self._weight = 0.0  # time covered by the samples of the current interval [s]
        self._last: tuple | None = None  # (t, accel, gyro, h) of the last sample
        self._covered_to: float | None = None  # end of the time the samples so far stand for
        self._prev: GnssFix | None = None
        self._prev_grade_angle = 0.0
        self._rows: list[tuple] = []  # (f̄(3), ω̄(3), dt, v0, v1, yaw0, yaw1, t, σ_bearing, grade angle)

    def add_imu(self, accel, gyro, t: float) -> None:
        """One IMU sample at time ``t``. Samples stand for contiguous time: each one from where the
        previous one ended up to t + h/2 (h = sample spacing; after a fix without an adjacent sample,
        from the fix time). So the interval means are time averages over exactly the GPS interval (F2,
        D48), and a sample that straddles a fix is split between the two intervals. Before, each
        interval took its samples up to and including the fix time, a half-sample lag that left
        −(h/2)·(a_last − a_first)/T in the levelling (the stop-and-go floor, residual_study.md)."""
        accel, gyro = np.asarray(accel, dtype=float), np.asarray(gyro, dtype=float)
        h = t - self._last[0] if self._last is not None else 0.0
        if not 0.0 < h <= MAX_SAMPLE_SPACING_S:
            h = self._last[3] if self._last is not None else 0.0  # after a gap: the previous spacing
        end = t + 0.5 * h
        start = self._covered_to if self._covered_to is not None else t - 0.5 * h
        weight = max(end - start, 0.0)
        self._sum_f += weight * accel
        self._sum_w += weight * gyro
        self._weight += weight
        self._covered_to = end
        self._last = (t, accel, gyro, h)

    def add_fix(self, fix: GnssFix, grade_angle: float = 0.0) -> None:
        """``grade_angle``: the map's road grade angle at this fix [rad] (0 without map grade)."""
        # The covered time beyond the fix (or the gap up to it) belongs to the next interval. Without
        # an adjacent sample (start, or after a gap) the next interval simply starts at the fix.
        carry_f, carry_w, carry = np.zeros(3), np.zeros(3), 0.0
        if self._last is not None and abs(self._last[0] - fix.t) <= max(self._last[3], 1e-9):
            _, accel, gyro, _ = self._last
            carry = self._covered_to - fix.t
            carry_f, carry_w = carry * accel, carry * gyro
            self._sum_f -= carry_f
            self._sum_w -= carry_w
            self._weight -= carry
        else:
            self._covered_to = fix.t
        prev = self._prev
        if prev is not None and self._weight > 0.0 and 0.0 < fix.t - prev.t <= self._max_gap:
            yaw0 = math.radians(90.0 - prev.bearing_deg)
            yaw1 = math.radians(90.0 - fix.bearing_deg)
            self._rows.append(
                (
                    self._sum_f / self._weight,
                    self._sum_w / self._weight,
                    fix.t - prev.t,
                    prev.speed_mps,
                    fix.speed_mps,
                    yaw0,
                    yaw1,
                    fix.t,
                    max(math.radians(fix.bearing_accuracy_deg), 1e-4),
                    0.5 * (self._prev_grade_angle + grade_angle),
                )
            )
        self._prev = fix
        self._prev_grade_angle = grade_angle
        self._sum_f, self._sum_w, self._weight = carry_f, carry_w, carry

    @property
    def intervals(self) -> int:
        return len(self._rows)

    def solve(self) -> Alignment | None:
        if len(self._rows) < 3:
            return None
        f = np.array([r[0] for r in self._rows])
        w = np.array([r[1] for r in self._rows])
        dt = np.array([r[2] for r in self._rows])
        v0 = np.array([r[3] for r in self._rows])
        v1 = np.array([r[4] for r in self._rows])
        # Predicted forward specific force: the speed change plus the gravity of the grade change since the
        # mean grade the levelling absorbs (F3, D48; zero without map grade). Its mean is zero, so the
        # levelling still absorbs the mean grade; but on a grade ramp inside the window the yaw fit no
        # longer mistakes the ramp's gravity for acceleration (0.34° yaw error with ideal sensors before,
        # which leaked the approach's lateral acceleration into the levelling, residual_study.md).
        grade = np.array([r[9] for r in self._rows])
        a_long = (v1 - v0) / dt + GRAVITY * np.sin(grade - grade.mean())
        v_mid = 0.5 * (v0 + v1)

        up = _unit(f.sum(axis=0))
        forward = left = None
        corr = excitation = 0.0
        for _ in range(3):
            w_up = w @ up
            a_lat = v_mid * w_up
            e1 = _unit(np.cross(up, [0.0, 0.0, 1.0]) if abs(up[2]) < 0.9 else np.cross(up, [1.0, 0.0, 0.0]))
            e2 = np.cross(up, e1)
            h = f - np.outer(f @ up, up)
            h1, h2 = h @ e1, h @ e2
            a1, a2 = a_long - a_long.mean(), a_lat - a_lat.mean()
            h1c, h2c = h1 - h1.mean(), h2 - h2.mean()
            theta = math.atan2(float(np.sum(h2c * a1 - h1c * a2)), float(np.sum(h1c * a1 + h2c * a2)))
            forward = math.cos(theta) * e1 + math.sin(theta) * e2
            left = np.cross(up, forward)
            # Refine "up": remove the predicted vehicle acceleration before averaging the specific force.
            predicted = np.outer(a_long, forward) + np.outer(a_lat, left)
            up = _unit((f - predicted).sum(axis=0))
            ra1 = a1 * math.cos(theta) - a2 * math.sin(theta)
            ra2 = a1 * math.sin(theta) + a2 * math.cos(theta)
            denom = math.sqrt(float(np.sum(h1c**2 + h2c**2) * np.sum(a1**2 + a2**2))) or 1.0
            corr = float(np.sum(h1c * ra1 + h2c * ra2)) / denom
            excitation = float(np.sqrt(np.mean(a1**2 + a2**2)))
        forward = _unit(forward - (forward @ up) * up)
        left = np.cross(up, forward)

        # Gyro bias about up: integrated gyro yaw change vs GPS bearing change (fast enough intervals).
        yaw0 = np.array([r[5] for r in self._rows])
        yaw1 = np.array([r[6] for r in self._rows])
        good = (v0 > MIN_SPEED_FOR_BEARING) & (v1 > MIN_SPEED_FOR_BEARING)
        bias = _gyro_bias_regression(
            r=(w @ up) * dt - np.angle(np.exp(1j * (yaw1 - yaw0))),
            dt=dt,
            t_end=np.array([r[7] for r in self._rows]),
            sigma=np.array([r[8] for r in self._rows]),
            good=good,
        )
        ready = len(self._rows) >= MIN_INTERVALS and excitation >= MIN_EXCITATION and corr >= MIN_CORRELATION
        return Alignment(
            up=up,
            forward=forward,
            left=left,
            gyro_bias_up=bias,
            ready=ready,
            intervals=len(self._rows),
            excitation=excitation,
            correlation=corr,
            calibration_grade_angle=float(np.mean([r[9] for r in self._rows])),
        )


def _gyro_bias_regression(r, dt, t_end, sigma, good) -> float:
    """Weighted slope of the accumulated gyro-minus-GPS heading over contiguous stretches."""
    num = den = 0.0
    run: list[int] = []

    def close(idx: list[int]) -> tuple[float, float]:
        if len(idx) < 3:
            return 0.0, 0.0
        acc = np.cumsum(r[idx])
        time = np.cumsum(dt[idx])
        wts = 1.0 / sigma[idx] ** 2
        tm, am = np.average(time, weights=wts), np.average(acc, weights=wts)
        return float(np.sum(wts * (time - tm) * (acc - am))), float(np.sum(wts * (time - tm) ** 2))

    for k in range(len(r)):
        contiguous = run and abs((t_end[k] - dt[k]) - t_end[run[-1]]) < 1e-6
        if good[k] and (not run or contiguous):
            run.append(k)
            continue
        n, d = close(run)
        num, den = num + n, den + d
        run = [k] if good[k] else []
    n, d = close(run)
    num, den = num + n, den + d
    return num / den if den > 0 else 0.0


def _unit(v) -> NDArray[np.float64]:
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)
