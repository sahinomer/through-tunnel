"""Spatial speed planning: what speed does a reasonable driver aim for at each point?

The plan is built on the road's arc-length grid:

1. Preferred speed = cruise speed + slow random variation, so speed is never
   artificially constant. The variation is a smooth stationary Gaussian process
   (squared-exponential covariance) in distance. A smooth process matters: e.g.
   an Ornstein-Uhlenbeck path is nowhere differentiable, and its slope would
   turn into jittery, jerk-saturated acceleration.
2. Curve limit v <= sqrt(a_lat_max / |κ|), with |κ| max-filtered over a short
   preview window so the driver is already at curve speed when the curve starts.
3. Forward pass (acceleration limit) and backward pass (deceleration limit, i.e.
   anticipatory braking before curves) — the classic minimum-time speed-profile
   construction. It uses only ``planning_margin`` of the accel/decel limits, so
   the jerk-limited tracker keeps authority to catch up when it lags.
4. Traffic (optional, D37): speed zones lower the cap (with their own gentle braking and
   acceleration ramps). Stops are not part of the spatial plan: standing still is time-based and is
   handled by the longitudinal model.

The result is a *reference*; the time-domain longitudinal model then follows it
with finite jerk (see ``longitudinal.py``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import maximum_filter1d
from scipy.signal import fftconvolve

from throughtunnel.road import RoadPath
from throughtunnel.vehicle.config import KMH, DriverConfig
from throughtunnel.vehicle.traffic import TrafficPlan, zone_speed_cap


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


def smooth_random_process(
    n: int, step: float, std: float, length_scale: float, rng: np.random.Generator
) -> NDArray[np.float64]:
    """Stationary Gaussian process on a uniform grid with covariance std^2 exp(-d^2 / (2 L^2)).

    Built as white noise convolved with a Gaussian kernel of width L / sqrt(2)
    (the convolution of two such kernels has width L), normalised so that the
    marginal standard deviation is exactly ``std``. Realisations are smooth
    (infinitely differentiable), with derivative std = std / L.
    """
    sigma_k = length_scale / math.sqrt(2.0) / step  # kernel width in samples
    half = math.ceil(4.0 * sigma_k)
    k = np.arange(-half, half + 1)
    kernel = np.exp(-0.5 * (k / sigma_k) ** 2)
    kernel /= math.sqrt(np.sum(kernel**2))
    noise = rng.standard_normal(n + 2 * half)  # always drawn: stream use independent of std
    if std == 0.0:
        return np.zeros(n)
    return std * fftconvolve(noise, kernel, mode="valid")


def plan_speed_profile(
    path: RoadPath, driver: DriverConfig, rng: np.random.Generator, traffic: TrafficPlan | None = None
) -> SpeedProfile:
    s = path.grid_s
    step = float(s[1] - s[0])
    kappa = np.abs(path.evaluate(s).curvature)

    v_min = driver.min_speed_kmh * KMH
    v_max = driver.max_speed_kmh * KMH
    variation = smooth_random_process(
        len(s), step, driver.speed_variability_kmh * KMH, driver.speed_correlation_length_m, rng
    )
    v_pref = np.clip(driver.cruise_speed_kmh * KMH + variation, v_min, v_max)

    window = 2 * round(driver.curve_preview_m / step) + 1
    kappa_preview = maximum_filter1d(kappa, size=window, mode="nearest")
    v_curve = np.sqrt(driver.max_lateral_accel / np.maximum(kappa_preview, 1e-9))

    v_lim = np.minimum(v_pref, v_curve)
    # The speed floor never overrides the curve limit (a hairpin is crawled, not skidded).
    v_lim = np.maximum(v_lim, np.minimum(v_min, v_curve))
    for zone in traffic.zones if traffic is not None else ():  # traffic may go below the driver's floor
        variation = smooth_random_process(
            len(s),
            step,
            zone.variation_mps,
            zone.variation_length_m,
            np.random.default_rng(zone.variation_seed),
        )
        v_lim = np.minimum(v_lim, zone_speed_cap(s, zone, variation))

    v = v_lim.copy()
    if driver.initial_speed_kmh is not None:
        v[0] = min(v[0], driver.initial_speed_kmh * KMH)
    two_acc = 2.0 * driver.planning_margin * driver.max_accel * step
    for i in range(1, len(v)):
        v[i] = min(v[i], math.sqrt(v[i - 1] ** 2 + two_acc))
    two_dec = 2.0 * driver.planning_margin * driver.max_decel * step
    for i in range(len(v) - 2, -1, -1):
        v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + two_dec))

    a_ref = np.gradient(0.5 * v**2, step)
    return SpeedProfile(s=s, v_preferred=v_pref, v_curve=v_curve, v_ref=v, a_ref=a_ref)
