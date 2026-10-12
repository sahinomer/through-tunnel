"""Interactive simulator page (NiceGUI).

The page only orchestrates: it collects parameters, calls the core simulation
(`throughtunnel.scenario.run_scenario`) and renders the result. No physics here.

Playback: the server owns the playback clock (readouts, plot cursor, slider at ~16 Hz). Map
motion is rendered in the browser (`static/track_player.js`) from a decimated copy of the track,
interpolated every animation frame and re-anchored to the server clock on each state change.
Server-pushed marker positions made the vehicle hold still for several frames and then jump.
"""

from __future__ import annotations

import html
import json
import math
import re
import time
from pathlib import Path
from typing import Any

import numpy as np
import plotly.graph_objects as go
from nicegui import context, events, run, ui

from throughtunnel.app.playback import SPEED_OPTIONS, PlaybackController
from throughtunnel.app.plots import (
    CURSOR_SHAPE_INDEX,
    cursor_relayout,
    empty_figure,
    ground_truth_figure,
    imu_figure,
)
from throughtunnel.app.track import playback_track
from throughtunnel.road import TUNNEL_MAX_LENGTH_M, TUNNEL_MIN_LENGTH_M, RoadConfig
from throughtunnel.routing import LatLon, OsrmRouteProvider, RawRoute, RoutingError
from throughtunnel.scenario import (
    ScenarioConfig,
    SimulationResult,
    list_presets,
    load_preset,
    run_scenario,
    scenario_from_json,
    with_imu_config,
)
from throughtunnel.sensors.imu import ImuConfig
from throughtunnel.sensors.mounting import MOUNT_PRESETS, PhoneMount, describe_phone_axes
from throughtunnel.vehicle.config import DRIVER_PRESETS, DriverConfig

