"""Phone GPS simulation: availability around the tunnel, error statistics, determinism."""

import math

import numpy as np
import pytest

from throughtunnel.randomness import rng_stream
from throughtunnel.routing.synthetic import Straight, synthetic_route
from throughtunnel.scenario import ScenarioConfig, load_preset, run_scenario, truth_at, with_sensor_config
from throughtunnel.sensors.gnss import ACCURACY_68_FACTOR, GnssConfig, gauss_markov
from throughtunnel.sensors.imu import ImuConfig
from throughtunnel.sensors.mounting import PhoneMount


@pytest.fixture(scope="module")
def demo():
    return run_scenario(load_preset("synthetic_demo_track"))


def enu(result, stream):
    return result.truth.frame.to_enu(stream.lat, stream.lon)[:, :2]


def test_availability_around_the_tunnel(demo):
    g, ev, sec, cfg = demo.gnss, demo.gnss_events, demo.sections, demo.config.gnss
    assert np.allclose(np.diff(g.t[g.t < ev.loss_t]), 1.0)  # 1 Hz before the tunnel
    # The loss starts at a random point at most loss_window_m before the entrance B (PD4).
    assert sec.entrance_s - cfg.loss_window_m <= ev.loss_s <= sec.entrance_s
    assert not np.any((g.t >= ev.loss_t) & (g.t < ev.reacquire_t))  # nothing in between
    tr = truth_at(demo, g.t)
    assert not np.any((tr.s > sec.entrance_s) & (tr.s < sec.exit_s))  # no fix inside B–C
    delay = ev.reacquire_t - sec.exit_t
    assert cfg.reacquisition_delay_s <= delay <= cfg.reacquisition_delay_s + cfg.reacquisition_jitter_s
    after = g.t[g.t >= ev.reacquire_t]
    assert after[0] - ev.reacquire_t < 1.0 and np.allclose(np.diff(after), 1.0)  # back at 1 Hz


def test_loss_point_is_random_but_seeded(demo):
    other = with_sensor_config(demo, gnss=demo.config.gnss.model_copy(update={"seed": 99}))
    assert other.gnss_events.loss_s != demo.gnss_events.loss_s
    again = with_sensor_config(demo, gnss=demo.config.gnss)
    assert again.gnss_events == demo.gnss_events


def test_ideal_fixes_are_the_true_phone_position_and_velocity():
    lever = (2.0, 0.4, 1.0)
    cfg = load_preset("synthetic_demo_track").model_copy(
        update={"imu": ImuConfig(mount=PhoneMount(lever_arm_m=lever))}
    )
    res = run_scenario(cfg)
    ideal = res.gnss_ideal
    tr = truth_at(res, ideal.t)
    phone = tr.point_enu(lever)[:, :2]
    # Fixes carry lat/lon only; re-projecting them at altitude 0 instead of the tangent plane's height
    # (-d^2/2R, ~1 m at 4 km) shifts them by ~1 mm. Irrelevant for GPS, hence the 1 cm tolerance.
    assert np.abs(enu(res, ideal) - phone).max() < 0.01
    # Speed and bearing are the phone point's course over ground. In turns this differs from the vehicle
    # heading (the lever arm adds omega x r), so check against the differentiated phone position.
    h = 1e-3
    vel = (
        truth_at(res, ideal.t[1:-1] + h).point_enu(lever) - truth_at(res, ideal.t[1:-1] - h).point_enu(lever)
    ) / (2 * h)
    assert np.abs(ideal.speed_mps[1:-1] - np.hypot(vel[:, 0], vel[:, 1])).max() < 1e-4
    bearing = np.mod(np.degrees(np.arctan2(vel[:, 0], vel[:, 1])), 360.0)
    assert np.abs((ideal.bearing_deg[1:-1] - bearing + 180.0) % 360.0 - 180.0).max() < 1e-3


def test_error_statistics_and_accuracy_fields():
    route = synthetic_route([Straight(40_000.0)], "long", 500.0)
    res = run_scenario(ScenarioConfig(route=route))  # no tunnel: GPS everywhere, ~30 min
    g, ideal, cfg = res.gnss, res.gnss_ideal, res.config.gnss
    err = enu(res, g) - enu(res, ideal)
    sigma = math.hypot(cfg.position_sigma_m, cfg.white_sigma_m)
    assert err.std(axis=0) == pytest.approx([sigma] * 2, rel=0.2)  # correlated: few independent samples
    lag = round(cfg.position_tau_s * cfg.rate_hz)
    corr = np.corrcoef(err[:-lag, 0], err[lag:, 0])[0, 1]
    assert 0.15 < corr < 0.6  # ~exp(-1) for the Gauss-Markov part: genuinely time-correlated
    assert np.std(g.speed_mps - ideal.speed_mps) == pytest.approx(cfg.speed_sigma_mps, rel=0.1)
    assert g.horizontal_accuracy_m[0] == pytest.approx(ACCURACY_68_FACTOR * sigma)
    radius = np.hypot(err[:, 0], err[:, 1])
    assert np.mean(radius <= g.horizontal_accuracy_m) == pytest.approx(0.68, abs=0.12)


def test_gauss_markov_process():
    x = gauss_markov(200_000, 1.0, 2.0, 20.0, rng_stream(0, "gm"))
    assert x.std(axis=0) == pytest.approx([2.0, 2.0], rel=0.03)
    assert np.corrcoef(x[:-20, 0], x[20:, 0])[0, 1] == pytest.approx(math.exp(-1.0), abs=0.03)


def test_gps_is_independent_of_imu_errors_and_vice_versa(demo):
    imu_cfg = demo.config.imu
    other_imu = with_sensor_config(
        demo, imu=imu_cfg.model_copy(update={"errors": imu_cfg.errors.model_copy(update={"seed": 7})})
    )
    assert np.array_equal(other_imu.gnss.lat, demo.gnss.lat)
    other_gps = with_sensor_config(demo, gnss=demo.config.gnss.model_copy(update={"seed": 7}))
    assert np.array_equal(other_gps.imu.accel, demo.imu.accel)
    assert not np.array_equal(other_gps.gnss.lat[:10], demo.gnss.lat[:10])


def test_disabled_and_ideal_configs(demo):
    off = with_sensor_config(demo, gnss=GnssConfig(enabled=False))
    assert len(off.gnss) == 0
    ideal = with_sensor_config(demo, gnss=GnssConfig.ideal())
    assert np.abs(enu(ideal, ideal.gnss) - enu(ideal, ideal.gnss_ideal)).max() < 1e-6


def test_observations_bundle_contains_only_measured_data(demo):
    obs = demo.observations()
    assert obs.imu is demo.imu and obs.gnss is demo.gnss and obs.route is demo.route_map
    assert obs.imu.source == "simulated:measured" and obs.gnss.source == "simulated:measured"
