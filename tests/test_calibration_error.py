"""Calibration error (D34, D40): the orientation the alignment stage uses vs. the actual mount.

The error is applied to the alignment stage's orientation, before any sample reaches an estimator; it
must not touch the simulation, and its effect must follow the analytic error mechanisms (gravity
leakage for pitch, lateral-acceleration leakage for yaw, negligible roll on a flat road).
"""

import math

import numpy as np
import pytest
from pydantic import ValidationError

from throughtunnel.evaluation.experiment import compare_estimators
from throughtunnel.evaluation.metrics import evaluate_track
from throughtunnel.positioning import ESTIMATORS, portal, run_estimator
from throughtunnel.positioning.alignment import with_orientation_error
from throughtunnel.positioning.mount_estimation import ALIGNED
from throughtunnel.routing.synthetic import Straight, synthetic_route
from throughtunnel.scenario import (
    ScenarioConfig,
    TunnelConfig,
    load_preset,
    run_scenario,
    scenario_from_json,
    truth_at,
    with_calibration,
)
from throughtunnel.sensors.errors import ImuErrorConfig
from throughtunnel.sensors.gnss import GnssConfig
from throughtunnel.sensors.mounting import CalibrationErrorConfig

G = 9.80


def error(yaw=0.0, pitch=0.0, roll=0.0) -> CalibrationErrorConfig:
    return CalibrationErrorConfig(enabled=True, yaw_deg=yaw, pitch_deg=pitch, roll_deg=roll)


def ideal(cfg: ScenarioConfig):
    imu = cfg.imu.model_copy(update={"errors": ImuErrorConfig.ideal()})
    return run_scenario(cfg.model_copy(update={"imu": imu, "gnss": GnssConfig.ideal()}))


def run(res, name, cal):
    obs = res.observations()
    return run_estimator(ESTIMATORS[name](obs.route), obs, calibration_error=cal.rotation_error())


def last_fix_before_loss(res) -> float:
    return float(res.gnss.t[res.gnss.t < res.gnss_events.loss_t][-1])


@pytest.fixture(scope="module")
def demo():
    return run_scenario(load_preset("synthetic_demo_track"))


@pytest.fixture(scope="module")
def ideal_demo():
    return ideal(load_preset("synthetic_demo_track"))


@pytest.fixture(scope="module")
def ideal_straight():
    route = synthetic_route([Straight(6000.0)], "straight", 100.0)
    return ideal(ScenarioConfig(route=route, tunnel=TunnelConfig(entrance_m=1500.0, exit_m=4500.0)))


# ------------------------------------------------------------------ configuration and separation
def test_config_defaults_and_validation():
    off = CalibrationErrorConfig()
    assert not off.enabled and off.rotation_error() is None and off.describe() == "off"
    assert np.allclose(error().rotation_error(), np.eye(3))
    with pytest.raises(ValidationError):
        CalibrationErrorConfig(enabled=True, pitch_deg=30.0)


def test_scenario_round_trip_and_older_files_default_to_off(demo):
    cfg = demo.config.model_copy(update={"calibration": error(yaw=2.0, pitch=0.3, roll=-1.0)})
    assert scenario_from_json(cfg.model_dump_json()).calibration == cfg.calibration
    v5 = demo.config.model_dump(exclude={"calibration"}) | {"schema_version": 5}
    assert ScenarioConfig.model_validate(v5).calibration == CalibrationErrorConfig()


def test_calibration_error_changes_no_simulated_data(demo):
    """Actual mounting and every observation stay identical; only the estimators' assumption changes."""
    erroneous = run_scenario(
        demo.config.model_copy(update={"calibration": error(yaw=5.0, pitch=1.0, roll=2.0)})
    )
    assert erroneous.config.imu.mount == demo.config.imu.mount
    assert np.array_equal(erroneous.imu.accel, demo.imu.accel) and np.array_equal(
        erroneous.imu.gyro, demo.imu.gyro
    )
    assert np.array_equal(erroneous.gnss.lat, demo.gnss.lat)
    assert erroneous.observations().route.length_m == demo.observations().route.length_m


def test_zero_error_is_bit_identical_to_no_error(demo):
    off = compare_estimators(demo)
    zero = compare_estimators(with_calibration(demo, error()))
    for a, b in zip(off.tracks, zero.tracks, strict=True):
        assert np.array_equal(a.east, b.east) and np.array_equal(a.speed, b.speed), a.name


