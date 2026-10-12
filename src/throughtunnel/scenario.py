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
import zlib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from throughtunnel.road import RoadConfig, RoadPath
from throughtunnel.routing.base import RawRoute
from throughtunnel.vehicle.config import DriverConfig
from throughtunnel.vehicle.longitudinal import simulate_longitudinal
from throughtunnel.vehicle.speed_profile import SpeedProfile, plan_speed_profile
from throughtunnel.vehicle.truth import GroundTruth, build_ground_truth

SCHEMA_VERSION = 1


class ScenarioConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = SCHEMA_VERSION
    name: str = "scenario"
    description: str = ""
    route: RawRoute
    road: RoadConfig = Field(default_factory=RoadConfig)
    driver: DriverConfig = Field(default_factory=DriverConfig)
    seed: int = Field(0, ge=0)
    sample_rate_hz: float = Field(100.0, ge=10.0, le=1000.0, description="Simulation and output rate")


@dataclass(frozen=True)
class SimulationResult:
    config: ScenarioConfig
    path: RoadPath
    profile: SpeedProfile
    truth: GroundTruth


def rng_stream(seed: int, name: str) -> np.random.Generator:
    """Independent, reproducible random stream for one named consumer."""
    return np.random.default_rng(np.random.SeedSequence([seed, zlib.crc32(name.encode())]))


def build_path(config: ScenarioConfig) -> RoadPath:
    return RoadPath.from_route(config.route, config.road)


def run_scenario(config: ScenarioConfig, path: RoadPath | None = None) -> SimulationResult:
    """Simulate the scenario. ``path`` may be passed to reuse an already processed road."""
    path = path or build_path(config)
    profile = plan_speed_profile(path, config.driver, rng_stream(config.seed, "driver"))
    motion = simulate_longitudinal(profile, path.length_m, config.driver, dt=1.0 / config.sample_rate_hz)
    truth = build_ground_truth(motion, path)
    return SimulationResult(config=config, path=path, profile=profile, truth=truth)


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
