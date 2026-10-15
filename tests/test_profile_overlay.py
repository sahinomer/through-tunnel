"""Road profile overlay on the map: the data it draws (display only)."""

import numpy as np
import pytest

from throughtunnel.app.profile_overlay import overlay_figure, route_heights, truth_route_distance
from throughtunnel.evaluation.slope_study import PROFILES, profile_config
from throughtunnel.road_profile import ElevationProfile
from throughtunnel.scenario import load_preset, run_scenario

V4 = next(p for p in PROFILES if p.key == "v4")


@pytest.fixture(scope="module")
def sloped():
    cfg = load_preset("synthetic_demo_track")
    return run_scenario(cfg.model_copy(update={"road_profile": profile_config(cfg, V4)}))


def test_heights_follow_the_road_profile(sloped):
    d, z = route_heights(sloped)
    assert d[0] == 0.0 and d[-1] == pytest.approx(sloped.route_map.length_m)
    expected = ElevationProfile.from_config(sloped.config.road_profile).evaluate(d)[0]
    assert np.allclose(z, expected)
    flat = run_scenario(load_preset("synthetic_demo_track"))
    assert not np.any(route_heights(flat)[1])


def test_vehicle_distance_along_the_map_matches_the_driven_distance(sloped):
    t, d = truth_route_distance(sloped)
    s = np.interp(t, sloped.truth.t, sloped.truth.s)
    assert np.max(np.abs(d - s)) < 15.0  # map vs driven distance differ by corner cuts only
    assert np.all(np.diff(d) > -1.0)  # never jumps backwards


def test_figure_has_one_marker_trace_per_object(sloped):
    fig = overlay_figure(sloped, ["dr_raw", "route_imu"])
    assert len(fig["data"]) == 1 + 1 + 2  # height line, vehicle, two estimators
    tunnel = fig["layout"]["shapes"][0]
    rm = sloped.route_map
    expected = (rm.tunnel_entrance_m / 1000, rm.tunnel_exit_m / 1000)
    assert (tunnel["x0"], tunnel["x1"]) == pytest.approx(expected)
