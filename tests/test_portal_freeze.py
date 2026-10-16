"""Portal freeze (D46): no GPS learning in the zone [B − 200 m, C].

Inside the zone the GPS + IMU alignment keeps its orientation, and the GPS-blending estimators keep
their speed (and heading) from the IMU: GPS speed and bearing there must not change their output.
"""

from dataclasses import replace

import numpy as np
import pytest

from throughtunnel.observations import Observations
from throughtunnel.positioning import ESTIMATORS, align_imu, portal, run_estimators
from throughtunnel.positioning.alignment import GpsImuAlignment
from throughtunnel.positioning.portal import PortalFreeze, portal_freeze
from throughtunnel.scenario import load_preset, run_scenario

ZONE_M = portal.FREEZE_BEFORE_ENTRANCE_M  # the default, before any test switches it off


@pytest.fixture(scope="module")
def demo():
    return run_scenario(load_preset("synthetic_demo_track"))


def _zone_mask(res, obs: Observations):
    """Fixes the vehicle took inside the zone (truth distance, 1 s margin at the zone start)."""
    s_zone = res.sections.entrance_s - ZONE_M
    t_zone = float(np.interp(s_zone, res.motion.s, res.motion.t))
    return (obs.gnss.t > t_zone + 1.0) & (obs.gnss.t < res.sections.exit_t)


def _perturbed_speed_and_bearing(res) -> tuple[Observations, Observations]:
    obs = res.observations()
    zone = _zone_mask(res, obs)
    assert zone.sum() >= 5
    gnss = replace(
        obs.gnss,
        speed_mps=np.where(zone, obs.gnss.speed_mps + 3.0, obs.gnss.speed_mps),
        bearing_deg=np.where(zone, obs.gnss.bearing_deg + 10.0, obs.gnss.bearing_deg),
    )
    return obs, Observations(obs.imu, gnss, obs.route)


def test_zone_spans_from_before_b_to_c(demo):
    route = demo.route_map
    zone = portal_freeze(route)
    assert isinstance(zone, PortalFreeze)
    assert zone.start_m == pytest.approx(route.tunnel_entrance_m - 200.0)
    assert zone.end_m == route.tunnel_exit_m
    assert not zone.active(None)
    assert not zone.active(zone.start_m - 1.0) and zone.active(zone.start_m) and zone.active(zone.end_m)
    assert not zone.active(zone.end_m + 1.0)


def test_freeze_can_be_switched_off(demo, monkeypatch):
    monkeypatch.setattr(portal, "FREEZE_BEFORE_ENTRANCE_M", None)
    assert portal_freeze(demo.route_map) is None


def test_no_zone_without_a_tunnel(demo):
    end = demo.route_map.length_m
    route = replace(demo.route_map, tunnel_entrance_m=end, tunnel_exit_m=end, announce_before_exit_m=None)
    assert portal_freeze(route) is None


def test_calibration_ignores_gps_in_the_zone(demo):
    obs, perturbed = _perturbed_speed_and_bearing(demo)
    a = align_imu(GpsImuAlignment(obs.route), obs)
    b = align_imu(GpsImuAlignment(obs.route), perturbed)
    assert a == b


def test_calibration_learns_in_the_zone_when_off(demo, monkeypatch):
    monkeypatch.setattr(portal, "FREEZE_BEFORE_ENTRANCE_M", None)
    obs, perturbed = _perturbed_speed_and_bearing(demo)
    assert align_imu(GpsImuAlignment(obs.route), obs) != align_imu(GpsImuAlignment(obs.route), perturbed)


@pytest.mark.parametrize("name", ["dr_filtered", "route_imu"])
def test_blending_estimators_carry_speed_through_the_zone(demo, name):
    obs, perturbed = _perturbed_speed_and_bearing(demo)
    a, b = (run_estimators([ESTIMATORS[name](o.route)], o)[0] for o in (obs, perturbed))
    for field in ("east", "north", "speed", "heading", "route_distance"):
        assert np.array_equal(getattr(a, field), getattr(b, field)), field


def test_route_imu_blends_in_the_zone_when_off(demo, monkeypatch):
    monkeypatch.setattr(portal, "FREEZE_BEFORE_ENTRANCE_M", None)
    obs, perturbed = _perturbed_speed_and_bearing(demo)
    a, b = (run_estimators([ESTIMATORS["route_imu"](o.route)], o)[0] for o in (obs, perturbed))
    assert not np.array_equal(a.speed, b.speed)


def test_calibration_resumes_after_c(demo):
    obs = demo.observations()
    stage = GpsImuAlignment(obs.route)
    align_imu(stage, obs)
    last_row_t = stage._solver._rows[-1][7]
    assert last_row_t > demo.sections.exit_t  # fixes after C are used again
