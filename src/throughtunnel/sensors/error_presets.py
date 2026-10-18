"""Sensor-error presets: one-click levels that set all phone sensor errors together (UI, D56).

A preset sets the IMU errors, the GPS errors (incl. the degradation before the portal) and the injected
calibration error. It leaves alone everything that is not a sensor error: the phone mount (the
calibration removes it), the outage geometry (GPS loss window, reacquisition delay), rates, seeds,
Earth rotation, the car's speed reading (reference only) and the map data.

Three levels equal the error-source benchmark's conditions (tested):

* ``error_free`` = ``floor``: no IMU, GPS or calibration error;
* ``realistic`` = ``realistic``, the benchmark setting: smartphone IMU noise and bias, in-run bias drift,
  GPS noise and the degradation before the portal;
* ``hard`` = ``hard`` without its tilted mount: realistic + the default calibration error
  (yaw 2°, pitch 0.5°, roll 0.5°).

``good`` lies between: realistic IMU noise and bias but no drift, clean GPS up to the portal, no
calibration error. It is what the bundled scenario files contain.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from throughtunnel.sensors.errors import ImuErrorConfig, SensorErrorConfig
from throughtunnel.sensors.gnss import GnssConfig
from throughtunnel.sensors.imu import ImuConfig
from throughtunnel.sensors.mounting import CalibrationErrorConfig

# The GPS fields a preset sets; the others (enabled, rate, outage geometry, seed) stay as they are.
GNSS_ERROR_FIELDS = (
    "position_sigma_m",
    "position_tau_s",
    "white_sigma_m",
    "speed_sigma_mps",
    "portal_degradation",
    "degradation_length_m",
    "degradation_sigma_m",
    "degradation_tau_s",
    "degradation_speed_sigma_mps",
    "outlier_probability",
    "outlier_sigma_m",
)


@dataclass(frozen=True)
class ErrorPreset:
    key: str
    label: str
    description: str
    imu_errors: bool  # noise and constant bias of both sensors
    imu_drift: bool  # in-run bias drift
    gps_noise: bool
    gps_degradation: bool  # before the portal
    cal_error: bool

    def imu(self) -> ImuErrorConfig:
        errors = ImuErrorConfig() if self.imu_errors else ImuErrorConfig.ideal()
        drift = {"drift_enabled": self.imu_drift}
        return errors.model_copy(
            update={
                "accel": errors.accel.model_copy(update=drift),
                "gyro": errors.gyro.model_copy(update=drift),
            }
        )

    def gnss(self) -> GnssConfig:
        base = GnssConfig() if self.gps_noise else GnssConfig.ideal()
        return base.model_copy(update={"portal_degradation": self.gps_degradation})

    def calibration(self) -> CalibrationErrorConfig:
        return CalibrationErrorConfig(enabled=self.cal_error)


ERROR_PRESETS: dict[str, ErrorPreset] = {
    p.key: p
    for p in (
        ErrorPreset(
            "error_free", "Error-free", "No IMU, GPS or calibration error: the algorithm floor.",
            imu_errors=False, imu_drift=False, gps_noise=False, gps_degradation=False, cal_error=False,
        ),
        ErrorPreset(
            "good", "Good",
            "A well-behaved phone on a good day: smartphone IMU noise and bias (the calibration removes the "
            "bias), no temperature drift, clean GPS up to the portal, a clean calibration.",
            imu_errors=True, imu_drift=False, gps_noise=True, gps_degradation=False, cal_error=False,
        ),
        ErrorPreset(
            "realistic", "Realistic",
            "The benchmark setting: Good + in-run IMU bias drift + GPS degradation (multipath) before the "
            "portal.",
            imu_errors=True, imu_drift=True, gps_noise=True, gps_degradation=True, cal_error=False,
        ),
        ErrorPreset(
            "hard", "Hard",
            "Realistic + a calibration error (yaw 2°, pitch 0.5°, roll 0.5°). The benchmark's hard condition "
            "also tilts the mount, which the calibration removes.",
            imu_errors=True, imu_drift=True, gps_noise=True, gps_degradation=True, cal_error=True,
        ),
    )
}  # fmt: skip
DEFAULT_ERROR_PRESET = "realistic"


def apply_error_preset(
    key: str, imu: ImuConfig, gnss: GnssConfig
) -> tuple[ImuConfig, GnssConfig, CalibrationErrorConfig]:
    """``imu`` and ``gnss`` with the preset's errors (seeds and all non-error settings kept), and the
    preset's calibration error."""
    preset = ERROR_PRESETS[key]
    errors = preset.imu().model_copy(update={"seed": imu.errors.seed})
    template = preset.gnss()
    gnss = gnss.model_copy(update={f: getattr(template, f) for f in GNSS_ERROR_FIELDS})
    return imu.model_copy(update={"errors": errors}), gnss, preset.calibration()


def matching_error_preset(
    imu: ImuConfig, gnss: GnssConfig, calibration: CalibrationErrorConfig
) -> str | None:
    """The preset these settings equal, or None (custom). Disabled errors match whatever their size."""
    for key, preset in ERROR_PRESETS.items():
        if (
            _same_imu(imu.errors, preset.imu())
            and _same_gnss(gnss, preset.gnss())
            and _same_calibration(calibration, preset.calibration())
        ):
            return key
    return None


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-12)  # tolerates the UI's unit round trips


def _same_sensor(a: SensorErrorConfig, b: SensorErrorConfig) -> bool:
    pairs = (
        (a.noise_enabled, b.noise_enabled, ((a.noise_density, b.noise_density),)),
        (a.bias_enabled, b.bias_enabled, ((a.bias_magnitude, b.bias_magnitude),)),
        (a.drift_enabled, b.drift_enabled, ((a.drift_sigma, b.drift_sigma), (a.drift_tau_s, b.drift_tau_s))),
    )
    for on_a, on_b, sizes in pairs:
        if on_a != on_b or (on_a and not all(_close(x, y) for x, y in sizes)):
            return False
    return not (a.bias_enabled and a.bias_vector is not None)


def _same_imu(a: ImuErrorConfig, b: ImuErrorConfig) -> bool:
    return _same_sensor(a.accel, b.accel) and _same_sensor(a.gyro, b.gyro)


def _same_gnss(a: GnssConfig, b: GnssConfig) -> bool:
    fields = GNSS_ERROR_FIELDS if a.portal_degradation else GNSS_ERROR_FIELDS[:5]
    if a.position_sigma_m == 0 and b.position_sigma_m == 0:  # no correlated error: its τ does not matter
        fields = tuple(f for f in fields if f != "position_tau_s")
    return all(
        getattr(a, f) == getattr(b, f)
        if isinstance(getattr(a, f), bool)
        else _close(getattr(a, f), getattr(b, f))
        for f in fields
    )


def _same_calibration(a: CalibrationErrorConfig, b: CalibrationErrorConfig) -> bool:
    def angles(c: CalibrationErrorConfig) -> tuple[float, float, float]:
        return (c.yaw_deg, c.pitch_deg, c.roll_deg) if c.enabled else (0.0, 0.0, 0.0)

    return all(_close(x, y) for x, y in zip(angles(a), angles(b), strict=True))
