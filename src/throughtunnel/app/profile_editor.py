"""Road profile editor (D36): drag points up and down on an elevation graph.

The points sit at fixed distances along the route (an even grid plus B and C) and move vertically
only. Each drag is clamped on the server so the whole profile stays within the grade limit. The
road between the points is the smooth curve of ``road_profile.ElevationProfile``. Templates give
quick starting shapes.

Dragging uses Plotly's editable shapes: every point is a pixel-sized circle shape anchored at its
data position. A drag fires ``plotly_relayout`` with ``shapes[i].yanchor``; the editor clamps the
height, ignores the horizontal movement and redraws. All other graph elements are traces, not
shapes, so only the points can be dragged.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable

import numpy as np
from nicegui import events, ui

from throughtunnel.road_profile import (
    DEFAULT_MAX_GRADE_PCT,
    TEMPLATES,
    ElevationProfile,
    RoadProfileConfig,
    clamp_height,
    point_distances,
    template_heights,
)

POINT_COLOR, CURVE_COLOR, LIMIT_COLOR, TUNNEL_FILL = "#2a78d6", "#1c5cab", "#9e9e9e", "rgba(120,120,120,0.15)"
INK_2, GRID = "#52514e", "#e4e3df"
_SHAPE_KEY = re.compile(r"^shapes\[(\d+)\]\.(yanchor|y0|y1)$")


def _line(x, y, color, width, yaxis="y", dash=None, hover=None) -> dict:
    trace = {"x": list(x), "y": list(y), "mode": "lines", "yaxis": yaxis, "showlegend": False}
    trace["line"] = {"color": color, "width": width, **({"dash": dash} if dash else {})}
    trace.update({"hovertemplate": hover} if hover else {"hoverinfo": "skip"})
    return trace


def profile_figure(
    distances: np.ndarray,
    heights: np.ndarray,
    entrance_m: float | None,
    exit_m: float | None,
    max_grade: float,
) -> dict:
    """Plotly figure (dict): height with draggable points (top), grade with the limit (bottom)."""
    km = distances / 1000.0
    s = np.linspace(distances[0], distances[-1], 600)
    if np.ptp(heights) > 0:
        z, g, _, _ = ElevationProfile(distances, heights).evaluate(s)
    else:
        z, g = np.full_like(s, heights[0]), np.zeros_like(s)
    lo, hi = min(-15.0, float(heights.min()) - 15.0), max(15.0, float(heights.max()) + 15.0)
    g_lim = 130.0 * max_grade  # grade axis range [%]
    tunnel = entrance_m is not None and exit_m is not None
    data = []
    if tunnel:
        b, c = entrance_m / 1000.0, exit_m / 1000.0
        for yaxis, (y0, y1) in (("y", (lo, hi)), ("y2", (-g_lim, g_lim))):
            band = _line([b, c, c, b, b], [y0, y0, y1, y1, y0], TUNNEL_FILL, 0, yaxis)
            data.append({**band, "fill": "toself", "fillcolor": TUNNEL_FILL})
    data.append(_line(s / 1000, z, CURVE_COLOR, 2, hover="%{x:.2f} km: %{y:.1f} m<extra></extra>"))
    data.append(
        _line(s / 1000, 100 * g, CURVE_COLOR, 1.5, "y2", hover="%{x:.2f} km: %{y:.2f} %<extra></extra>")
    )
    for sign in (1, -1):
        data.append(_line([km[0], km[-1]], [sign * 100 * max_grade] * 2, LIMIT_COLOR, 1, "y2", dash="dot"))
    point = {"type": "circle", "xref": "x", "yref": "y", "xsizemode": "pixel", "ysizemode": "pixel"}
    point |= {"x0": -6, "x1": 6, "y0": -6, "y1": 6, "fillcolor": POINT_COLOR}
    point |= {"line": {"color": "#ffffff", "width": 1.5}}
    shapes = [{**point, "xanchor": float(x), "yanchor": float(h)} for x, h in zip(km, heights, strict=True)]
    annotations = []
    if tunnel:
        for label, x in (("B", entrance_m / 1000.0), ("C", exit_m / 1000.0)):
            note = {"x": x, "y": 1.0, "xref": "x", "yref": "paper", "text": label, "showarrow": False}
            annotations.append({**note, "yanchor": "bottom", "font": {"size": 11, "color": INK_2}})

    def axis(title: str, **kw) -> dict:
        base = {"gridcolor": GRID, "zeroline": False, "fixedrange": True, "color": INK_2}
        return {**base, "title": {"text": title, "font": {"size": 11}}, **kw}

    layout = {
        "height": 330,
        "margin": {"l": 50, "r": 10, "t": 18, "b": 36},
        "showlegend": False,
        "dragmode": False,
        "plot_bgcolor": "#fcfcfb",
        "paper_bgcolor": "#fcfcfb",
        "font": {"size": 10},
        "xaxis": axis("distance from A [km]", anchor="y2"),
        "yaxis": axis("height [m]", domain=[0.42, 1.0], range=[lo, hi]),
        "yaxis2": axis("grade [%]", domain=[0.0, 0.3], range=[-g_lim, g_lim]),
        "shapes": shapes,
        "annotations": annotations,
    }
    config = {"edits": {"shapePosition": True}, "displayModeBar": False, "responsive": True}
    return {"data": data, "layout": layout, "config": config}


def dragged_heights(args: dict) -> dict[int, float]:
    """Point index -> new height from a ``plotly_relayout`` payload (other keys are ignored)."""
    found: dict[int, dict[str, float]] = {}
    for key, value in (args or {}).items():
        m = _SHAPE_KEY.match(str(key))
        if m and isinstance(value, int | float):
            found.setdefault(int(m.group(1)), {})[m.group(2)] = float(value)
    out = {}
    for i, v in found.items():
        if "yanchor" in v:
            out[i] = v["yanchor"]
        elif "y0" in v and "y1" in v:  # data-sized shapes report their corners
            out[i] = 0.5 * (v["y0"] + v["y1"])
    return out


class ProfileEditor:
    """The *Road profile* panel: templates, grade limit and the draggable elevation graph."""

    def __init__(self, on_change: Callable[[], Awaitable[None]]) -> None:
        self._on_change = on_change
        self.distances = np.array([0.0, 1000.0])
        self.heights = np.zeros(2)
        self.entrance_m: float | None = None
        self.exit_m: float | None = None
        self.max_grade_pct = DEFAULT_MAX_GRADE_PCT
        with ui.column().classes("w-full gap-1"):
            with ui.row().classes("w-full items-center gap-1"):
                for key, label in TEMPLATES.items():
                    ui.button(label, on_click=lambda _, k=key: self._apply_template(k)).props(
                        "dense flat no-caps"
                    )
            with ui.row().classes("w-full items-center no-wrap gap-2"):
                ui.label("Max grade").classes("text-sm w-40 shrink-0")
                self.limit = ui.slider(min=1.0, max=10.0, step=0.5, value=self.max_grade_pct).classes(
                    "flex-grow"
                )
                ui.label().bind_text_from(self.limit, "value", lambda v: f"{v:g} %").classes(
                    "text-sm w-20 text-right font-mono shrink-0"
                )
            self.limit.on("change", self._on_limit)
            self.plot = ui.plotly(self._figure()).classes("w-full")
            self.plot.on("plotly_relayout", self._on_relayout)
            self.info = ui.label().classes("text-xs text-gray-600")
            ui.label(
                "Drag the points up or down; the road follows a smooth curve through them and never gets "
                "steeper than the limit. The estimators know the grade only if the switch below is on."
            ).classes("text-xs text-gray-500")
        self._update_info()

    # ------------------------------------------------------------------ state <-> config
    def set(
        self, config: RoadProfileConfig, length_m: float, entrance_m: float | None, exit_m: float | None
    ) -> None:
        """Show ``config`` for a route (points on an even grid with B and C if the profile is flat)."""
        self.entrance_m, self.exit_m = entrance_m, exit_m
        self.max_grade_pct = config.max_grade_pct
        self.limit.value = config.max_grade_pct
        if config.points:
            p = np.asarray(config.points, dtype=float)
            self.distances, self.heights = p[:, 0], p[:, 1]
        else:
            b = entrance_m if entrance_m is not None else length_m / 3
            c = exit_m if exit_m is not None else 2 * length_m / 3
            self.distances = point_distances(length_m, b, c)
            self.heights = np.zeros(len(self.distances))
        self._redraw()

    def config(self) -> RoadProfileConfig:
        if not np.any(self.heights):
            return RoadProfileConfig(max_grade_pct=self.max_grade_pct)
        pts = tuple(zip(self.distances.tolist(), self.heights.tolist(), strict=True))
        return RoadProfileConfig(points=pts, max_grade_pct=self.max_grade_pct)

    # ------------------------------------------------------------------ interaction
    async def _on_relayout(self, e: events.GenericEventArguments) -> None:
        moved = dragged_heights(e.args if isinstance(e.args, dict) else {})
        if not moved:
            return
        limit = self.max_grade_pct / 100.0
        for i, target in moved.items():
            if 0 <= i < len(self.heights):
                self.heights[i] = clamp_height(self.distances, self.heights, i, target, limit)
        self._redraw()  # also snaps the point back to its distance (horizontal moves are ignored)
        await self._on_change()

    async def _apply_template(self, key: str) -> None:
        b = self.entrance_m if self.entrance_m is not None else self.distances[-1] / 3
        c = self.exit_m if self.exit_m is not None else 2 * self.distances[-1] / 3
        self.heights = template_heights(key, self.distances, b, c, self.max_grade_pct / 100.0)
        self._redraw()
        await self._on_change()

    def _on_limit(self, _: object = None) -> None:
        new = float(self.limit.value)
        current = ElevationProfile(self.distances, self.heights).max_grade() if np.ptp(self.heights) else 0.0
        if 100.0 * current > new + 1e-9:
            reached = f"The current profile reaches {100 * current:.1f} % grade"
            ui.notify(f"{reached}; lower it before tightening the limit.")
            self.limit.value = self.max_grade_pct
            return
        self.max_grade_pct = new
        self._redraw()

    # ------------------------------------------------------------------ display
    def _figure(self) -> dict:
        return profile_figure(
            self.distances, self.heights, self.entrance_m, self.exit_m, self.max_grade_pct / 100.0
        )

    def _redraw(self) -> None:
        self.plot.update_figure(self._figure())
        self._update_info()

    def _update_info(self) -> None:
        if not np.ptp(self.heights):
            self.info.text = f"Flat road · {len(self.distances)} points"
            return
        prof = ElevationProfile(self.distances, self.heights)
        self.info.text = (
            f"Height {self.heights.min():+.1f} … {self.heights.max():+.1f} m · max grade "
            f"{100 * prof.max_grade():.1f} % (limit {self.max_grade_pct:g} %) · {len(self.distances)} points"
        )
