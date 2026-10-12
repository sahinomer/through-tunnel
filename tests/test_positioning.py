"""Positioning pipeline: causality, runner semantics, baseline physics, calibration, evaluation."""

import math
from dataclasses import replace

import numpy as np
import pytest

from throughtunnel.evaluation.metrics import _recovery_time, evaluate_track
from throughtunnel.observations import GnssStream, ImuStream, Observations
from throughtunnel.positioning import ESTIMATORS, Estimator, StateEstimate, run_estimator
from throughtunnel.positioning.dead_reckoning import CalibratedDeadReckoning, RawDeadReckoning
from throughtunnel.positioning.runner import EstimateTrack
from throughtunnel.scenario import load_preset, run_scenario, truth_at
from throughtunnel.sensors.errors import ImuErrorConfig
from throughtunnel.sensors.gnss import GnssConfig
from throughtunnel.sensors.mounting import MOUNT_PRESETS


def scenario(**imu_update):
    """Demo route with ideal GPS and an IMU configured by ``imu_update`` (default: ideal)."""
    cfg = load_preset("synthetic_demo_track")
    imu = cfg.imu.model_copy(update={"errors": ImuErrorConfig.ideal(), **imu_update})
    return run_scenario(cfg.model_copy(update={"imu": imu, "gnss": GnssConfig.ideal()}))


def biased(accel=None, gyro=None) -> ImuErrorConfig:
    ideal = ImuErrorConfig.ideal()
    return ImuErrorConfig(
        accel=ideal.accel.model_copy(update={"bias_enabled": accel is not None, "bias_vector": accel}),
        gyro=ideal.gyro.model_copy(update={"bias_enabled": gyro is not None, "bias_vector": gyro}),
    )


@pytest.fixture(scope="module")
def demo():
    return run_scenario(load_preset("synthetic_demo_track"))


# ------------------------------------------------------------------ causality and runner
@pytest.mark.parametrize("name", sorted(ESTIMATORS))
def test_estimators_are_causal(demo, name):
    """Changing every observation after t* must not change any estimate (or announcement) before t*."""
    obs = demo.observations()
    t_star = 0.5 * (demo.sections.entrance_t + demo.sections.exit_t)
    rng = np.random.default_rng(0)
    after_i, after_g = obs.imu.t > t_star, obs.gnss.t > t_star
    accel, gyro = obs.imu.accel.copy(), obs.imu.gyro.copy()
    accel[after_i] += rng.normal(0, 1.0, (after_i.sum(), 3))
    gyro[after_i] += 0.1
    lat = obs.gnss.lat.copy()
    lat[after_g] += 1e-3
    perturbed = Observations(
        imu=ImuStream(t=obs.imu.t, accel=accel, gyro=gyro),
        gnss=replace(obs.gnss, lat=lat),
        route=obs.route,
    )
    a = run_estimator(ESTIMATORS[name](obs.route), obs)
    b = run_estimator(ESTIMATORS[name](obs.route), perturbed)
    before = a.t <= t_star
    for f in ("east", "north", "speed", "heading", "route_distance"):
        assert np.array_equal(getattr(a, f)[before], getattr(b, f)[: before.sum()]), f
    early = {k: v for k, v in a.announcements.items() if v <= t_star}
    assert all(b.announcements[k] == v for k, v in early.items())


class Recorder(Estimator):
    name = label = "recorder"

    def __init__(self, route):
        super().__init__(route)
        self.events = []
        self.t = None

    def on_imu(self, t, accel, gyro):
        self.events.append(("imu", t))
        self.t = t

    def on_gnss(self, fix):
        self.events.append(("gnss", fix.t))

    def state(self):
        return StateEstimate(t=self.t, east=0.0, north=0.0, speed=0.0, heading=0.0, mode="gnss")


