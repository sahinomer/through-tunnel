"""Traffic scenarios (D37): plans anchored to B/C, real stops, physically consistent motion and sensors."""

import numpy as np
import pytest
from helpers import stationary_truth

from throughtunnel.geodesy import normal_gravity
from throughtunnel.scenario import load_preset, run_scenario, with_imu_config
from throughtunnel.sensors.errors import ImuErrorConfig
from throughtunnel.sensors.gnss import GnssConfig, GnssEvents, simulate_gnss
from throughtunnel.sensors.imu import ImuConfig
from throughtunnel.sensors.mounting import PhoneMount
from throughtunnel.vehicle.traffic import SCENARIO_LABELS, TrafficConfig, build_traffic_plan

KMH = 1 / 3.6
TILTED = PhoneMount(label="test", yaw_deg=37.0, pitch_deg=-22.0, roll_deg=71.0, lever_arm_m=(1.6, 0.35, 0.8))


def run(scenario: str, **kw):
    cfg = load_preset("synthetic_demo_track")
    imu = ImuConfig(rate_hz=100.0, errors=ImuErrorConfig.ideal())
    return run_scenario(
        cfg.model_copy(update={"traffic": TrafficConfig(scenario=scenario, **kw), "imu": imu})
    )


@pytest.fixture(scope="module")
def stop_and_go():
    return run("stop_and_go")


# ------------------------------------------------------------------ plans
def test_plans_are_anchored_to_b_and_c_and_reproducible():
    rng = lambda s: np.random.default_rng(s)  # noqa: E731
    b, c, cruise = 1600.0, 3600.0, 70 * KMH
    assert build_traffic_plan(TrafficConfig(), b, c, cruise, rng(0)).empty
    sg = build_traffic_plan(TrafficConfig(scenario="stop_and_go", stop_count=4), b, c, cruise, rng(1))
    assert len(sg.stops) == 4 and all(b < st.at_m < c for st in sg.stops)
    assert all(10.0 <= st.duration_s <= 60.0 for st in sg.stops)
    assert sg == build_traffic_plan(TrafficConfig(scenario="stop_and_go", stop_count=4), b, c, cruise, rng(1))
    assert sg != build_traffic_plan(TrafficConfig(scenario="stop_and_go", stop_count=4), b, c, cruise, rng(2))
    q = build_traffic_plan(TrafficConfig(scenario="exit_queue", jitter=0.0), b, c, cruise, rng(0))
    assert q.zones[0].end_m == c and q.zones[0].start_m == pytest.approx(c - 400.0)
    assert all(c - 400.0 < st.at_m < c for st in q.stops)
    portal = build_traffic_plan(TrafficConfig(scenario="portal", jitter=0.0), b, c, cruise, rng(0)).zones[0]
    assert portal.start_m == b and portal.speed_mps == pytest.approx(cruise - 15 * KMH)
    limit = build_traffic_plan(TrafficConfig(scenario="speed_limit", jitter=0.0), b, c, cruise, rng(0)).zones[
        0
    ]
    assert (limit.start_m, limit.end_m, limit.speed_mps) == (b, c, pytest.approx(60 * KMH))


def test_config_validation():
    with pytest.raises(ValueError):
        TrafficConfig(stop_min_s=50.0, stop_max_s=20.0)


# ------------------------------------------------------------------ motion
@pytest.mark.parametrize("scenario", [s for s in SCENARIO_LABELS if s != "free"])
def test_every_scenario_respects_the_driver_limits(scenario):
    res = run(scenario)
    m, d = res.motion, res.config.driver
    assert m.v.min() >= 0.0
    assert np.abs(m.jerk).max() <= d.max_jerk + 1e-9
    assert -d.max_decel - 1e-9 <= m.a.min() and m.a.max() <= d.max_accel + 1e-9
    tunnel = (m.s >= res.sections.entrance_s) & (m.s <= res.sections.exit_s)
    assert m.v[tunnel].mean() < 0.95 * res.config.driver.cruise_speed_kmh * KMH  # traffic slows the tunnel
    assert (m.s >= res.sections.exit_s).any()  # and the vehicle still gets through


