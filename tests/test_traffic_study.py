"""The traffic study's bookkeeping: stops, standing time and route-end capping are recorded correctly."""

from throughtunnel.evaluation.slope_study import ideal_sensors
from throughtunnel.evaluation.traffic_study import _capped, run_records
from throughtunnel.scenario import load_preset, run_scenario, with_sensor_config
from throughtunnel.vehicle.traffic import TrafficConfig


def test_records_for_stop_and_go_with_ideal_sensors():
    cfg = load_preset("synthetic_demo_track")
    base = run_scenario(cfg.model_copy(update={"traffic": TrafficConfig(scenario="stop_and_go", seed=0)}))
    imu, gnss = ideal_sensors(cfg)
    recs = {r["estimator"]: r for r in run_records(with_sensor_config(base, imu=imu, gnss=gnss), {"tag": 1})}
    dc, hold = recs["dr_calibrated"], recs["route_hold"]
    assert dc["standing_s"] > 30.0 and dc["tunnel_time_s"] > 200.0 and dc["outage_s"] > dc["tunnel_time_s"]
    assert dc["exit_total_m"] < 10.0  # perfect sensors measure the stops: the IMU follows them
    assert hold["route_end_reached"] and not dc["route_end_reached"]  # speed hold overruns to D
    assert hold["exit_total_m"] > 500.0


def test_capped_values_are_marked_as_lower_bounds():
    capped, free = {"route_end_reached": True}, {"route_end_reached": False}
    assert _capped("782", [capped, capped, free]) == "≥782 §2"
    assert _capped("30", [free, free, capped]) == "30 §1"
    assert _capped("30", [free]) == "30"
