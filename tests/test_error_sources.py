"""Error-source benchmark (D45): each condition adds exactly one error source; the diagnostics are right."""

import pytest

from throughtunnel.evaluation.benchmark import Case
from throughtunnel.evaluation.benchmark import run_config as benchmark_run_config
from throughtunnel.evaluation.error_sources import (
    BY_KEY,
    CONDITIONS,
    alignment_at_loss,
    run_condition,
    run_config,
)
from throughtunnel.positioning import ESTIMATORS
from throughtunnel.scenario import run_scenario


def _active(cfg) -> set[str]:
    """Which error sources a scenario config switches on."""
    on = set()
    for sensor in ("accel", "gyro"):
        e = getattr(cfg.imu.errors, sensor)
        on |= {f"{sensor}_{k}" for k in ("noise", "bias", "drift") if getattr(e, f"{k}_enabled")}
    g = cfg.gnss
    on |= {"gps_position"} if g.position_sigma_m > 0 or g.white_sigma_m > 0 else set()
    on |= {"gps_speed"} if g.speed_sigma_mps > 0 else set()
    on |= {"gps_degradation"} if g.portal_degradation else set()
    on |= {"calibration"} if cfg.calibration.enabled else set()
    on |= {"mount"} if cfg.imu.mount.label != "aligned" else set()
    return on


EXPECTED = {
    "floor": set(), "acc_noise": {"accel_noise"}, "acc_bias": {"accel_bias"}, "acc_drift": {"accel_drift"},
    "gyro_noise": {"gyro_noise"}, "gyro_bias": {"gyro_bias"}, "gyro_drift": {"gyro_drift"},
    "mount_dash": {"mount"}, "cal_pitch_0.1": {"calibration"}, "cal_pitch_0.5": {"calibration"},
    "cal_yaw_2": {"calibration"}, "cal_roll_0.5": {"calibration"}, "gps_position": {"gps_position"},
    "gps_speed": {"gps_speed"}, "gps_degr": {"gps_degradation"}, "gps_degr_harsh": {"gps_degradation"},
}  # fmt: skip


@pytest.mark.parametrize("key", list(EXPECTED))
def test_each_condition_adds_exactly_one_error_source(key):
    assert _active(run_config(BY_KEY[key], 0, "free")) == EXPECTED[key]


def test_combined_conditions_and_pairing():
    assert len(CONDITIONS) == 18
    real = run_config(BY_KEY["realistic"], 3, "stop_and_go")
    bench = benchmark_run_config(Case("ladder_5km", "flat", "stop_and_go"), 3)
    assert real.imu == bench.imu and real.gnss == bench.gnss and real.traffic == bench.traffic
    hard = run_config(BY_KEY["hard"], 3, "free")
    assert hard.calibration.enabled and hard.imu.mount.label == "dash_portrait_tilted"
    drives = {run_config(c, 3, "free").seed for c in CONDITIONS} | {real.seed}
    assert drives == {1003}  # same drive in every condition (paired)


def test_forward_offset_diagnostic():
    """A 0.1° pitch error leaks g·sin(0.1°) ≈ 1.7 mg; an accelerometer bias is cancelled by the levelling."""
    pitch = alignment_at_loss(run_scenario(run_config(BY_KEY["cal_pitch_0.1"], 0, "free")))
    assert abs(pitch["forward_offset_mg"]) == pytest.approx(1.71, abs=0.05)
    assert abs(pitch["align_pitch_deg"]) == pytest.approx(0.1, abs=0.005)
    bias = alignment_at_loss(run_scenario(run_config(BY_KEY["acc_bias"], 0, "free")))
    assert abs(bias["forward_offset_mg"]) < 0.1 and abs(bias["align_pitch_deg"]) > 0.1


def test_floor_is_near_perfect():
    records = run_condition("floor", "free", [0])
    assert len(records) == len(ESTIMATORS)
    by = {r["estimator"]: r for r in records}
    for name in ("dr_calibrated", "dr_filtered", "route_imu", "route_vspeed"):
        assert by[name]["err_5km_m"] < 5.0, name
