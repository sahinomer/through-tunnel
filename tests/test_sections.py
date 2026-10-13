"""A–D route structure: tunnel B–C, exit announcement point, map vs. truth, hidden crossing times."""

import json
from importlib import resources

import numpy as np
import pytest
from pydantic import ValidationError

from throughtunnel.observations import RouteMap
from throughtunnel.routing.osrm import parse_osrm_response
from throughtunnel.routing.synthetic import Straight, synthetic_route
from throughtunnel.scenario import (
    DEFAULT_ANNOUNCE_BEFORE_EXIT_M,
    ScenarioConfig,
    TunnelConfig,
    load_preset,
    run_scenario,
    scenario_warnings,
    truth_at,
)


@pytest.fixture(scope="module")
def demo():
    return run_scenario(load_preset("synthetic_demo_track"))


def test_route_map_is_the_original_polyline(demo):
    coords = np.asarray(demo.config.route.coordinates)
    assert np.array_equal(demo.route_map.lat, coords[:, 0]) and np.array_equal(
        demo.route_map.lon, coords[:, 1]
    )
    assert demo.route_map.tunnel_entrance_m == pytest.approx(demo.config.tunnel.entrance_m)
    rm = demo.route_map
    assert rm.announce_before_exit_m == DEFAULT_ANNOUNCE_BEFORE_EXIT_M == 300.0
    assert rm.announcement_m == pytest.approx(rm.tunnel_exit_m - 300.0)  # measured from the physical exit C


def test_section_truth_locates_b_and_c_on_the_true_path(demo):
    sec, rm = demo.sections, demo.route_map
    for d, s_true, t_true in (
        (rm.tunnel_entrance_m, sec.entrance_s, sec.entrance_t),
        (rm.tunnel_exit_m, sec.exit_s, sec.exit_t),
    ):
        tr = truth_at(demo, [t_true])
        map_point = np.array(rm.enu_at(d))
        # The vehicle is at the map point when the hidden crossing time says so (map vs. smoothed path < 1 m).
        assert np.hypot(tr.x[0] - map_point[0], tr.y[0] - map_point[1]) < 1.0
        assert tr.s[0] == pytest.approx(s_true, abs=1e-3)
        assert s_true == pytest.approx(d, abs=5.0)  # map and true arc lengths differ only slightly
    assert 0 < sec.entrance_t < sec.announcement_t < sec.exit_t


def test_true_announcement_point_is_the_set_distance_before_c(demo):
    sec = demo.sections
    assert sec.exit_s - sec.announcement_s == pytest.approx(300.0, abs=2.0)  # map vs. true arc length
    tr = truth_at(demo, [sec.announcement_t])
    assert tr.s[0] == pytest.approx(sec.announcement_s, abs=1e-3)


def test_tunnel_config_validation():
    with pytest.raises(ValidationError):
        TunnelConfig(entrance_m=1000.0, exit_m=900.0)
    with pytest.raises(ValidationError, match="within the tunnel length"):
        TunnelConfig(entrance_m=1000.0, exit_m=2000.0, announce_before_exit_m=1500.0)
    with pytest.raises(ValidationError):
        TunnelConfig(entrance_m=1000.0, exit_m=2000.0, announce_before_exit_m=-1.0)
    for d in (0.0, 1000.0):  # at C itself, and at B (the whole tunnel)
        tunnel = TunnelConfig(entrance_m=1000.0, exit_m=2000.0, announce_before_exit_m=d)
        assert tunnel.announce_before_exit_m == d
    with pytest.raises(ValueError, match="within the tunnel length"):
        RouteMap(
            lat=np.array([0.0, 0.0]), lon=np.array([0.0, 0.01]), tunnel_entrance_m=100.0, tunnel_exit_m=600.0,
            announce_before_exit_m=600.0,
        )  # fmt: skip


def test_announcement_is_capped_when_c_is_clipped_to_the_route_end():
    route = synthetic_route([Straight(3000.0)], "straight", 100.0)
    tunnel = TunnelConfig(entrance_m=1000.0, exit_m=5000.0, announce_before_exit_m=2500.0)
    rm = run_scenario(ScenarioConfig(route=route, tunnel=tunnel)).route_map
    assert rm.tunnel_exit_m == pytest.approx(3000.0)
    assert rm.announce_before_exit_m == pytest.approx(2000.0)
    assert rm.announcement_m == pytest.approx(1000.0)


def test_v4_files_drop_the_navigation_event_and_get_one_announcement():
    text = resources.files("throughtunnel.presets").joinpath("synthetic_demo_track.json").read_text()
    data = json.loads(text)
    tun = {k: v for k, v in data["tunnel"].items() if k != "announce_before_exit_m"}
    old_tunnel = {**tun, "exit_event_m": None, "announce_leads_m": [300.0, 0.0]}
    v4 = {**data, "schema_version": 4, "tunnel": old_tunnel}
    cfg = ScenarioConfig.model_validate(v4)
    assert cfg.tunnel.announce_before_exit_m == 300.0
    assert "exit_event_m" not in cfg.tunnel.model_dump()
    short = {**v4, "tunnel": {**old_tunnel, "exit_m": tun["entrance_m"] + 200.0}}
    assert ScenarioConfig.model_validate(short).tunnel.announce_before_exit_m == pytest.approx(200.0)


