"""Interactive simulator page (NiceGUI).

The page only orchestrates: it collects parameters, calls the core simulation
(`throughtunnel.scenario.run_scenario`) and renders the result. No physics here.
"""

from __future__ import annotations

import html
import math
import re
import time
from typing import Any

import numpy as np
from nicegui import events, run, ui

from throughtunnel.app.playback import SPEED_OPTIONS, PlaybackController
from throughtunnel.app.plots import cursor_relayout, empty_figure, ground_truth_figure
from throughtunnel.road import TUNNEL_MAX_LENGTH_M, TUNNEL_MIN_LENGTH_M, RoadConfig
from throughtunnel.routing import LatLon, OsrmRouteProvider, RawRoute, RoutingError
from throughtunnel.scenario import (
    ScenarioConfig,
    SimulationResult,
    list_presets,
    load_preset,
    run_scenario,
    scenario_from_json,
)
from throughtunnel.vehicle.config import DRIVER_PRESETS, DriverConfig

DEFAULT_PRESET = "seattle_sr99_tunnel"
TICK_S = 0.05  # 20 Hz UI refresh
PLOT_CURSOR_EVERY = 2  # ticks -> 10 Hz
SLIDER_EVERY = 5  # ticks -> 4 Hz
TRAIL_STEP_S = 0.5  # spacing of travelled-trail points (simulation time)
HEADING_ARROW_M = 40.0

ROUTE_STYLE_RAW = {"color": "#555555", "weight": 2, "dashArray": "4 6", "opacity": 0.9}
ROUTE_STYLE_PATH = {"color": "#1565c0", "weight": 5, "opacity": 0.55}
TRAIL_STYLE = {"color": "#e65100", "weight": 4, "opacity": 0.9}


def _fmt_km(m: float) -> str:
    return f"{m / 1000:.3f} km"


