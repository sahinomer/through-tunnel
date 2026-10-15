"""Parameter panels of the simulator page.

Each panel builds its controls and converts them to and from the core configuration models. Panels
run no simulation: they call back into the page, which decides what a change triggers. Values set
from code (loading a scenario) are applied under ``_quiet()`` so they do not count as user changes.

Change handlers are synchronous and *return* the page callback (F10): NiceGUI calls a handler when the
value changes but runs a returned awaitable later, as a background task. An ``async`` handler would
check the guard only in that task, after ``_quiet()`` has already ended.
"""

from __future__ import annotations

import math
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from typing import Any, ClassVar

import numpy as np
from nicegui import events, ui

from throughtunnel.road import RoadConfig
from throughtunnel.scenario import (
    DEFAULT_ANNOUNCE_BEFORE_EXIT_M,
    MapDataConfig,
    SimulationResult,
    TunnelConfig,
)
from throughtunnel.sensors.errors import DEG, MDPS, MG, UG, ImuErrorConfig, SensorErrorConfig
from throughtunnel.sensors.gnss import GnssConfig
from throughtunnel.sensors.imu import ImuConfig
from throughtunnel.sensors.mounting import (
    MOUNT_PRESETS,
    CalibrationErrorConfig,
    PhoneMount,
    describe_phone_axes,
)
from throughtunnel.vehicle.config import DRIVER_PRESETS, DriverConfig
from throughtunnel.vehicle.traffic import SCENARIO_LABELS, TrafficConfig

Callback = Callable[[], Awaitable[None]]
SIMULATION_RATES = (50, 100, 200)


def slider(label: str, lo: float, hi: float, step: float, value: float, unit: str) -> ui.slider:
    """A labelled slider with its current value and unit on the right."""
    with ui.row().classes("w-full items-center no-wrap gap-2"):
        ui.label(label).classes("text-sm w-40 shrink-0")
        s = ui.slider(min=lo, max=hi, step=step, value=value).classes("flex-grow")
        ui.label().bind_text_from(s, "value", lambda v: f"{v:g} {unit}").classes(
            "text-sm w-20 text-right font-mono shrink-0"
        )
    return s


class Panel:
    """A group of controls whose user changes call ``on_change``."""

    def __init__(self, on_change: Callback) -> None:
        self._on_change = on_change
        self._loading = False

    @contextmanager
    def _quiet(self) -> Iterator[None]:
        self._loading = True
        try:
            yield
        finally:
            self._loading = False

    def _changed(self, _: Any = None) -> Awaitable[None] | None:
        """Event handler: the user's change, or None (nothing to run) for a value set from code."""
        return None if self._loading else self._on_change()


