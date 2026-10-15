"""Map grade (D39): the map's grade data is exact, switching it on changes only the estimators, and
it removes the gravity leakage of a sloped road from every IMU estimator."""

import json
import math

import numpy as np
import pytest

from throughtunnel.evaluation.experiment import compare_estimators
from throughtunnel.evaluation.slope_study import PROFILES, ideal_sensors, profile_config
from throughtunnel.observations import RouteMap
from throughtunnel.positioning import ESTIMATORS, MAIN_ESTIMATORS, align_imu, run_estimator
from throughtunnel.positioning.alignment import GpsImuAlignment
from throughtunnel.positioning.map_grade import GradeCompensation, grade_compensation
from throughtunnel.scenario import (
    MapDataConfig,
    load_preset,
    run_scenario,
    scenario_from_json,
    with_map_data,
    with_sensor_config,
)

BY_KEY = {p.key: p for p in PROFILES}
ON, OFF = MapDataConfig(road_grade=True), MapDataConfig()


def sloped(preset: str, key: str, ideal: bool = True):
    cfg = load_preset(preset)
    base = run_scenario(cfg.model_copy(update={"road_profile": profile_config(cfg, BY_KEY[key])}))
    if not ideal:
        return base
    imu, gnss = ideal_sensors(cfg)
    return with_sensor_config(base, imu=imu, gnss=gnss)


def exit_errors(result) -> dict[str, float]:
    return {e.name: e.summary["exit_total_m"] for e in compare_estimators(result).evaluations}


def test_route_map_grade_lookup_interpolates_and_holds_the_ends():
    rm = RouteMap(
        lat=np.array([0.0, 0.0]),
        lon=np.array([0.0, 0.001]),
        tunnel_entrance_m=0.0,
        tunnel_exit_m=0.0,
        road_grade=np.array([0.0, 0.02, 0.04]),
        grade_step_m=10.0,
    )
    assert rm.has_grade
    assert rm.grade_at(5.0) == pytest.approx(0.01)
    assert rm.grade_at(15.0) == pytest.approx(0.03)
    assert rm.grade_at(-3.0) == 0.0 and rm.grade_at(1e6) == 0.04
    no_grade = RouteMap(lat=rm.lat, lon=rm.lon, tunnel_entrance_m=0.0, tunnel_exit_m=0.0)
    assert not no_grade.has_grade and grade_compensation(no_grade) is None
    with pytest.raises(ValueError):
        GradeCompensation(no_grade)
    with pytest.raises(ValueError):
        RouteMap(lat=rm.lat, lon=rm.lon, tunnel_entrance_m=0.0, tunnel_exit_m=0.0, road_grade=np.array([0.0]))


def test_default_map_has_no_grade_and_the_switch_round_trips():
    cfg = load_preset("synthetic_demo_track")
    assert cfg.map_data == OFF
    assert run_scenario(cfg).route_map.road_grade is None
    on = cfg.model_copy(update={"map_data": ON})
    assert scenario_from_json(on.model_dump_json()).map_data == ON
    old = json.loads(cfg.model_dump_json())  # a v8 file has no map_data: it loads with the default
    old.pop("map_data")
    old["schema_version"] = 8
    assert scenario_from_json(json.dumps(old)).map_data == OFF


@pytest.mark.parametrize("preset", ["seattle_sr99_tunnel", "eisenhower_tunnel"])
def test_map_grade_is_the_true_grade_at_the_vehicle_position(preset):
    """Exact map (D39), including near polyline corners where map and driven distance diverge."""
    res = with_map_data(sloped(preset, "v4", ideal=False), ON)
    rm, tr = res.route_map, res.truth
    east, north = tr.x[::200], tr.y[::200]
    d_prev, errors = 0.0, []
    for e, n, g in zip(east, north, tr.grade[::200], strict=True):
        d_prev = rm.project_enu(e, n, lo_m=max(d_prev - 50.0, 0.0), hi_m=d_prev + 500.0)[0]
        errors.append(rm.grade_at(d_prev) - g)
    assert np.max(np.abs(errors)) < 2e-4  # vs 4 % grade; the rest is the 10 m sampling


def test_switching_the_map_grade_changes_no_simulated_data():
    res = sloped("synthetic_demo_track", "up2", ideal=False)
    on = with_map_data(res, ON)
    assert on.imu is res.imu and on.gnss is res.gnss and on.truth is res.truth
    assert on.config.map_data == ON and on.route_map.has_grade
    assert with_map_data(on, OFF).route_map.road_grade is None


def test_map_grade_on_a_flat_road_changes_no_estimate():
    """A flat map grade is zero everywhere, so every estimate is bit-identical to running without it."""
    res = run_scenario(load_preset("synthetic_demo_track"))  # realistic sensors
    on = with_map_data(res, ON)
    assert not np.any(on.route_map.road_grade)
    for name, cls in ESTIMATORS.items():
        a = run_estimator(cls(res.route_map), res.observations())
        b = run_estimator(cls(on.route_map), on.observations())
        assert np.array_equal(a.east, b.east) and np.array_equal(a.north, b.north), name


def test_alignment_reports_the_grade_it_calibrated_in():
    res = with_map_data(sloped("synthetic_demo_track", "steady"), ON)
    stage = GpsImuAlignment(res.route_map)
    align_imu(stage, res.observations())
    assert stage.alignment.calibration_grade_angle == pytest.approx(math.atan(0.02), rel=1e-3)


@pytest.mark.parametrize("key", ["up2", "down2", "v4", "steady"])
def test_map_grade_removes_the_gravity_leakage_with_ideal_sensors(key):
    res = sloped("synthetic_demo_track", key)
    off, on = exit_errors(res), exit_errors(with_map_data(res, ON))
    for name in ("dr_raw", "dr_calibrated", "dr_filtered", "route_imu"):
        assert on[name] < 10.0, (name, on[name])
        if key != "steady" or name == "dr_raw":  # a steady climb is absorbed by the levelling anyway
            assert off[name] > 300.0, (name, off[name])
    assert on["route_hold"] == off["route_hold"]  # no IMU, no change


def test_study_pairs_each_run_with_the_grade_off_and_on():
    from throughtunnel.evaluation.map_grade_study import run_records

    res = sloped("synthetic_demo_track", "up2")
    records, curves = run_records(res, {"preset": "synthetic_demo_track", "sensors": "ideal", "seed": 0})
    by = {(r["map_grade"], r["estimator"]): r for r in records}
    assert len(records) == 2 * len(MAIN_ESTIMATORS) and set(curves) == set(by)  # the study is phone-only
    assert by[(True, "route_hold")]["exit_total_m"] == by[(False, "route_hold")]["exit_total_m"]
    assert by[(True, "route_imu")]["exit_total_m"] < 0.05 * by[(False, "route_imu")]["exit_total_m"]