DEFAULT_PRESET = "seattle_sr99_tunnel"
TICK_S = 0.05  # server UI refresh (readouts, plot cursor, slider); map motion is client-side
PLOT_CURSOR_EVERY = 2  # ticks
SLIDER_EVERY = 5  # ticks
RESYNC_EVERY = 100  # ticks: periodic re-anchoring of the browser clock while playing (safety net)
TRACK_PLAYER_JS = (Path(__file__).parent / "static" / "track_player.js").read_text(encoding="utf-8")

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
        self.base_imu = ImuConfig()
        self.pick_start: LatLon | None = None
        self.pick_end: LatLon | None = None
        self.layers: dict[str, Any] = {}
        self.client = context.client
        self._loading_controls = False
        self._last_tick = time.perf_counter()
        self._tick_count = 0
        self._shown_playing: bool | None = None
        self._busy = False
        self._build()

    # ================================================================== layout
    def _build(self) -> None:
        ui.add_body_html(f"<script>{TRACK_PLAYER_JS}</script>")
        with ui.header().classes("items-center py-2"):
            ui.label("ThroughTunnel").classes("text-lg font-bold")
            ui.label("Vehicle and smartphone IMU simulation (milestone 2)").classes("text-sm opacity-80")

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
                self._build_phone_card()

        # keep_alive=False: the hidden plot is unmounted (Plotly cannot resize a hidden div); only the
        # visible plot receives cursor updates, and a newly shown plot starts from the current cursor.
        with ui.tabs(on_change=self._on_tab).classes("w-full") as self.tabs:
            ui.tab("truth", label="Vehicle ground truth")
            ui.tab("imu", label="Phone IMU (ideal, phone axes)")
        with ui.tab_panels(self.tabs, value="truth", keep_alive=False).classes("w-full"):
            with ui.tab_panel("truth"):
                self.plot = ui.plotly(empty_figure()).classes("w-full")
            with ui.tab_panel("imu"):
                self.imu_plot = ui.plotly(empty_figure()).classes("w-full")
        for plot in (self.plot, self.imu_plot):
            plot.on("plotly_click", self._on_plot_click)
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
                    on_change=self._on_speed,
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

    def _build_phone_card(self) -> None:
        m = self.base_imu.mount
        options = {k: k.replace("_", " ") for k in MOUNT_PRESETS} | {"custom": "custom"}
        with ui.expansion("Phone mounting (IMU)", icon="smartphone", value=False).classes(
            "w-full border rounded"
        ):
            self.mount_select = ui.select(
                options, value=m.label, label="Mount preset", on_change=self._on_mount_preset
            ).classes("w-full")
            self.s_myaw = self._slider("Yaw (about vehicle z)", -180, 180, 5, m.yaw_deg, "°")
            self.s_mpitch = self._slider("Pitch", -90, 90, 5, m.pitch_deg, "°")
            self.s_mroll = self._slider("Roll", -180, 180, 5, m.roll_deg, "°")
            self.s_lx = self._slider("Lever arm x (fwd)", -3, 3, 0.1, m.lever_arm_m[0], "m")
            self.s_ly = self._slider("Lever arm y (left)", -1.5, 1.5, 0.1, m.lever_arm_m[1], "m")
            self.s_lz = self._slider("Lever arm z (up)", -1, 2, 0.1, m.lever_arm_m[2], "m")
            self.earth_switch = ui.switch(
                "Earth rotation (gyro Earth rate, Coriolis)", value=self.base_imu.earth_rotation
            )
            self.earth_switch.on_value_change(self._on_mount_control)
            self.axes_label = ui.html().classes("text-sm")
            ui.label(
                "Android axes: x = right edge, y = top edge, z = out of the screen. "
                "Lever arm = phone position relative to the vehicle reference point (rear-axle centre)."
            ).classes("text-xs text-gray-500")
            for slider in (self.s_myaw, self.s_mpitch, self.s_mroll, self.s_lx, self.s_ly, self.s_lz):
                slider.on("change", self._on_mount_control)
        self._update_axes_label()

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

    def _imu_from_controls(self) -> ImuConfig:
        mount = PhoneMount(
            label=self.mount_select.value or "custom",
            yaw_deg=float(self.s_myaw.value),
            pitch_deg=float(self.s_mpitch.value),
            roll_deg=float(self.s_mroll.value),
            lever_arm_m=(float(self.s_lx.value), float(self.s_ly.value), float(self.s_lz.value)),
        )
        return self.base_imu.model_copy(
            update={"mount": mount, "earth_rotation": bool(self.earth_switch.value)}
        )

    def _set_mount_controls(self, imu: ImuConfig) -> None:
        self._loading_controls = True
        try:
            self.base_imu, m = imu, imu.mount
            self.mount_select.value = m.label if m.label in MOUNT_PRESETS else "custom"
            self.s_myaw.value, self.s_mpitch.value, self.s_mroll.value = m.yaw_deg, m.pitch_deg, m.roll_deg
            self.s_lx.value, self.s_ly.value, self.s_lz.value = m.lever_arm_m
            self.earth_switch.value = imu.earth_rotation
        finally:
            self._loading_controls = False
        self._update_axes_label()

    def _on_mount_preset(self, e: events.ValueChangeEventArguments) -> None:
        if self._loading_controls or e.value not in MOUNT_PRESETS:
            return
        lever = self._imu_from_controls().mount.lever_arm_m  # presets only set the rotation
        mount = MOUNT_PRESETS[e.value].model_copy(update={"lever_arm_m": lever})
        self._set_mount_controls(self.base_imu.model_copy(update={"mount": mount}))
        self._apply_imu()

    def _on_mount_control(self, _: Any = None) -> None:
        if self._loading_controls:
            return
        preset = MOUNT_PRESETS.get(self.mount_select.value)
        angles = (self.s_myaw.value, self.s_mpitch.value, self.s_mroll.value)
        if preset is not None and angles != (preset.yaw_deg, preset.pitch_deg, preset.roll_deg):
            self._loading_controls = True
            self.mount_select.value = "custom"
            self._loading_controls = False
        self._apply_imu()

    def _apply_imu(self) -> None:
        """Re-run only the sensor model: the vehicle motion (ground truth) is unchanged."""
        self.base_imu = self._imu_from_controls()
        self._update_axes_label()
        if self.result is None:
            return
        self.result = with_imu_config(self.result, self.base_imu)
        self.imu_plot.update_figure(imu_figure(self.result))
        self._render(force=True)

    def _update_axes_label(self) -> None:
        axes = describe_phone_axes(self._imu_from_controls().mount.rotation_body_from_phone())
        mapping = " · ".join(f"<b>{k}</b> → {v}" for k, v in axes.items())
        self.axes_label.content = f"Phone axes in the vehicle: {mapping}"

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
        self._set_mount_controls(cfg.imu)
        self.scenario_name = cfg.name
        self._set_route(cfg.route)
        await self._generate()

    def _set_route(self, route: RawRoute) -> None:
        self.route = route
        self.result = None
        self.playback.load(0.0)
        self._remove_layers("raw", "path", "vehicle", "heading", "trail", "link", "start", "end")
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
                imu=self._imu_from_controls(),
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

        self._remove_layers("path", "vehicle", "heading", "trail", "link")
        path_ll = result.path.latlon(step_m=5.0).tolist()
        self.layers["path"] = self.map.generic_layer(name="polyline", args=[path_ll, ROUTE_STYLE_PATH])
        self.layers["trail"] = self.map.generic_layer(name="polyline", args=[[], TRAIL_STYLE])
        self.layers["link"] = self.map.generic_layer(name="polyline", args=[[], TRAIL_STYLE])
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
        ids = {k: self.layers[k].id for k in ("vehicle", "heading", "trail", "link")}
        track = json.dumps(playback_track(result.truth))
        self.client.run_javascript(f"ttPlayer.load({self.map.id}, {track}, {json.dumps(ids)})")
        self.plot.update_figure(ground_truth_figure(result))
        self.imu_plot.update_figure(imu_figure(result))
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
    def _sync_client(self, soft: bool = False) -> None:
        """Re-anchor the browser's map animation to the server playback clock."""
        pb = self.playback
        args = f"{pb.t:.4f}, {pb.speed}, {'true' if pb.playing else 'false'}, {'true' if soft else 'false'}"
        self.client.run_javascript(f"window.ttPlayer && ttPlayer.sync({args})")

    def _after_control(self) -> None:
        self._last_tick = time.perf_counter()
        self._sync_client()
        self._render(force=True)

    def _toggle_play(self) -> None:
        self.playback.toggle()
        self._after_control()

    def _restart(self) -> None:
        self.playback.restart()
        self._after_control()

    def _on_speed(self, e: events.ValueChangeEventArguments) -> None:
        self.playback.speed = float(e.value)
        self._after_control()

    def _on_seek(self, e: events.GenericEventArguments) -> None:
        self.playback.seek(float(e.args))
        self._after_control()

    def _on_plot_click(self, e: events.GenericEventArguments) -> None:
        points = e.args.get("points") or []
        if points and self.result is not None:
            self.playback.seek(float(points[0]["x"]))
            self._after_control()

    def _tick(self) -> None:
        now = time.perf_counter()
        wall_dt = min(now - self._last_tick, 1.0)  # guard against a stalled server event loop
        self._last_tick = now
        self._tick_count += 1
        if self.result is None or not self.playback.advance(wall_dt):
            return
        if not self.playback.playing:
            self._sync_client()  # reached the end
        elif self._tick_count % RESYNC_EVERY == 0:
            self._sync_client(soft=True)
        self._render()

    def _render(self, force: bool = False) -> None:
        if self.result is None:
            return
        tr, t = self.result.truth, self.playback.t
        if force or self._tick_count % PLOT_CURSOR_EVERY == 0:
            self._visible_plot().run_plot_method("relayout", cursor_relayout(t))
        if force or self._tick_count % SLIDER_EVERY == 0 or not self.playback.playing:
            self.progress.value = round(t, 1)
        self.time_label.text = f"{t:6.1f} / {tr.duration_s:.1f} s"
        if self._shown_playing != self.playback.playing:
            self._shown_playing = self.playback.playing
            self.play_button.props(f"icon={'pause' if self.playback.playing else 'play_arrow'}")
        self.readouts.content = self._readout_html(tr.sample(t), *self.result.imu.at(t))

    def _visible_plot(self) -> ui.plotly:
        return self.imu_plot if self.tabs.value == "imu" else self.plot

    def _on_tab(self, _: events.ValueChangeEventArguments) -> None:
        plot = self._visible_plot()
        if self.result is not None and isinstance(plot.figure, go.Figure) and plot.figure.layout.shapes:
            plot.figure.update_shapes(x0=self.playback.t, x1=self.playback.t, selector=CURSOR_SHAPE_INDEX)
            plot.update()

    @staticmethod
    def _readout_html(st: dict[str, float], accel: np.ndarray, gyro: np.ndarray) -> str:
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
        acc = " ".join(f"{v:+7.3f}" for v in accel)
        gyr = " ".join(f"{v:+7.4f}" for v in gyro)
        imu = (
            "<div class='mt-2 text-xs text-gray-500'>phone IMU (ideal, phone axes x / y / z)</div>"
            f"<div class='font-mono text-sm'>accel {acc} m/s²</div>"
            f"<div class='font-mono text-sm'>gyro&nbsp; {gyr} rad/s</div>"
        )
        return f"<div class='grid grid-cols-4 gap-x-4 gap-y-1'>{cells}</div>{imu}"

    # ================================================================== helpers
    def _remove_layers(self, *names: str) -> None:
        for name in names:
            layer = self.layers.pop(name, None)
            if layer is not None:
                self.map.remove_layer(layer)


@ui.page("/")
def index() -> None:
    SimulatorPage()