class DrivePanel(Panel):
    """Driver, road processing, random seed and simulation rate; applied with *Generate*."""

    def __init__(self, on_generate: Callback, driver: DriverConfig, road: RoadConfig) -> None:
        super().__init__(on_generate)
        self.base_driver, self.base_road = driver, road
        d, r = driver, road
        with ui.expansion("Scenario parameters", icon="tune", value=False).classes("w-full border rounded"):
            self.style_select = ui.select(
                list(DRIVER_PRESETS), value=d.style, label="Driver style", on_change=self._on_style
            ).classes("w-full")
            self.s_cruise = slider("Cruise speed", 20, 130, 1, d.cruise_speed_kmh, "km/h")
            self.s_var = slider("Speed variability σ", 0, 15, 0.5, d.speed_variability_kmh, "km/h")
            self.s_lat = slider("Max lateral accel", 0.5, 5.0, 0.1, d.max_lateral_accel, "m/s²")
            self.s_acc = slider("Max acceleration", 0.3, 4.0, 0.1, d.max_accel, "m/s²")
            self.s_dec = slider("Max deceleration", 0.5, 6.0, 0.1, d.max_decel, "m/s²")
            self.s_jerk = slider("Max jerk", 0.5, 8.0, 0.1, d.max_jerk, "m/s³")
            ui.separator()
            self.s_wave = slider("Road smoothing λc", 0, 400, 10, r.smoothing_wavelength_m, "m")
            self.s_cut = slider("Max corner cut", 0.5, 10, 0.5, r.max_corner_cut_m, "m")
            with ui.row().classes("w-full items-center no-wrap gap-2"):
                self.seed_input = ui.number("Random seed", value=0, min=0, step=1, format="%d").classes(
                    "w-32"
                )
                self.rate_select = ui.select(list(SIMULATION_RATES), value=100, label="Rate [Hz]").classes(
                    "w-28"
                )
                ui.button("Generate", icon="play_circle", on_click=on_generate).props("unelevated")

    def driver(self) -> DriverConfig:
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

    def road(self) -> RoadConfig:
        values = {
            **self.base_road.model_dump(),
            "smoothing_wavelength_m": float(self.s_wave.value),
            "max_corner_cut_m": float(self.s_cut.value),
        }
        return RoadConfig(**values)

    @property
    def seed(self) -> int:
        return int(self.seed_input.value or 0)

    @property
    def sample_rate_hz(self) -> float:
        return float(self.rate_select.value)

    def set(self, driver: DriverConfig, road: RoadConfig, seed: int, rate: float) -> None:
        with self._quiet():
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
            if rate in SIMULATION_RATES:
                self.rate_select.value = int(rate)

    def _on_style(self, e: events.ValueChangeEventArguments) -> None:
        if self._loading or e.value not in DRIVER_PRESETS:
            return
        self.set(DRIVER_PRESETS[e.value], self.base_road, self.seed, self.rate_select.value)


class TunnelPanel(Panel):
    """The exit announcement distance before C (D32); B and C themselves come from the route."""

    def __init__(self, on_change: Callback) -> None:
        super().__init__(on_change)
        self.tunnel: TunnelConfig | None = None
        with ui.expansion("Tunnel exit announcement", icon="campaign", value=False).classes(
            "w-full border rounded"
        ):
            self.s_announce = slider(
                "Announce before exit C", 0, 5000, 10, DEFAULT_ANNOUNCE_BEFORE_EXIT_M, "m"
            )
            ui.label(
                "Each estimator triggers one announcement when its own estimate (never the truth) is this "
                "far before the tunnel exit C. Limited to the tunnel length."
            ).classes("text-xs text-gray-500")
            self.s_announce.on("change", self._changed)

    def config(self) -> TunnelConfig | None:
        if self.tunnel is None:
            return None
        tun = self.tunnel
        announce = min(float(self.s_announce.value), tun.exit_m - tun.entrance_m)
        return tun.model_copy(update={"announce_before_exit_m": announce})

    def for_route(self, entrance_m: float, exit_m: float) -> TunnelConfig:
        """A new tunnel B–C, keeping the user's announcement distance where it fits."""
        announce = min(float(self.s_announce.value), exit_m - entrance_m)
        return TunnelConfig(entrance_m=entrance_m, exit_m=exit_m, announce_before_exit_m=announce)

    def set(self, tunnel: TunnelConfig | None) -> None:
        with self._quiet():
            self.tunnel = tunnel
            if tunnel is not None:
                self.s_announce.props(f"max={math.floor(tunnel.exit_m - tunnel.entrance_m)}")
                self.s_announce.value = tunnel.announce_before_exit_m


