"""Scenario definition and the simulation entry point.

A :class:`ScenarioConfig` is everything needed to reproduce a run exactly: the
road geometry *as fetched* (not just endpoints), all processing/driver
parameters, the sample rate and the random seed. ``run_scenario`` is a pure
function of it.

Randomness: each consumer gets its own named stream derived from the scenario
seed (``rng_stream(seed, "driver")``), so adding a new random consumer later
(e.g. sensor noise) never changes the realisation of existing ones.

Route structure (D11): a route runs from A (start) to D (end). The GPS-denied tunnel is the section B–C,
given as distances along the *map* route (the original polyline the navigation app knows). The
navigation exit to announce is a point inside B–C (D14). Where the true (smoothed) path crosses these
map points, and when, is hidden simulator state (``SectionTruth``).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace
from importlib import resources
from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from throughtunnel.observations import GnssStream, NavigationEvent, Observations, RouteMap
from throughtunnel.randomness import rng_stream
from throughtunnel.road import RoadConfig, RoadPath
from throughtunnel.routing.base import RawRoute
from throughtunnel.sensors.errors import ImuErrorConfig, ImuErrorRealization, apply_imu_errors
from throughtunnel.sensors.gnss import GnssConfig, GnssEvents, gnss_timestamps, simulate_gnss
from throughtunnel.sensors.imu import ImuConfig, ImuStream, ideal_imu, imu_timestamps
from throughtunnel.vehicle.config import DriverConfig
from throughtunnel.vehicle.longitudinal import LongitudinalTrajectory, simulate_longitudinal
from throughtunnel.vehicle.speed_profile import SpeedProfile, plan_speed_profile
from throughtunnel.vehicle.truth import GroundTruth, build_ground_truth

# v2: added `imu` (phone mounting, gravity model).
# v3: added `imu.rate_hz` and `imu.errors`. Older files are migrated to what they meant: IMU sampled at
#     the simulation rate, ideal sensors.
# v4: added `tunnel` (A-D route structure). Older files meant "the whole route is GPS-denied" (D10) and
#     are migrated to a tunnel covering the whole route (PD7).
SCHEMA_VERSION = 4

TUNNEL_MIN_LENGTH_M = 500.0
TUNNEL_MAX_LENGTH_M = 5000.0
MIN_APPROACH_S = 30.0  # GPS time before B that the estimator needs to initialise (warning threshold)
MIN_RECOVERY_M = 200.0
MIN_DRIVABLE_RADIUS_M = 3.0  # tighter turns are not drivable in one go (car turning radius ~5 m)
U_TURN_DEG = 150.0


class TunnelConfig(BaseModel):
    """GPS-denied section B–C and the navigation exit inside it, as distances along the map route from A."""

    model_config = ConfigDict(frozen=True)

    entrance_m: float = Field(ge=0.0, description="Point B: tunnel entrance")
    exit_m: float = Field(gt=0.0, description="Point C: tunnel exit (clipped to the route length)")
    exit_event_m: float | None = Field(
        None, description="Navigation exit to announce (inside B–C); None = middle of the tunnel"
    )
    announce_leads_m: tuple[float, ...] = Field(
        (300.0, 0.0), description="Announce this far before the navigation exit"
    )

    @model_validator(mode="after")
    def _ordered(self) -> TunnelConfig:
        if not self.entrance_m < self.exit_m:
            raise ValueError("tunnel entrance must come before the tunnel exit")
        if self.exit_event_m is not None and not self.entrance_m <= self.exit_event_m <= self.exit_m:
            raise ValueError("the navigation exit must lie inside the tunnel")
        return self


class ScenarioConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = SCHEMA_VERSION
    name: str = "scenario"
    description: str = ""
    route: RawRoute
    road: RoadConfig = Field(default_factory=RoadConfig)
    driver: DriverConfig = Field(default_factory=DriverConfig)
    imu: ImuConfig = Field(default_factory=ImuConfig)
    tunnel: TunnelConfig | None = Field(None, description="None = no tunnel (GPS on the whole route)")
    gnss: GnssConfig = Field(default_factory=GnssConfig)
    seed: int = Field(0, ge=0)
    sample_rate_hz: float = Field(100.0, ge=10.0, le=1000.0, description="Simulation and output rate")

    @model_validator(mode="before")
    @classmethod
    def _migrate(cls, data: object) -> object:
        # Only files that declare an older version are migrated (every saved file records it);
        # configs built in code without a version are current.
        if isinstance(data, dict) and data.get("schema_version", SCHEMA_VERSION) < 3:
            imu = dict(data.get("imu") or {})
            imu.setdefault("rate_hz", data.get("sample_rate_hz", 100.0))
            imu.setdefault("errors", ImuErrorConfig.ideal().model_dump())
            data = {**data, "imu": imu}
        if isinstance(data, dict) and data.get("schema_version", SCHEMA_VERSION) < 4:
            data = {**data, "tunnel": data.get("tunnel") or {"entrance_m": 0.0, "exit_m": 1e9}}
        return data

    @field_validator("schema_version")
    @classmethod
    def _upgrade_schema(cls, v: int) -> int:
        if v > SCHEMA_VERSION:
            raise ValueError(f"scenario schema v{v} is newer than this simulator (v{SCHEMA_VERSION})")
        return SCHEMA_VERSION  # older files only lack fields that have defaults


@dataclass(frozen=True)
class SectionTruth:
    """Where (true-path arc length) and when the vehicle crosses map-defined points. Hidden state."""

    entrance_s: float
    exit_s: float
    entrance_t: float
    exit_t: float
    targets: dict[str, tuple[float, float]]  # announcement target name -> (true s, true time)


@dataclass(frozen=True)
class SimulationResult:
    """Everything the simulator produced.

    Observations (what a positioning algorithm may see): ``imu`` (measured phone IMU) and
    ``route_map`` (the navigation route as the app knows it). Hidden simulator state (for display,
    debugging and evaluation only): everything else, including ``imu_ideal`` (error-free readings),
    ``imu_errors`` (the bias/noise actually applied) and ``sections`` (true crossing times).
    """

    config: ScenarioConfig
    path: RoadPath
    profile: SpeedProfile
    motion: LongitudinalTrajectory
    truth: GroundTruth
    imu: ImuStream
    imu_ideal: ImuStream
    imu_errors: ImuErrorRealization
    route_map: RouteMap
    sections: SectionTruth | None
    gnss: GnssStream
    gnss_ideal: GnssStream
    gnss_events: GnssEvents

    def observations(self) -> Observations:
        """The only data an estimator may use (D15): measured IMU, measured GPS, the route map."""
        return Observations(imu=self.imu, gnss=self.gnss, route=self.route_map)


def build_path(config: ScenarioConfig) -> RoadPath:
    return RoadPath.from_route(config.route, config.road)


def run_scenario(config: ScenarioConfig, path: RoadPath | None = None) -> SimulationResult:
    """Simulate the scenario. ``path`` may be passed to reuse an already processed road."""
    path = path or build_path(config)
    if path.diagnostics.min_radius_m < MIN_DRIVABLE_RADIUS_M:
        raise ValueError(
            f"the road geometry contains a turn of radius {path.diagnostics.min_radius_m:.1f} m, which a car "
            "cannot drive; usually the route makes a U-turn at a selected point"
        )
    profile = plan_speed_profile(path, config.driver, rng_stream(config.seed, "driver"))
    motion = simulate_longitudinal(profile, path.length_m, config.driver, dt=1.0 / config.sample_rate_hz)
    truth = build_ground_truth(motion, path)
    imu, ideal, errors = simulate_imu(motion, path, config.imu, config.seed)
    route_map = build_route_map(config)
    sections = section_truth(route_map, path, motion) if config.tunnel is not None else None
    gnss, gnss_ideal, gnss_events = simulate_gps(motion, path, sections, config.gnss, config.imu, config.seed)
    return SimulationResult(
        config=config,
        path=path,
        profile=profile,
        motion=motion,
        truth=truth,
        imu=imu,
        imu_ideal=ideal,
        imu_errors=errors,
        route_map=route_map,
        sections=sections,
        gnss=gnss,
        gnss_ideal=gnss_ideal,
        gnss_events=gnss_events,
    )


def gnss_events(
    sections: SectionTruth | None, motion: LongitudinalTrajectory, config: GnssConfig, seed: int
) -> GnssEvents:
    """Random (seeded) GPS loss point before B and reacquisition time after C."""
    if sections is None:
        return GnssEvents(loss_s=math.inf, loss_t=math.inf, reacquire_t=math.inf)
    s = config.seed if config.seed is not None else seed
    u_loss, u_reacq = rng_stream(s, "gnss.availability").uniform(size=2)
    loss_s = max(sections.entrance_s - u_loss * config.loss_window_m, float(motion.s[0]))
    loss_t = float(np.interp(loss_s, motion.s, motion.t))
    reacquire = sections.exit_t + config.reacquisition_delay_s + u_reacq * config.reacquisition_jitter_s
    return GnssEvents(
        loss_s=loss_s, loss_t=loss_t, reacquire_t=reacquire if math.isfinite(reacquire) else math.inf
    )


def simulate_gps(
    motion: LongitudinalTrajectory,
    path: RoadPath,
    sections: SectionTruth | None,
    config: GnssConfig,
    imu: ImuConfig,
    seed: int,
) -> tuple[GnssStream, GnssStream, GnssEvents]:
    """Phone GPS fixes (measured, ideal) and the hidden availability events."""
    events = gnss_events(sections, motion, config, seed)
    kinematics = build_ground_truth(motion.at(gnss_timestamps(float(motion.t[-1]), config.rate_hz)), path)
    measured, ideal = simulate_gnss(kinematics, imu.mount.lever_arm_m, events, config, seed)
    return measured, ideal, events


def build_route_map(config: ScenarioConfig) -> RouteMap:
    """The navigation route as the app knows it: the original polyline (not the smoothed truth path)."""
    coords = np.asarray(config.route.coordinates, dtype=float)
    lat, lon = coords[:, 0], coords[:, 1]
    length = RouteMap(lat=lat, lon=lon, tunnel_entrance_m=0.0, tunnel_exit_m=0.0).length_m
    tun = config.tunnel
    if tun is None:
        return RouteMap(lat=lat, lon=lon, tunnel_entrance_m=length, tunnel_exit_m=length)
    entrance, exit_ = min(tun.entrance_m, length), min(tun.exit_m, length)
    event_m = tun.exit_event_m if tun.exit_event_m is not None else 0.5 * (entrance + exit_)
    event = NavigationEvent("exit", min(max(event_m, entrance), exit_), tuple(tun.announce_leads_m))
    return RouteMap(lat=lat, lon=lon, tunnel_entrance_m=entrance, tunnel_exit_m=exit_, events=(event,))


def section_truth(route_map: RouteMap, path: RoadPath, motion: LongitudinalTrajectory) -> SectionTruth:
    """Project map-defined points onto the true path (same ENU frame) and find the crossing times."""

    def true_s(map_distance: float, s_lo: float = 0.0) -> float:
        east, north = route_map.enu_at(map_distance)
        return path.project(east, north, s_lo=s_lo)

    def crossing_time(s: float) -> float:
        return float(np.interp(s, motion.s, motion.t)) if motion.s[0] <= s <= motion.s[-1] else math.nan

    s_b = true_s(route_map.tunnel_entrance_m)
    s_c = true_s(route_map.tunnel_exit_m, s_lo=s_b)
    targets = {}
    for name, d in route_map.announcement_targets().items():
        s = true_s(d)
        targets[name] = (s, crossing_time(s))
    return SectionTruth(
        entrance_s=s_b, exit_s=s_c, entrance_t=crossing_time(s_b), exit_t=crossing_time(s_c), targets=targets
    )


def truth_at(result: SimulationResult, times: ArrayLike) -> GroundTruth:
    """Exact ground truth at arbitrary times (constant jerk between simulation steps)."""
    return build_ground_truth(result.motion.at(times), result.path)


def scenario_warnings(result: SimulationResult) -> list[str]:
    """Checks of the A-D structure (complements the road-geometry diagnostics)."""
    rm, sec = result.route_map, result.sections
    out = []
    if sec is None:
        out.append("No tunnel section is defined: GPS is available on the whole route.")
        return out
    tunnel = rm.tunnel_exit_m - rm.tunnel_entrance_m
    if not TUNNEL_MIN_LENGTH_M <= tunnel <= TUNNEL_MAX_LENGTH_M:
        out.append(f"Tunnel B–C is {tunnel / 1000:.2f} km, outside the 0.5–5 km range of the case study.")
    if not sec.entrance_t >= MIN_APPROACH_S:
        out.append(
            f"The approach A–B lasts only {sec.entrance_t:.0f} s with GPS; "
            "the estimator may not initialise well."
        )
    if rm.length_m - rm.tunnel_exit_m < MIN_RECOVERY_M:
        out.append(f"The recovery section C–D is only {rm.length_m - rm.tunnel_exit_m:.0f} m long.")
    if has_u_turn(rm):
        out.append("The route doubles back (U-turn) at some point; check the selected points.")
    return out


def has_u_turn(route_map: RouteMap) -> bool:
    """True if the route reverses direction somewhere (typically OSRM turning back at a waypoint)."""
    return _max_turn_deg(route_map) > U_TURN_DEG


def _max_turn_deg(route_map: RouteMap) -> float:
    seg = np.diff(route_map.enu, axis=0)
    seg = seg[np.linalg.norm(seg, axis=1) > 0.5]
    if len(seg) < 2:
        return 0.0
    heading = np.arctan2(seg[:, 1], seg[:, 0])
    return float(np.degrees(np.abs(np.angle(np.exp(1j * np.diff(heading))))).max())


def simulate_imu(
    motion: LongitudinalTrajectory, path: RoadPath, config: ImuConfig, seed: int
) -> tuple[ImuStream, ImuStream, ImuErrorRealization]:
    """Phone IMU at its own sample rate: (measured, ideal, applied errors).

    The vehicle state is evaluated *exactly* at the IMU timestamps (piecewise-constant jerk between
    simulation steps), so a sensor faster than the simulation gets genuinely new samples.
    """
    t_imu = imu_timestamps(float(motion.t[-1]), config.rate_hz)
    kinematics = build_ground_truth(motion.at(t_imu), path)
    ideal = ideal_imu(kinematics, config)
    accel, gyro, errors = apply_imu_errors(ideal.accel, ideal.gyro, config.rate_hz, config.errors, seed)
    measured = replace(ideal, accel=accel, gyro=gyro, source="simulated:measured")
    return measured, ideal, errors


def with_sensor_config(
    result: SimulationResult, imu: ImuConfig | None = None, gnss: GnssConfig | None = None
) -> SimulationResult:
    """Re-run only the phone sensor models; the vehicle motion is unchanged.

    GPS is re-simulated too when the IMU config changes, because the lever arm (phone position) is
    also the GPS antenna position.
    """
    imu = imu or result.config.imu
    gnss = gnss or result.config.gnss
    config = result.config.model_copy(update={"imu": imu, "gnss": gnss})
    measured, ideal, errors = simulate_imu(result.motion, result.path, imu, config.seed)
    g, g_ideal, g_events = simulate_gps(result.motion, result.path, result.sections, gnss, imu, config.seed)
    return replace(
        result,
        config=config,
        imu=measured,
        imu_ideal=ideal,
        imu_errors=errors,
        gnss=g,
        gnss_ideal=g_ideal,
        gnss_events=g_events,
    )


def with_imu_config(result: SimulationResult, imu: ImuConfig) -> SimulationResult:
    """Re-run only the sensor models with a new IMU config (mounting, rate, errors)."""
    return with_sensor_config(result, imu=imu)


# ---------------------------------------------------------------------- persistence
def save_scenario(config: ScenarioConfig, file: str | Path) -> None:
    Path(file).write_text(config.model_dump_json(indent=1), encoding="utf-8")


def load_scenario(file: str | Path) -> ScenarioConfig:
    return ScenarioConfig.model_validate_json(Path(file).read_text(encoding="utf-8"))


def scenario_from_json(text: str | bytes) -> ScenarioConfig:
    return ScenarioConfig.model_validate_json(text)


PRESET_PACKAGE = "throughtunnel.presets"


def list_presets() -> dict[str, str]:
    """Preset id -> human-readable name, for the bundled scenario files."""
    out = {}
    for entry in sorted(resources.files(PRESET_PACKAGE).iterdir(), key=lambda p: p.name):
        if entry.name.endswith(".json"):
            out[entry.name.removesuffix(".json")] = json.loads(entry.read_text(encoding="utf-8"))["name"]
    return out


def load_preset(preset_id: str) -> ScenarioConfig:
    text = resources.files(PRESET_PACKAGE).joinpath(f"{preset_id}.json").read_text(encoding="utf-8")
    return scenario_from_json(text)
