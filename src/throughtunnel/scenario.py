"""Scenario definition and the simulation entry point.

A :class:`ScenarioConfig` is everything needed to reproduce a run exactly: the
road geometry *as fetched* (not just endpoints), all processing/driver
parameters, the sample rate and the random seed. ``run_scenario`` is a pure
function of it.

Randomness: each consumer gets its own named stream derived from the scenario
seed (``rng_stream(seed, "driver")``), so adding a new random consumer later
(e.g. sensor noise) never changes the realisation of existing ones.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from importlib import resources
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from throughtunnel.randomness import rng_stream
from throughtunnel.road import RoadConfig, RoadPath
from throughtunnel.routing.base import RawRoute
from throughtunnel.sensors.errors import ImuErrorConfig, ImuErrorRealization, apply_imu_errors
from throughtunnel.sensors.imu import ImuConfig, ImuStream, ideal_imu, imu_timestamps
from throughtunnel.vehicle.config import DriverConfig
from throughtunnel.vehicle.longitudinal import LongitudinalTrajectory, simulate_longitudinal
from throughtunnel.vehicle.speed_profile import SpeedProfile, plan_speed_profile
from throughtunnel.vehicle.truth import GroundTruth, build_ground_truth

# v2: added `imu` (phone mounting, gravity model).
# v3: added `imu.rate_hz` and `imu.errors`. Older files are migrated to what they meant: IMU sampled at
#     the simulation rate, ideal sensors.
SCHEMA_VERSION = 3


class ScenarioConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = SCHEMA_VERSION
    name: str = "scenario"
    description: str = ""
    route: RawRoute
    road: RoadConfig = Field(default_factory=RoadConfig)
    driver: DriverConfig = Field(default_factory=DriverConfig)
    imu: ImuConfig = Field(default_factory=ImuConfig)
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
        return data

    @field_validator("schema_version")
    @classmethod
    def _upgrade_schema(cls, v: int) -> int:
        if v > SCHEMA_VERSION:
            raise ValueError(f"scenario schema v{v} is newer than this simulator (v{SCHEMA_VERSION})")
        return SCHEMA_VERSION  # older files only lack fields that have defaults


@dataclass(frozen=True)
class SimulationResult:
    """Everything the simulator produced.

    Observation (what a positioning algorithm may see): ``imu``, the measured phone IMU stream.
    Hidden simulator state (for display, debugging and evaluation only): everything else, including
    ``imu_ideal`` (error-free readings) and ``imu_errors`` (the bias/noise actually applied).
    """

    config: ScenarioConfig
    path: RoadPath
    profile: SpeedProfile
    motion: LongitudinalTrajectory
    truth: GroundTruth
    imu: ImuStream
    imu_ideal: ImuStream
    imu_errors: ImuErrorRealization


def build_path(config: ScenarioConfig) -> RoadPath:
    return RoadPath.from_route(config.route, config.road)


def run_scenario(config: ScenarioConfig, path: RoadPath | None = None) -> SimulationResult:
    """Simulate the scenario. ``path`` may be passed to reuse an already processed road."""
    path = path or build_path(config)
    profile = plan_speed_profile(path, config.driver, rng_stream(config.seed, "driver"))
    motion = simulate_longitudinal(profile, path.length_m, config.driver, dt=1.0 / config.sample_rate_hz)
    truth = build_ground_truth(motion, path)
    imu, ideal, errors = simulate_imu(motion, path, config.imu, config.seed)
    return SimulationResult(
        config=config,
        path=path,
        profile=profile,
        motion=motion,
        truth=truth,
        imu=imu,
        imu_ideal=ideal,
        imu_errors=errors,
    )


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


def with_imu_config(result: SimulationResult, imu: ImuConfig) -> SimulationResult:
    """Re-run only the sensor model (mounting, rate, errors); the vehicle motion is unchanged."""
    config = result.config.model_copy(update={"imu": imu})
    measured, ideal, errors = simulate_imu(result.motion, result.path, imu, config.seed)
    return replace(result, config=config, imu=measured, imu_ideal=ideal, imu_errors=errors)


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