class TrafficPanel(Panel):
    """Traffic scenario in the tunnel (D37) with the parameters of the chosen scenario."""

    # scenario -> the parameter sliders it uses (attribute names)
    USES: ClassVar[dict[str, tuple[str, ...]]] = {
        "portal": ("s_drop", "s_recovery"),
        "speed_limit": ("s_limit",),
        "stop_and_go": ("s_moving", "s_count", "s_stop_min", "s_stop_max"),
        "exit_queue": ("s_queue_len", "s_queue_speed", "s_queue_stops", "s_stop_min", "s_stop_max"),
        "congested": ("s_cong_speed", "s_cong_var"),
    }

    def __init__(self, on_change: Callback) -> None:
        super().__init__(on_change)
        t = TrafficConfig()
        with ui.expansion("Traffic in the tunnel", icon="traffic", value=False).classes(
            "w-full border rounded"
        ):
            self.select = ui.select(SCENARIO_LABELS, value=t.scenario, label="Scenario").classes("w-full")
            self.s_drop = slider("Speed drop at B", 0, 40, 1, t.portal_drop_kmh, "km/h")
            self.s_recovery = slider("Speeds up after", 0, 2000, 50, t.portal_recovery_m, "m")
            self.s_limit = slider("Tunnel speed limit", 20, 120, 5, t.speed_limit_kmh, "km/h")
            self.s_moving = slider("Speed between stops", 10, 60, 1, t.moving_speed_kmh, "km/h")
            self.s_count = slider("Number of stops", 0, 8, 1, t.stop_count, "")
            self.s_queue_len = slider("Queue length before C", 100, 1500, 50, t.queue_length_m, "m")
            self.s_queue_speed = slider("Queue speed", 5, 40, 1, t.queue_speed_kmh, "km/h")
            self.s_queue_stops = slider("Stops in the queue", 0, 4, 1, t.queue_stops, "")
            self.s_stop_min = slider("Shortest stop", 1, 120, 1, t.stop_min_s, "s")
            self.s_stop_max = slider("Longest stop", 1, 300, 5, t.stop_max_s, "s")
            self.s_cong_speed = slider("Congested speed", 10, 60, 1, t.congested_speed_kmh, "km/h")
            self.s_cong_var = slider("Speed variation σ", 0, 20, 1, t.congested_variation_kmh, "km/h")
            self.s_jitter = slider("Random variation", 0, 0.5, 0.05, t.jitter, "")
            self.seed = ui.number(
                "Traffic seed (empty = scenario seed)", value=None, min=0, step=1, format="%d"
            )
            self.seed.classes("w-full")
            ui.label(
                "Events are anchored to the tunnel B–C; positions, durations and speeds vary randomly by the "
                "given fraction (reproducible with the seed). Stops are real standstills."
            ).classes("text-xs text-gray-500")
            sliders = {name for names in self.USES.values() for name in names}
            for name in sliders:
                getattr(self, name).parent_slot.parent.bind_visibility_from(
                    self.select, "value", backward=lambda v, n=name: n in self.USES.get(v, ())
                )
            self.s_jitter.parent_slot.parent.bind_visibility_from(
                self.select, "value", backward=lambda v: v != "free"
            )
            self.seed.bind_visibility_from(self.select, "value", backward=lambda v: v != "free")
            self.select.on_value_change(self._changed)
            for name in (*sliders, "s_jitter"):
                getattr(self, name).on("change", self._changed)
            self.seed.on("blur", self._changed)
            self.seed.on("keydown.enter", self._changed)

    def config(self) -> TrafficConfig:
        lo, hi = sorted((float(self.s_stop_min.value), float(self.s_stop_max.value)))
        seed = self.seed.value
        return TrafficConfig(
            scenario=self.select.value or "free",
            seed=int(seed) if seed is not None else None,
            jitter=float(self.s_jitter.value),
            portal_drop_kmh=float(self.s_drop.value),
            portal_recovery_m=float(self.s_recovery.value),
            speed_limit_kmh=float(self.s_limit.value),
            moving_speed_kmh=float(self.s_moving.value),
            stop_count=int(self.s_count.value),
            stop_min_s=lo,
            stop_max_s=hi,
            queue_length_m=float(self.s_queue_len.value),
            queue_speed_kmh=float(self.s_queue_speed.value),
            queue_stops=int(self.s_queue_stops.value),
            congested_speed_kmh=float(self.s_cong_speed.value),
            congested_variation_kmh=float(self.s_cong_var.value),
        )

    def set(self, t: TrafficConfig) -> None:
        with self._quiet():
            self.select.value = t.scenario
            self.seed.value = t.seed
            self.s_jitter.value = t.jitter
            self.s_drop.value, self.s_recovery.value = t.portal_drop_kmh, t.portal_recovery_m
            self.s_limit.value = t.speed_limit_kmh
            self.s_moving.value, self.s_count.value = t.moving_speed_kmh, t.stop_count
            self.s_stop_min.value, self.s_stop_max.value = t.stop_min_s, t.stop_max_s
            self.s_queue_len.value, self.s_queue_speed.value = t.queue_length_m, t.queue_speed_kmh
            self.s_queue_stops.value = t.queue_stops
            self.s_cong_speed.value, self.s_cong_var.value = t.congested_speed_kmh, t.congested_variation_kmh


