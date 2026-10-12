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
