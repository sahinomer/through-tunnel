"""Road elevation profile (D36): the curve, its limits, the editing helpers and the 3-D ground truth.

The IMU on a sloped road is validated end to end in test_sensors.py (numerical differentiation of
the phone pose).
"""

import numpy as np
import pytest
from pydantic import ValidationError

from throughtunnel.evaluation.metrics import evaluate_track
from throughtunnel.positioning import ESTIMATORS, run_estimator
from throughtunnel.road_profile import (
    TEMPLATES,
    ElevationProfile,
    RoadProfileConfig,
    clamp_height,
    point_distances,
    template_heights,
)
from throughtunnel.scenario import ScenarioConfig, load_preset, run_scenario, scenario_from_json
from throughtunnel.sensors.errors import ImuErrorConfig
from throughtunnel.sensors.gnss import GnssConfig


def profile_config(distances, heights, **kw) -> RoadProfileConfig:
    return RoadProfileConfig(
        points=tuple(zip(np.asarray(distances).tolist(), np.asarray(heights).tolist(), strict=True)), **kw
    )


def with_template(cfg: ScenarioConfig, name: str) -> ScenarioConfig:
    length = run_scenario(cfg).route_map.length_m
    d = point_distances(length, cfg.tunnel.entrance_m, cfg.tunnel.exit_m)
    z = template_heights(name, d, cfg.tunnel.entrance_m, cfg.tunnel.exit_m, 0.06)
    return cfg.model_copy(update={"road_profile": profile_config(d, z)})


# ------------------------------------------------------------------ the curve
def test_curve_passes_through_points_without_overshoot():
    d = np.array([0.0, 200.0, 400.0, 600.0, 800.0, 1000.0])
    z = np.array([0.0, 0.0, 5.0, 5.0, 2.0, 2.0])
    prof = ElevationProfile(d, z)
    assert np.allclose(prof.evaluate(d)[0], z)
    s = np.linspace(0.0, 1000.0, 2001)
    h = prof.evaluate(s)[0]
    assert h.min() >= -1e-9 and h.max() <= 5.0 + 1e-9  # no invented hills or dips
    assert np.all(np.diff(h[(s >= 200) & (s <= 400)]) >= -1e-12)  # monotone where the data is


def test_grade_and_vertical_curvature_are_continuous():
    d = np.arange(0.0, 1201.0, 200.0)
    prof = ElevationProfile(d, [0.0, 1.0, 6.0, 8.0, 7.0, 3.0, 3.0])
    for knot in d[1:-1]:
        before, after = prof.evaluate([knot - 1e-6])[1:3], prof.evaluate([knot + 1e-6])[1:3]
        assert np.allclose(before, after, atol=1e-8)  # grade and z'' both continuous (C2)
    z, g, c, r = prof.evaluate([-50.0, 1250.0])  # beyond the ends: straight with the end grade
    assert np.allclose(c, 0.0) and np.allclose(r, 0.0)
    assert z[1] == pytest.approx(3.0 + g[1] * 50.0)


def test_grade_limit_is_validated():
    with pytest.raises(ValidationError, match="above the 6% limit"):
        profile_config([0.0, 100.0, 200.0], [0.0, 10.0, 10.0])  # 10 % on average
    assert profile_config([0.0, 100.0, 200.0], [0.0, 3.0, 3.0]).points
    with pytest.raises(ValidationError):
        RoadProfileConfig(points=((0.0, 0.0), (0.0, 1.0)))  # distances must increase
    assert RoadProfileConfig().is_flat and profile_config([0.0, 10.0], [4.0, 4.0]).is_flat


def test_clamp_keeps_the_whole_profile_within_the_limit():
    d = np.arange(0.0, 1001.0, 200.0)
    h = np.zeros(len(d))
    clamped = clamp_height(d, h, 2, 100.0, 0.06)  # dragged far too high
    h[2] = clamped
    assert ElevationProfile(d, h).max_grade() == pytest.approx(0.06, rel=1e-6)  # as high as allowed
    assert 0.0 < clamped < 100.0
    assert clamp_height(d, np.zeros(len(d)), 2, 3.0, 0.06) == 3.0  # feasible drags are not changed


@pytest.mark.parametrize("name", list(TEMPLATES))
def test_templates_respect_the_limit_and_are_gentle(name):
    d = point_distances(5600.0, 1500.0, 4470.0)
    z = template_heights(name, d, 1500.0, 4470.0, 0.06)
    assert z[0] == 0.0
    if name != "flat":
        prof = ElevationProfile(d, z)
        assert prof.max_grade() <= 0.06
        assert prof.max_vertical_curvature() * 25.0**2 < 0.3  # vertical acceleration at 90 km/h
    tight = template_heights("underwater", d, 1500.0, 4470.0, 0.02)
    assert ElevationProfile(d, tight).max_grade() <= 0.02 * (1 + 1e-9)  # scaled down to a tighter limit