class MountPanel(Panel):
    """Phone mounting (rotation, lever arm) and the Earth-rotation switch."""

    def __init__(self, on_change: Callback, imu: ImuConfig) -> None:
        super().__init__(on_change)
        m = imu.mount
        options = {k: k.replace("_", " ") for k in MOUNT_PRESETS} | {"custom": "custom"}
        with ui.expansion("Phone mounting (IMU)", icon="smartphone", value=False).classes(
            "w-full border rounded"
        ):
            self.mount_select = ui.select(
                options, value=m.label, label="Mount preset", on_change=self._on_preset
            ).classes("w-full")
            self.s_yaw = slider("Yaw (about vehicle z)", -180, 180, 5, m.yaw_deg, "°")
            self.s_pitch = slider("Pitch", -90, 90, 5, m.pitch_deg, "°")
            self.s_roll = slider("Roll", -180, 180, 5, m.roll_deg, "°")
            self.s_lx = slider("Lever arm x (fwd)", -3, 3, 0.1, m.lever_arm_m[0], "m")
            self.s_ly = slider("Lever arm y (left)", -1.5, 1.5, 0.1, m.lever_arm_m[1], "m")
            self.s_lz = slider("Lever arm z (up)", -1, 2, 0.1, m.lever_arm_m[2], "m")
            self.earth_switch = ui.switch(
                "Earth rotation (gyro Earth rate, Coriolis)", value=imu.earth_rotation
            )
            self.earth_switch.on_value_change(self._on_control)
            self.axes_label = ui.html().classes("text-sm")
            ui.label(
                "Android axes: x = right edge, y = top edge, z = out of the screen. "
                "Lever arm = phone position relative to the vehicle reference point (rear-axle centre)."
            ).classes("text-xs text-gray-500")
            for s in (self.s_yaw, self.s_pitch, self.s_roll, self.s_lx, self.s_ly, self.s_lz):
                s.on("change", self._on_control)
        self._update_axes_label()

    def mount(self) -> PhoneMount:
        return PhoneMount(
            label=self.mount_select.value or "custom",
            yaw_deg=float(self.s_yaw.value),
            pitch_deg=float(self.s_pitch.value),
            roll_deg=float(self.s_roll.value),
            lever_arm_m=(float(self.s_lx.value), float(self.s_ly.value), float(self.s_lz.value)),
        )

    @property
    def earth_rotation(self) -> bool:
        return bool(self.earth_switch.value)

    def set(self, imu: ImuConfig) -> None:
        with self._quiet():
            m = imu.mount
            self.mount_select.value = m.label if m.label in MOUNT_PRESETS else "custom"
            self.s_yaw.value, self.s_pitch.value, self.s_roll.value = m.yaw_deg, m.pitch_deg, m.roll_deg
            self.s_lx.value, self.s_ly.value, self.s_lz.value = m.lever_arm_m
            self.earth_switch.value = imu.earth_rotation
        self._update_axes_label()

    def _on_preset(self, e: events.ValueChangeEventArguments) -> Awaitable[None] | None:
        if self._loading or e.value not in MOUNT_PRESETS:
            return None
        preset = MOUNT_PRESETS[e.value]  # presets only set the rotation; the lever arm is kept
        with self._quiet():
            self.s_yaw.value, self.s_pitch.value, self.s_roll.value = (
                preset.yaw_deg,
                preset.pitch_deg,
                preset.roll_deg,
            )
        self._update_axes_label()
        return self._on_change()

    def _on_control(self, _: Any = None) -> Awaitable[None] | None:
        if self._loading:
            return None
        preset = MOUNT_PRESETS.get(self.mount_select.value)
        angles = (self.s_yaw.value, self.s_pitch.value, self.s_roll.value)
        if preset is not None and angles != (preset.yaw_deg, preset.pitch_deg, preset.roll_deg):
            with self._quiet():
                self.mount_select.value = "custom"
        self._update_axes_label()
        return self._on_change()

    def _update_axes_label(self) -> None:
        axes = describe_phone_axes(self.mount().rotation_body_from_phone())
        mapping = " · ".join(f"<b>{k}</b> → {v}" for k, v in axes.items())
        self.axes_label.content = f"Phone axes in the vehicle: {mapping}"


