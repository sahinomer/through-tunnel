"""Smartphone IMU physics: gravity, motion, mounting rotation, lever arm, Earth rotation.

These tests validate the *ideal* sensor model, so they use error-free sensors sampled at the
simulation rate (one IMU sample per ground-truth sample). Sample-rate handling and sensor errors are
covered in test_imu_rate_and_errors.py.
"""

from dataclasses import fields

import numpy as np
import pytest
from helpers import stationary_truth

from throughtunnel.geodesy import LocalFrame
from throughtunnel.routing.synthetic import Straight, synthetic_route
from throughtunnel.scenario import ScenarioConfig, load_preset, run_scenario, with_imu_config
from throughtunnel.sensors.errors import ImuErrorConfig
from throughtunnel.sensors.imu import OMEGA_EARTH, ImuConfig, ImuStream, ideal_imu, normal_gravity
from throughtunnel.sensors.mounting import MOUNT_PRESETS, PhoneMount, describe_phone_axes, euler_zyx
from throughtunnel.vehicle.config import KMH, DriverConfig

TILTED = PhoneMount(label="test", yaw_deg=37.0, pitch_deg=-22.0, roll_deg=71.0, lever_arm_m=(1.6, 0.35, 0.8))


def ideal_at_sim_rate(**kwargs) -> ImuConfig:
    """Error-free IMU sampled at the 100 Hz simulation rate (aligned mount unless overridden)."""
    return ImuConfig(rate_hz=100.0, errors=ImuErrorConfig.ideal(), **kwargs)


@pytest.fixture(scope="module")
def demo():
    cfg = load_preset("synthetic_demo_track")
    assert cfg.sample_rate_hz == 100.0
    return run_scenario(cfg.model_copy(update={"imu": ideal_at_sim_rate()}))


@pytest.fixture(scope="module")
def sloped_demo():
    """The demo drive on an underwater-tunnel profile (descent, bottom, climb; grades up to ~4 %)."""
    from throughtunnel.road_profile import RoadProfileConfig, point_distances, template_heights

    cfg = load_preset("synthetic_demo_track")
    length = run_scenario(cfg).route_map.length_m
    d = point_distances(length, cfg.tunnel.entrance_m, cfg.tunnel.exit_m)
    z = template_heights("underwater", d, cfg.tunnel.entrance_m, cfg.tunnel.exit_m, 0.06)
    profile = RoadProfileConfig(points=tuple(zip(d.tolist(), z.tolist(), strict=True)))
    return run_scenario(cfg.model_copy(update={"imu": ideal_at_sim_rate(), "road_profile": profile}))


def central_diff(y: np.ndarray, dt: float) -> np.ndarray:
    return (y[2:] - y[:-2]) / (2.0 * dt)


# ------------------------------------------------------------------ mounting / frames
def test_mount_rotations_are_proper_rotations():
    rng = np.random.default_rng(0)
    mounts = [*MOUNT_PRESETS.values(), TILTED]
    angles = rng.uniform([-180, -90, -180], [180, 90, 180], size=(20, 3))
    mounts += [PhoneMount(yaw_deg=a, pitch_deg=b, roll_deg=c) for a, b, c in angles]
    for m in mounts:
        r = m.rotation_body_from_phone()
        assert np.allclose(r.T @ r, np.eye(3), atol=1e-12)
        assert np.linalg.det(r) == pytest.approx(1.0)


def test_euler_convention():
    assert np.allclose(euler_zyx(np.pi / 2, 0, 0) @ [1, 0, 0], [0, 1, 0])  # yaw: x -> y (left)
    assert np.allclose(euler_zyx(0, np.pi / 2, 0) @ [1, 0, 0], [0, 0, -1])  # pitch: nose down
    assert np.allclose(euler_zyx(0, 0, np.pi / 2) @ [0, 1, 0], [0, 0, 1])  # roll: y -> z