def test_runner_feeds_events_in_time_order(demo):
    obs = demo.observations()
    rec = Recorder(obs.route)
    track = run_estimator(rec, obs, output_rate_hz=20.0)
    times = [t for _, t in rec.events]
    assert times == sorted(times)
    assert sum(k == "gnss" for k, _ in rec.events) == len(obs.gnss)
    assert sum(k == "imu" for k, _ in rec.events) == len(obs.imu)
    i = rec.events.index(("gnss", 1.0))  # tie: IMU sample at t = 1.0 s comes before the fix at 1.0 s
    assert rec.events[i - 1] == ("imu", 1.0)
    assert np.allclose(np.diff(track.t), 0.05)  # 20 Hz output


# ------------------------------------------------------------------ baseline physics
def last_fix_before(res, t):
    g = res.gnss.t
    return float(g[g < t][-1])


def test_zero_error_dead_reckoning_is_accurate():
    """Ideal sensors and ideal GPS: the remaining error is pure integration/model error."""
    res = scenario()
    for cls in (RawDeadReckoning, CalibratedDeadReckoning):
        ev = evaluate_track(run_estimator(cls(res.route_map), res.observations()), res)
        assert ev.summary["outage_max_m"] < 1.0, cls.name


def test_forward_accel_bias_error_matches_analytic_prediction():
    """A forward bias b adds speed error b*(t - t0); with correct heading the position error is the
    vector integral of b*(t - t0) along the true direction of travel (= 1/2 b t^2 on a straight road)."""
    b = 0.1  # m/s^2 on phone x = vehicle forward (aligned mount)
    res = scenario(errors=biased(accel=(b, 0.0, 0.0)))
    track = run_estimator(RawDeadReckoning(res.route_map), res.observations())
    t_c = res.sections.exit_t
    t0 = last_fix_before(res, t_c)
    tau = np.linspace(t0, t_c, 20_001)
    yaw = truth_at(res, tau).yaw
    w = b * (tau - t0)
    expected = np.array([np.trapezoid(w * np.cos(yaw), tau), np.trapezoid(w * np.sin(yaw), tau)])
    truth_c = truth_at(res, [t_c]).point_enu(res.config.imu.mount.lever_arm_m)[0, :2]
    est_c = np.array([np.interp(t_c, track.t, track.east), np.interp(t_c, track.t, track.north)])
    assert np.linalg.norm((est_c - truth_c) - expected) < 0.01 * np.linalg.norm(expected)
    assert np.linalg.norm(expected) <= 0.5 * b * (t_c - t0) ** 2  # equality only on a straight road


def test_gyro_bias_gives_linear_heading_error():
    bg = math.radians(0.1)
    res = scenario(errors=biased(gyro=(0.0, 0.0, bg)))
    track = run_estimator(RawDeadReckoning(res.route_map), res.observations())
    t_c = res.sections.exit_t
    k = int(np.argmin(np.abs(track.t - t_c)))
    heading_err = track.heading[k] - truth_at(res, [track.t[k]]).yaw[0]
    tau = track.t[k] - last_fix_before(res, t_c)
    assert heading_err == pytest.approx(bg * tau, rel=0.05)


def test_calibration_removes_most_of_the_bias_errors():
    res = scenario(errors=biased(accel=(0.1, 0.0, 0.0), gyro=(0.0, 0.0, math.radians(0.1))))
    raw = evaluate_track(run_estimator(RawDeadReckoning(res.route_map), res.observations()), res)
    cal = evaluate_track(run_estimator(CalibratedDeadReckoning(res.route_map), res.observations()), res)
    assert abs(cal.summary["exit_along_m"]) < 0.05 * abs(raw.summary["exit_along_m"])
    assert abs(cal.summary["exit_cross_m"]) < 0.2 * abs(raw.summary["exit_cross_m"])


