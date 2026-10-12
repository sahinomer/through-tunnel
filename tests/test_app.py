"""UI-independent parts of the app: playback clock and figure building."""

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