def test_stops_are_real_standstills_of_the_planned_duration(stop_and_go):
    m, plan = stop_and_go.motion, stop_and_go.traffic
    dt = m.t[1] - m.t[0]
    standing = m.v == 0.0
    edges = np.flatnonzero(np.diff(standing.astype(int)))  # rest starts (+1) and ends
    starts, ends = edges[::2] + 1, edges[1::2] + 1
    assert len(starts) == len(plan.stops) == 3
    for st, i0, i1 in zip(plan.stops, starts, ends, strict=True):
        assert (i1 - i0) * dt == pytest.approx(st.duration_s, abs=2 * dt)
        assert abs(m.s[i0] - st.at_m) < 6.0  # stops where the plan says (map vs path distance)
        assert np.all(m.a[i0:i1] == 0.0) and np.ptp(m.s[i0:i1]) == 0.0


def test_motion_is_self_consistent_through_stops(stop_and_go):
    """ds/dt = v and dv/dt = a hold everywhere, also across stopping and pulling away; the snap to
    exact rest is below 0.02 m/s² in acceleration."""
    m = stop_and_go.motion
    dt = m.t[1] - m.t[0]
    assert np.abs((m.s[2:] - m.s[:-2]) / (2 * dt) - m.v[1:-1]).max() < 1e-3
    dv = (m.v[2:] - m.v[:-2]) / (2 * dt)
    assert np.abs(dv - m.a[1:-1]).max() < 0.02
    assert np.abs(np.diff(m.a)).max() <= m.jerk.__abs__().max() * dt + 0.02


def test_imu_at_standstill_and_against_numerical_differentiation(stop_and_go):
    """The phone sees only gravity while the vehicle stands, and the IMU matches the numerically
    differentiated phone pose through the stops (tilted mount with lever arm)."""
    res = with_imu_config(stop_and_go, ImuConfig(rate_hz=100.0, errors=ImuErrorConfig.ideal(), mount=TILTED))
    tr, imu = res.truth, res.imu
    still = tr.speed == 0.0
    g = normal_gravity(tr.lat[still])
    assert np.allclose(np.linalg.norm(imu.accel[still], axis=1), g, atol=1e-9)
    # Not exactly zero at the first standing sample: the IMU evaluates the final braking step, whose
    # speed is within the documented snap (< 1e-4 m/s) of rest. Physically negligible.
    assert np.abs(imu.gyro[still]).max() < 1e-6
    dt = 1.0 / tr.sample_rate_hz
    c_nb = tr.rotation_enu_from_body()
    pos = np.column_stack([tr.x, tr.y, tr.z]) + np.einsum("nij,j->ni", c_nb, np.asarray(TILTED.lever_arm_m))
    acc_n = (pos[2:] - 2 * pos[1:-1] + pos[:-2]) / dt**2
    f_n = acc_n + np.column_stack([np.zeros(len(acc_n)), np.zeros(len(acc_n)), normal_gravity(tr.lat[1:-1])])
    c_ns = np.einsum("nij,jk->nik", c_nb, TILTED.rotation_body_from_phone())
    f_s = np.einsum("nji,nj->ni", c_ns[1:-1], f_n)
    assert np.abs(f_s - imu.accel[1:-1]).max() < 0.02  # includes the stop snaps


def test_gps_outage_lengthens_with_traffic():
    free, sg = run("free"), run("stop_and_go")
    out = lambda r: r.gnss_events.reacquire_t - r.gnss_events.loss_t  # noqa: E731
    assert out(sg) > out(free) + 60.0


def test_gps_bearing_at_standstill_is_the_vehicle_heading():
    truth = stationary_truth(n=300, yaw_deg=30.0)  # ENU yaw 30° = compass bearing 60°
    events = GnssEvents(loss_s=np.inf, loss_t=np.inf, reacquire_t=np.inf)
    _, ideal = simulate_gnss(truth.__class__(**{**truth.__dict__, "t": truth.t}), (0.0, 0.0, 0.0), events,
                             GnssConfig.ideal(), 0)  # fmt: skip
    assert np.allclose(ideal.bearing_deg, 60.0)