def test_preset_axis_directions():
    expected = {
        "aligned": {"x": "forward", "y": "left", "z": "up"},
        "flat_portrait": {"x": "right", "y": "forward", "z": "up"},
        "dash_portrait": {"x": "right", "y": "up", "z": "backward"},
        "dash_landscape": {"x": "up", "y": "left", "z": "backward"},
    }
    for name, axes in expected.items():
        assert describe_phone_axes(MOUNT_PRESETS[name].rotation_body_from_phone()) == axes


# ------------------------------------------------------------------ gravity
def test_normal_gravity():
    assert normal_gravity(0.0) == pytest.approx(9.7803253, abs=1e-6)
    assert normal_gravity(90.0) == pytest.approx(9.8321849, abs=1e-6)
    assert normal_gravity(45.0) == pytest.approx(9.80620, abs=1e-4)


@pytest.mark.parametrize(
    ("mount", "axis", "sign"),
    [
        ("aligned", 2, 1),  # flat, screen up: +g on z (Android convention)
        ("flat_portrait", 2, 1),
        ("dash_portrait", 1, 1),  # upright portrait: +g on y
        ("dash_landscape", 0, 1),  # upright landscape, top to the left: +g on x
    ],
)
def test_stationary_phone_measures_gravity_only(mount, axis, sign):
    truth = stationary_truth(lat=47.6, yaw_deg=33.0)
    imu = ideal_imu(truth, ImuConfig(mount=MOUNT_PRESETS[mount]))
    expected = np.zeros(3)
    expected[axis] = sign * normal_gravity(47.6)
    assert np.allclose(imu.accel, expected, atol=1e-12)
    assert np.allclose(imu.gyro, 0.0, atol=1e-15)


def test_face_down_phone_reads_minus_g():
    imu = ideal_imu(stationary_truth(), ImuConfig(mount=PhoneMount(roll_deg=180.0)))
    assert np.allclose(imu.accel[:, 2], -normal_gravity(47.6))


def test_standard_gravity_option():
    imu = ideal_imu(stationary_truth(lat=0.0), ImuConfig(gravity_model="standard"))
    assert np.allclose(imu.accel[:, 2], 9.80665)


# ------------------------------------------------------------------ vehicle motion
def test_aligned_phone_measures_vehicle_motion(demo):
    tr, imu = demo.truth, demo.imu
    assert np.allclose(imu.t, tr.t)
    assert np.allclose(imu.accel[:, 0], tr.accel_long, atol=1e-12)
    assert np.allclose(imu.accel[:, 1], tr.accel_lat, atol=1e-12)
    assert np.allclose(imu.accel[:, 2], normal_gravity(tr.lat), atol=1e-12)
    assert np.allclose(imu.gyro[:, 2], tr.yaw_rate, atol=1e-15)
    assert np.allclose(imu.gyro[:, :2], 0.0, atol=1e-15)


def test_flat_portrait_axis_mapping(demo):
    imu = with_imu_config(demo, ideal_at_sim_rate(mount=MOUNT_PRESETS["flat_portrait"])).imu
    assert np.allclose(imu.accel[:, 1], demo.truth.accel_long, atol=1e-12)  # y = forward
    assert np.allclose(imu.accel[:, 0], -demo.truth.accel_lat, atol=1e-12)  # x = right
    assert np.allclose(imu.gyro[:, 2], demo.truth.yaw_rate, atol=1e-15)


