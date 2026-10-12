import numpy as np
import pytest
from helpers import enu_to_route

from throughtunnel.road import RoadConfig, RoadPath, point_to_polyline_distance
from throughtunnel.routing.synthetic import Arc, Corner, Straight, build_enu_polyline, synthetic_route
from throughtunnel.scenario import list_presets, load_preset, run_scenario


def test_synthetic_arc_endpoints():
    left = build_enu_polyline([Arc(100.0, 90.0)], 1.0)
    right = build_enu_polyline([Arc(100.0, -90.0)], 1.0)
    assert np.allclose(left[-1], [100.0, 100.0], atol=1e-9)
    assert np.allclose(right[-1], [100.0, -100.0], atol=1e-9)


def test_straight_road_is_exact():
    route = synthetic_route([Straight(1000.0)], "straight", vertex_spacing_m=50.0, initial_heading_deg=30.0)
    path = RoadPath.from_route(route)
    st = path.evaluate(path.grid_s)
    assert path.length_m == pytest.approx(1000.0, abs=1e-3)
    assert np.abs(st.curvature).max() < 1e-6  # numerical floor of the smoother (R > 1000 km)
    assert np.allclose(st.yaw, np.radians(30.0), atol=1e-8)
    assert path.diagnostics.max_deviation_m < 1e-6


def test_arc_length_parametrisation():
    for preset in list_presets():
        path = RoadPath.from_route(load_preset(preset).route)
        assert np.abs(path.tangent_norm(path.grid_s) - 1.0).max() < 1e-5


def test_circle_curvature_recovered():
    radius = 200.0
    route = synthetic_route([Straight(200.0), Arc(radius, 270.0), Straight(200.0)], "circle", 2.0)
    path = RoadPath.from_route(route, RoadConfig(smoothing_wavelength_m=60.0))
    st = path.evaluate(path.grid_s)
    inside = (st.s > 260.0) & (st.s < 200.0 + radius * np.radians(270.0) - 60.0)
    assert st.curvature[inside] * radius == pytest.approx(1.0, abs=0.03)
    assert path.diagnostics.max_deviation_m < 0.5
    # Total heading change equals the arc angle.
    assert st.yaw[-1] - st.yaw[0] == pytest.approx(np.radians(270.0), abs=np.radians(0.5))


def test_uneven_node_spacing_and_jitter_do_not_create_curvature_ripple(uneven_jittered_circle):
    """A naive approach yields ±50-150 % curvature ripple here (fake oscillating yaw rate)."""
    route, radius, (s0, s1) = uneven_jittered_circle
    path = RoadPath.from_route(route)
    st = path.evaluate(path.grid_s)
    inside = (st.s > s0) & (st.s < s1)
    kr = st.curvature[inside] * radius
    assert kr.min() > 0.88
    assert kr.max() < 1.12
    assert path.diagnostics.max_deviation_m < 1.5


def test_sharp_corner_is_rounded_with_bounded_cut():
    cfg = RoadConfig()
    route = synthetic_route([Straight(300.0), Corner(90.0), Straight(300.0)], "corner", 100.0)
    path = RoadPath.from_route(route, cfg)
    st = path.evaluate(path.grid_s)
    # Heading is continuous (no jump at the vertex) and turns by exactly 90°.
    assert np.abs(np.diff(st.yaw)).max() < 0.15  # per 1 m step
    assert st.yaw[-1] - st.yaw[0] == pytest.approx(np.pi / 2, abs=np.radians(0.15))
    # Finite curvature with a car-like turn radius; corner cut bounded by the configuration.
    assert 5.0 < path.diagnostics.min_radius_m < 30.0
    assert path.diagnostics.max_deviation_m <= cfg.max_corner_cut_m + cfg.smoothing_corridor_m + 0.1


def test_curvature_is_continuous_on_real_tunnels():
    """Inside the real tunnels (B–C): smooth, gentle highway geometry close to the map polyline."""
    for preset in ("seattle_sr99_tunnel", "eisenhower_tunnel"):
        res = run_scenario(load_preset(preset))
        path, sec = res.path, res.sections
        s = path.grid_s[(path.grid_s > sec.entrance_s) & (path.grid_s < sec.exit_s)]
        st = path.evaluate(s)
        assert np.abs(np.diff(st.curvature)).max() < 2e-4  # per metre: no curvature steps
        assert np.abs(st.curvature).max() < 1 / 300.0
        assert point_to_polyline_distance(st.xy[::10], path.reference_enu).max() < 1.5
        assert 500.0 <= sec.exit_s - sec.entrance_s <= 5000.0


def test_duplicates_and_spikes_removed():
    pts = np.array(
        [[0, 0], [100, 0], [100.1, 0], [200, 0], [210, 0.5], [205, 0.4], [300, 0], [400, 0]], float
    )
    path = RoadPath.from_route(enu_to_route(pts))
    d = path.diagnostics
    assert d.removed_duplicates == 1
    assert d.removed_spikes >= 1
    assert path.length_m == pytest.approx(400.0, abs=0.5)
    assert d.min_radius_m > 50.0


def test_point_to_polyline_distance():
    poly = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0]])
    q = np.array([[5.0, 3.0], [12.0, 5.0], [-4.0, 3.0], [15.0, 15.0]])
    assert np.allclose(point_to_polyline_distance(q, poly), [3.0, 2.0, 5.0, np.hypot(5.0, 5.0)])


def test_too_short_road_rejected():
    with pytest.raises(ValueError, match="too short"):
        RoadPath.from_route(enu_to_route(np.array([[0.0, 0.0], [5.0, 0.0]])))
