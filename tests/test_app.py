"""UI-independent parts of the app: playback clock and figure building."""

import numpy as np
import pytest

from throughtunnel.app.playback import PlaybackController
from throughtunnel.app.plots import CURSOR_SHAPE_INDEX, cursor_relayout, ground_truth_figure
from throughtunnel.scenario import list_presets, load_preset, run_scenario


def test_playback_clock():
    pb = PlaybackController()
    pb.play()
    assert not pb.playing  # nothing loaded
    pb.load(10.0)
    assert (pb.t, pb.playing) == (0.0, False)
    assert not pb.advance(1.0)  # paused: time does not move
    pb.play()
    pb.speed = 2.0
    assert pb.advance(1.0) and pb.t == pytest.approx(2.0)
    pb.pause()
    pb.advance(1.0)
    assert pb.t == pytest.approx(2.0)
    pb.seek(99.0)
    assert pb.t == 10.0 and pb.at_end
    pb.seek(-5.0)
    assert pb.t == 0.0


def test_playback_stops_at_end_and_replays():
    pb = PlaybackController()
    pb.load(5.0)
    pb.play()
    pb.advance(10.0)
    assert pb.t == 5.0 and not pb.playing and pb.progress == 1.0
    pb.play()  # play at the end restarts from zero
    assert pb.t == 0.0 and pb.playing
    pb.advance(1.0)
    pb.restart()
    assert pb.t == 0.0 and pb.playing


def test_ground_truth_figure():
    res = run_scenario(load_preset("synthetic_demo_track"))
    fig = ground_truth_figure(res)
    assert len(fig.data) == 6
    # Display is decimated to ~10 Hz but spans the whole run.
    assert fig.data[0].x[-1] == pytest.approx(res.truth.duration_s, abs=0.2)
    assert len(fig.data[0].x) < len(res.truth) / 5
    assert fig.layout.shapes[CURSOR_SHAPE_INDEX].x0 == 0.0
    assert cursor_relayout(12.5) == {"shapes[0].x0": 12.5, "shapes[0].x1": 12.5}


def test_page_module_imports():
    from throughtunnel.app import page

    assert page.DEFAULT_PRESET in list_presets()


def test_playback_track_for_browser():
    from throughtunnel.app.track import HEADING_ARROW_M, playback_track

    tr = run_scenario(load_preset("synthetic_demo_track")).truth
    track = playback_track(tr, rate_hz=10.0)
    t = np.array(track["t"])
    assert t[0] == 0.0 and t[-1] == pytest.approx(tr.duration_s)  # covers the whole run
    assert np.all(np.diff(t) > 0) and np.diff(t).max() <= 0.1 + 1e-9
    assert {len(v) for v in track.values()} == {len(t)}
    # Positions are the ground truth (to the 1e-8 deg rounding), the heading tip is ahead of the vehicle.
    i = len(t) // 2
    k = int(np.argmin(np.abs(tr.t - t[i])))
    assert track["lat"][i] == pytest.approx(tr.lat[k], abs=1e-8)
    enu = tr.frame.to_enu(track["hlat"][i], track["hlon"][i])
    ahead = (enu[0] - tr.x[k]) * np.cos(tr.yaw[k]) + (enu[1] - tr.y[k]) * np.sin(tr.yaw[k])
    assert ahead == pytest.approx(HEADING_ARROW_M, abs=0.01)


def test_imu_figure():
    from throughtunnel.app.plots import MIN_SPAN_ACCEL, imu_figure

    res = run_scenario(load_preset("seattle_sr99_tunnel"))
    fig = imu_figure(res)
    assert len(fig.data) == 12  # measured + ideal for 3 accel and 3 gyro axes
    assert [d.name for d in fig.data[:2]] == ["measured", "ideal"]
    assert sum(d.showlegend for d in fig.data) == 2
    # accel z (gravity, varies ~1e-5 m/s^2 along the route) is not blown up by autoscaling
    lo, hi = fig.layout.yaxis3.range
    assert hi - lo >= MIN_SPAN_ACCEL
    assert lo < res.imu.accel[:, 2].min() and hi > res.imu.accel[:, 2].max()  # measured (noisy) fits


def test_readouts_render_for_a_preset():
    from throughtunnel.app.readouts import estimate_readout_html, route_info_html, state_readout_html

    res = run_scenario(load_preset("synthetic_demo_track"))
    info = route_info_html(res, res.config.route)
    assert "Tunnel B–C" in info and "fixes · outage" in info
    t = 0.5 * res.truth.duration_s
    state = state_readout_html(res.truth.sample(t), res.imu.at(t), res.imu_ideal.at(t))
    assert "speed" in state and "phone IMU" in state
    assert estimate_readout_html([], set(), t) == ""


def test_every_estimator_has_a_tooltip():
    """D57: each registered estimator says what it does and how information flows; the category comes from
    its declared inputs."""
    from throughtunnel.app.positioning_view import estimator_category, estimator_tooltip_html
    from throughtunnel.positioning import ESTIMATORS, ORACLE_ESTIMATORS, REFERENCE_ESTIMATORS

    for name, cls in ESTIMATORS.items():
        assert cls.description and "→" in cls.pipeline, name
        assert cls.pipeline in estimator_tooltip_html(cls).replace("&#x27;", "'")
        category = estimator_category(cls)
        if name in REFERENCE_ESTIMATORS:
            assert category.startswith("†")
        elif name in ORACLE_ESTIMATORS:
            assert category.startswith("‡")
        else:
            assert category == "phone-only"
    descriptions = [cls.description for cls in ESTIMATORS.values()]
    assert len(set(descriptions)) == len(descriptions)  # no text inherited by accident


def test_every_estimator_has_its_own_style():
    """D58: a colour and line style per registered estimator, no two alike; the four main phone-only
    estimators are solid, the greys are kept for the reference and the oracles."""
    from throughtunnel.app.positioning_view import ESTIMATOR_STYLES, color_of, dash_of
    from throughtunnel.positioning import ESTIMATORS, MAIN_ESTIMATORS

    assert set(ESTIMATOR_STYLES) == set(ESTIMATORS)
    assert len(set(ESTIMATOR_STYLES.values())) == len(ESTIMATOR_STYLES)
    assert {dash_of(n) for n in ("route_kf", "route_kf_yaw", "route_kf_map", "route_imu")} == {"solid"}
    greys = {"#52514e", "#898781"}
    assert all((color_of(n) in greys) == (n not in MAIN_ESTIMATORS) for n in ESTIMATORS)