def test_mounting_changes_sensor_axes_but_not_vehicle_motion():
    cfg = load_preset("synthetic_demo_track").model_copy(update={"imu": ideal_at_sim_rate()})
    a = run_scenario(cfg)
    b = run_scenario(
        cfg.model_copy(
            update={"imu": ideal_at_sim_rate(mount=TILTED.model_copy(update={"lever_arm_m": (0, 0, 0)}))}
        )
    )
    for name, col in a.truth.scalar_columns().items():
        assert np.array_equal(col, b.truth.scalar_columns()[name]), name
    assert not np.allclose(a.imu.accel, b.imu.accel)
    # Same physical vectors, different axes: magnitudes agree and rotating back gives identical body vectors.
    assert np.allclose(np.linalg.norm(a.imu.accel, axis=1), np.linalg.norm(b.imu.accel, axis=1))
    assert np.allclose(np.linalg.norm(a.imu.gyro, axis=1), np.linalg.norm(b.imu.gyro, axis=1))
    r_bs = TILTED.rotation_body_from_phone()
    assert np.allclose(b.imu.accel @ r_bs.T, a.imu.accel, atol=1e-12)
    assert np.allclose(b.imu.gyro @ r_bs.T, a.imu.gyro, atol=1e-15)


@pytest.mark.parametrize("road", ["flat", "sloped"])
def test_imu_matches_numerical_differentiation_of_phone_pose(request, road):
    """End-to-end check independent of the closed-form model: differentiate the phone's actual
    trajectory (vehicle pose + lever arm) and orientation, then compare with the IMU output. On the
    sloped road this checks the 3-D kinematics: height, pitch, pitch rate and their lever-arm terms."""
    demo = request.getfixturevalue("demo" if road == "flat" else "sloped_demo")
    tr = demo.truth
    if road == "sloped":
        assert np.ptp(tr.z) > 20.0 and np.abs(tr.pitch).max() > np.radians(2.0)
    imu = with_imu_config(demo, ideal_at_sim_rate(mount=TILTED)).imu
    dt = 1.0 / tr.sample_rate_hz
    c_nb = tr.rotation_enu_from_body()
    r_bs = TILTED.rotation_body_from_phone()
    lever = np.asarray(TILTED.lever_arm_m)

    pos = np.column_stack([tr.x, tr.y, tr.z]) + np.einsum("nij,j->ni", c_nb, lever)
    acc_n = (pos[2:] - 2 * pos[1:-1] + pos[:-2]) / dt**2
    f_n = acc_n + np.column_stack([np.zeros(len(acc_n)), np.zeros(len(acc_n)), normal_gravity(tr.lat[1:-1])])
    c_ns = np.einsum("nij,jk->nik", c_nb, r_bs)
    f_s = np.einsum("nji,nj->ni", c_ns[1:-1], f_n)
    assert np.abs(f_s - imu.accel[1:-1]).max() < 0.005  # lever-arm terms alone reach ~0.06

    dc = (c_ns[2:] - c_ns[:-2]) / (2 * dt)
    skew = np.einsum("nji,njk->nik", c_ns[1:-1], dc)  # C^T dC/dt = [ω×] in phone axes
    omega_s = np.column_stack([skew[:, 2, 1], skew[:, 0, 2], skew[:, 1, 0]])
    # The profile is C2, so the pitch *acceleration* steps at each profile point. A central difference
    # across such a step is off by ~1e-5 rad/s, so samples within 1 m of a point are excluded (9 of
    # 23 000); everywhere else the agreement is ~3e-7 rad/s.
    points = np.array([d for d, _ in demo.config.road_profile.points] or [-1e9])
    away = np.abs(tr.s[1:-1, None] - points[None, :]).min(axis=1) > 1.0
    assert np.abs(omega_s - imu.gyro[1:-1])[away].max() < 5e-6