def test_alignment_recovers_an_unknown_mount():
    mount = MOUNT_PRESETS["dash_portrait_tilted"]
    res = scenario(mount=mount)
    est = CalibratedDeadReckoning(res.route_map)
    ev = evaluate_track(run_estimator(est, res.observations()), res)
    axes = est.alignment
    r_bs = mount.rotation_body_from_phone()
    fwd_true, up_true = r_bs.T @ [1.0, 0.0, 0.0], r_bs.T @ [0.0, 0.0, 1.0]
    assert math.degrees(math.acos(min(1.0, axes.forward @ fwd_true))) < 1.0
    assert math.degrees(math.acos(min(1.0, axes.up @ up_true))) < 0.2
    assert ev.summary["exit_total_m"] < 5.0


# ------------------------------------------------------------------ route-constrained and announcements
def test_route_constrained_estimates_stay_on_the_route(demo):
    obs = demo.observations()
    for name in ("route_imu", "route_hold"):
        track = run_estimator(ESTIMATORS[name](obs.route), obs)
        offsets = [
            abs(obs.route.project_enu(e, n)[1])
            for e, n in zip(track.east[::50], track.north[::50], strict=True)
        ]
        assert max(offsets) < 1e-6
        # Distance to the true road (not to the true vehicle position): only the map-vs-road deviation.
        path = demo.path
        for e, n in zip(track.east[::40], track.north[::40], strict=True):
            p = path.evaluate(path.project(e, n)).xy
            assert math.hypot(p[0] - e, p[1] - n) < 2.0


def test_route_hold_keeps_the_last_gps_speed(demo):
    obs = demo.observations()
    track = run_estimator(ESTIMATORS["route_hold"](obs.route), obs)
    out = track.mode == "dead_reckoning"
    assert np.ptp(track.speed[out & (track.t < demo.sections.exit_t)]) == 0.0


def test_perfect_information_announces_on_time():
    res = scenario()
    ev = evaluate_track(run_estimator(CalibratedDeadReckoning(res.route_map), res.observations()), res)
    for name, err in ev.announcement_time_error_s.items():
        assert abs(err) < 0.1, name  # within two output samples


# ------------------------------------------------------------------ evaluation definitions
def shifted_truth_track(res, along=0.0, left=0.0) -> EstimateTrack:
    t = np.arange(0.0, res.truth.duration_s, 0.05)
    tr = truth_at(res, t)
    p = tr.point_enu(res.config.imu.mount.lever_arm_m)
    c, s = np.cos(tr.yaw), np.sin(tr.yaw)
    n = len(t)
    return EstimateTrack(
        name="shifted",
        label="shifted",
        t=t,
        east=p[:, 0] + along * c - left * s,
        north=p[:, 1] + along * s + left * c,
        speed=tr.speed,
        heading=tr.yaw,
        mode=np.full(n, "gnss"),
        route_distance=np.full(n, np.nan),
        position_std_m=np.full(n, np.nan),
    )


def test_error_decomposition_signs(demo):
    ev = evaluate_track(shifted_truth_track(demo, along=5.0, left=3.0), demo)
    assert np.allclose(ev.along, 5.0) and np.allclose(ev.cross, 3.0)
    assert np.allclose(ev.total, math.hypot(5.0, 3.0))
    assert set(ev.phase) == {"approach", "tunnel", "recovery"}
    exact = evaluate_track(shifted_truth_track(demo), demo)
    assert np.abs(exact.total).max() < 1e-9


def test_recovery_time_definition():
    t = np.arange(0.0, 30.0, 0.5)
    err = np.where(t < 12.0, 50.0, 2.0)
    assert _recovery_time(t, err, start=10.0, threshold=10.0, hold=5.0) == 12.0
    assert math.isnan(_recovery_time(t, np.full_like(t, 50.0), 10.0, 10.0, 5.0))


def test_empty_gnss_means_no_estimate(demo):
    obs = demo.observations()
    empty = GnssStream(*(np.array([]) for _ in range(8)))
    track = run_estimator(ESTIMATORS["dr_calibrated"](obs.route), Observations(obs.imu, empty, obs.route))
    assert len(track) == 0  # never initialised: positioning needs GPS before the tunnel