class SimulatorPage:
    def __init__(self) -> None:
        self.provider = OsrmRouteProvider()
        self.playback = PlaybackController()
        self.route: RawRoute | None = None
        self.result: SimulationResult | None = None
        self.scenario_name = "Custom route"
        self.base_driver: DriverConfig = DRIVER_PRESETS["normal"]
        self.base_road = RoadConfig()
        self.pick_start: LatLon | None = None
        self.pick_end: LatLon | None = None
        self.layers: dict[str, Any] = {}
        self._loading_controls = False
        self._last_tick = time.perf_counter()
        self._tick_count = 0
        self._trail_until = -1.0
        self._busy = False
        self._build()

    # ================================================================== layout
    def _build(self) -> None:
        with ui.header().classes("items-center py-2"):
            ui.label("ThroughTunnel").classes("text-lg font-bold")
            ui.label("Vehicle simulation · ground truth (milestone 1)").classes("text-sm opacity-80")

        with ui.row().classes("w-full no-wrap items-start gap-4"):
            with ui.column().classes("gap-1").style("flex: 3 1 0; min-width: 0"):
                self.map = ui.leaflet(center=(47.6086, -122.3398), zoom=13).classes("w-full")
                self.map.style("height: 62vh")
                self.map.on("map-click", self._on_map_click)
                with ui.row().classes("items-center gap-3"):
                    self.pick_switch = ui.switch("Select route by clicking the map", value=True)
                    ui.button("Clear selection", on_click=self._clear_selection).props("flat dense")
                self.pick_hint = ui.label().classes("text-xs text-gray-600")
                self._set_pick_hint()

            with ui.column().classes("gap-3").style("flex: 2 1 0; min-width: 360px"):
                self._build_scenario_card()
                self._build_playback_card()
                self._build_parameter_card()

        self.plot = ui.plotly(empty_figure()).classes("w-full")
        self.plot.on("plotly_click", self._on_plot_click)
        ui.timer(TICK_S, self._tick)
        ui.timer(0.1, self._initial_load, once=True)

    def _build_scenario_card(self) -> None:
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center no-wrap"):
                self.preset_select = ui.select(
                    list_presets(), label="Preset scenario", on_change=self._on_preset
                ).classes("flex-grow")
            self.route_info = ui.html().classes("text-sm w-full")
            with ui.row().classes("items-center gap-2"):
                ui.button("Save scenario", icon="download", on_click=self._download_scenario).props(
                    "outline dense"
                )
                ui.upload(
                    label="Load scenario (.json)", auto_upload=True, max_files=1, on_upload=self._on_upload
                ).props("accept=.json dense flat").classes("w-56")

    def _build_playback_card(self) -> None:
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center no-wrap gap-2"):
                self.play_button = ui.button(icon="play_arrow", on_click=self._toggle_play).props("round")
                ui.button(icon="replay", on_click=self._restart).props("round flat").tooltip("Restart")
                self.speed_select = ui.select(
                    {s: f"{s:g}×" for s in SPEED_OPTIONS},
                    value=1.0,
                    label="Speed",
                    on_change=lambda e: setattr(self.playback, "speed", float(e.value)),
                ).classes("w-24")
                self.time_label = ui.label("0.0 / 0.0 s").classes("text-sm font-mono ml-auto")
            self.progress = ui.slider(min=0.0, max=1.0, step=0.1, value=0.0).classes("w-full")
            self.progress.on("change", self._on_seek)
            self.readouts = ui.html().classes("w-full")

    def _slider(self, label: str, lo: float, hi: float, step: float, value: float, unit: str) -> ui.slider:
        with ui.row().classes("w-full items-center no-wrap gap-2"):
            ui.label(label).classes("text-sm w-40 shrink-0")
            slider = ui.slider(min=lo, max=hi, step=step, value=value).classes("flex-grow")
            ui.label().bind_text_from(slider, "value", lambda v: f"{v:g} {unit}").classes(
                "text-sm w-20 text-right font-mono shrink-0"
            )
        return slider

    def _build_parameter_card(self) -> None:
        d, r = self.base_driver, self.base_road
        with ui.expansion("Scenario parameters", icon="tune", value=False).classes("w-full border rounded"):
            self.style_select = ui.select(
                list(DRIVER_PRESETS), value=d.style, label="Driver style", on_change=self._on_style
            ).classes("w-full")
            self.s_cruise = self._slider("Cruise speed", 20, 130, 1, d.cruise_speed_kmh, "km/h")
            self.s_var = self._slider("Speed variability σ", 0, 15, 0.5, d.speed_variability_kmh, "km/h")
            self.s_lat = self._slider("Max lateral accel", 0.5, 5.0, 0.1, d.max_lateral_accel, "m/s²")
            self.s_acc = self._slider("Max acceleration", 0.3, 4.0, 0.1, d.max_accel, "m/s²")
            self.s_dec = self._slider("Max deceleration", 0.5, 6.0, 0.1, d.max_decel, "m/s²")
            self.s_jerk = self._slider("Max jerk", 0.5, 8.0, 0.1, d.max_jerk, "m/s³")
            ui.separator()
            self.s_wave = self._slider("Road smoothing λc", 0, 400, 10, r.smoothing_wavelength_m, "m")
            self.s_cut = self._slider("Max corner cut", 0.5, 10, 0.5, r.max_corner_cut_m, "m")
            with ui.row().classes("w-full items-center no-wrap gap-2"):
                self.seed_input = ui.number("Random seed", value=0, min=0, step=1, format="%d").classes(
                    "w-32"
                )
                self.rate_select = ui.select([50, 100, 200], value=100, label="Rate [Hz]").classes("w-28")
                ui.button("Generate", icon="play_circle", on_click=self._generate).props("unelevated")

    # ================================================================== parameters <-> controls
    def _driver_from_controls(self) -> DriverConfig:
        values = {
            **self.base_driver.model_dump(),
            "cruise_speed_kmh": float(self.s_cruise.value),
            "speed_variability_kmh": float(self.s_var.value),
            "max_lateral_accel": float(self.s_lat.value),
            "max_accel": float(self.s_acc.value),
            "max_decel": float(self.s_dec.value),
            "max_jerk": float(self.s_jerk.value),
        }
        return DriverConfig(**values)

    def _road_from_controls(self) -> RoadConfig:
        values = {
            **self.base_road.model_dump(),
            "smoothing_wavelength_m": float(self.s_wave.value),
            "max_corner_cut_m": float(self.s_cut.value),
        }
        return RoadConfig(**values)

    def _set_controls(self, driver: DriverConfig, road: RoadConfig, seed: int, rate: float) -> None:
        self._loading_controls = True
        try:
            self.base_driver, self.base_road = driver, road
            if driver.style in DRIVER_PRESETS:
                self.style_select.value = driver.style
            self.s_cruise.value = driver.cruise_speed_kmh
            self.s_var.value = driver.speed_variability_kmh
            self.s_lat.value = driver.max_lateral_accel
            self.s_acc.value = driver.max_accel
            self.s_dec.value = driver.max_decel
            self.s_jerk.value = driver.max_jerk
            self.s_wave.value = road.smoothing_wavelength_m
            self.s_cut.value = road.max_corner_cut_m
            self.seed_input.value = seed
            if rate in (50, 100, 200):
                self.rate_select.value = int(rate)
        finally:
            self._loading_controls = False

    def _on_style(self, e: events.ValueChangeEventArguments) -> None:
        if self._loading_controls or e.value not in DRIVER_PRESETS:
            return
        preset = DRIVER_PRESETS[e.value]
        self._set_controls(preset, self.base_road, int(self.seed_input.value or 0), self.rate_select.value)

    # ================================================================== scenario loading
    async def _initial_load(self) -> None:
        await self.map.initialized()
        self.preset_select.value = DEFAULT_PRESET  # triggers _on_preset

    async def _on_preset(self, e: events.ValueChangeEventArguments) -> None:
        if e.value:
            await self._load_scenario(load_preset(e.value))

    async def _on_upload(self, e: events.UploadEventArguments) -> None:
        try:
            cfg = scenario_from_json(await e.file.text())
        except ValueError as exc:
            ui.notify(f"Invalid scenario file: {exc}", type="negative", multi_line=True)
            return
        finally:
            e.sender.reset()
        await self._load_scenario(cfg)

    async def _load_scenario(self, cfg: ScenarioConfig) -> None:
        self._set_controls(cfg.driver, cfg.road, cfg.seed, cfg.sample_rate_hz)
        self.scenario_name = cfg.name
        self._set_route(cfg.route)
        await self._generate()

    def _set_route(self, route: RawRoute) -> None:
        self.route = route
        self.result = None
        self.playback.load(0.0)
        self._remove_layers("raw", "path", "vehicle", "heading", "trail", "start", "end")
        coords = [list(c) for c in route.coordinates]
        self.layers["raw"] = self.map.generic_layer(name="polyline", args=[coords, ROUTE_STYLE_RAW])
        self._draw_endpoint("start", coords[0], "#2e7d32")
        self._draw_endpoint("end", coords[-1], "#c62828")
        lats, lons = [c[0] for c in coords], [c[1] for c in coords]
        self.map.run_map_method(
            "fitBounds", [[min(lats), min(lons)], [max(lats), max(lons)]], {"padding": [30, 30]}
        )

    # ================================================================== map route selection
    def _set_pick_hint(self) -> None:
        if self.pick_start is None or self.pick_end is not None:
            text = "Click the map to set the START point (snapped to the nearest road)."
        else:
            text = "Now click the DESTINATION. A driving route is computed with OSRM (OpenStreetMap)."
        self.pick_hint.text = text

    def _draw_endpoint(self, name: str, latlng: list[float], color: str) -> None:
        self._remove_layers(name)
        style = {"radius": 8, "color": color, "weight": 2, "fillColor": color, "fillOpacity": 0.85}
        self.layers[name] = self.map.generic_layer(name="circleMarker", args=[latlng, style])

    def _clear_selection(self) -> None:
        self.pick_start = self.pick_end = None
        self._set_pick_hint()

    async def _on_map_click(self, e: events.GenericEventArguments) -> None:
        if not self.pick_switch.value or self._busy:
            return
        point = LatLon(lat=e.args["latlng"]["lat"], lon=e.args["latlng"]["lng"])
        if self.pick_start is None or self.pick_end is not None:
            self.pick_start, self.pick_end = point, None
            self._remove_layers("end", "pick_end")
            self._draw_endpoint("pick_start", [point.lat, point.lon], "#2e7d32")
            self._set_pick_hint()
            return
        self.pick_end = point
        self._draw_endpoint("pick_end", [point.lat, point.lon], "#c62828")
        self._set_pick_hint()
        await self._route_from_picks()

    async def _route_from_picks(self) -> None:
        assert self.pick_start is not None and self.pick_end is not None
        self._busy = True
        note = ui.notification("Computing route (OSRM)…", spinner=True, timeout=None)
        try:
            route = await run.io_bound(self.provider.route, self.pick_start, self.pick_end)
        except RoutingError as exc:
            ui.notify(str(exc), type="negative", multi_line=True)
            return
        finally:
            note.dismiss()
            self._busy = False
        self._remove_layers("pick_start", "pick_end")
        self.preset_select.set_value(None)
        self.scenario_name = "Custom route"
        self._set_route(route)
        await self._generate()

    # ================================================================== simulation
    async def _generate(self) -> None:
        if self.route is None:
            ui.notify("Select a route or a preset first.", type="warning")
            return
        try:
            cfg = ScenarioConfig(
                name=self.scenario_name,
                route=self.route,
                road=self._road_from_controls(),
                driver=self._driver_from_controls(),
                seed=int(self.seed_input.value or 0),
                sample_rate_hz=float(self.rate_select.value),
            )
            result = await run.io_bound(run_scenario, cfg)
        except (ValueError, RuntimeError) as exc:
            ui.notify(f"Cannot simulate this scenario: {exc}", type="negative", multi_line=True)
            return
        self.result = result
        self.playback.load(result.truth.duration_s)
        self.progress.props(f"max={result.truth.duration_s:.2f}")
        self.progress.value = 0.0

        self._remove_layers("path", "vehicle", "heading", "trail")
        path_ll = result.path.latlon(step_m=5.0).tolist()
        self.layers["path"] = self.map.generic_layer(name="polyline", args=[path_ll, ROUTE_STYLE_PATH])
        self.layers["trail"] = self.map.generic_layer(name="polyline", args=[[], TRAIL_STYLE])
        self.layers["heading"] = self.map.generic_layer(
            name="polyline", args=[[path_ll[0], path_ll[0]], {"color": "#000000", "weight": 3}]
        )
        self.layers["vehicle"] = self.map.generic_layer(
            name="circleMarker",
            args=[
                path_ll[0],
                {"radius": 9, "color": "#000000", "weight": 2, "fillColor": "#ffb300", "fillOpacity": 1.0},
            ],
        )
        self._trail_until = -1.0
        self.plot.update_figure(ground_truth_figure(result))
        self._update_route_info()
        self._render(force=True)

    def _update_route_info(self) -> None:
        if self.result is None or self.route is None:
            self.route_info.content = ""
            return
        res, d = self.result, self.result.path.diagnostics
        tr = res.truth
        names = ", ".join(self.route.metadata.get("road_names", [])[:6])
        in_range = TUNNEL_MIN_LENGTH_M <= res.path.length_m <= TUNNEL_MAX_LENGTH_M
        length_style = "" if in_range else "color:#e65100;font-weight:bold"
        rows = [
            ("Scenario", html.escape(res.config.name)),
            ("Source", html.escape(self.route.source) + (f" · {html.escape(names)}" if names else "")),
            ("Route length", f"<span style='{length_style}'>{_fmt_km(res.path.length_m)}</span>"),
            ("Map polyline", f"{_fmt_km(d.raw_length_m)} · {d.raw_vertices} vertices"),
            ("Smoothing deviation", f"max {d.max_deviation_m:.2f} m · rms {d.rms_deviation_m:.2f} m"),
            ("Min turn radius", f"{d.min_radius_m:,.0f} m" if math.isfinite(d.min_radius_m) else "∞"),
            ("Duration", f"{tr.duration_s:.1f} s · mean {np.mean(tr.speed) * 3.6:.1f} km/h"),
            (
                "Peaks",
                f"|a_lat| {np.abs(tr.accel_lat).max():.2f} m/s² · a_long "
                f"{tr.accel_long.min():.2f}…{tr.accel_long.max():.2f} m/s²",
            ),
        ]
        body = "".join(f"<tr><td class='pr-3 text-gray-500'>{k}</td><td>{v}</td></tr>" for k, v in rows)
        warn = "".join(f"<div style='color:#e65100'>⚠ {html.escape(w)}</div>" for w in d.warnings)
        self.route_info.content = f"<table>{body}</table>{warn}"

    def _download_scenario(self) -> None:
        if self.result is None:
            ui.notify("Nothing to save yet.", type="warning")
            return
        slug = re.sub(r"[^a-z0-9]+", "_", self.result.config.name.lower()).strip("_") or "scenario"
        ui.download.content(self.result.config.model_dump_json(indent=1), f"{slug}.json", "application/json")

    # ================================================================== playback
    def _toggle_play(self) -> None:
        self.playback.toggle()
        self._last_tick = time.perf_counter()
        self._render(force=True)

    def _restart(self) -> None:
        self.playback.restart()
        self._last_tick = time.perf_counter()
        self._render(force=True)

    def _on_seek(self, e: events.GenericEventArguments) -> None:
        self.playback.seek(float(e.args))
        self._render(force=True)

    def _on_plot_click(self, e: events.GenericEventArguments) -> None:
        points = e.args.get("points") or []
        if points and self.result is not None:
            self.playback.seek(float(points[0]["x"]))
            self._render(force=True)

    def _tick(self) -> None:
        now = time.perf_counter()
        wall_dt = min(now - self._last_tick, 0.25)  # avoid jumps after the tab was throttled
        self._last_tick = now
        self._tick_count += 1
        if self.result is not None and self.playback.advance(wall_dt):
            self._render()

    def _render(self, force: bool = False) -> None:
        if self.result is None:
            return
        tr, t = self.result.truth, self.playback.t
        st = tr.sample(t)
        pos = [st["lat"], st["lon"]]
        self.layers["vehicle"].run_method("setLatLng", pos)
        yaw = st["yaw"]
        tip = [st["x"] + HEADING_ARROW_M * math.cos(yaw), st["y"] + HEADING_ARROW_M * math.sin(yaw), 0.0]
        tlat, tlon, _ = tr.frame.to_geodetic(np.array([tip]))
        self.layers["heading"].run_method("setLatLngs", [pos, [float(tlat[0]), float(tlon[0])]])
        self._update_trail(t, pos)

        if force or self._tick_count % PLOT_CURSOR_EVERY == 0:
            self.plot.run_plot_method("relayout", cursor_relayout(t))
        if force or self._tick_count % SLIDER_EVERY == 0 or not self.playback.playing:
            self.progress.value = round(t, 1)
        self.time_label.text = f"{t:6.1f} / {tr.duration_s:.1f} s"
        self.play_button.props(f"icon={'pause' if self.playback.playing else 'play_arrow'}")
        self.readouts.content = self._readout_html(st)

    def _update_trail(self, t: float, pos: list[float]) -> None:
        tr = self.result.truth  # type: ignore[union-attr]
        trail = self.layers["trail"]
        if t < self._trail_until or self._trail_until < 0:
            # Seek / restart: rebuild the travelled part from the ground truth.
            step = max(1, round(TRAIL_STEP_S * tr.sample_rate_hz))
            n = int(np.searchsorted(tr.t, t, side="right"))
            pts = [*np.column_stack([tr.lat[:n:step], tr.lon[:n:step]]).tolist(), pos]
            trail.run_method("setLatLngs", pts)
            self._trail_until = t
        elif t >= self._trail_until + TRAIL_STEP_S:
            trail.run_method("addLatLng", pos)
            self._trail_until = t

    @staticmethod
    def _readout_html(st: dict[str, float]) -> str:
        kappa = st["curvature"]
        radius = "straight" if abs(kappa) < 1e-4 else f"{1 / abs(kappa):,.0f} m {'L' if kappa > 0 else 'R'}"
        items = [
            ("t", f"{st['t']:.2f} s"),
            ("distance", f"{st['s']:.1f} m"),
            ("speed", f"{st['speed'] * 3.6:.1f} km/h"),
            ("a long", f"{st['accel_long']:+.2f} m/s²"),
            ("a lat", f"{st['accel_lat']:+.2f} m/s²"),
            ("bearing", f"{st['bearing_deg']:.1f}°"),
            ("yaw rate", f"{math.degrees(st['yaw_rate']):+.2f} °/s"),
            ("turn radius", radius),
        ]
        cells = "".join(
            f"<div><div class='text-xs text-gray-500'>{k}</div><div class='font-mono'>{v}</div></div>"
            for k, v in items
        )
        return f"<div class='grid grid-cols-4 gap-x-4 gap-y-1'>{cells}</div>"

    # ================================================================== helpers
    def _remove_layers(self, *names: str) -> None:
        for name in names:
            layer = self.layers.pop(name, None)
            if layer is not None:
                self.map.remove_layer(layer)


@ui.page("/")
def index() -> None:
    SimulatorPage()
