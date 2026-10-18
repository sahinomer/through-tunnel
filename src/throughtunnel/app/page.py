"""Interactive simulator page (NiceGUI).

The page only orchestrates: it collects parameters, calls the core simulation
(`throughtunnel.scenario.run_scenario`) and the estimators, and renders the result. No physics here.
Components: parameter panels (`controls.py`), the map (`map_view.py`), the A–D click selection
(`route_picker.py`), text readouts (`readouts.py`) and figures (`plots.py`, `positioning_view.py`).

Playback: the server owns the playback clock (readouts, plot cursor, slider at ~16 Hz). Map motion is
rendered in the browser and re-anchored to the server clock on each state change (`map_view.py`).
"""

from __future__ import annotations

import html
import re
import time
from collections.abc import Callable
from typing import Any

import plotly.graph_objects as go
from nicegui import events, run, ui

from throughtunnel.app.controls import (
    CalibrationPanel,
    DrivePanel,
    ErrorPresetPanel,
    GpsPanel,
    ImuErrorPanel,
    MapDataPanel,
    MountPanel,
    TrafficPanel,
    TunnelPanel,
    box,
    group,
    section,
)
from throughtunnel.app.map_view import MapView
from throughtunnel.app.playback import SPEED_OPTIONS, PlaybackController
from throughtunnel.app.plots import (
    CURSOR_SHAPE_INDEX,
    cursor_relayout,
    empty_figure,
    ground_truth_figure,
    imu_figure,
)
from throughtunnel.app.positioning_view import error_figure, estimator_tooltip_html, summary_html, swatch_html
from throughtunnel.app.profile_editor import ProfileEditor
from throughtunnel.app.profile_overlay import ProfileOverlay
from throughtunnel.app.readouts import estimate_readout_html, route_info_html, state_readout_html
from throughtunnel.app.route_picker import RoutePicker
from throughtunnel.evaluation.benchmark import ladder_config, straight_tunnel_config
from throughtunnel.evaluation.experiment import Comparison, compare_estimators
from throughtunnel.positioning import ESTIMATORS, ORACLE_ESTIMATORS
from throughtunnel.road import RoadConfig
from throughtunnel.road_profile import RoadProfileConfig
from throughtunnel.routing import OsrmRouteProvider, RawRoute
from throughtunnel.scenario import (
    MapDataConfig,
    ScenarioConfig,
    SimulationResult,
    build_route_map,
    list_presets,
    load_preset,
    run_scenario,
    scenario_from_json,
    with_calibration,
    with_map_data,
    with_sensor_config,
)
from throughtunnel.sensors.error_presets import (
    DEFAULT_ERROR_PRESET,
    apply_error_preset,
    matching_error_preset,
)
from throughtunnel.sensors.gnss import GnssConfig
from throughtunnel.sensors.imu import ImuConfig
from throughtunnel.sensors.mounting import CalibrationErrorConfig
from throughtunnel.sensors.vehicle_speed import VehicleSpeedConfig
from throughtunnel.vehicle.config import DRIVER_PRESETS

DEFAULT_PRESET = "seattle_sr99_tunnel"
# Synthetic tunnels built in code, next to the bundled scenario files (not as files: the benchmark and the
# studies use every bundled file). The 5 km one is exactly the benchmark's ladder geometry.
GENERATED_SCENARIOS: dict[str, tuple[str, Callable[[], ScenarioConfig]]] = {
    "ladder_5km": ("Synthetic 5 km tunnel (benchmark geometry)", lambda: ladder_config(5.0)),
    "straight_10km": (
        "Synthetic 10 km tunnel, nearly straight (beyond the case-study range, not benchmarked)",
        lambda: straight_tunnel_config(10.0),
    ),
}
TICK_S = 0.05  # server UI refresh (readouts, plot cursor, slider); map motion is client-side
PLOT_CURSOR_EVERY = 2  # ticks
SLIDER_EVERY = 5  # ticks
COLUMNS_HEIGHT = "calc(100vh - 84px)"  # viewport minus the header and the page padding
TOOLTIP_PROPS = 'max-width="420px" anchor="bottom left" self="top left" :offset="[0, 4]"'  # estimator notes
RESYNC_EVERY = 100  # ticks: periodic re-anchoring of the browser clock while playing (safety net)


