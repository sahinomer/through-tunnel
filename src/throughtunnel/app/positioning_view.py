"""Figures, tables and map payloads for comparing position estimates (UI only)."""

from __future__ import annotations

import html
import math

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from throughtunnel.app.plots import cursor_shape
from throughtunnel.evaluation.metrics import TrackEvaluation
from throughtunnel.positioning import EstimateTrack, Estimator
from throughtunnel.scenario import SimulationResult

# Colour and line style per estimator (D58). Eleven lines can all overlap, and only four hues of a validated
# categorical palette stay distinguishable in every pair (also with colour-vision deficiency): blue, orange,
# aqua and violet. They go to the four main phone-only estimators (solid). The baselines are dashed or dotted
# in the remaining hues; greys mean "not phone-only" (dark: † reference, light: ‡ oracles).
ESTIMATOR_STYLES: dict[str, tuple[str, str]] = {
    "route_kf": ("#2a78d6", "solid"),
    "route_kf_yaw": ("#1baf7a", "solid"),
    "route_kf_map": ("#eb6834", "solid"),
    "route_imu": ("#4a3aa7", "solid"),
    "route_hold": ("#eda100", "dash"),
    "dr_calibrated": ("#e87ba4", "dash"),
    "dr_filtered": ("#008300", "dash"),
    "dr_raw": ("#e34948", "dot"),
    "route_vspeed": ("#52514e", "solid"),
    "route_imu_stop": ("#898781", "dash"),
    "route_imu_zupt": ("#898781", "dot"),
}
DEFAULT_STYLE = ("#616161", "solid")
LEAFLET_DASH = {"solid": None, "dash": "9 6", "dot": "2 6"}  # map tracks (weight 3)
SVG_DASH = {"solid": "none", "dash": "5 3", "dot": "2 2"}  # legend swatches (16 px)
MAP_TRACK_RATE_HZ = 5.0  # decimation of estimated tracks for the map


def color_of(name: str) -> str:
    return ESTIMATOR_STYLES.get(name, DEFAULT_STYLE)[0]


def dash_of(name: str) -> str:
    """Plotly dash name ("solid", "dash", "dot")."""
    return ESTIMATOR_STYLES.get(name, DEFAULT_STYLE)[1]


def swatch_html(name: str) -> str:
    """A short line sample in the estimator's colour and line style (checkboxes, tables, readouts)."""
    return (
        f"<svg width='18' height='8' style='display:inline-block;vertical-align:middle'>"
        f"<line x1='1' y1='4' x2='17' y2='4' stroke='{color_of(name)}' stroke-width='3' "
        f"stroke-dasharray='{SVG_DASH[dash_of(name)]}'/></svg>"
    )


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"


def estimator_category(cls: type[Estimator]) -> str:
    """Which information an estimator uses, from its declared inputs (D41, D49)."""
    if cls.uses_vehicle_speed:
        return "† reference: uses the car's speed reading, which a phone app doesn't have"
    if cls.uses_standstill:
        return "‡ oracle: told the true standstill moments, not a real detector"
    return "phone-only"


def estimator_tooltip_html(cls: type[Estimator]) -> str:
    """Hover text of an estimator's checkbox (D57): category, what it does, the flow of information."""
    return (
        f"<div class='font-bold'>{html.escape(estimator_category(cls))}</div>"
        f"<div class='mt-1'>{html.escape(cls.description)}</div>"
        f"<div class='mt-1 font-mono'>{html.escape(cls.pipeline)}</div>"
    )


