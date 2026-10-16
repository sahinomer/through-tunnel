"""The road-slope study: its profiles are what their labels say, and its gravity-leakage prediction holds."""

import numpy as np
import pytest

from throughtunnel.evaluation.slope_study import (
    PROFILES,
    ideal_sensors,
    predicted_speed_error,
    profile_config,
    run_records,
)
from throughtunnel.road_profile import ElevationProfile
from throughtunnel.scenario import build_route_map, load_preset, run_scenario, with_sensor_config

BY_KEY = {p.key: p for p in PROFILES}


@pytest.mark.parametrize("key", [p.key for p in PROFILES])
def test_profiles_are_valid_and_shaped_as_labelled(key):
    cfg = load_preset("seattle_sr99_tunnel")
    prof_cfg = profile_config(cfg, BY_KEY[key])
    if key == "flat":
        assert prof_cfg.is_flat
        return
    rm = build_route_map(cfg)
    prof = ElevationProfile.from_points(prof_cfg.points)
    assert prof.max_grade() <= 0.06
    mid = 0.5 * (rm.tunnel_entrance_m + rm.tunnel_exit_m)
    approach_grade = prof.evaluate([0.5 * rm.tunnel_entrance_m])[1][0]
    if key == "steady":
        assert approach_grade == pytest.approx(0.02, abs=1e-3)
    else:  # tunnel profiles start from a level approach
        assert abs(approach_grade) < 1e-6
    if key.startswith(("up", "down")):
        design = {"up1": 0.01, "up2": 0.02, "up4": 0.04, "down2": -0.02}[key]
        assert prof.evaluate([mid])[1][0] == pytest.approx(design, rel=0.1)


def test_gravity_leakage_prediction_matches_the_estimator(monkeypatch):
    # The slope study predates the portal freeze (D46): its predictor takes the calibration up to GPS loss.
    from throughtunnel.positioning import portal

    monkeypatch.setattr(portal, "FREEZE_BEFORE_ENTRANCE_M", None)
    cfg = load_preset("synthetic_demo_track")
    base = run_scenario(cfg.model_copy(update={"road_profile": profile_config(cfg, BY_KEY["up2"])}))
    imu, gnss = ideal_sensors(cfg)
    res = with_sensor_config(base, imu=imu, gnss=gnss)
    records, _ = run_records(res, BY_KEY["up2"], "ideal", 0, "synthetic_demo_track")
    dc = next(r for r in records if r["estimator"] == "dr_calibrated")
    assert dc["speed_error_mps"] == pytest.approx(predicted_speed_error(res), rel=0.01)
    assert abs(dc["heading_error_deg"]) < 0.05  # the slope leaves the heading intact
    assert np.isfinite(dc["exit_total_m"]) and dc["exit_along_m"] > 500.0  # ahead on a climb