class CalibrationPanel(Panel):
    """Calibration error: the phone orientation the alignment stage uses vs. the actual mount (D34, D40)."""

    def __init__(self, on_change: Callback, calibration: CalibrationErrorConfig) -> None:
        super().__init__(on_change)
        c = calibration
        with ui.expansion(
            "Calibration error (assumed orientation)", icon="screen_rotation", value=False
        ).classes("w-full border rounded"):
            self.enabled = ui.switch("Calibration error", value=c.enabled)
            self.s_yaw = slider("Heading (yaw) error", -10, 10, 0.5, c.yaw_deg, "°")
            self.s_pitch = slider("Pitch error", -2, 2, 0.05, c.pitch_deg, "°")
            self.s_roll = slider("Roll error", -5, 5, 0.1, c.roll_deg, "°")
            ui.label(
                "The alignment step before the estimators uses the phone-to-vehicle orientation from its "
                "calibration, rotated by these angles (vehicle axes). The actual mount and all sensor data "
                "stay unchanged. "
                "+ yaw: assumed forward to the left; + pitch: assumed forward nose-down (gravity leaks in "
                "as −g·sin pitch); + roll: assumed up tilted to the right."
            ).classes("text-xs text-gray-500")
            self.enabled.on_value_change(self._changed)
            for s in (self.s_yaw, self.s_pitch, self.s_roll):
                s.on("change", self._changed)

    def config(self) -> CalibrationErrorConfig:
        return CalibrationErrorConfig(
            enabled=bool(self.enabled.value),
            yaw_deg=float(self.s_yaw.value),
            pitch_deg=float(self.s_pitch.value),
            roll_deg=float(self.s_roll.value),
        )

    def set(self, calibration: CalibrationErrorConfig) -> None:
        with self._quiet():
            self.enabled.value = calibration.enabled
            self.s_yaw.value = calibration.yaw_deg
            self.s_pitch.value = calibration.pitch_deg
            self.s_roll.value = calibration.roll_deg


class MapDataPanel(Panel):
    """What the navigation map gives the estimators beyond the route geometry (D39)."""

    def __init__(self, on_change: Callback, map_data: MapDataConfig) -> None:
        super().__init__(on_change)
        with ui.expansion("Map data (estimators)", icon="terrain", value=False).classes(
            "w-full border rounded"
        ):
            self.grade_on = ui.switch("Road grade from the map", value=map_data.road_grade)
            ui.label(
                "The map provides the road grade along the route (assumed exact). The IMU estimators "
                "subtract the gravity it adds to the forward accelerometer axis, relative to the grade "
                "they were calibrated in. Only positioning re-runs; the simulated data stay unchanged."
            ).classes("text-xs text-gray-500")
            self.grade_on.on_value_change(self._changed)

    def config(self) -> MapDataConfig:
        return MapDataConfig(road_grade=bool(self.grade_on.value))

    def set(self, map_data: MapDataConfig) -> None:
        with self._quiet():
            self.grade_on.value = map_data.road_grade