def test_warnings_for_bad_structure():
    route = synthetic_route([Straight(3000.0)], "straight", 100.0)
    ok = run_scenario(ScenarioConfig(route=route, tunnel=TunnelConfig(entrance_m=1000.0, exit_m=2500.0)))
    assert scenario_warnings(ok) == []
    short_tunnel = run_scenario(
        ScenarioConfig(route=route, tunnel=TunnelConfig(entrance_m=1000.0, exit_m=1300.0))
    )
    assert any("outside the 0.5–5 km" in w for w in scenario_warnings(short_tunnel))
    short_approach = run_scenario(
        ScenarioConfig(route=route, tunnel=TunnelConfig(entrance_m=100.0, exit_m=1500.0))
    )
    assert any("approach A–B lasts only" in w for w in scenario_warnings(short_approach))
    short_recovery = run_scenario(
        ScenarioConfig(route=route, tunnel=TunnelConfig(entrance_m=1000.0, exit_m=2950.0))
    )
    assert any("recovery section" in w for w in scenario_warnings(short_recovery))


def test_no_tunnel_means_gps_everywhere():
    res = run_scenario(ScenarioConfig(route=synthetic_route([Straight(1000.0)], "s", 100.0)))
    assert res.sections is None
    assert (
        res.route_map.tunnel_entrance_m
        == res.route_map.tunnel_exit_m
        == pytest.approx(res.route_map.length_m)
    )
    assert "No tunnel section" in scenario_warnings(res)[0]


def test_route_map_projection():
    rm = RouteMap(
        lat=np.array([0.0, 0.0, 0.0]),
        lon=np.array([0.0, 0.009, 0.018]),
        tunnel_entrance_m=500.0,
        tunnel_exit_m=1500.0,
    )  # straight eastward line, ~2 km
    along, offset = rm.project_enu(700.0, 12.0)
    assert along == pytest.approx(700.0, abs=1e-6) and offset == pytest.approx(
        12.0, abs=1e-6
    )  # + = left (north)
    assert rm.project_enu(700.0, -3.0)[1] == pytest.approx(-3.0)
    assert rm.project_enu(-50.0, 0.0)[0] == 0.0
    assert rm.project_enu(700.0, 0.0, lo_m=900.0)[0] == pytest.approx(900.0)  # search window respected
    assert rm.heading_at(100.0) == pytest.approx(0.0, abs=1e-6)  # east
    lat, lon = rm.latlon_at(1000.0)
    assert rm.locate(lat, lon) == pytest.approx(1000.0, abs=1e-3)


def test_truth_at_is_exact_and_phone_point(demo):
    tr = demo.truth
    again = truth_at(demo, tr.t[::50])
    assert np.allclose(again.x, tr.x[::50], atol=1e-9) and np.allclose(again.yaw, tr.yaw[::50], atol=1e-12)
    phone = tr.point_enu((2.0, 0.5, 1.0))
    expect_x = tr.x + 2.0 * np.cos(tr.yaw) - 0.5 * np.sin(tr.yaw)
    assert np.allclose(phone[:, 0], expect_x) and np.allclose(phone[:, 2], 1.0)


def test_road_path_projection(demo):
    path = demo.path
    for s in (10.0, 1234.5, 3999.0):
        xy = path.evaluate(s).xy
        assert path.project(xy[0], xy[1]) == pytest.approx(s, abs=1e-6)


def test_osrm_waypoints_are_kept():
    data = {
        "code": "Ok",
        "waypoints": [
            {"location": [10.0, 50.0]},
            {"location": [10.001, 50.0]},
            {"location": [10.002, 50.001]},
        ],
        "routes": [
            {
                "distance": 200.0,
                "duration": 20.0,
                "geometry": {"coordinates": [[10.0, 50.0], [10.001, 50.0], [10.002, 50.001]]},
                "legs": [{"distance": 71.0, "steps": []}, {"distance": 129.0, "steps": []}],
            }
        ],
    }
    route = parse_osrm_response(data)
    assert route.metadata["waypoints"][1] == {"lat": 50.0, "lon": 10.001}
    assert route.metadata["leg_distances_m"] == [71.0, 129.0]


def test_u_turn_routes_are_rejected():
    from throughtunnel.routing.synthetic import Corner

    route = synthetic_route([Straight(800.0), Corner(179.0), Straight(800.0)], "u-turn", 50.0)
    cfg = ScenarioConfig(route=route, tunnel=TunnelConfig(entrance_m=200.0, exit_m=1400.0))
    from throughtunnel.scenario import build_route_map, has_u_turn

    assert has_u_turn(build_route_map(cfg))
    with pytest.raises(ValueError, match="U-turn"):
        run_scenario(cfg)
    assert not has_u_turn(build_route_map(load_preset("seattle_sr99_tunnel")))
