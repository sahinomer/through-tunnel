"""Vehicle speed sensor (D41): the car's speed reading, and the boundary that keeps it out of the main
estimators (D20): only an estimator that declares ``uses_vehicle_speed`` ever receives it."""

import json

import numpy as np
import pytest
from pydantic import ValidationError

from throughtunnel.evaluation.slope_study import PROFILES, profile_config
from throughtunnel.positioning import ESTIMATORS, Estimator, StateEstimate, run_estimator
from throughtunnel.scenario import load_preset, run_scenario, scenario_from_json, with_vehicle_speed
from throughtunnel.sensors.vehicle_speed import VehicleSpeedConfig
from throughtunnel.vehicle.traffic import TrafficConfig

V4 = next(p for p in PROFILES if p.key == "v4")


@pytest.fixture(scope="module")
def demo():
    return run_scenario(load_preset("synthetic_demo_track"))


class Recorder(Estimator):
    name = label = "recorder"
    alignment = None

    def __init__(self, route):
        super().__init__(route)
        self.events, self.t = [], 0.0

    def on_imu(self, t, imu):
        self.events.append(("imu", t))
        self.t = t

    def on_gnss(self, fix):
        self.events.append(("gnss", fix.t))

    def on_vehicle_speed(self, t, speed_mps):
        self.events.append(("speed", t))

    def state(self):
        return StateEstimate(t=self.t, east=0.0, north=0.0, speed=0.0, heading=0.0, mode="gnss")


class SpeedRecorder(Recorder):
    name = "speed_recorder"
    uses_vehicle_speed = True


def test_config_default_validation_and_older_files():
    assert VehicleSpeedConfig().scale_error_pct == 2.0
    with pytest.raises(ValidationError):
        VehicleSpeedConfig(scale_error_pct=20.0)
    cfg = load_preset("synthetic_demo_track")
    edited = cfg.model_copy(update={"vehicle_speed": VehicleSpeedConfig(scale_error_pct=-3.0)})
    assert scenario_from_json(edited.model_dump_json()).vehicle_speed.scale_error_pct == -3.0
    old = json.loads(cfg.model_dump_json())
    old.pop("vehicle_speed")
    old["schema_version"] = 9
    assert scenario_from_json(json.dumps(old)).vehicle_speed == VehicleSpeedConfig()


def test_reading_is_the_along_road_speed_times_the_scale_error():
    cfg = load_preset("synthetic_demo_track")
    res = run_scenario(cfg.model_copy(update={"road_profile": profile_config(cfg, V4)}))
    vs = res.vehicle_speed
    assert np.allclose(np.diff(vs.t), 0.1) and vs.t[-1] <= res.truth.duration_s + 1e-9
    v = np.interp(vs.t, res.truth.t, res.truth.speed)
    g = np.interp(vs.t, res.truth.t, res.truth.grade)
    assert np.allclose(vs.speed_mps, 1.02 * v * np.sqrt(1.0 + g**2))
    assert np.abs(g).max() > 0.03  # the slope term is exercised


def test_standstill_reads_exactly_zero():
    cfg = load_preset("synthetic_demo_track")
    res = run_scenario(cfg.model_copy(update={"traffic": TrafficConfig(scenario="stop_and_go")}))
    stopped = np.interp(res.vehicle_speed.t, res.truth.t, res.truth.speed) == 0.0
    assert stopped.any() and np.all(res.vehicle_speed.speed_mps[stopped] == 0.0)


def test_changing_the_sensor_re_simulates_only_the_reading(demo):
    other = with_vehicle_speed(demo, VehicleSpeedConfig(scale_error_pct=-4.0))
    assert other.imu is demo.imu and other.gnss is demo.gnss and other.truth is demo.truth
    assert np.allclose(other.vehicle_speed.speed_mps * 1.02, demo.vehicle_speed.speed_mps * 0.96)


