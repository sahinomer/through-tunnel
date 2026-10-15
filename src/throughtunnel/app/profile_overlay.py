"""Road profile overlay on the map: height along the route with the vehicle and the estimates on it.

A semi-transparent panel at the bottom of the map, hidable with its close button (a small *Profile*
button brings it back). It shows the road height along the map route (flat roads included), the
tunnel B–C, the exit-announcement point, and moving markers for the true vehicle and each visible
estimator (its own along-route distance). The header gives the true grade at the vehicle. Display only:
everything comes from the simulation result and the estimate tracks the page already has.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

import numpy as np
from nicegui import ui

from throughtunnel.app.positioning_view import color_of
from throughtunnel.positioning import EstimateTrack
from throughtunnel.road_profile import ElevationProfile
from throughtunnel.scenario import SimulationResult

PANEL_STYLE = (
    "width: 100%; background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(2px); "
    "border-radius: 6px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25)"
)
VEHICLE_COLOR = "#ffb300"  # the map's vehicle marker
LINE_COLOR, TUNNEL_FILL, INK_2, GRID = "#1c5cab", "rgba(120, 120, 120, 0.18)", "#52514e", "#d9d8d4"
GRID_STEP_M = 10.0
TRUTH_STEP_S = 0.5  # true along-route distance precomputed at this interval


def route_heights(result: SimulationResult) -> tuple[np.ndarray, np.ndarray]:
    """Distances along the map route [m] and the road height there [m] (zeros for a flat road)."""
    length = result.route_map.length_m
    d = np.append(np.arange(0.0, length, GRID_STEP_M), length)
    profile = ElevationProfile.from_config(result.config.road_profile)
    return d, (profile.evaluate(d)[0] if profile is not None else np.zeros_like(d))


def truth_route_distance(result: SimulationResult) -> tuple[np.ndarray, np.ndarray]:
    """Times and the true vehicle position projected onto the map route (for display)."""
    tr, rm = result.truth, result.route_map
    t = np.arange(0.0, tr.duration_s + TRUTH_STEP_S, TRUTH_STEP_S)
    east, north = np.interp(t, tr.t, tr.x), np.interp(t, tr.t, tr.y)
    out, last = np.empty(len(t)), 0.0
    for i, (e, n) in enumerate(zip(east, north, strict=True)):
        last = out[i] = rm.project_enu(float(e), float(n), lo_m=max(last - 50.0, 0.0), hi_m=last + 300.0)[0]
    return t, out


def overlay_figure(result: SimulationResult, names: Sequence[str]) -> dict:
    """Plotly figure: height line, tunnel band, announcement line, one marker trace per object."""
    d, z = route_heights(result)
    rm = result.route_map
    km = (d / 1000.0).tolist()
    lo, hi = float(z.min()), float(z.max())
    pad = max(5.0, 0.15 * (hi - lo))
    shapes = []
    if result.sections is not None:
        shapes.append({
            "type": "rect", "xref": "x", "yref": "paper", "x0": rm.tunnel_entrance_m / 1000.0,
            "x1": rm.tunnel_exit_m / 1000.0, "y0": 0, "y1": 1, "fillcolor": TUNNEL_FILL, "line": {"width": 0},
            "layer": "below",
        })  # fmt: skip
        if rm.announcement_m is not None:
            x = rm.announcement_m / 1000.0
            shapes.append({"type": "line", "xref": "x", "yref": "paper", "x0": x, "x1": x, "y0": 0, "y1": 1,
                           "line": {"color": INK_2, "width": 1, "dash": "dot"}})  # fmt: skip
    traces = [{
        "x": km, "y": z.tolist(), "mode": "lines", "line": {"color": LINE_COLOR, "width": 2},
        "hovertemplate": "%{x:.2f} km · %{y:.1f} m<extra></extra>", "showlegend": False,
    }]  # fmt: skip
    marker_line = {"color": "#ffffff", "width": 1.5}
    vehicle = {"size": 13, "color": VEHICLE_COLOR, "line": {"color": "#000000", "width": 2}}
    traces.append({"x": [None], "y": [None], "mode": "markers", "name": "vehicle", "hoverinfo": "skip",
                   "marker": vehicle})  # fmt: skip
    for name in names:
        traces.append({"x": [None], "y": [None], "mode": "markers", "name": name, "hoverinfo": "skip",
                       "marker": {"size": 9, "color": color_of(name), "line": marker_line}})  # fmt: skip
    annotations = [
        {"x": x / 1000.0, "y": 1.0, "xref": "x", "yref": "paper", "text": label, "showarrow": False,
         "yanchor": "bottom", "font": {"size": 10, "color": INK_2}}
        for label, x in (("B", rm.tunnel_entrance_m), ("C", rm.tunnel_exit_m))
        if result.sections is not None
    ]  # fmt: skip
    return {
        "data": traces,
        "layout": {
            "height": 150, "margin": {"l": 40, "r": 10, "t": 14, "b": 26},
            "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)", "showlegend": False,
            "xaxis": {"title": {"text": "distance from A [km]", "font": {"size": 10}, "standoff": 2},
                      "range": [0, rm.length_m / 1000.0], "gridcolor": GRID, "tickfont": {"size": 9},
                      "zeroline": False},
            "yaxis": {"title": {"text": "height [m]", "font": {"size": 10}}, "range": [lo - pad, hi + pad],
                      "gridcolor": GRID, "tickfont": {"size": 9}, "zeroline": False},
            "shapes": shapes, "annotations": annotations,
        },
        "config": {"displayModeBar": False, "staticPlot": False},
    }  # fmt: skip


class ProfileOverlay:
    """Built inside a ``relative`` container that also holds the map."""

    def __init__(self) -> None:
        self._result: SimulationResult | None = None
        self._t = 0.0  # last time shown (markers are restored after every redraw)
        self._tracks: list[EstimateTrack] = []
        self._visible: set[str] = set()
        self._names: list[str] = []
        self._truth_t = self._truth_d = np.zeros(0)
        self._heights: tuple[np.ndarray, np.ndarray] = (np.zeros(2), np.zeros(2))
        with (
            ui.element("div")
            .classes("absolute left-2 bottom-6")
            .style("z-index: 1000; width: 62%; min-width: 320px")
        ):
            with ui.column().classes("gap-0 p-1").style(PANEL_STYLE) as self.panel:
                with ui.row().classes("w-full items-center no-wrap gap-2 px-1"):
                    ui.label("Road profile").classes("text-xs font-bold")
                    self.info = ui.label().classes("text-xs text-gray-700")
                    ui.button(icon="close", on_click=lambda: self.set_shown(False)).props(
                        "flat dense round size=sm"
                    ).classes("ml-auto").tooltip("Hide the road profile")
                self.plot = ui.plotly({"data": [], "layout": {"height": 150}}).classes("w-full")
            self.show_button = ui.button("Profile", icon="terrain", on_click=lambda: self.set_shown(True))
            self.show_button.props("dense size=sm color=white text-color=black")
            self.show_button.tooltip("Show the road profile")
        self.show_button.set_visibility(False)

    @property
    def shown(self) -> bool:
        return self.panel.visible

    def set_shown(self, shown: bool) -> None:
        self.panel.set_visibility(shown)
        self.show_button.set_visibility(not shown)
        if shown:
            self._redraw()  # Plotly cannot size a hidden div: draw again once visible

    def show_result(self, result: SimulationResult) -> None:
        self._result, self._tracks, self._t = result, [], 0.0
        self._heights = route_heights(result)
        self._truth_t, self._truth_d = truth_route_distance(result)
        self._names = []
        self._redraw()

    def show_estimates(self, tracks: Sequence[EstimateTrack], visible: Iterable[str]) -> None:
        self._tracks, self._visible = list(tracks), set(visible)
        self._names = [tr.name for tr in self._tracks]
        self._redraw()

    def set_visible_estimators(self, visible: Iterable[str]) -> None:
        self._visible = set(visible)

    def update(self, t: float) -> None:
        """Move the markers to time ``t`` (called from the page's playback render)."""
        self._t = t
        if self._result is None or not self.shown:
            return
        xs, ys = [], []
        for d in [self._truth_at(t), *(self._estimate_at(tr, t) for tr in self._tracks)]:
            xs.append([d / 1000.0 if math.isfinite(d) else None])
            ys.append([self._height_at(d) if math.isfinite(d) else None])
        self.plot.run_plot_method("restyle", {"x": xs, "y": ys}, list(range(1, 2 + len(self._tracks))))
        grade = float(np.interp(t, self._result.truth.t, self._result.truth.grade))
        self.info.text = f"t = {t:.1f} s · grade at the vehicle {100 * grade:+.1f} %"

    # ------------------------------------------------------------------ helpers
    def _redraw(self) -> None:
        if self._result is None:
            return
        self.plot.update_figure(overlay_figure(self._result, self._names))
        self.update(self._t)

    def _truth_at(self, t: float) -> float:
        return float(np.interp(t, self._truth_t, self._truth_d)) if len(self._truth_t) else math.nan

    def _estimate_at(self, track: EstimateTrack, t: float) -> float:
        if track.name not in self._visible or not len(track.t) or t < track.t[0]:
            return math.nan
        return float(np.interp(t, track.t, track.route_distance))

    def _height_at(self, d: float) -> float:
        return float(np.interp(d, *self._heights))