def test_orientation_error_rotates_the_vehicle_axes():
    tilted = with_orientation_error(ALIGNED, error(pitch=10.0).rotation_error())
    s, c = math.sin(math.radians(10.0)), math.cos(math.radians(10.0))
    assert np.allclose(tilted.forward, [c, 0.0, -s])  # + pitch: assumed forward nose-down
    assert np.allclose(np.column_stack([tilted.forward, tilted.left, tilted.up]).T
                       @ np.column_stack([tilted.forward, tilted.left, tilted.up]), np.eye(3))  # fmt: skip
    assert with_orientation_error(ALIGNED, None) is ALIGNED


# ------------------------------------------------------------------ error mechanisms
@pytest.mark.parametrize("pitch", [0.1, 0.5])
def test_pitch_error_leaks_gravity_into_the_forward_channel(ideal_straight, pitch):
    """Along-track error = -1/2 g sin(pitch) tau^2, tau = time since the last fix; ideal sensors."""
    res, cal = ideal_straight, error(pitch=pitch)
    tau = res.sections.exit_t - last_fix_before_loss(res)
    predicted = -0.5 * G * math.sin(math.radians(pitch)) * tau**2
    dr = evaluate_track(run(res, "dr_calibrated", cal), res).summary["exit_along_m"]
    assert dr == pytest.approx(predicted, rel=0.02)
    # GPS speed blending during the approach settles to a speed lag of ~4 g sin(pitch) (5 s filter, 1 Hz),
    # which the route estimator carries into the tunnel: worse than plain dead reckoning, never better.
    # Blending stops at the portal freeze zone (D46), so the leak also acts for the Δ seconds between the
    # last blended fix and the last fix (position still follows the fixes there).
    route = evaluate_track(run(res, "route_imu", cal), res).summary["exit_along_m"]
    t_zone = float(
        np.interp(res.sections.entrance_s - portal.FREEZE_BEFORE_ENTRANCE_M, res.motion.s, res.motion.t)
    )
    delta = last_fix_before_loss(res) - float(res.gnss.t[res.gnss.t < t_zone][-1])
    g_pitch = G * math.sin(math.radians(pitch))
    assert route == pytest.approx(predicted - 4.0 * g_pitch * tau - g_pitch * delta * tau, rel=0.03)


@pytest.mark.parametrize("yaw", [2.0, -2.0, 5.0])
def test_yaw_error_leaks_lateral_acceleration_into_speed(ideal_demo, yaw):
    """Speed error = sin(yaw) * integral(a_lat) + (cos(yaw) - 1) * integral(a_long) since the last fix."""
    res = ideal_demo
    track = run(res, "dr_calibrated", error(yaw=yaw))
    t_f = last_fix_before_loss(res)
    k = int(np.flatnonzero(track.t < res.sections.exit_t)[-1])
    m = (res.truth.t >= t_f) & (res.truth.t <= track.t[k])
    d = math.radians(yaw)
    predicted = math.sin(d) * np.trapezoid(res.truth.accel_lat[m], res.truth.t[m]) + (
        math.cos(d) - 1.0
    ) * np.trapezoid(res.truth.accel_long[m], res.truth.t[m])
    speed_error = track.speed[k] - truth_at(res, [track.t[k]]).speed[0]
    assert abs(predicted) > 0.3  # the demo tunnel curves, so the effect is not trivially zero
    assert speed_error == pytest.approx(predicted, rel=0.02)


def test_yaw_error_does_not_matter_on_a_straight_road(ideal_straight):
    base = evaluate_track(run(ideal_straight, "dr_calibrated", CalibrationErrorConfig()), ideal_straight)
    yawed = evaluate_track(run(ideal_straight, "dr_calibrated", error(yaw=5.0)), ideal_straight)
    assert abs(yawed.summary["exit_total_m"] - base.summary["exit_total_m"]) < 1.0


def test_roll_error_is_negligible_on_a_flat_road(ideal_demo):
    """Roll tilts only the assumed up axis: the yaw rate is scaled by cos(roll) and nothing leaks forward."""
    for name in ("dr_calibrated", "route_imu"):
        base = evaluate_track(run(ideal_demo, name, CalibrationErrorConfig()), ideal_demo).summary
        rolled = evaluate_track(run(ideal_demo, name, error(roll=2.0)), ideal_demo).summary
        assert abs(rolled["exit_total_m"] - base["exit_total_m"]) < 2.0, name


def test_naive_reference_ignores_the_imu_orientation(demo):
    """route_hold uses no IMU, so it is the control of every calibration experiment."""
    a = run(demo, "route_hold", CalibrationErrorConfig())
    b = run(demo, "route_hold", error(yaw=5.0, pitch=1.0, roll=2.0))
    assert np.array_equal(a.route_distance, b.route_distance)
