"""Plotly figure builders (pure functions of simulation results)."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from throughtunnel.scenario import SimulationResult

PLOT_RATE_HZ = 10.0  # display decimation; the data itself stays at the simulation rate
CURSOR_SHAPE_INDEX = 0

COLORS = {
    "speed": "#1f77b4",
    "reference": "#9aa5b1",
    "long": "#d62728",
    "lat": "#2ca02c",
    "yaw_rate": "#9467bd",
    "curvature": "#8c564b",
}


def _decimate(n: int, rate_hz: float) -> slice:
    return slice(None, None, max(1, round(rate_hz / PLOT_RATE_HZ)))


def ground_truth_figure(result: SimulationResult) -> go.Figure:
    tr = result.truth
    sl = _decimate(len(tr), tr.sample_rate_hz)
    t = tr.t[sl]
    v_ref_at_t = np.interp(tr.s[sl], result.profile.s, result.profile.v_ref)

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=(
            "Speed [km/h]",
            "Acceleration [m/s²] (body frame)",
            "Yaw rate [deg/s] (+ = left)",
            "Curvature [1/km] (+ = left)",
        ),
    )
    line = {"width": 1.5}
    fig.add_trace(
        go.Scatter(x=t, y=tr.speed[sl] * 3.6, name="speed", line={**line, "color": COLORS["speed"]}), 1, 1
    )
    fig.add_trace(
        go.Scatter(
            x=t,
            y=v_ref_at_t * 3.6,
            name="planned reference",
            line={**line, "color": COLORS["reference"], "dash": "dot"},
        ),
        1,
        1,
    )
    fig.add_trace(
        go.Scatter(x=t, y=tr.accel_long[sl], name="longitudinal", line={**line, "color": COLORS["long"]}),
        2,
        1,
    )
    fig.add_trace(
        go.Scatter(x=t, y=tr.accel_lat[sl], name="lateral", line={**line, "color": COLORS["lat"]}), 2, 1
    )
    fig.add_trace(
        go.Scatter(
            x=t,
            y=np.degrees(tr.yaw_rate[sl]),
            name="yaw rate",
            line={**line, "color": COLORS["yaw_rate"]},
        ),
        3,
        1,
    )
    fig.add_trace(
        go.Scatter(
            x=t,
            y=tr.curvature[sl] * 1000.0,
            name="curvature",
            line={**line, "color": COLORS["curvature"]},
        ),
        4,
        1,
    )
    fig.update_layout(
        height=640,
        margin={"l": 50, "r": 20, "t": 30, "b": 40},
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.08},
        template="plotly_white",
        shapes=[cursor_shape(0.0)],
        uirevision="keep-zoom",
    )
    fig.update_xaxes(title_text="time [s]", row=4, col=1)
    fig.update_annotations(font_size=12)
    return fig


def cursor_shape(t: float) -> dict:
    return {
        "type": "line",
        "xref": "x",
        "yref": "paper",
        "x0": t,
        "x1": t,
        "y0": 0.0,
        "y1": 1.0,
        "line": {"color": "rgba(0,0,0,0.55)", "width": 1.5},
    }


def cursor_relayout(t: float) -> dict:
    """Minimal ``Plotly.relayout`` update that moves the time cursor."""
    i = CURSOR_SHAPE_INDEX
    return {f"shapes[{i}].x0": t, f"shapes[{i}].x1": t}


def empty_figure(message: str = "Select a route or a preset to generate a scenario") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        height=640,
        template="plotly_white",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{"text": message, "showarrow": False, "font": {"size": 16}}],
    )
    return fig
