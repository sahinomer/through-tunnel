"""Map-feature fixes (step 5): curves inside the tunnel as position information for the route filter."""

import numpy as np
import pytest

from throughtunnel.evaluation.benchmark import (
    VERTEX_SPACING_M,
    Case,
    _polyline_length,
    run_config,
)
from throughtunnel.positioning import MAIN_ESTIMATORS
from throughtunnel.positioning.alignment import GpsImuAlignment
from throughtunnel.positioning.map_heading import MapHeading
from throughtunnel.positioning.route_kalman import HEADING_STEP_M, RouteKalman, RouteKalmanMap
from throughtunnel.positioning.runner import align_imu, replay
from throughtunnel.routing.synthetic import DEMO_APPROACH, DEMO_RECOVERY, Straight, synthetic_route
from throughtunnel.scenario import TunnelConfig, load_preset, run_scenario


def _replay_both(res):
    obs = res.observations()
    stream = align_imu(GpsImuAlignment(obs.route, res.config.calibration.rotation_error()), obs)
    kf, kf_map = RouteKalman(obs.route), RouteKalmanMap(obs.route)
    return replay(kf, obs, stream), replay(kf_map, obs, stream), kf_map


def test_registered_as_phone_only():
    assert MAIN_ESTIMATORS["route_kf_map"] is RouteKalmanMap
    assert not RouteKalmanMap.uses_standstill and not RouteKalmanMap.uses_vehicle_speed


def test_map_heading_is_smooth_and_follows_an_arc():
    """On an 800 m arc the smoothed map heading turns by the arc's angle and the curvature is ~1/800."""
    res = run_scenario(run_config(Case("ladder_2km", "flat", "free"), 0))
    route = res.route_map
    mh = MapHeading(route)
    b = route.tunnel_entrance_m
    arc_start, arc_len = b + 600.0, 300.0  # ladder: straight 30 %, then an arc of 15 % (2 km: 300 m)
    mid = arc_start + arc_len / 2
    assert abs(mh.curvature(mid)) == pytest.approx(1 / 800.0, rel=0.1)
    assert abs(mh.curvature(b + 300.0)) < 1e-5  # on the straight


def test_a_straight_tunnel_gives_no_position_information():
    """Straight tunnel: heading only calibrates the gyro drift, so d equals route_kf's exactly until C."""
    length = 3000.0
    route = synthetic_route([*DEMO_APPROACH, Straight(length), *DEMO_RECOVERY], "straight-3km",
                            vertex_spacing_m=VERTEX_SPACING_M)  # fmt: skip
    entrance = _polyline_length(DEMO_APPROACH)
    base = load_preset("synthetic_demo_track")
    cfg = base.model_copy(update={
        "name": "straight tunnel", "route": route,
        "tunnel": TunnelConfig(entrance_m=entrance, exit_m=entrance + length, announce_before_exit_m=300.0),
    })  # fmt: skip
    res = run_scenario(cfg)
    track, track_map, kf_map = _replay_both(res)
    inside = track.t < res.sections.exit_t
    assert kf_map.heading_updates > 50  # the heading channel did run
    assert np.max(np.abs(track_map.route_distance[inside] - track.route_distance[inside])) < 1e-6


def test_one_heading_measurement_per_25_m_driven():
    """The trigger counts distance driven, not the estimate (an update moves the estimate; a trigger on it
    fired again at once and ran away in validation)."""
    res = run_scenario(run_config(Case("ladder_5km", "flat", "stop_and_go"), 0))
    _, _, kf_map = _replay_both(res)
    driven = res.sections.exit_s - res.sections.entrance_s
    total = kf_map.heading_updates + kf_map.heading_rejected
    assert total == pytest.approx(driven / HEADING_STEP_M, rel=0.1)


def test_curves_bound_the_error_in_a_curved_tunnel():
    """5 km ladder (two S-arcs), a run where route_kf ends far off: the curve fixes bring it within ~30 m."""
    res = run_scenario(run_config(Case("ladder_5km", "flat", "free"), 1))
    track, track_map, _ = _replay_both(res)
    sec = res.sections

    def error_at_c(tr) -> float:
        i = int(np.searchsorted(tr.t, sec.exit_t))
        e, n = res.route_map.enu_at(tr.route_distance[i])
        k = int(np.searchsorted(res.truth.t, tr.t[i]))
        return float(np.hypot(e - res.truth.x[k], n - res.truth.y[k]))

    assert error_at_c(track) > 100.0
    assert error_at_c(track_map) < 40.0
