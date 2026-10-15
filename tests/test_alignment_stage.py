"""Alignment stage (D40): the pipeline observations → alignment → estimator.

The stage is causal, loses no information, carries the calibration error, and can be swapped; the
estimators take only finished vehicle-axis data and no error argument.
"""

import inspect
import math
from dataclasses import replace

import numpy as np
import pytest

from throughtunnel.observations import ImuStream, Observations
from throughtunnel.positioning import ALIGNMENTS, ESTIMATORS, align_imu, run_estimator, run_estimators
from throughtunnel.positioning.alignment import DeclaredAlignment, GpsImuAlignment
from throughtunnel.scenario import MapDataConfig, load_preset, run_scenario, with_map_data
from throughtunnel.sensors.mounting import CalibrationErrorConfig


@pytest.fixture(scope="module")
def demo():
    return run_scenario(load_preset("synthetic_demo_track"))


def test_estimators_take_no_calibration_error():
    for name, cls in ESTIMATORS.items():
        assert list(inspect.signature(cls.__init__).parameters) == ["self", "route"], name
        assert cls.alignment is None or cls.alignment in ALIGNMENTS, name


@pytest.mark.parametrize("name", sorted(ALIGNMENTS))
def test_alignment_stage_is_causal(demo, name):
    obs = demo.observations()
    t_star = 0.5 * (demo.sections.entrance_t + demo.sections.exit_t)
    after = obs.imu.t > t_star
    accel, gyro = obs.imu.accel.copy(), obs.imu.gyro.copy()
    accel[after] += 1.0
    gyro[after] += 0.1
    lat = obs.gnss.lat.copy()
    lat[obs.gnss.t > t_star] += 1e-3
    imu = ImuStream(t=obs.imu.t, accel=accel, gyro=gyro)
    perturbed = Observations(imu, replace(obs.gnss, lat=lat), obs.route)
    a = align_imu(ALIGNMENTS[name](obs.route), obs)
    b = align_imu(ALIGNMENTS[name](obs.route), perturbed)
    n = int(np.searchsorted(obs.imu.t, t_star, side="right"))
    assert a[:n] == b[:n]
    assert a[n:] != b[n:]


def test_stage_output_is_the_measured_data_rotated(demo):
    """Nothing filtered: declared = the phone samples as they are; GPS + IMU = an exact rotation (norms
    kept), with only the gyro bias estimate removed from the yaw rate."""
    obs = demo.observations()
    declared = align_imu(DeclaredAlignment(obs.route), obs)
    phone = zip(declared, obs.imu.accel.tolist(), obs.imu.gyro.tolist(), strict=True)
    assert all(s.accel == tuple(a) and s.gyro == tuple(g) for s, a, g in phone)
    stage = GpsImuAlignment(obs.route)
    out = align_imu(stage, obs)
    k = next(i for i, s in enumerate(out) if s is not None)
    assert k > 0 and all(s is None for s in out[:k])  # no orientation before the calibration is ready
    s = out[-1]
    assert np.linalg.norm(s.accel) == pytest.approx(np.linalg.norm(obs.imu.accel[-1]), rel=1e-12)
    gyro = np.array(s.gyro) + np.array([0.0, 0.0, stage.alignment.gyro_bias_up])
    assert np.linalg.norm(gyro) == pytest.approx(np.linalg.norm(obs.imu.gyro[-1]), rel=1e-12)


def test_calibration_error_is_applied_in_the_stage(demo):
    obs = demo.observations()
    err = CalibrationErrorConfig(enabled=True, yaw_deg=2.0, pitch_deg=0.5, roll_deg=-1.0).rotation_error()
    stage = GpsImuAlignment(obs.route, err)
    out = align_imu(stage, obs)
    clean = align_imu(GpsImuAlignment(obs.route), obs)
    s, c = out[-1], clean[-1]
    assert np.allclose(np.array(s.accel), err.T @ np.array(c.accel), atol=1e-9)
    est = ESTIMATORS["dr_calibrated"](obs.route)
    track = run_estimator(est, obs, calibration_error=err)
    assert not np.array_equal(track.east, run_estimator(ESTIMATORS["dr_calibrated"](obs.route), obs).east)


def test_alignment_can_be_swapped_per_estimator(demo):
    """dr_raw is the same dead reckoning as dr_calibrated behind the declared stage."""
    obs = demo.observations()
    swapped = ESTIMATORS["dr_calibrated"](obs.route)
    swapped.alignment = "declared"
    a = run_estimator(swapped, obs)
    b = run_estimator(ESTIMATORS["dr_raw"](obs.route), obs)
    assert np.array_equal(a.east, b.east) and np.array_equal(a.speed, b.speed)


def test_a_shared_stage_gives_the_same_tracks_as_separate_runs(demo):
    obs = demo.observations()
    shared = run_estimators([cls(obs.route) for cls in ESTIMATORS.values()], obs)
    for track, cls in zip(shared, ESTIMATORS.values(), strict=True):
        alone = run_estimator(cls(obs.route), obs)
        assert np.array_equal(track.east, alone.east) and np.array_equal(track.north, alone.north), cls.name


def test_grade_lookup_after_an_outage_finds_the_vehicle():
    """Regression: after a long outage the first fix lies far beyond the pre-outage search window; the
    window grows with the time since the last fix, so the calibration gets the true grade."""
    from throughtunnel.evaluation.slope_study import PROFILES, profile_config
    from throughtunnel.scenario import truth_at
    from throughtunnel.vehicle.traffic import TrafficConfig

    cfg = load_preset("eisenhower_tunnel")
    up2 = next(p for p in PROFILES if p.key == "up2")
    traffic = TrafficConfig(scenario="stop_and_go")
    res = run_scenario(cfg.model_copy(update={"road_profile": profile_config(cfg, up2), "traffic": traffic}))
    res = with_map_data(res, MapDataConfig(road_grade=True))
    stage = GpsImuAlignment(res.route_map)
    gaps = np.diff(res.gnss.t)
    k = int(np.argmax(gaps)) + 1  # first fix after the outage
    assert gaps[k - 1] > 300.0
    for i in range(k + 1):
        stage.on_gnss(res.gnss.fix(i))
    grade = res.route_map.grade_at(stage._d)
    assert grade == pytest.approx(truth_at(res, [res.gnss.t[k]]).grade[0], abs=1e-3)
    assert math.isfinite(grade)
