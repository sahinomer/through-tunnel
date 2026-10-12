"""Spatial speed planning: what speed does a reasonable driver aim for at each point?

The plan is built on the road's arc-length grid:

1. Preferred speed = cruise speed + slow random variation (Ornstein-Uhlenbeck
   process in distance), so speed is never artificially constant.
2. Curve limit v <= sqrt(a_lat_max / |κ|), with |κ| max-filtered over a short
   preview window so the driver is already at curve speed when the curve starts.
3. Forward pass (acceleration limit) and backward pass (deceleration limit, i.e.
   anticipatory braking before curves) — the classic minimum-time speed-profile
   construction, giving a reference that respects all limits.

The result is a *reference*; the time-domain longitudinal model then follows it
with finite jerk (see ``longitudinal.py``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import maximum_filter1d
from scipy.signal import lfilter

from throughtunnel.road import RoadPath
from throughtunnel.vehicle.config import KMH, DriverConfig


@dataclass(frozen=True)
class SpeedProfile:
    s: NDArray[np.float64]  # uniform arc-length grid [m]
    v_preferred: NDArray[np.float64]  # driver's wish incl. random variation [m/s]
    v_curve: NDArray[np.float64]  # curvature-imposed limit [m/s]
    v_ref: NDArray[np.float64]  # feasible reference speed [m/s]
    a_ref: NDArray[np.float64]  # d(v_ref^2 / 2)/ds = acceleration implied by v_ref [m/s^2]

    @property
    def step(self) -> float:
        return float(self.s[1] - self.s[0])


def ornstein_uhlenbeck(n: int, step: float, std: float, corr_length: float, rng: np.random.Generator):
    """Stationary OU sequence on a uniform grid (exact discretisation)."""
    rho = math.exp(-step / corr_length)
    e = rng.standard_normal(n)
    if std == 0.0:
        return np.zeros(n)
    gain = std * math.sqrt(1.0 - rho**2)
    e[0] /= math.sqrt(1.0 - rho**2)  # so that x[0] ~ N(0, std^2): stationary start
    return lfilter([gain], [1.0, -rho], e)


def plan_speed_profile(path: RoadPath, driver: DriverConfig, rng: np.random.Generator) -> SpeedProfile:
    s = path.grid_s
    step = float(s[1] - s[0])
    kappa = np.abs(path.evaluate(s).curvature)

    v_min = driver.min_speed_kmh * KMH
    v_max = driver.max_speed_kmh * KMH
    variation = ornstein_uhlenbeck(
        len(s), step, driver.speed_variability_kmh * KMH, driver.speed_correlation_length_m, rng
    )
    v_pref = np.clip(driver.cruise_speed_kmh * KMH + variation, v_min, v_max)

    window = 2 * round(driver.curve_preview_m / step) + 1
    kappa_preview = maximum_filter1d(kappa, size=window, mode="nearest")
    v_curve = np.sqrt(driver.max_lateral_accel / np.maximum(kappa_preview, 1e-9))

    v_lim = np.minimum(v_pref, v_curve)
    # The speed floor never overrides the curve limit (a hairpin is crawled, not skidded).
    v_lim = np.maximum(v_lim, np.minimum(v_min, v_curve))

    v = v_lim.copy()
    if driver.initial_speed_kmh is not None:
        v[0] = min(v[0], driver.initial_speed_kmh * KMH)
    two_acc = 2.0 * driver.max_accel * step
    for i in range(1, len(v)):
        v[i] = min(v[i], math.sqrt(v[i - 1] ** 2 + two_acc))
    two_dec = 2.0 * driver.max_decel * step
    for i in range(len(v) - 2, -1, -1):
        v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + two_dec))

    a_ref = np.gradient(0.5 * v**2, step)
    return SpeedProfile(s=s, v_preferred=v_pref, v_curve=v_curve, v_ref=v, a_ref=a_ref)
