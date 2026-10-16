"""Sensor imperfections: Gaussian white noise, constant bias and optional bias drift (phone frame).

    measured = ideal + b + n_k,      n_k ~ N(0, σ² I),   σ = N_d · sqrt(f_s)

Noise is specified as a **noise density** N_d (units/√Hz), the white-noise coefficient used in
datasheets and Allan-variance analysis (velocity/angle random walk). The per-sample standard
deviation then follows from the sample rate f_s: a faster sensor has more noise per sample but the
same noise after averaging over a fixed time (the Allan deviation at τ = 1 s equals N_d). This is
what makes changing the sample rate physically meaningful.

Optional bias drift (D38, off by default): a slowly wandering component on top of the constant bias,
modelled per axis as a stationary first-order Gauss-Markov process (std ``drift_sigma``, correlation
time ``drift_tau_s``). It stands for in-run bias instability and temperature drift, which a one-off
calibration during the approach cannot remove.

The bias is constant during a run (a turn-on bias). It is either given explicitly as a vector, or
drawn with the configured magnitude in a random (seeded) direction.

Randomness: each source (accel noise, accel bias direction, gyro noise, gyro bias direction) has its
own named stream, and the standard-normal draws happen whether or not a source is enabled. So
toggling or rescaling one source never changes the realisation of another, and changing a magnitude
rescales the same noise pattern.

Defaults are typical consumer-MEMS / smartphone-class values (order of magnitude from common phone
IMU datasheets, e.g. Bosch BMI-series and ST LSM6-series): accelerometer ~180 µg/√Hz, gyroscope
~0.007 °/s/√Hz, and residual offsets after factory/OS calibration of order 10 mg and 0.1 °/s.
Real devices vary widely.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, model_validator

from throughtunnel.geodesy import STANDARD_GRAVITY  # g-based unit conversions (mg, µg)
from throughtunnel.randomness import rng_stream

MG = 1e-3 * STANDARD_GRAVITY  # 1 mg in m/s^2
UG = 1e-6 * STANDARD_GRAVITY  # 1 µg in m/s^2
DEG = math.pi / 180.0  # 1 degree in rad
MDPS = 1e-3 * DEG  # 1 milli-degree per second in rad/s

DEFAULT_ACCEL_NOISE_DENSITY = 180.0 * UG  # m/s^2/√Hz
DEFAULT_ACCEL_BIAS = 10.0 * MG  # m/s^2
DEFAULT_GYRO_NOISE_DENSITY = 7.0 * MDPS  # rad/s/√Hz
DEFAULT_GYRO_BIAS = 0.1 * DEG  # rad/s
# In-run bias drift (D38), off by default: a slowly wandering component on top of the constant bias,
# e.g. from temperature changes of a phone in a car mount. Order-of-magnitude assumptions.
DEFAULT_ACCEL_DRIFT = 0.5 * MG  # m/s^2 (std of the drifting part)
DEFAULT_GYRO_DRIFT = 5.0 * MDPS  # rad/s
DEFAULT_DRIFT_TAU_S = 300.0  # correlation time [s]


class SensorErrorConfig(BaseModel):
    """Error model of one 3-axis sensor, in SI units (m/s^2 or rad/s)."""

    model_config = ConfigDict(frozen=True)

    noise_enabled: bool = True
    noise_density: float = Field(0.0, ge=0, description="White-noise density per axis [SI unit / √Hz]")
    bias_enabled: bool = True
    bias_magnitude: float = Field(0.0, ge=0, description="Norm of the constant bias vector [SI unit]")
    bias_vector: tuple[float, float, float] | None = Field(
        None, description="Explicit bias in phone axes [SI unit]; overrides magnitude + random direction"
    )
    drift_enabled: bool = Field(False, description="Add a slowly wandering bias (first-order Gauss-Markov)")
    drift_sigma: float = Field(0.0, ge=0, description="Std of the bias drift per axis [SI unit]")
    drift_tau_s: float = Field(
        DEFAULT_DRIFT_TAU_S, gt=0, description="Correlation time of the bias drift [s]"
    )

    def noise_std(self, rate_hz: float) -> float:
        """Per-sample, per-axis standard deviation at the given sample rate."""
        return self.noise_density * math.sqrt(rate_hz)


def _default_accel() -> SensorErrorConfig:
    return SensorErrorConfig(
        noise_density=DEFAULT_ACCEL_NOISE_DENSITY,
        bias_magnitude=DEFAULT_ACCEL_BIAS,
        drift_sigma=DEFAULT_ACCEL_DRIFT,
    )


def _default_gyro() -> SensorErrorConfig:
    return SensorErrorConfig(
        noise_density=DEFAULT_GYRO_NOISE_DENSITY,
        bias_magnitude=DEFAULT_GYRO_BIAS,
        drift_sigma=DEFAULT_GYRO_DRIFT,
    )


class ImuErrorConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    accel: SensorErrorConfig = Field(default_factory=_default_accel)
    gyro: SensorErrorConfig = Field(default_factory=_default_gyro)
    seed: int | None = Field(
        None,
        ge=0,
        description="Sensor-error seed; None = the scenario seed. Vary it for Monte-Carlo runs "
        "over sensor errors on an identical drive.",
    )

    @model_validator(mode="before")
    @classmethod
    def _drift_defaults(cls, data: object) -> object:
        """Files written before D38 (all presets) have no drift fields: give each sensor its own default
        drift size, so that switching drift on has an effect (it stays off unless enabled)."""
        if isinstance(data, dict):
            for key, default in (("accel", DEFAULT_ACCEL_DRIFT), ("gyro", DEFAULT_GYRO_DRIFT)):
                sensor = data.get(key)
                if isinstance(sensor, dict) and "drift_sigma" not in sensor:
                    data = {**data, key: {**sensor, "drift_sigma": default}}
        return data

    @classmethod
    def ideal(cls) -> ImuErrorConfig:
        """All error sources disabled (magnitudes kept at the defaults, so they can be re-enabled)."""
        off = {"noise_enabled": False, "bias_enabled": False, "drift_enabled": False}
        return cls(accel=_default_accel().model_copy(update=off), gyro=_default_gyro().model_copy(update=off))


@dataclass(frozen=True)
class SensorErrorRealization:
    """The error values actually applied in a run. Hidden simulation truth: not part of the observation."""

    bias: NDArray[np.float64]  # (3,) applied constant bias, zero if disabled
    noise_std: float  # applied per-sample per-axis std, zero if disabled
    drift: NDArray[np.float64] | None = None  # (N, 3) applied bias drift, None if disabled


def gauss_markov_series(z: NDArray[np.float64], dt: float, sigma: float, tau: float) -> NDArray[np.float64]:
    """Stationary first-order Gauss-Markov sequence from standard-normal draws ``z`` (rows = samples).

    x[0] = sigma z[0];  x[k] = phi x[k-1] + sigma sqrt(1 - phi^2) z[k],  phi = exp(-dt / tau) (exact)."""
    from scipy.signal import lfilter

    phi = math.exp(-dt / tau)
    gain = sigma * math.sqrt(1.0 - phi**2)
    out = np.empty_like(z)
    out[0] = sigma * z[0]
    if len(z) > 1:
        out[1:] = lfilter([gain], [1.0, -phi], z[1:], axis=0, zi=phi * out[:1])[0]
    return out


def apply_sensor_errors(
    ideal: NDArray[np.float64],
    rate_hz: float,
    config: SensorErrorConfig,
    rng_noise: np.random.Generator,
    rng_bias: np.random.Generator,
    rng_drift: np.random.Generator | None = None,
) -> tuple[NDArray[np.float64], SensorErrorRealization]:
    z = rng_noise.standard_normal(ideal.shape)  # drawn unconditionally (see module docstring)
    direction = rng_bias.standard_normal(3)
    direction /= np.linalg.norm(direction)
    if config.bias_vector is not None:
        bias = np.asarray(config.bias_vector, dtype=float)
    else:
        bias = config.bias_magnitude * direction
    bias = bias if config.bias_enabled else np.zeros(3)
    sigma = config.noise_std(rate_hz) if config.noise_enabled else 0.0
    measured = ideal + bias + sigma * z
    drift = None
    if rng_drift is not None:
        z_drift = rng_drift.standard_normal(ideal.shape)  # drawn unconditionally, like the others
        if config.drift_enabled and config.drift_sigma > 0.0 and len(ideal):
            drift = gauss_markov_series(z_drift, 1.0 / rate_hz, config.drift_sigma, config.drift_tau_s)
            measured = measured + drift
    return measured, SensorErrorRealization(bias=bias, noise_std=sigma, drift=drift)


@dataclass(frozen=True)
class ImuErrorRealization:
    accel: SensorErrorRealization
    gyro: SensorErrorRealization


def apply_imu_errors(
    accel: NDArray[np.float64],
    gyro: NDArray[np.float64],
    rate_hz: float,
    config: ImuErrorConfig,
    seed: int,
) -> tuple[NDArray[np.float64], NDArray[np.float64], ImuErrorRealization]:
    """Add the configured errors to ideal accelerometer and gyroscope samples."""
    s = config.seed if config.seed is not None else seed
    acc, acc_real = apply_sensor_errors(
        accel, rate_hz, config.accel, rng_stream(s, "imu.accel.noise"), rng_stream(s, "imu.accel.bias"),
        rng_stream(s, "imu.accel.drift"),
    )  # fmt: skip
    gyr, gyr_real = apply_sensor_errors(
        gyro, rate_hz, config.gyro, rng_stream(s, "imu.gyro.noise"), rng_stream(s, "imu.gyro.bias"),
        rng_stream(s, "imu.gyro.drift"),
    )  # fmt: skip
    return acc, gyr, ImuErrorRealization(accel=acc_real, gyro=gyr_real)