class SimulatorPage:
    def __init__(self) -> None:
        self.playback = PlaybackController()
        self.route: RawRoute | None = None
        self.result: SimulationResult | None = None
        self.scenario_name = "Custom route"
        self.base_imu = ImuConfig()  # fields without controls (e.g. gravity model) come from here
        self.base_gnss = GnssConfig()
        self.base_vehicle_speed = VehicleSpeedConfig()  # rate etc. (no controls) come from here
        self.comparison: Comparison | None = None
        # Oracle estimators (D49: standstill from the truth) start hidden; default: phone-only + reference.
        self.visible_estimators: set[str] = set(ESTIMATORS) - set(ORACLE_ESTIMATORS)
        self._last_tick = time.perf_counter()
        self._tick_count = 0
        self._shown_playing: bool | None = None
        self._build()

    # ================================================================== layout
    def _build(self) -> None:
        with ui.header().classes("items-center py-2"):
            ui.label("ThroughTunnel").classes("text-lg font-bold")
            ui.label("Tunnel positioning: vehicle, phone sensors, GPS and estimators").classes(
                "text-sm opacity-80"
            )

        # Two columns that scroll independently (the page itself does not): map and plots on the left,
        # cards and settings on the right, so scrolling the settings never moves the map or the plots.
        with ui.row().classes("w-full no-wrap items-stretch gap-4").style(f"height: {COLUMNS_HEIGHT}"):
            with ui.column().classes("gap-1 h-full overflow-y-auto").style("flex: 3 1 0; min-width: 0"):
                with ui.element("div").classes("relative w-full"):  # the profile overlays the map
                    self.map_view = MapView()
                    self.profile_overlay = ProfileOverlay()
                self.picker = RoutePicker(self.map_view, OsrmRouteProvider(), self._on_picked_route)
                self._build_plots()

            with (
                ui.column()
                .classes("gap-3 h-full overflow-y-auto pr-1")
                .style("flex: 2 1 0; min-width: 360px")
            ):
                self._build_scenario_card()
                self._build_playback_card()
                self._build_positioning_card()
                self._build_settings()
        for plot in (self.plot, self.imu_plot, self.err_plot):
            plot.on("plotly_click", self._on_plot_click)
        ui.timer(TICK_S, self._tick)
        ui.timer(0.1, self._initial_load, once=True)

    def _build_plots(self) -> None:
        # keep_alive=False: the hidden plot is unmounted (Plotly cannot resize a hidden div); only the
        # visible plot receives cursor updates, and a newly shown plot starts from the current cursor.
        with ui.tabs(on_change=self._on_tab).classes("w-full") as self.tabs:
            ui.tab("truth", label="Vehicle ground truth")
            ui.tab("imu", label="Phone IMU (measured vs ideal, phone axes)")
            ui.tab("errors", label="Positioning errors")
        with ui.tab_panels(self.tabs, value="truth", keep_alive=False).classes("w-full"):
            with ui.tab_panel("truth"):
                self.plot = ui.plotly(empty_figure()).classes("w-full")
            with ui.tab_panel("imu"):
                self.imu_plot = ui.plotly(empty_figure()).classes("w-full")
            with ui.tab_panel("errors"):
                self.err_plot = ui.plotly(
                    empty_figure("Positioning runs after a scenario is generated")
                ).classes("w-full")

    def _build_settings(self) -> None:
        """Settings groups, most used first; within a group the least used settings come last."""
        with ui.column().classes("w-full border rounded px-3 py-2 gap-1"):
            self.error_preset_panel = ErrorPresetPanel(self._apply_error_preset, DEFAULT_ERROR_PRESET)
        with group("Tunnel: exit announcement and traffic", "traffic"):
            section("Exit announcement")
            self.tunnel_panel = TunnelPanel(self._on_tunnel_change)
            section("Traffic in the tunnel")
            self.traffic_panel = TrafficPanel(self._on_tunnel_change)
        with group("Road profile (elevation)", "terrain"):
            self.profile_editor = ProfileEditor(self._on_profile_change)
            self.map_data_panel = MapDataPanel(self._apply_map_data, MapDataConfig())
        with group("Phone IMU: mounting, errors, calibration", "smartphone"):
            section("Mounting")
            mount_box = box()
            section("Sensor errors")
            errors_box = box()
            section("Calibration error (alignment before the estimators)")
            calibration_box = box()
            with ui.expansion("More: lever arm, Earth rotation, IMU rate, sensor seed").classes("w-full"):
                advanced = box()
        with mount_box:
            self.mount_panel = MountPanel(self._apply_sensors, self.base_imu, advanced)
        with errors_box:
            self.imu_panel = ImuErrorPanel(self._apply_sensors, self.base_imu, advanced)
        with calibration_box:
            self.calibration_panel = CalibrationPanel(self._apply_calibration, CalibrationErrorConfig())
        with group("Phone GPS", "satellite_alt"):
            self.gps_panel = GpsPanel(self._apply_sensors, self.base_gnss)
        with group("Drive and simulation", "tune"):
            self.drive_panel = DrivePanel(self._generate, DRIVER_PRESETS["normal"], RoadConfig())

    def _build_scenario_card(self) -> None:
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center no-wrap"):
                self.preset_select = ui.select(
                    list_presets() | {k: label for k, (label, _) in GENERATED_SCENARIOS.items()},
                    label="Preset scenario",
                    on_change=self._on_preset,
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

    def _build_positioning_card(self) -> None:
        with ui.card().classes("w-full"):
            ui.label("Positioning (estimators see only phone IMU, GPS fixes and the route map)").classes(
                "text-sm font-bold"
            )
            with ui.row().classes("w-full gap-x-4 gap-y-0"):
                self.est_toggles = {}
                for name, cls in ESTIMATORS.items():
                    box = ui.checkbox(
                        value=name in self.visible_estimators, on_change=self._on_estimator_toggle
                    )
                    with box.add_slot("default"):
                        ui.html(f"{swatch_html(name)} {html.escape(cls.label)}").classes("text-sm")
                        # in the label slot: the custom slot replaces the checkbox's default slot
                        with ui.tooltip().classes("text-sm").props(TOOLTIP_PROPS):
                            ui.html(estimator_tooltip_html(cls))
                    self.est_toggles[name] = box
            self.positioning_summary = ui.html().classes("w-full overflow-x-auto")

    # ================================================================== scenario loading
    async def _initial_load(self) -> None:
        await self.map_view.map.initialized()
        self.preset_select.value = DEFAULT_PRESET  # triggers _on_preset

    async def _on_preset(self, e: events.ValueChangeEventArguments) -> None:
        if e.value:
            generated = GENERATED_SCENARIOS.get(e.value)
            cfg = generated[1]() if generated is not None else load_preset(e.value)
            key = self.error_preset_panel.key  # bundled scenarios load with the chosen level (D56)
            if key is not None:
                imu, gnss, calibration = apply_error_preset(key, cfg.imu, cfg.gnss)
                cfg = cfg.model_copy(update={"imu": imu, "gnss": gnss, "calibration": calibration})
            await self._load_scenario(cfg)

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
        self.drive_panel.set(cfg.driver, cfg.road, cfg.seed, cfg.sample_rate_hz)
        self.drive_panel.set_vehicle_speed(cfg.vehicle_speed)
        self.base_vehicle_speed = cfg.vehicle_speed
        self.base_imu, self.base_gnss = cfg.imu, cfg.gnss
        self.mount_panel.set(cfg.imu)
        self.calibration_panel.set(cfg.calibration)
        self.map_data_panel.set(cfg.map_data)
        self.imu_panel.set_imu(cfg.imu)
        self.gps_panel.set_gnss(cfg.gnss)
        self.tunnel_panel.set(cfg.tunnel)
        self.traffic_panel.set(cfg.traffic)
        self.error_preset_panel.show(matching_error_preset(cfg.imu, cfg.gnss, cfg.calibration))
        rm = build_route_map(cfg)
        b, c = (rm.tunnel_entrance_m, rm.tunnel_exit_m) if cfg.tunnel is not None else (None, None)
        self.profile_editor.set(cfg.road_profile, rm.length_m, b, c)
        self.scenario_name = cfg.name
        self._set_route(cfg.route)
        await self._generate()

    async def _on_picked_route(self, route: RawRoute, entrance_m: float, exit_m: float) -> None:
        self.preset_select.set_value(None)
        self.scenario_name = "Custom route"
        self.tunnel_panel.set(self.tunnel_panel.for_route(entrance_m, exit_m))
        length = build_route_map(ScenarioConfig(route=route)).length_m
        limit = self.profile_editor.max_grade_pct
        self.profile_editor.set(
            RoadProfileConfig(max_grade_pct=limit), length, entrance_m, exit_m
        )  # new road: flat
        self._set_route(route)
        await self._generate()

    def _set_route(self, route: RawRoute) -> None:
        self.route = route
        self.result = None
        self.playback.load(0.0)
        self.map_view.show_route(route, self.tunnel_panel.tunnel)

    def _download_scenario(self) -> None:
        if self.result is None:
            ui.notify("Nothing to save yet.", type="warning")
            return
        slug = re.sub(r"[^a-z0-9]+", "_", self.result.config.name.lower()).strip("_") or "scenario"
        ui.download.content(self.result.config.model_dump_json(indent=1), f"{slug}.json", "application/json")

    # ================================================================== simulation
    def _imu_from_controls(self) -> ImuConfig:
        mounted = self.base_imu.model_copy(
            update={"mount": self.mount_panel.mount(), "earth_rotation": self.mount_panel.earth_rotation}
        )
        return self.imu_panel.imu(mounted)

    async def _generate(self) -> None:
        if self.route is None:
            ui.notify("Select a route or a preset first.", type="warning")
            return
        try:
            cfg = ScenarioConfig(
                name=self.scenario_name,
                route=self.route,
                road=self.drive_panel.road(),
                road_profile=self.profile_editor.config(),
                driver=self.drive_panel.driver(),
                imu=self._imu_from_controls(),
                calibration=self.calibration_panel.config(),
                map_data=self.map_data_panel.config(),
                vehicle_speed=self.drive_panel.vehicle_speed(self.base_vehicle_speed),
                gnss=self.gps_panel.gnss(self.base_gnss),
                tunnel=self.tunnel_panel.config(),
                traffic=self.traffic_panel.config(),
                seed=self.drive_panel.seed,
                sample_rate_hz=self.drive_panel.sample_rate_hz,
            )
            result = await run.io_bound(run_scenario, cfg)
        except (ValueError, RuntimeError) as exc:
            ui.notify(f"Cannot simulate this scenario: {exc}", type="negative", multi_line=True)
            return
        self.result = result
        self.playback.load(result.truth.duration_s)
        self.progress.props(f"max={result.truth.duration_s:.2f}")
        self.progress.value = 0.0
        self.map_view.show_result(result)
        self.profile_overlay.show_result(result)
        self.plot.update_figure(ground_truth_figure(result))
        self.imu_plot.update_figure(imu_figure(result))
        self.imu_panel.show_applied_errors(result)
        self._update_route_info()
        self._render(force=True)
        await self._run_positioning()

    async def _on_profile_change(self) -> None:
        if self.result is not None:
            await self._generate()

    async def _on_tunnel_change(self) -> None:
        if self.result is not None:
            await self._generate()

    async def _apply_sensors(self) -> None:
        """Re-run only the sensor models (IMU and GPS) and positioning; the vehicle motion is unchanged."""
        self.base_imu = self._imu_from_controls()
        self.base_gnss = self.gps_panel.gnss(self.base_gnss)
        self._show_error_preset()
        if self.result is None:
            return
        self._resimulate_sensors()
        self._update_route_info()
        await self._run_positioning()

    async def _apply_calibration(self) -> None:
        """Re-run only positioning: the calibration error changes no simulated data (D34)."""
        self._show_error_preset()
        if self.result is None:
            return
        self.result = with_calibration(self.result, self.calibration_panel.config())
        self._update_route_info()
        await self._run_positioning()

    async def _apply_error_preset(self, key: str) -> None:
        """Set all sensor errors to a preset (D56): re-run the sensors only if they changed, then positioning
        once. The vehicle motion, the mount and the seeds are unchanged."""
        imu, gnss, calibration = apply_error_preset(
            key, self._imu_from_controls(), self.gps_panel.gnss(self.base_gnss)
        )
        self.imu_panel.set_imu(imu)
        self.gps_panel.set_gnss(gnss)
        self.calibration_panel.set(calibration)
        self.base_imu, self.base_gnss = imu, gnss
        if self.result is None:
            return
        if (imu, gnss) != (self.result.config.imu, self.result.config.gnss):
            self._resimulate_sensors()
        self.result = with_calibration(self.result, calibration)
        self._update_route_info()
        await self._run_positioning()

    def _resimulate_sensors(self) -> None:
        self.result = with_sensor_config(self.result, imu=self.base_imu, gnss=self.base_gnss)
        self.imu_plot.update_figure(imu_figure(self.result))
        self.imu_panel.show_applied_errors(self.result)
        self.map_view.show_gps(self.result)

    def _show_error_preset(self) -> None:
        """Show which preset the current controls equal (or custom)."""
        key = matching_error_preset(
            self._imu_from_controls(), self.gps_panel.gnss(self.base_gnss), self.calibration_panel.config()
        )
        self.error_preset_panel.show(key)

    async def _apply_map_data(self) -> None:
        """Re-run only positioning: the map data is information for the estimators (D39)."""
        if self.result is None:
            return
        self.result = with_map_data(self.result, self.map_data_panel.config())
        self._update_route_info()
        await self._run_positioning()

    async def _run_positioning(self) -> None:
        if self.result is None:
            return
        result = self.result
        note = ui.notification("Running position estimators…", spinner=True, timeout=None)
        try:
            comparison = await run.io_bound(compare_estimators, result)
        finally:
            note.dismiss()
        if result is not self.result:  # a newer scenario replaced this one meanwhile
            return
        self.comparison = comparison
        self.map_view.show_estimates(comparison.tracks, result, self.visible_estimators)
        self.profile_overlay.show_estimates(comparison.tracks, self.visible_estimators)
        self._update_positioning_views()
        self._render(force=True)

    def _update_positioning_views(self) -> None:
        if self.comparison is None or self.result is None:
            return
        evals = [e for e in self.comparison.evaluations if e.name in self.visible_estimators]
        self.positioning_summary.content = summary_html(evals, self.result.route_map.announce_before_exit_m)
        self.err_plot.update_figure(
            error_figure(self.comparison.evaluations, self.result, self.visible_estimators)
        )

    def _on_estimator_toggle(self, _: Any = None) -> None:
        self.visible_estimators = {n for n, box in self.est_toggles.items() if box.value}
        self.map_view.set_estimate_visibility(ESTIMATORS, self.visible_estimators)
        self.profile_overlay.set_visible_estimators(self.visible_estimators)
        self._update_positioning_views()
        self._render(force=True)

    def _update_route_info(self) -> None:
        if self.result is None or self.route is None:
            self.route_info.content = ""
            return
        self.route_info.content = route_info_html(self.result, self.route)

    # ================================================================== playback
    def _sync_client(self, soft: bool = False) -> None:
        pb = self.playback
        self.map_view.sync_player(pb.t, pb.speed, pb.playing, soft)

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
            plot = self._visible_plot()
            if plot is not None:
                plot.run_plot_method("relayout", cursor_relayout(t))
            self.profile_overlay.update(t)
        if force or self._tick_count % SLIDER_EVERY == 0 or not self.playback.playing:
            self.progress.value = round(t, 1)
        self.time_label.text = f"{t:6.1f} / {tr.duration_s:.1f} s"
        if self._shown_playing != self.playback.playing:
            self._shown_playing = self.playback.playing
            self.play_button.props(f"icon={'pause' if self.playback.playing else 'play_arrow'}")
        state = state_readout_html(tr.sample(t), self.result.imu.at(t), self.result.imu_ideal.at(t))
        evaluations = self.comparison.evaluations if self.comparison is not None else []
        self.readouts.content = state + estimate_readout_html(evaluations, self.visible_estimators, t)

    def _visible_plot(self) -> ui.plotly | None:
        name = {"imu": "imu_plot", "errors": "err_plot"}.get(self.tabs.value, "plot")
        return getattr(self, name, None)  # None while the page is still being built

    def _on_tab(self, _: events.ValueChangeEventArguments) -> None:
        plot = self._visible_plot()
        if plot is None or self.result is None:
            return
        if isinstance(plot.figure, go.Figure) and plot.figure.layout.shapes:
            plot.figure.update_shapes(x0=self.playback.t, x1=self.playback.t, selector=CURSOR_SHAPE_INDEX)
            plot.update()


@ui.page("/")
def index() -> None:
    SimulatorPage()
