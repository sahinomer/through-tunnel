"""Figures, tables and map payloads for comparing position estimates (UI only)."""

from __future__ import annotations

import html
import math

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from throughtunnel.app.plots import cursor_shape
from throughtunnel.evaluation.metrics import TrackEvaluation
from throughtunnel.positioning import EstimateTrack
from throughtunnel.scenario import SimulationResult

ESTIMATOR_COLORS = {
    "dr_raw": "#d81b60",
    "dr_calibrated": "#1e88e5",
    "dr_filtered": "#fb8c00",
    "route_imu": "#43a047",
    "route_kf": "#00897b",
    "route_kf_yaw": "#3949ab",
    "route_hold": "#8e24aa",
    "route_vspeed": "#455a64",  # reference (car speed): neutral, not a phone-only solution
}
MAP_TRACK_RATE_HZ = 5.0  # decimation of estimated tracks for the map


def color_of(name: str) -> str:
    return ESTIMATOR_COLORS.get(name, "#616161")


def track_payload(track: EstimateTrack, result: SimulationResult) -> dict[str, list[float]]:
    """Decimated lat/lon over time of an estimated track (for the static polyline and the moving marker)."""
    step = max(1, round(1.0 / (MAP_TRACK_RATE_HZ * np.median(np.diff(track.t))))) if len(track) > 1 else 1
    lat, lon, _ = result.route_map.frame.to_geodetic(
        np.column_stack([track.east[::step], track.north[::step], np.zeros(len(track.t[::step]))])
    )
    return {"t": np.round(track.t[::step], 3).tolist(), "lat": lat.tolist(), "lon": lon.tolist()}


def _vspan(x0: float, x1: float, **style) -> dict:
    return {
        "type": "rect",
        "xref": "x",
        "yref": "paper",
        "x0": x0,
        "x1": x1,
        "y0": 0,
        "y1": 1,
        "layer": "below",
        **style,
    }


def _vline(x: float, **style) -> dict:
    return {"type": "line", "xref": "x", "yref": "paper", "x0": x, "x1": x, "y0": 0, "y1": 1, **style}


def phase_shapes(result: SimulationResult) -> list[dict]:
    """Shaded tunnel (B–C), GPS-outage outline and the true announcement time (all subplots)."""
    sec, ev = result.sections, result.gnss_events
    if sec is None:
        return []
    shapes = [_vspan(sec.entrance_t, sec.exit_t, fillcolor="rgba(120,120,120,0.15)", line={"width": 0})]
    if math.isfinite(ev.loss_t):
        x1 = min(ev.reacquire_t, float(result.truth.t[-1]))
        outline = {"width": 1, "dash": "dot", "color": "#9e9e9e"}
        shapes.append(_vspan(ev.loss_t, x1, fillcolor="rgba(0,0,0,0)", line=outline))
    if math.isfinite(sec.announcement_t):
        shapes.append(_vline(sec.announcement_t, line={"color": "#ff6f00", "width": 1, "dash": "dash"}))
    return shapes


def error_figure(
    evaluations: list[TrackEvaluation], result: SimulationResult, visible: set[str]
) -> go.Figure:
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=(
            "Horizontal position error [m] (log scale)",
            "Along-track error [m] (+ = estimate ahead)",
            "Cross-track error [m] (+ = estimate left)",
        ),
    )
    for ev in evaluations:
        show = ev.name in visible
        style = {"width": 1.6, "color": color_of(ev.name)}
        for row, y in ((1, np.maximum(ev.total, 0.01)), (2, ev.along), (3, ev.cross)):
            fig.add_trace(
                go.Scatter(
                    x=ev.t[::2], y=y[::2], name=ev.label, legendgroup=ev.name, showlegend=row == 1,
                    line=style, visible=True if show else "legendonly",
                ),
                row,
                1,
            )  # fmt: skip
    fig.update_yaxes(type="log", row=1, col=1)
    fig.update_layout(
        height=760,
        margin={"l": 60, "r": 20, "t": 50, "b": 40},
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.06, "x": 0.0},
        template="plotly_white",
        shapes=[cursor_shape(0.0), *phase_shapes(result)],  # the cursor must stay shape 0
        uirevision="keep-zoom",
    )
    fig.update_xaxes(
        title_text="time [s]  (grey: tunnel B–C · dotted: GPS outage · orange: true announcement time)",
        row=3,
        col=1,
    )
    fig.update_annotations(font_size=12)
    return fig


def summary_html(evaluations: list[TrackEvaluation], announce_before_exit_m: float | None) -> str:
    if not evaluations:
        return ""
    head = ["Estimator", "error at C", "max in tunnel", "RMS in tunnel", "recovered after C"]
    if announce_before_exit_m is not None:
        head.append(f"announcement ({announce_before_exit_m:g} m before C)")
    rows = []
    for ev in evaluations:
        s = ev.summary
        cells = [
            f"<span style='color:{color_of(ev.name)}'>■</span> {html.escape(ev.label)}",
            _m(s.get("exit_total_m")),
            _m(s.get("tunnel_max_m")),
            _m(s.get("tunnel_rms_m")),
            _s(s.get("recovery_time_s")),
        ]
        if announce_before_exit_m is not None:
            dt, dd = ev.announcement_time_error_s, ev.announcement_distance_error_m
            cells.append("missed" if not math.isfinite(dt) else f"{dt:+.1f} s ({dd:+.0f} m)")
        rows.append("<tr>" + "".join(f"<td class='pr-3'>{c}</td>" for c in cells) + "</tr>")
    head_html = "".join(f"<th class='pr-3 text-left text-gray-500 font-normal'>{h}</th>" for h in head)
    return (
        f"<table class='text-sm'><tr>{head_html}</tr>{''.join(rows)}</table>"
        "<div class='text-xs text-gray-500 mt-1'>Announcement error: + = late (vehicle already past). "
        "Errors are against the true phone position: evaluation-only information.</div>"
    )


def _m(v: float | None) -> str:
    return "n/a" if v is None or not math.isfinite(v) else f"{v:,.1f} m"


def _s(v: float | None) -> str:
    return "n/a" if v is None or not math.isfinite(v) else f"{v:.1f} s"