def test_point_distances_include_b_and_c():
    d = point_distances(5600.0, 1500.0, 4470.0)
    assert {0.0, 1500.0, 4470.0, 5600.0} <= set(d.tolist())
    assert np.diff(d).min() >= 0.4 * 200.0 and np.diff(d).max() <= 1.5 * 200.0  # about even


# ------------------------------------------------------------------ 3-D ground truth
@pytest.fixture(scope="module")
def underwater():
    return run_scenario(with_template(load_preset("synthetic_demo_track"), "underwater"))


def test_truth_follows_the_profile(underwater):
    tr, prof = underwater.truth, underwater.path.elevation
    z, g, _, _ = prof.evaluate(tr.s)
    assert np.allclose(tr.z, z) and np.allclose(tr.grade, g)
    assert np.allclose(np.tan(-tr.pitch), g)  # ISO pitch: + = nose down, so a climb has pitch < 0
    assert tr.z.min() < -25.0
    # Body x points along the 3-D velocity (the vehicle pitches with the road).
    x_b = tr.rotation_enu_from_body()[:, :, 0]
    v = tr.vel_enu
    assert np.allclose(x_b, v / np.linalg.norm(v, axis=1, keepdims=True), atol=1e-9)
    # The geodetic track carries the height (ENU up; ellipsoidal altitude also includes Earth
    # curvature), and the vertical velocity is dz/dt.
    enu = tr.frame.to_enu(tr.lat, tr.lon, tr.alt)
    assert np.abs(enu[:, 2] - tr.z).max() < 1e-6
    dt = 1.0 / tr.sample_rate_hz
    assert np.abs((tr.z[2:] - tr.z[:-2]) / (2 * dt) - v[1:-1, 2]).max() < 1e-3


def test_flat_profile_is_identical_to_no_profile():
    cfg = load_preset("synthetic_demo_track")
    a = run_scenario(cfg)
    b = run_scenario(cfg.model_copy(update={"road_profile": profile_config([0.0, 5000.0], [7.0, 7.0])}))
    assert b.path.elevation is None
    assert np.array_equal(a.imu.accel, b.imu.accel) and np.array_equal(a.truth.omega_body, b.truth.omega_body)


def test_scenario_round_trip_and_older_files_are_flat(underwater):
    cfg = underwater.config
    assert scenario_from_json(cfg.model_dump_json()).road_profile == cfg.road_profile
    v6 = cfg.model_dump(exclude={"road_profile"}) | {"schema_version": 6}
    assert ScenarioConfig.model_validate(v6).road_profile.is_flat


# ------------------------------------------------------------------ effect on positioning (sanity only)
def ideal(cfg: ScenarioConfig):
    imu = cfg.imu.model_copy(update={"errors": ImuErrorConfig.ideal()})
    return run_scenario(cfg.model_copy(update={"imu": imu, "gnss": GnssConfig.ideal()}))


def along_at_c(res, name="dr_calibrated") -> float:
    obs = res.observations()
    return evaluate_track(run_estimator(ESTIMATORS[name](obs.route), obs), res).summary["exit_along_m"]


def test_grade_change_after_calibration_leaks_gravity_but_a_constant_grade_does_not():
    """The calibration levels the phone on the approach. A constant grade along the whole route is
    absorbed; a grade that changes in the tunnel leaks g·sin(grade) into the forward channel (the
    estimate runs ahead on a climb), like a pitch calibration error of the same angle."""
    cfg = load_preset("synthetic_demo_track")
    steady = abs(along_at_c(ideal(with_template(cfg, "climb"))))
    climbing = along_at_c(ideal(with_template(cfg, "tunnel_climb")))
    assert steady < 5.0
    assert climbing > 300.0  # ~1/2 g sin(atan 0.03) t^2 over ~100 s, minus the transitions


# ------------------------------------------------------------------ editor (UI)
def test_drag_events_are_parsed_and_other_relayouts_ignored():
    from throughtunnel.app.profile_editor import dragged_heights

    assert dragged_heights({"shapes[3].xanchor": 1.2, "shapes[3].yanchor": 7.5}) == {3: 7.5}
    assert dragged_heights({"shapes[2].y0": 4.0, "shapes[2].y1": 6.0}) == {2: 5.0}
    assert dragged_heights({"xaxis.range[0]": 0.0, "autosize": True}) == {}


def test_only_the_points_are_draggable_shapes():
    from throughtunnel.app.profile_editor import profile_figure

    d = point_distances(5000.0, 1500.0, 4000.0)
    fig = profile_figure(d, np.zeros(len(d)), 1500.0, 4000.0, 0.06)
    shapes = fig["layout"]["shapes"]
    assert len(shapes) == len(d) and all(sh["type"] == "circle" for sh in shapes)
    assert [sh["xanchor"] for sh in shapes] == (d / 1000).tolist()
    assert fig["config"]["edits"] == {"shapePosition": True}
