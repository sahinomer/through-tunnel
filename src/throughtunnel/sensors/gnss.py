"""Phone GPS simulation: Android-``Location``-style fixes (D16), not raw GNSS measurements.

What is modelled (first version; refinements are in the roadmap, R4):

* Fixes at a constant rate (default 1 Hz) on the simulation clock, of the **phone** position:
  reference point + lever arm (the antenna is in the phone, PD2).
* Horizontal position error = first-order Gauss-Markov process per axis (east, north), i.e. slowly
  wandering, time-correlated error (typical of phone GPS: multipath and atmospheric errors change over
  tens of seconds), plus a small white component. The process keeps evolving during outages.
* Speed (Doppler) noise is white. Bearing noise is speed noise / speed, so bearings are poor when slow.
* Reported accuracy fields consistent with the model (horizontal accuracy = 68 % radius).
* Availability (``GnssEvents``):
  * fixes on A–B;
  * the loss starts at a random point up to ``loss_window_m`` before the tunnel entrance B, so the
    moment GPS disappears is not an exact entrance marker (PD4);
  * no fixes inside B–C;
  * fixes return ``reacquisition_delay_s`` + U(0, ``reacquisition_jitter_s``) after the true exit
    crossing.
* Not modelled yet: degradation before the entrance, outliers/multipath jumps, poor first fixes after
  reacquisition, latency, altitude.

Randomness: named streams ``gnss.*`` (``GnssConfig.seed``, default = scenario seed), drawn
unconditionally, as for the IMU errors.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

from throughtunnel.geodesy import LocalFrame
from throughtunnel.observations import GnssStream
from throughtunnel.randomness import rng_stream
from throughtunnel.sensors.errors import gauss_markov_series
from throughtunnel.vehicle.truth import GroundTruth

ACCURACY_68_FACTOR = 1.515  # radius containing 68 % of an isotropic 2-D Gaussian, in units of sigma


class GnssConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    rate_hz: float = Field(1.0, gt=0.0, le=10.0)
    position_sigma_m: float = Field(2.5, ge=0.0, description="Gauss-Markov std per horizontal axis")
    position_tau_s: float = Field(30.0, gt=0.0, description="Correlation time of the position error")
    white_sigma_m: float = Field(0.5, ge=0.0, description="White position noise per axis")
    speed_sigma_mps: float = Field(0.2, ge=0.0, description="Speed noise; bearing noise = this / speed")
    loss_window_m: float = Field(30.0, ge=0.0, description="GPS loss starts up to this far before B")
    reacquisition_delay_s: float = Field(3.0, ge=0.0, description="Minimum delay after C before fixes return")
    reacquisition_jitter_s: float = Field(2.0, ge=0.0, description="Extra uniform random delay [0, jitter)")
    seed: int | None = Field(None, ge=0, description="None = the scenario seed")
    # Degradation approaching the tunnel portal (D38), off by default: cuttings and urban canyons in
    # front of portals cause multipath. The extra errors grow linearly over the last
    # ``degradation_length_m`` before B and reach the values below at B.
    portal_degradation: bool = Field(False, description="Degrade the fixes approaching the tunnel entrance")
    degradation_length_m: float = Field(
        150.0, ge=0.0, description="Degradation grows over this distance before B"
    )
    degradation_sigma_m: float = Field(
        8.0, ge=0.0, description="Extra time-correlated position error per axis at B"
    )
    degradation_tau_s: float = Field(5.0, gt=0.0, description="Correlation time of the extra position error")
    degradation_speed_sigma_mps: float = Field(0.5, ge=0.0, description="Extra speed noise at B")
    outlier_probability: float = Field(
        0.05, ge=0.0, le=1.0, description="Chance per fix of a multipath jump at B"
    )
    outlier_sigma_m: float = Field(25.0, ge=0.0, description="Size (std per axis) of a multipath jump")

    def horizontal_sigma_m(self) -> float:
        return math.hypot(self.position_sigma_m, self.white_sigma_m)

    @classmethod
    def ideal(cls) -> GnssConfig:
        return cls(position_sigma_m=0.0, white_sigma_m=0.0, speed_sigma_mps=0.0)


@dataclass(frozen=True)
class GnssEvents:
    """When GPS was actually lost and regained (hidden simulator state)."""

    loss_s: float  # true-path arc length where fixes stop
    loss_t: float  # first time without fixes (inf: never lost)
    reacquire_t: float  # first time fixes may return (inf: never)
    entrance_s: float = math.inf  # true-path arc length of B (anchor of the portal degradation)


def gnss_timestamps(t_end: float, rate_hz: float) -> NDArray[np.float64]:
    n = int(np.floor(t_end * rate_hz + 1e-9)) + 1
    return np.arange(n) / rate_hz


def gauss_markov(
    n: int, dt: float, sigma: float, tau: float, rng: np.random.Generator
) -> NDArray[np.float64]:
    """Stationary first-order Gauss-Markov sequence (exact discretisation), shape (n, 2)."""
    z = rng.standard_normal((n, 2))
    phi = math.exp(-dt / tau)
    out = np.empty((n, 2))
    out[0] = sigma * z[0]
    gain = sigma * math.sqrt(1.0 - phi**2)
    for k in range(1, n):
        out[k] = phi * out[k - 1] + gain * z[k]
    return out


def simulate_gnss(
    kinematics: GroundTruth,
    lever_arm_m: tuple[float, float, float],
    events: GnssEvents,
    config: GnssConfig,
    seed: int,
) -> tuple[GnssStream, GnssStream]:
    """(measured, ideal) fixes. ``kinematics`` is the exact truth at all candidate fix times."""
    s = config.seed if config.seed is not None else seed
    t = kinematics.t
    n = len(t)
    frame: LocalFrame = kinematics.frame

    lever = np.asarray(lever_arm_m, dtype=float)
    pos = kinematics.point_enu(lever)[:, :2]
    vel = kinematics.vel_enu + np.einsum(
        "nij,nj->ni", kinematics.rotation_enu_from_body(), np.cross(kinematics.omega_body, lever)
    )
    speed = np.hypot(vel[:, 0], vel[:, 1])
    s_true = kinematics.s
    bearing = np.mod(np.degrees(np.arctan2(vel[:, 0], vel[:, 1])), 360.0)
    standing = speed < 1e-6  # traffic stop: report the vehicle heading (the velocity direction is undefined)
    if np.any(standing):
        bearing[standing] = np.mod(90.0 - np.degrees(kinematics.yaw[standing]), 360.0)

    # Errors are drawn for every candidate time, unconditionally (independent of availability/enable).
    dt = 1.0 / config.rate_hz
    gm = gauss_markov(n, dt, config.position_sigma_m, config.position_tau_s, rng_stream(s, "gnss.position"))
    white = config.white_sigma_m * rng_stream(s, "gnss.white").standard_normal((n, 2))
    z_speed = rng_stream(s, "gnss.speed").standard_normal(n)
    z_bearing = rng_stream(s, "gnss.bearing").standard_normal(n)
    bearing_sigma_rad = config.speed_sigma_mps / np.maximum(speed, 1.0)
    # Portal degradation: own streams, drawn unconditionally (off = bit-identical to before).
    z_deg = rng_stream(s, "gnss.degradation").standard_normal((n, 2))
    z_deg_speed = rng_stream(s, "gnss.degradation.speed").standard_normal(n)
    u_outlier = rng_stream(s, "gnss.outlier").random(n)
    z_outlier = rng_stream(s, "gnss.outlier.size").standard_normal((n, 2))
    position_extra = np.zeros((n, 2))
    speed_extra = np.zeros(n)
    accuracy_m = np.full(n, max(ACCURACY_68_FACTOR * config.horizontal_sigma_m(), 0.1))
    speed_accuracy = np.full(n, max(config.speed_sigma_mps, 0.01))
    if config.portal_degradation and config.degradation_length_m > 0.0 and math.isfinite(events.entrance_s):
        start = events.entrance_s - config.degradation_length_m
        ramp = np.clip((s_true - start) / config.degradation_length_m, 0.0, 1.0) * (
            s_true <= events.entrance_s
        )
        correlated = gauss_markov_series(z_deg, dt, config.degradation_sigma_m, config.degradation_tau_s)
        jump = (u_outlier < config.outlier_probability * ramp)[:, None] * config.outlier_sigma_m * z_outlier
        position_extra = ramp[:, None] * correlated + jump
        speed_extra = ramp * config.degradation_speed_sigma_mps * z_deg_speed
        extra_speed_sigma = ramp * config.degradation_speed_sigma_mps
        bearing_sigma_rad = np.hypot(config.speed_sigma_mps, extra_speed_sigma) / np.maximum(speed, 1.0)
        # The phone reports the larger correlated error in its accuracy, but not the multipath jumps.
        accuracy_m = ACCURACY_68_FACTOR * np.hypot(
            config.horizontal_sigma_m(), ramp * config.degradation_sigma_m
        )
        accuracy_m = np.maximum(accuracy_m, 0.1)
        speed_accuracy = np.maximum(np.hypot(config.speed_sigma_mps, extra_speed_sigma), 0.01)

    available = (t < events.loss_t) | (t >= events.reacquire_t)
    if not config.enabled:
        available[:] = False

    def stream(position_error, speed_error, bearing_error, source: str, acc, speed_acc) -> GnssStream:
        p = pos + position_error
        lat, lon, _ = frame.to_geodetic(np.column_stack([p, np.zeros(n)]))
        full = GnssStream(
            t=t,
            lat=lat,
            lon=lon,
            horizontal_accuracy_m=acc,
            speed_mps=np.maximum(speed + speed_error, 0.0),
            bearing_deg=np.mod(bearing + bearing_error, 360.0),
            speed_accuracy_mps=speed_acc,
            bearing_accuracy_deg=np.degrees(np.maximum(bearing_sigma_rad, 1e-4)),
            source=source,
        )
        return full.select(available)

    if config.portal_degradation:
        position_error = gm + white + position_extra
        speed_error = config.speed_sigma_mps * z_speed + speed_extra
    else:
        position_error, speed_error = gm + white, config.speed_sigma_mps * z_speed
    measured = stream(
        position_error,
        speed_error,
        np.degrees(bearing_sigma_rad * z_bearing),
        "simulated:measured",
        accuracy_m,
        speed_accuracy,
    )
    zero = np.zeros(n)
    base_acc = np.full(n, max(ACCURACY_68_FACTOR * config.horizontal_sigma_m(), 0.1))
    ideal = stream(
        np.zeros((n, 2)),
        zero,
        zero,
        "simulated:ideal",
        base_acc,
        np.full(n, max(config.speed_sigma_mps, 0.01)),
    )
    return measured, ideal