PLOTS_HEIGHT_PX = 760  # the three error plots without the legend
LEGEND_ROW_PX = 22
AXIS_TITLE_PX = 60  # time ticks and axis title below the bottom plot
UNCERTAINTY_K = 2.0  # the band on the along-track plot: ±2σ of the estimator's own uncertainty


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
            "Along-track error [m] (+ = estimate ahead; band: the filter's own ±2σ)",
            "Cross-track error [m] (+ = estimate left)",
        ),
    )
    for ev in evaluations:
        show = ev.name in visible
        std = ev.position_std_m
        if len(std) == len(ev.t) and np.isfinite(std).any():
            # ±2σ band of the estimator's own uncertainty: an honest σ keeps its error line inside ~95 % of
            # the time (step 6.1). Drawn first, so the error line lies on top.
            band = UNCERTAINTY_K * std[::2]
            common = {
                "x": ev.t[::2], "legendgroup": ev.name, "showlegend": False, "hoverinfo": "skip",
                "line": {"width": 0}, "visible": True if show else "legendonly",
            }  # fmt: skip
            fig.add_trace(go.Scatter(y=band, **common), 2, 1)
            fig.add_trace(
                go.Scatter(y=-band, fill="tonexty", fillcolor=_rgba(color_of(ev.name), 0.15), **common), 2, 1
            )
        style = {"width": 1.6, "color": color_of(ev.name), "dash": dash_of(ev.name)}
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
    # The legend sits below the time axis, in space of its own, so it never covers a plot. Labels are long:
    # about two entries per row.
    legend_px = LEGEND_ROW_PX * math.ceil(len(evaluations) / 2)
    fig.update_layout(
        height=PLOTS_HEIGHT_PX + legend_px,
        margin={"l": 60, "r": 20, "t": 50, "b": AXIS_TITLE_PX + legend_px},
        hovermode="x unified",
        legend={
            "orientation": "h",
            "x": 0.0,
            "xanchor": "left",
            "yref": "container",
            "y": 0.0,
            "yanchor": "bottom",
        },
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
    head = ["Estimator", "error at C", "own σ at C", "max in tunnel", "RMS in tunnel", "recovered after C"]
    if announce_before_exit_m is not None:
        head += [f"announcement ({announce_before_exit_m:g} m before C)", "own σ then", "uncertainty-aware"]
    rows = []
    for ev in evaluations:
        s = ev.summary
        cells = [
            f"{swatch_html(ev.name)} {html.escape(ev.label)}",
            _m(s.get("exit_total_m")),
            _m(s.get("exit_std_m")),
            _m(s.get("tunnel_max_m")),
            _m(s.get("tunnel_rms_m")),
            _s(s.get("recovery_time_s")),
        ]
        if announce_before_exit_m is not None:
            dt, dd = ev.announcement_time_error_s, ev.announcement_distance_error_m
            cells.append("missed" if not math.isfinite(dt) else f"{dt:+.1f} s ({dd:+.0f} m)")
            cells.append(_m(s.get("announce_std_m")))
            aware = ev.aware_announcement_time_error_s
            kind = {True: "precise", False: "hedged"}.get(ev.aware_announcement_precise, "")
            cells.append(f"{aware:+.1f} s ({kind})" if math.isfinite(aware) else "n/a")
        rows.append("<tr>" + "".join(f"<td class='pr-3'>{c}</td>" for c in cells) + "</tr>")
    head_html = "".join(f"<th class='pr-3 text-left text-gray-500 font-normal'>{h}</th>" for h in head)
    return (
        f"<table class='text-sm'><tr>{head_html}</tr>{''.join(rows)}</table>"
        "<div class='text-xs text-gray-500 mt-1'>Announcement error: + = late (vehicle already past). "
        "Errors are against the true phone position: evaluation-only information. Own σ: the estimator's "
        "1σ along-route uncertainty (Kalman filters only), at C and when it announced. Uncertainty-aware: "
        "fires when the estimate + min(2σ, 300 m) reaches the point; precise if σ ≤ 30 m, else hedged "
        "(step 6.2).</div>"
    )


def _m(v: float | None) -> str:
    return "n/a" if v is None or not math.isfinite(v) else f"{v:,.1f} m"


def _s(v: float | None) -> str:
    return "n/a" if v is None or not math.isfinite(v) else f"{v:.1f} s"