class SensorPanel(Panel):
    """IMU sample rate and error switches/magnitudes, and the phone GPS error model."""

    def __init__(self, on_change: Callback, imu: ImuConfig, gnss: GnssConfig) -> None:
        super().__init__(on_change)
        acc, gyr = imu.errors.accel, imu.errors.gyro
        with ui.expansion("IMU sample rate & errors", icon="sensors", value=False).classes(
            "w-full border rounded"
        ):
            with ui.row().classes("w-full items-center no-wrap gap-2"):
                self.imu_rate = ui.number(
                    "IMU rate [Hz]", value=imu.rate_hz, min=10, max=2000, step=1, format="%g"
                )
                self.imu_rate.classes("w-32")
                self.sensor_seed = ui.number(
                    "Sensor seed (empty = scenario seed)", value=imu.errors.seed, min=0, step=1, format="%d"
                ).classes("flex-grow")
            ui.label("Accelerometer").classes("text-sm font-bold mt-1")
            self.acc_noise_on = ui.switch("White noise", value=acc.noise_enabled)
            self.s_acc_nd = slider("Noise density", 0, 1000, 10, acc.noise_density / UG, "µg/√Hz")
            self.acc_bias_on = ui.switch("Constant bias", value=acc.bias_enabled)
            self.s_acc_bias = slider("Bias magnitude", 0, 100, 1, acc.bias_magnitude / MG, "mg")
            self.acc_drift_on = ui.switch("Bias drift (in-run)", value=acc.drift_enabled)
            self.s_acc_drift = slider("Drift σ", 0, 5, 0.1, acc.drift_sigma / MG, "mg")
            ui.label("Gyroscope").classes("text-sm font-bold mt-1")
            self.gyr_noise_on = ui.switch("White noise", value=gyr.noise_enabled)
            self.s_gyr_nd = slider("Noise density", 0, 50, 0.5, gyr.noise_density / MDPS, "mdps/√Hz")
            self.gyr_bias_on = ui.switch("Constant bias", value=gyr.bias_enabled)
            self.s_gyr_bias = slider("Bias magnitude", 0, 2, 0.01, gyr.bias_magnitude / DEG, "°/s")
            self.gyr_drift_on = ui.switch("Bias drift (in-run)", value=gyr.drift_enabled)
            self.s_gyr_drift = slider("Drift σ", 0, 50, 0.5, gyr.drift_sigma / MDPS, "mdps")
            self.s_drift_tau = slider("Drift correlation time", 10, 1800, 10, acc.drift_tau_s, "s")
            self.errors_label = ui.html().classes("text-sm")
            ui.label(
                "Noise density N: per-sample σ = N·√rate (rate-independent after averaging). Bias: constant "
                "vector with the given norm, direction drawn from the seed. Bias drift: a slowly wandering "
                "bias (Gauss-Markov, σ and correlation time per axis), e.g. temperature; the approach "
                "calibration cannot remove it."
            ).classes("text-xs text-gray-500")
            switches = (self.acc_noise_on, self.acc_bias_on, self.acc_drift_on, self.gyr_noise_on,
                        self.gyr_bias_on, self.gyr_drift_on)  # fmt: skip
            for switch in switches:
                switch.on_value_change(self._changed)
            sliders = (self.s_acc_nd, self.s_acc_bias, self.s_acc_drift, self.s_gyr_nd, self.s_gyr_bias,
                       self.s_gyr_drift, self.s_drift_tau)  # fmt: skip
            for s in sliders:
                s.on("change", self._changed)
            for number in (self.imu_rate, self.sensor_seed):
                number.on("blur", self._changed)
                number.on("keydown.enter", self._changed)
            ui.label("GPS (phone location fixes)").classes("text-sm font-bold mt-2")
            self.gps_on = ui.switch("GPS enabled", value=gnss.enabled)
            self.s_gps_sigma = slider("Position error σ", 0, 10, 0.5, gnss.position_sigma_m, "m")
            self.s_gps_tau = slider("Error correlation", 5, 120, 5, gnss.position_tau_s, "s")
            self.s_gps_speed = slider("Speed noise σ", 0, 1, 0.05, gnss.speed_sigma_mps, "m/s")
            self.s_gps_window = slider("Loss up to … before B", 0, 200, 10, gnss.loss_window_m, "m")
            self.s_gps_delay = slider("Reacquisition delay", 0, 20, 0.5, gnss.reacquisition_delay_s, "s")
            self.deg_on = ui.switch(
                "Degradation before the tunnel (multipath)", value=gnss.portal_degradation
            )
            self.s_deg_len = slider("Degradation zone before B", 0, 500, 10, gnss.degradation_length_m, "m")
            self.s_deg_sigma = slider("Extra error σ at B", 0, 30, 0.5, gnss.degradation_sigma_m, "m")
            self.s_deg_outlier = slider(
                "Jump probability at B", 0, 50, 1, 100 * gnss.outlier_probability, "%"
            )
            ui.label(
                "Degradation grows linearly over the zone and reaches these values at B: extra correlated "
                "position error, extra speed noise and occasional multipath jumps (not reflected in the "
                "reported accuracy)."
            ).classes("text-xs text-gray-500")
            self.gps_on.on_value_change(self._changed)
            self.deg_on.on_value_change(self._changed)
            gps_sliders = (self.s_gps_sigma, self.s_gps_tau, self.s_gps_speed, self.s_gps_window,
                           self.s_gps_delay, self.s_deg_len, self.s_deg_sigma,
                           self.s_deg_outlier)  # fmt: skip
            for s in gps_sliders:
                s.on("change", self._changed)

    def imu(self, base: ImuConfig) -> ImuConfig:
        """``base`` with the rate and errors from the controls (an explicit bias keeps its direction)."""
        rate = self.imu_rate.value
        rate = float(min(max(rate, 10.0), 2000.0)) if rate is not None else base.rate_hz
        seed = self.sensor_seed.value
        tau = float(self.s_drift_tau.value)

        def drift(on, s_sigma, unit) -> dict:
            return {
                "drift_enabled": bool(on.value),
                "drift_sigma": float(s_sigma.value) * unit,
                "drift_tau_s": tau,
            }

        accel = _sensor_errors(
            base.errors.accel, self.acc_noise_on, self.s_acc_nd, UG, self.acc_bias_on, self.s_acc_bias, MG
        ).model_copy(update=drift(self.acc_drift_on, self.s_acc_drift, MG))
        gyro = _sensor_errors(
            base.errors.gyro, self.gyr_noise_on, self.s_gyr_nd, MDPS, self.gyr_bias_on, self.s_gyr_bias, DEG
        ).model_copy(update=drift(self.gyr_drift_on, self.s_gyr_drift, MDPS))
        errors = ImuErrorConfig(accel=accel, gyro=gyro, seed=int(seed) if seed is not None else None)
        return base.model_copy(update={"rate_hz": rate, "errors": errors})

    def gnss(self, base: GnssConfig) -> GnssConfig:
        return base.model_copy(
            update={
                "enabled": bool(self.gps_on.value),
                "position_sigma_m": float(self.s_gps_sigma.value),
                "position_tau_s": float(self.s_gps_tau.value),
                "speed_sigma_mps": float(self.s_gps_speed.value),
                "loss_window_m": float(self.s_gps_window.value),
                "reacquisition_delay_s": float(self.s_gps_delay.value),
                "portal_degradation": bool(self.deg_on.value),
                "degradation_length_m": float(self.s_deg_len.value),
                "degradation_sigma_m": float(self.s_deg_sigma.value),
                "outlier_probability": float(self.s_deg_outlier.value) / 100.0,
            }
        )

    def set_imu(self, imu: ImuConfig) -> None:
        with self._quiet():
            self.imu_rate.value = imu.rate_hz
            self.sensor_seed.value = imu.errors.seed
            acc, gyr = imu.errors.accel, imu.errors.gyro
            self.acc_noise_on.value, self.acc_bias_on.value = acc.noise_enabled, acc.bias_enabled
            self.s_acc_nd.value, self.s_acc_bias.value = acc.noise_density / UG, acc.bias_magnitude / MG
            self.gyr_noise_on.value, self.gyr_bias_on.value = gyr.noise_enabled, gyr.bias_enabled
            self.s_gyr_nd.value, self.s_gyr_bias.value = gyr.noise_density / MDPS, gyr.bias_magnitude / DEG
            self.acc_drift_on.value, self.s_acc_drift.value = acc.drift_enabled, acc.drift_sigma / MG
            self.gyr_drift_on.value, self.s_gyr_drift.value = gyr.drift_enabled, gyr.drift_sigma / MDPS
            self.s_drift_tau.value = acc.drift_tau_s

    def set_gnss(self, gnss: GnssConfig) -> None:
        with self._quiet():
            self.gps_on.value = gnss.enabled
            self.s_gps_sigma.value, self.s_gps_tau.value = gnss.position_sigma_m, gnss.position_tau_s
            self.s_gps_speed.value, self.s_gps_window.value = gnss.speed_sigma_mps, gnss.loss_window_m
            self.s_gps_delay.value = gnss.reacquisition_delay_s
            self.deg_on.value, self.s_deg_len.value = gnss.portal_degradation, gnss.degradation_length_m
            self.s_deg_sigma.value = gnss.degradation_sigma_m
            self.s_deg_outlier.value = 100.0 * gnss.outlier_probability

    def show_applied_errors(self, result: SimulationResult) -> None:
        """The per-sample noise σ and the bias actually drawn for this run (hidden simulation state)."""
        real, rate = result.imu_errors, result.config.imu.rate_hz
        acc_b = ", ".join(f"{v / MG:+.1f}" for v in real.accel.bias)
        gyr_b = ", ".join(f"{v / DEG:+.3f}" for v in real.gyro.bias)
        self.errors_label.content = (
            f"At {rate:g} Hz, per-sample σ: accel {real.accel.noise_std / MG:.2f} mg "
            f"({real.accel.noise_std:.4f} m/s²), gyro {real.gyro.noise_std / DEG:.3f} °/s<br>"
            f"Applied bias (phone x, y, z): accel [{acc_b}] mg, gyro [{gyr_b}] °/s"
        )
        drift = []
        if real.accel.drift is not None:
            drift.append(f"accel up to {np.abs(real.accel.drift).max() / MG:.2f} mg")
        if real.gyro.drift is not None:
            drift.append(f"gyro up to {np.abs(real.gyro.drift).max() / MDPS:.1f} mdps")
        if drift:
            self.errors_label.content += "<br>Bias drift over the run: " + ", ".join(drift)


def _sensor_errors(
    base: SensorErrorConfig, noise_on, s_noise, noise_unit: float, bias_on, s_bias, bias_unit: float
) -> SensorErrorConfig:
    magnitude = float(s_bias.value) * bias_unit
    vector = base.bias_vector
    if vector is not None:  # an explicit bias (e.g. from a loaded file) keeps its direction
        norm = float(np.linalg.norm(vector))
        vector = tuple(float(v) * magnitude / norm for v in vector) if norm > 0 else None
    return base.model_copy(
        update={
            "noise_enabled": bool(noise_on.value),
            "noise_density": float(s_noise.value) * noise_unit,
            "bias_enabled": bool(bias_on.value),
            "bias_magnitude": magnitude,
            "bias_vector": vector,
        }
    )
