"""Physical consistency and driver-constraint tests for the vehicle simulation."""

import numpy as np
import pytest

from throughtunnel.road import RoadConfig
from throughtunnel.routing.synthetic import Arc, Corner, Straight, synthetic_route
from throughtunnel.scenario import ScenarioConfig, list_presets, load_preset, run_scenario
from throughtunnel.vehicle.config import DRIVER_PRESETS, KMH, DriverConfig
from throughtunnel.vehicle.speed_profile import smooth_random_process


@pytest.fixture(scope="module")
def demo_result():
    return run_scenario(load_preset("synthetic_demo_track"))


def central_diff(y: np.ndarray, dt: float) -> np.ndarray:
    return (y[2:] - y[:-2]) / (2.0 * dt)


# ------------------------------------------------------------------ self-consistency of ground truth
def test_speed_is_derivative_of_distance(demo_result):
    tr = demo_result.truth
    dt = 1.0 / tr.sample_rate_hz
    # s(t) is piecewise cubic: the central difference carries the Taylor term j * dt^2 / 6.
    bound = demo_result.config.driver.max_jerk * dt**2 / 6
    assert np.abs(central_diff(tr.s, dt) - tr.speed[1:-1]).max() <= bound + 1e-9


def test_acceleration_is_derivative_of_speed(demo_result):
    tr = demo_result.truth
    dt = 1.0 / tr.sample_rate_hz
    # Piecewise-constant jerk: the central difference differs from a(t) by at most j_max * dt / 2.
    err = np.abs(central_diff(tr.speed, dt) - tr.accel_long[1:-1])
    assert err.max() <= demo_result.config.driver.max_jerk * dt / 2 + 1e-9


def test_jerk_is_derivative_of_acceleration(demo_result):
    tr = demo_result.truth
    dt = 1.0 / tr.sample_rate_hz
    assert np.allclose(np.diff(tr.accel_long) / dt, tr.jerk[:-1], atol=1e-6)


def test_yaw_rate_is_derivative_of_heading(demo_result):
    tr = demo_result.truth
    dt = 1.0 / tr.sample_rate_hz
    assert np.abs(central_diff(tr.yaw, dt) - tr.yaw_rate[1:-1]).max() < 2e-5


def test_turning_relations(demo_result):
    tr = demo_result.truth
    assert np.allclose(tr.yaw_rate, tr.curvature * tr.speed)
    assert np.allclose(tr.accel_lat, tr.speed * tr.yaw_rate)


def test_position_second_derivative_matches_body_acceleration(demo_result):
    """End-to-end: differentiate the ENU trajectory twice, rotate into the body frame,
    and compare with the reported longitudinal and lateral acceleration."""
    tr = demo_result.truth
    dt = 1.0 / tr.sample_rate_hz
    ax = (tr.x[2:] - 2 * tr.x[1:-1] + tr.x[:-2]) / dt**2
    ay = (tr.y[2:] - 2 * tr.y[1:-1] + tr.y[:-2]) / dt**2
    c, s = np.cos(tr.yaw[1:-1]), np.sin(tr.yaw[1:-1])
    a_fwd = c * ax + s * ay
    a_left = -s * ax + c * ay
    assert np.abs(a_fwd - tr.accel_long[1:-1]).max() < 0.02
    assert np.abs(a_left - tr.accel_lat[1:-1]).max() < 0.02
    assert np.allclose(tr.acc_enu[1:-1, 0], ax, atol=0.02)
    assert np.allclose(tr.acc_enu[1:-1, 1], ay, atol=0.02)


def test_body_frame_vectors(demo_result):
    tr = demo_result.truth
    rot = tr.rotation_enu_from_body()
    assert np.allclose(np.einsum("nij,nj->ni", rot, tr.acc_body), tr.acc_enu, atol=1e-12)
    assert np.allclose(tr.omega_body[:, 2], tr.yaw_rate)
    assert np.allclose(tr.omega_body[:, :2], 0.0)
    assert np.allclose(tr.acc_body[:, 2], 0.0)


def test_geodetic_track_matches_enu(demo_result):
    tr = demo_result.truth
    enu = tr.frame.to_enu(tr.lat, tr.lon, tr.alt)
    assert np.abs(enu[:, 0] - tr.x).max() < 1e-6
    assert np.abs(enu[:, 1] - tr.y).max() < 1e-6


# ------------------------------------------------------------------ controlled scenarios
def test_constant_speed_on_circle():
    """Steady cornering: yaw rate v/R and lateral acceleration v^2/R, no longitudinal acceleration."""
    radius, v = 200.0, 15.0
    route = synthetic_route([Straight(300.0), Arc(radius, 180.0), Straight(300.0)], "circle", 2.0)
    driver = DriverConfig(
        cruise_speed_kmh=v / KMH,
        speed_variability_kmh=0.0,
        initial_speed_kmh=v / KMH,
        max_lateral_accel=5.0,
    )
    cfg = ScenarioConfig(route=route, driver=driver, road=RoadConfig(smoothing_wavelength_m=60.0))
    tr = run_scenario(cfg).truth
    assert np.allclose(tr.speed, v, atol=1e-9)
    assert np.allclose(tr.accel_long, 0.0, atol=1e-9)
    inside = (tr.s > 360.0) & (tr.s < 300.0 + radius * np.pi - 60.0)
    assert tr.yaw_rate[inside] == pytest.approx(v / radius, rel=0.03)
    assert tr.accel_lat[inside] == pytest.approx(v**2 / radius, rel=0.03)
    straight = tr.s < 200.0  # >= 100 m before the arc: only the smoother's transition tail remains
    assert np.abs(tr.yaw_rate[straight]).max() < np.radians(0.03)
    # Left turn => positive yaw rate and leftward (positive) lateral acceleration.
    assert np.all(tr.yaw_rate[inside] > 0) and np.all(tr.accel_lat[inside] > 0)


