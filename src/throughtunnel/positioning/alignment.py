"""Phone-to-vehicle alignment and IMU calibration from data available while GPS works (PD5).

A reusable component (composition, D18): estimators feed it IMU samples and GPS fixes; it returns
the vehicle axes expressed in phone coordinates, plus a gyro bias estimate. It uses only past
observations, so it is causal.

Method (per GPS interval of ~1 s, using the mean phone specific force f̄ and angular rate ω̄):

1. Up axis: direction of the mean specific force (gravity dominates), refined by first subtracting the
   vehicle acceleration predicted from GPS (step 3). On a level road this also absorbs the horizontal
   accelerometer bias: a bias tilts the estimated up axis so the forward specific force is unbiased,
   to first order. With road grade this cancellation breaks (roadmap R1).
2. Forward axis: in the horizontal plane, find the rotation θ that best maps the vehicle acceleration
   predicted from GPS and gyro, (a_long = Δv_GPS/Δt, a_lat = v·ω_up), onto the phone's horizontal
   specific force (2-D Procrustes, means removed). ω_up = up·ω does not depend on θ. θ is observable
   only if the approach contains speed changes or turns ("excitation"); otherwise ``ready`` stays False.
3. Gyro bias about up: integrated gyro heading change minus GPS bearing change, summed over contiguous
   intervals. The sum telescopes, so only the bearing noise at the ends matters.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from throughtunnel.observations import GnssFix

MIN_INTERVALS = 20  # ~20 s of GPS
MIN_EXCITATION = 0.05  # rms predicted vehicle acceleration [m/s^2] needed to observe the yaw angle
MIN_CORRELATION = 0.6  # agreement between predicted and measured horizontal acceleration
MIN_SPEED_FOR_BEARING = 3.0  # [m/s]


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
        self._n = 0
        self._prev: GnssFix | None = None
        self._rows: list[tuple] = []  # (f̄(3), ω̄(3), dt, v0, v1, yaw0, yaw1)

    def add_imu(self, accel, gyro) -> None:
        self._sum_f += accel
        self._sum_w += gyro
        self._n += 1

    def add_fix(self, fix: GnssFix) -> None:
        prev = self._prev
        if prev is not None and self._n > 0 and 0.0 < fix.t - prev.t <= self._max_gap:
            yaw0 = math.radians(90.0 - prev.bearing_deg)
            yaw1 = math.radians(90.0 - fix.bearing_deg)
            self._rows.append(
                (
                    self._sum_f / self._n,
                    self._sum_w / self._n,
                    fix.t - prev.t,
                    prev.speed_mps,
                    fix.speed_mps,
                    yaw0,
                    yaw1,
                )
            )
        self._prev = fix
        self._sum_f = np.zeros(3)
        self._sum_w = np.zeros(3)
        self._n = 0

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
        a_long = (v1 - v0) / dt
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
        bias = 0.0
        if good.sum() >= 3:
            d_gps = np.angle(np.exp(1j * (yaw1 - yaw0)))
            d_gyro = (w @ up) * dt
            bias = float(np.sum((d_gyro - d_gps)[good]) / np.sum(dt[good]))
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
        )


def _unit(v) -> NDArray[np.float64]:
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)
