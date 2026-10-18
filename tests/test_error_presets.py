"""Sensor-error presets (D56): the levels equal the error-source benchmark's conditions."""

import pytest

from throughtunnel.evaluation import error_sources
from throughtunnel.evaluation.benchmark import Case
from throughtunnel.evaluation.benchmark import run_config as benchmark_run_config
from throughtunnel.scenario import list_presets, load_preset
from throughtunnel.sensors.error_presets import (
    ERROR_PRESETS,
    GNSS_ERROR_FIELDS,
    apply_error_preset,
    matching_error_preset,
)
from throughtunnel.sensors.mounting import MOUNT_PRESETS

CONDITION_OF = {"error_free": "floor", "realistic": "realistic", "hard": "hard"}


@pytest.mark.parametrize("key", sorted(CONDITION_OF))
@pytest.mark.parametrize("traffic", ["free", "stop_and_go"])
def test_preset_equals_the_error_source_condition(key, traffic):
    cond = error_sources.run_config(error_sources.BY_KEY[CONDITION_OF[key]], 3, traffic)
    assert matching_error_preset(cond.imu, cond.gnss, cond.calibration) == key
    # Applied to the benchmark setting, the preset gives the condition's errors exactly (seeds kept).
    real = error_sources.realistic_config(3, traffic)
    imu, gnss, calibration = apply_error_preset(key, real.imu, real.gnss)
    assert imu.errors == cond.imu.errors
    assert gnss == cond.gnss.model_copy(update={"seed": real.gnss.seed})
    assert calibration == cond.calibration
    assert imu.mount == real.imu.mount  # hard's tilted mount is not part of the preset


def test_benchmark_runs_are_realistic_and_bundled_scenarios_good():
    for geometry in ("ladder_2km", *list_presets()):
        cfg = benchmark_run_config(Case(geometry, "flat", "free"), 7)
        assert matching_error_preset(cfg.imu, cfg.gnss, cfg.calibration) == "realistic"
    for pid in list_presets():
        cfg = load_preset(pid)
        assert matching_error_preset(cfg.imu, cfg.gnss, cfg.calibration) == "good"


def test_preset_keeps_everything_but_the_errors():
    cfg = load_preset("synthetic_demo_track")
    imu0 = cfg.imu.model_copy(
        update={"mount": MOUNT_PRESETS["dash_portrait_tilted"], "rate_hz": 100.0,
                "errors": cfg.imu.errors.model_copy(update={"seed": 42})}
    )  # fmt: skip
    gnss0 = cfg.gnss.model_copy(update={"seed": 5, "loss_window_m": 80.0, "reacquisition_delay_s": 6.0})
    for key in ERROR_PRESETS:
        imu, gnss, _ = apply_error_preset(key, imu0, gnss0)
        assert (imu.mount, imu.rate_hz, imu.errors.seed) == (imu0.mount, 100.0, 42)
        assert gnss.model_dump(exclude=set(GNSS_ERROR_FIELDS)) == gnss0.model_dump(
            exclude=set(GNSS_ERROR_FIELDS)
        )
        assert matching_error_preset(imu, gnss, apply_error_preset(key, imu0, gnss0)[2]) == key


def test_a_changed_setting_is_custom():
    cfg = load_preset("synthetic_demo_track")
    imu, gnss, cal = apply_error_preset("realistic", cfg.imu, cfg.gnss)
    noisier = imu.errors.model_copy(
        update={"accel": imu.errors.accel.model_copy(update={"noise_density": 0.01})}
    )
    assert matching_error_preset(imu.model_copy(update={"errors": noisier}), gnss, cal) is None
    assert matching_error_preset(imu, gnss.model_copy(update={"speed_sigma_mps": 0.5}), cal) is None
    assert matching_error_preset(imu, gnss, cal.model_copy(update={"enabled": True})) == "hard"
    assert matching_error_preset(imu, gnss, cal.model_copy(update={"enabled": True, "yaw_deg": 1.0})) is None
    # A disabled error matches whatever its size; an enabled calibration error of zero is none.
    off = ERROR_PRESETS["error_free"]
    imu0, gnss0, _ = apply_error_preset("error_free", cfg.imu, cfg.gnss)
    bigger = imu0.errors.model_copy(
        update={"gyro": imu0.errors.gyro.model_copy(update={"bias_magnitude": 1.0})}
    )
    zero_cal = off.calibration().model_copy(
        update={"enabled": True, "yaw_deg": 0.0, "pitch_deg": 0.0, "roll_deg": 0.0}
    )
    assert matching_error_preset(imu0.model_copy(update={"errors": bigger}), gnss0, zero_cal) == "error_free"