def test_lever_arm_in_steady_turn():
    """Phone 2 m ahead of the reference point in a steady left turn: extra centripetal term -ω²r on x."""
    from throughtunnel.road import RoadConfig
    from throughtunnel.routing.synthetic import Arc

    radius, v = 100.0, 12.0
    route = synthetic_route([Straight(200.0), Arc(radius, 180.0), Straight(200.0)], "circle", 2.0)
    driver = DriverConfig(
        cruise_speed_kmh=v / KMH, speed_variability_kmh=0.0, initial_speed_kmh=v / KMH, max_lateral_accel=5.0
    )
    imu_cfg = ideal_at_sim_rate(mount=PhoneMount(lever_arm_m=(2.0, 0.0, 0.0)))
    cfg = ScenarioConfig(
        route=route, driver=driver, imu=imu_cfg, road=RoadConfig(smoothing_wavelength_m=60.0)
    )
    res = run_scenario(cfg)
    tr = res.truth
    inside = (tr.s > 280.0) & (tr.s < 200.0 + radius * np.pi - 80.0)
    assert np.allclose(res.imu.accel[inside, 0], -(tr.yaw_rate[inside] ** 2) * 2.0, atol=1e-9)
    assert res.imu.accel[inside, 0].mean() == pytest.approx(-((v / radius) ** 2) * 2.0, rel=0.05)


# ------------------------------------------------------------------ Earth rotation
def test_stationary_gyro_measures_earth_rate():
    lat = 47.6
    truth = stationary_truth(lat=lat, yaw_deg=90.0)  # vehicle (and aligned phone x) pointing north
    imu = ideal_imu(truth, ImuConfig(earth_rotation=True))
    phi = np.radians(lat)
    assert np.allclose(imu.gyro, [OMEGA_EARTH * np.cos(phi), 0.0, OMEGA_EARTH * np.sin(phi)], atol=1e-15)
    assert np.allclose(np.linalg.norm(imu.gyro, axis=1), OMEGA_EARTH)
    assert np.allclose(imu.accel, [0.0, 0.0, normal_gravity(lat)])  # no Coriolis at rest


def test_coriolis_and_eotvos_when_driving_east():
    lat, v = 45.0, 25.0
    route = synthetic_route(
        [Straight(1500.0)], "east", 100.0, initial_heading_deg=0.0, frame=LocalFrame(lat, 7.0)
    )
    driver = DriverConfig(
        cruise_speed_kmh=v / KMH, speed_variability_kmh=0.0, initial_speed_kmh=v / KMH, max_speed_kmh=150
    )
    res = run_scenario(ScenarioConfig(route=route, driver=driver, imu=ideal_at_sim_rate(earth_rotation=True)))
    phi = np.radians(res.truth.lat)
    # Driving east: Coriolis pushes to the right of travel in the north. A left-pointing (north) y axis
    # reads +2Ωv sinφ. The vertical part (Eötvös effect) makes the car "lighter" by 2Ωv cosφ.
    assert np.allclose(res.imu.accel[:, 1], 2 * OMEGA_EARTH * v * np.sin(phi), atol=1e-9)
    assert np.allclose(res.imu.accel[:, 2], normal_gravity(res.truth.lat) - 2 * OMEGA_EARTH * v * np.cos(phi))


# ------------------------------------------------------------------ observation type
def test_imu_stream_validation():
    t = np.arange(5) * 0.01
    with pytest.raises(ValueError, match="shape"):
        ImuStream(t=t, accel=np.zeros((4, 3)), gyro=np.zeros((5, 3)))
    with pytest.raises(ValueError, match="increasing"):
        ImuStream(t=t[::-1], accel=np.zeros((5, 3)), gyro=np.zeros((5, 3)))
    assert ImuStream(t=t, accel=np.zeros((5, 3)), gyro=np.zeros((5, 3))).rate_hz == pytest.approx(100.0)


def test_imu_stream_carries_no_ground_truth(demo):
    """The observation must not leak hidden simulation state (e.g. the true phone mounting)."""
    assert {f.name for f in fields(ImuStream)} == {"t", "accel", "gyro", "frame", "source", "metadata"}
    assert demo.imu.metadata == {}
    assert demo.imu.frame == "android"
    assert demo.imu.source == "simulated:measured"


def test_imu_is_deterministic(demo):
    again = run_scenario(demo.config).imu
    assert np.array_equal(again.accel, demo.imu.accel) and np.array_equal(again.gyro, demo.imu.gyro)
