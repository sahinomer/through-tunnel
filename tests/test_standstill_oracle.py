"""Standstill oracle (D49): exact standstill from the true motion, delivered only to estimators that
declare ``uses_standstill``, which stay out of the phone-only set."""

import numpy as np
import pytest

from throughtunnel.positioning import (
    ESTIMATORS,
    MAIN_ESTIMATORS,
    ORACLE_ESTIMATORS,
    Estimator,
    StateEstimate,
    run_estimator,
    run_estimators,
)
from throughtunnel.scenario import load_preset, run_scenario
from throughtunnel.vehicle.traffic import TrafficConfig


@pytest.fixture(scope="module")
def stop_and_go():
    cfg = load_preset("synthetic_demo_track")
    return run_scenario(cfg.model_copy(update={"traffic": TrafficConfig(scenario="stop_and_go", seed=1)}))


@pytest.fixture(scope="module")
def free():
    return run_scenario(load_preset("synthetic_demo_track"))


def test_oracle_marks_exactly_the_true_stops(stop_and_go):
    ss = stop_and_go.standstill
    assert len(ss) >= 2 and len(ss) % 2 == 0
    assert list(ss.standing) == [True, False] * (len(ss) // 2)
    truth = stop_and_go.truth
    for start, end in zip(ss.t[::2], ss.t[1::2], strict=True):
        inside = (truth.t >= start) & (truth.t < end)
        assert np.all(truth.speed[inside] == 0.0)
        assert truth.speed[np.searchsorted(truth.t, start) - 1] > 0.0  # moving just before
        assert truth.speed[np.searchsorted(truth.t, end)] > 0.0  # and again from the end


def test_free_flow_has_no_standstill(free):
    assert len(free.standstill) == 0


def test_oracle_estimators_are_kept_out_of_the_phone_only_set():
    assert set(ORACLE_ESTIMATORS) == {"route_imu_stop", "route_imu_zupt"}
    assert not set(ORACLE_ESTIMATORS) & set(MAIN_ESTIMATORS)
    assert not any(cls.uses_standstill for cls in MAIN_ESTIMATORS.values())
    assert all("oracle" in cls.label for cls in ORACLE_ESTIMATORS.values())


class Recorder(Estimator):
    name = label = "recorder"
    alignment = None

    def __init__(self, route):
        super().__init__(route)
        self.events, self.t = [], 0.0

    def on_imu(self, t, imu):
        self.t = t

    def on_gnss(self, fix):
        pass

    def on_standstill(self, t, standing):
        self.events.append((t, standing))

    def state(self):
        return StateEstimate(t=self.t, east=0.0, north=0.0, speed=0.0, heading=0.0, mode="gnss")


class StandstillRecorder(Recorder):
    name = "standstill_recorder"
    uses_standstill = True


def test_only_a_declaring_estimator_receives_the_oracle(stop_and_go):
    obs = stop_and_go.observations()
    plain, declaring = Recorder(obs.route), StandstillRecorder(obs.route)
    run_estimator(plain, obs)
    run_estimator(declaring, obs)
    assert plain.events == []
    assert [s for _, s in declaring.events] == list(obs.standstill.standing)
    assert np.allclose([t for t, _ in declaring.events], obs.standstill.t)


def test_without_stops_the_oracle_estimators_equal_route_imu(free):
    obs = free.observations()
    tracks = run_estimators([ESTIMATORS[n](obs.route) for n in ("route_imu", *ORACLE_ESTIMATORS)], obs)
    for tr in tracks[1:]:
        assert np.array_equal(tr.route_distance, tracks[0].route_distance)
        assert np.array_equal(tr.speed, tracks[0].speed)


@pytest.mark.parametrize("name", sorted(ORACLE_ESTIMATORS))
def test_a_standing_car_has_zero_speed_and_holds_its_position(stop_and_go, name):
    obs = stop_and_go.observations()
    track = run_estimator(ESTIMATORS[name](obs.route), obs)
    ss = obs.standstill
    for start, end in zip(ss.t[::2], ss.t[1::2], strict=True):
        inside = (track.t > start + 0.01) & (track.t < end - 0.01)
        assert inside.sum() > 10
        assert np.all(track.speed[inside] == 0.0)
        assert np.ptp(track.route_distance[inside]) < 1e-9


# ------------------------------------------------------------------ error model (D50)
def test_delay_shifts_every_report(stop_and_go):
    from throughtunnel.scenario import with_standstill_oracle
    from throughtunnel.sensors.standstill import StandstillOracleConfig

    late = with_standstill_oracle(stop_and_go, StandstillOracleConfig(delay_s=1.5)).standstill
    assert np.allclose(late.t, stop_and_go.standstill.t + 1.5)
    assert list(late.standing) == list(stop_and_go.standstill.standing)


def test_a_slow_threshold_widens_each_stop_around_the_true_one(stop_and_go):
    from throughtunnel.scenario import with_standstill_oracle
    from throughtunnel.sensors.standstill import StandstillOracleConfig

    true = stop_and_go.standstill
    slow = with_standstill_oracle(stop_and_go, StandstillOracleConfig(false_standstill_kmh=3.0)).standstill
    assert len(slow) == len(true)
    assert np.all(slow.t[::2] < true.t[::2]) and np.all(slow.t[1::2] > true.t[1::2])  # early on, late off
    v_on = np.interp(slow.t[::2], stop_and_go.truth.t, stop_and_go.truth.speed)
    assert np.all(v_on < 3.0 / 3.6)  # reported only once the car is really slow


def test_missed_stops_are_reproducible_and_nested(stop_and_go):
    from throughtunnel.scenario import with_standstill_oracle
    from throughtunnel.sensors.standstill import StandstillOracleConfig

    def starts(p):
        return set(
            with_standstill_oracle(stop_and_go, StandstillOracleConfig(miss_probability=p)).standstill.t[::2]
        )

    assert starts(0.3) == starts(0.3)
    assert starts(0.3) <= starts(0.1) <= starts(0.0)
    assert starts(1.0) == set()


def test_oracle_config_in_the_scenario_schema():
    import json

    from throughtunnel.scenario import scenario_from_json
    from throughtunnel.sensors.standstill import StandstillOracleConfig

    cfg = load_preset("synthetic_demo_track")
    assert cfg.standstill_oracle == StandstillOracleConfig() and cfg.standstill_oracle.perfect
    edited = cfg.model_copy(update={"standstill_oracle": StandstillOracleConfig(delay_s=2.0)})
    assert scenario_from_json(edited.model_dump_json()).standstill_oracle.delay_s == 2.0
    old = json.loads(cfg.model_dump_json())
    old.pop("standstill_oracle")
    old["schema_version"] = 10
    assert scenario_from_json(json.dumps(old)).standstill_oracle == StandstillOracleConfig()