def test_straight_line_acceleration_phase():
    """From a slow entry speed the driver accelerates at the planned rate (planning_margin * max_accel):
    a constant-acceleration phase where v is linear and s quadratic in t."""
    route = synthetic_route([Straight(2000.0)], "straight", 100.0)
    driver = DriverConfig(cruise_speed_kmh=90.0, speed_variability_kmh=0.0, initial_speed_kmh=20.0)
    tr = run_scenario(ScenarioConfig(route=route, driver=driver)).truth
    assert tr.speed[0] == pytest.approx(20.0 * KMH)
    assert tr.accel_long.max() <= driver.max_accel + 1e-9
    a_plan = driver.planning_margin * driver.max_accel
    plateau = np.flatnonzero((np.abs(tr.accel_long - a_plan) < 0.05 * a_plan) & (np.abs(tr.jerk) < 0.01))
    i0, i1 = plateau[0], plateau[-1]
    assert i1 - i0 > 500  # several seconds of (nearly) constant acceleration
    t = tr.t[i0 : i1 + 1] - tr.t[i0]
    # v and s follow from integrating a(t) (trapezoid on a smooth signal), linear/quadratic in t.
    a, v = tr.accel_long[i0 : i1 + 1], tr.speed[i0 : i1 + 1]
    v_int = v[0] + np.concatenate([[0.0], np.cumsum(0.5 * (a[1:] + a[:-1]) * np.diff(t))])
    s_int = tr.s[i0] + np.concatenate([[0.0], np.cumsum(0.5 * (v[1:] + v[:-1]) * np.diff(t))])
    assert np.allclose(v, v_int, atol=1e-5)
    assert np.allclose(tr.s[i0 : i1 + 1], s_int, atol=1e-4)
    assert np.allclose(v, v[0] + a_plan * t, rtol=0.03)
    assert tr.speed[-1] == pytest.approx(90.0 * KMH, rel=0.02)


# ------------------------------------------------------------------ driver constraints on all presets
@pytest.mark.parametrize("preset", sorted(list_presets()))
@pytest.mark.parametrize("style", sorted(DRIVER_PRESETS))
def test_driver_limits_respected(preset, style):
    driver = DRIVER_PRESETS[style]
    cfg = load_preset(preset).model_copy(update={"driver": driver})
    res = run_scenario(cfg)
    tr = res.truth
    assert tr.accel_long.max() <= driver.max_accel + 1e-9
    assert tr.accel_long.min() >= -driver.max_decel - 1e-9
    assert np.abs(tr.jerk).max() <= driver.max_jerk + 1e-9
    assert np.abs(tr.accel_lat).max() <= 1.06 * driver.max_lateral_accel
    assert tr.speed.max() <= driver.max_speed_kmh * KMH * 1.01
    # Never stops: stays above the floor (or the curve limit if that is lower).
    floor = np.minimum(driver.min_speed_kmh * KMH, res.profile.v_curve.min())
    assert tr.speed.min() >= 0.95 * floor > 0
    # Speed genuinely varies (not a constant-speed toy).
    assert tr.speed.std() > 0.2
    assert tr.s[-1] <= res.path.length_m < tr.s[-1] + tr.speed[-1] / tr.sample_rate_hz + 1e-9


def test_smooth_random_process_statistics():
    std, length = 2.0, 50.0
    x = smooth_random_process(400_000, 1.0, std, length, np.random.default_rng(5))
    assert x.std() == pytest.approx(std, rel=0.05)
    lag = int(length)
    corr = np.corrcoef(x[:-lag], x[lag:])[0, 1]
    assert corr == pytest.approx(np.exp(-0.5), abs=0.05)  # squared-exponential covariance
    # Smooth (differentiable) realisations: derivative std = std / L. A rough process
    # (e.g. Ornstein-Uhlenbeck) would give a far larger, step-size dependent value.
    assert np.diff(x).std() == pytest.approx(std / length, rel=0.1)


def test_steady_driving_is_smooth():
    """In a gentle tunnel the driver should rarely hit the jerk limit (no bang-bang jitter)."""
    tr = run_scenario(load_preset("seattle_sr99_tunnel")).truth
    driver = load_preset("seattle_sr99_tunnel").driver
    assert np.mean(np.abs(tr.jerk) > 0.9 * driver.max_jerk) < 0.02
    assert np.abs(tr.accel_long).max() < 1.0


@pytest.mark.parametrize("style", sorted(DRIVER_PRESETS))
def test_sharp_urban_corners_respect_lateral_limit(style):
    """Intersections between long straights: hard braking into tight (R ~ 10 m) turns."""
    route = synthetic_route(
        [Straight(300.0), Corner(90.0), Straight(200.0), Corner(-90.0), Straight(150.0), Corner(-60.0),
         Straight(300.0)],
        "urban",
        100.0,
    )  # fmt: skip
    driver = DRIVER_PRESETS[style]
    tr = run_scenario(ScenarioConfig(route=route, driver=driver)).truth
    assert np.abs(tr.accel_lat).max() <= 1.06 * driver.max_lateral_accel
    assert tr.accel_long.min() >= -driver.max_decel - 1e-9
    assert tr.speed.min() > 0.0