def test_only_the_reference_estimator_declares_the_vehicle_speed():
    from throughtunnel.positioning import MAIN_ESTIMATORS, REFERENCE_ESTIMATORS

    assert set(REFERENCE_ESTIMATORS) == {"route_vspeed"}
    assert not any(cls.uses_vehicle_speed for cls in MAIN_ESTIMATORS.values())
    assert set(MAIN_ESTIMATORS) | set(REFERENCE_ESTIMATORS) == set(ESTIMATORS)


def test_only_a_declaring_estimator_receives_the_vehicle_speed(demo):
    obs = demo.observations()
    assert obs.vehicle_speed is not None and len(obs.vehicle_speed) > 0
    plain = Recorder(obs.route)
    run_estimator(plain, obs)
    assert not any(kind == "speed" for kind, _ in plain.events)  # never delivered

    rec = SpeedRecorder(obs.route)
    run_estimator(rec, obs)
    times = [t for _, t in rec.events]
    assert times == sorted(times)
    assert sum(kind == "speed" for kind, _ in rec.events) == len(obs.vehicle_speed)
    i = rec.events.index(("speed", 1.0))  # tie: after the IMU sample and the GPS fix at 1.0 s
    assert rec.events[i - 2 : i] == [("imu", 1.0), ("gnss", 1.0)]


def test_a_declaring_estimator_without_a_reading_fails_loudly(demo):
    from dataclasses import replace

    obs = replace(demo.observations(), vehicle_speed=None)
    with pytest.raises(ValueError, match="needs the vehicle speed"):
        run_estimator(SpeedRecorder(obs.route), obs)


# ------------------------------------------------------------------ the reference estimator
def ideal_run(scale_pct: float, **update):
    from throughtunnel.evaluation.slope_study import ideal_sensors
    from throughtunnel.scenario import with_sensor_config

    cfg = load_preset("synthetic_demo_track")
    cfg = cfg.model_copy(update={"vehicle_speed": VehicleSpeedConfig(scale_error_pct=scale_pct), **update})
    imu, gnss = ideal_sensors(cfg)
    return with_sensor_config(run_scenario(cfg), imu=imu, gnss=gnss)


def along_error_at_c(res, est):
    from throughtunnel.evaluation.metrics import evaluate_track

    return evaluate_track(run_estimator(est, res.observations()), res).summary["exit_along_m"]


def test_reference_with_a_perfect_speed_reading_is_accurate():
    res = ideal_run(0.0)
    est = ESTIMATORS["route_vspeed"](res.route_map)
    assert abs(along_error_at_c(res, est)) < 10.0  # only map vs driven distance remains
    assert est.scale == pytest.approx(1.0, abs=1e-3)


def test_reference_calibrates_the_scale_error_away():
    res = ideal_run(3.0)
    raw = ESTIMATORS["route_vspeed"](res.route_map)
    raw.calibrate_scale = False
    calibrated = ESTIMATORS["route_vspeed"](res.route_map)
    raw_err, cal_err = along_error_at_c(res, raw), along_error_at_c(res, calibrated)
    t_f = float(res.gnss.t[res.gnss.t < res.gnss_events.loss_t][-1])
    s_at = lambda t: float(np.interp(t, res.truth.t, res.truth.s))  # noqa: E731
    travelled = s_at(res.sections.exit_t) - s_at(t_f)
    assert raw_err == pytest.approx(0.03 * travelled, rel=0.1)  # reads 3 % high: 3 % of the distance ahead
    assert calibrated.scale == pytest.approx(1 / 1.03, rel=2e-3)
    assert abs(cal_err) < 0.15 * abs(raw_err)


def test_reference_is_unaffected_by_stops():
    res = ideal_run(2.0, traffic=TrafficConfig(scenario="stop_and_go"))
    assert (res.motion.v == 0.0).any()
    assert abs(along_error_at_c(res, ESTIMATORS["route_vspeed"](res.route_map))) < 10.0
