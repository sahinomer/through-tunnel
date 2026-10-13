"""Traffic scenarios in the tunnel (R2, D37): shared primitives composed into realistic variants.

Two primitives cover every scenario (docs/traffic_research.md):

* ``SpeedZone``: traffic caps the driver's speed between two distances. The driver brakes gently
  into the zone (``decel``), may vary speed inside it (smooth random variation, e.g. congested
  flow), and accelerates out of it (``accel``). Zones only lower the driver's own preferred speed.
* ``Stop``: the vehicle brakes to a standstill at a distance, stands still for a time, and pulls away.
  Standing still is time-based, so it is handled by the longitudinal model (a spatial speed plan
  cannot express "stay here for 30 s").

Scenarios are compositions, anchored to the tunnel entrance B and exit C:

* ``portal`` (T1): a zone from B at the cruise speed minus ``portal_drop_kmh``, braking before B,
  speeding up again after ``portal_recovery_m``;
* ``speed_limit`` (T2): a zone B–C at ``speed_limit_kmh``;
* ``stop_and_go`` (T3): a zone B–C at ``moving_speed_kmh`` plus ``stop_count`` stops spread through
  the tunnel;
* ``exit_queue`` (T5): a zone over the last ``queue_length_m`` before C at ``queue_speed_kmh`` plus
  ``queue_stops`` stops;
* ``congested`` (T6): a zone B–C at ``congested_speed_kmh`` with smooth variation.

Randomness (seeded, stream "traffic"): positions, durations and speeds are varied by ``jitter``
(a fraction) around the nominal parameters, so repeated runs differ but each run is reproducible.
Defaults come from the research note (portal braking ~0.6 m/s², car-following braking ~1.5 m/s²,
acceleration out of a queue ~1 m/s², stops of 10–60 s).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, Self

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, model_validator

KMH = 1.0 / 3.6

Scenario = Literal["free", "portal", "speed_limit", "stop_and_go", "exit_queue", "congested"]
SCENARIO_LABELS: dict[str, str] = {
    "free": "Free flow",
    "portal": "Portal slowdown (T1)",
    "speed_limit": "Tunnel speed limit (T2)",
    "stop_and_go": "Stop-and-go (T3)",
    "exit_queue": "Exit queue (T5)",
    "congested": "Congested slow flow (T6)",
}


class TrafficConfig(BaseModel):
    """Traffic scenario in the tunnel and its parameters (only those of the chosen scenario apply)."""

    model_config = ConfigDict(frozen=True)

    scenario: Scenario = "free"
    seed: int | None = Field(None, ge=0, description="Traffic randomness; None = the scenario seed")
    jitter: float = Field(
        0.2, ge=0.0, le=0.5, description="Relative random variation of positions/durations/speeds"
    )
    brake_decel: float = Field(1.5, gt=0.0, le=3.0, description="Braking into queues and stops [m/s²]")
    go_accel: float = Field(1.0, gt=0.0, le=2.0, description="Accelerating out of queues and stops [m/s²]")
    # T1 portal slowdown
    portal_drop_kmh: float = Field(15.0, ge=0.0, le=60.0, description="Speed drop at the portal")
    portal_brake: float = Field(0.6, gt=0.0, le=2.0, description="Braking before the portal [m/s²]")
    portal_recovery_m: float = Field(400.0, ge=0.0, description="Distance after B before speeding up again")
    # T2 tunnel speed limit
    speed_limit_kmh: float = Field(60.0, ge=10.0, le=130.0)
    # T3 stop-and-go
    moving_speed_kmh: float = Field(30.0, ge=5.0, le=80.0, description="Speed between the stops")
    stop_count: int = Field(3, ge=0, le=10)
    stop_min_s: float = Field(10.0, ge=1.0, le=600.0, description="Shortest standstill")
    stop_max_s: float = Field(60.0, ge=1.0, le=600.0, description="Longest standstill")
    # T5 exit queue
    queue_length_m: float = Field(400.0, ge=50.0, le=2000.0, description="Queue length before C")
    queue_speed_kmh: float = Field(15.0, ge=3.0, le=60.0)
    queue_stops: int = Field(1, ge=0, le=5)
    # T6 congested slow flow
    congested_speed_kmh: float = Field(30.0, ge=5.0, le=80.0)
    congested_variation_kmh: float = Field(8.0, ge=0.0, le=30.0)

    @model_validator(mode="after")
    def _ranges(self) -> Self:
        if self.stop_min_s > self.stop_max_s:
            raise ValueError("stop_min_s must not exceed stop_max_s")
        return self


@dataclass(frozen=True)
class SpeedZone:
    start_m: float
    end_m: float
    speed_mps: float
    decel: float  # braking into the zone [m/s^2]
    accel: float  # accelerating out of it [m/s^2]
    variation_mps: float = 0.0  # std of a smooth random variation inside the zone
    variation_length_m: float = 200.0
    min_speed_mps: float = 5.0 * KMH  # floor of the varied speed (congested flow never quite stops)
    variation_seed: int = 0  # own seed, so the driver's random stream is unaffected


@dataclass(frozen=True)
class Stop:
    at_m: float
    duration_s: float


@dataclass(frozen=True)
class TrafficPlan:
    zones: tuple[SpeedZone, ...] = ()
    stops: tuple[Stop, ...] = ()
    stop_decel: float = 1.5  # braking to a stop [m/s^2]
    go_accel: float = 1.0  # pulling away from a stop [m/s^2]
    notes: tuple[str, ...] = field(default=())

    @property
    def empty(self) -> bool:
        return not self.zones and not self.stops


def _jit(rng: np.random.Generator, value: float, jitter: float) -> float:
    """value × U(1 - jitter, 1 + jitter); always draws, so the stream use does not depend on jitter."""
    return value * (1.0 + jitter * (2.0 * rng.random() - 1.0))


def _stop_positions(rng, start: float, end: float, count: int, jitter: float, margin: float) -> list[float]:
    """``count`` stops spread evenly over [start, end], each moved within ±jitter of its slot."""
    if count == 0 or end - start <= 2 * margin:
        return []
    span = end - start - 2 * margin
    slot = span / count
    out = []
    for k in range(count):
        centre = start + margin + (k + 0.5) * slot
        out.append(centre + jitter * slot * (2.0 * rng.random() - 1.0))
    return out


def build_traffic_plan(
    config: TrafficConfig, entrance_m: float, exit_m: float, cruise_mps: float, rng: np.random.Generator
) -> TrafficPlan:
    """Zones and stops of the configured scenario, anchored to B (entrance) and C (exit)."""
    c, j = config, config.jitter
    if c.scenario == "free" or exit_m <= entrance_m:
        return TrafficPlan()
    tunnel = exit_m - entrance_m
    durations = lambda n: [c.stop_min_s + (c.stop_max_s - c.stop_min_s) * rng.random() for _ in range(n)]  # noqa: E731
    if c.scenario == "portal":
        drop = _jit(rng, c.portal_drop_kmh, j) * KMH
        recovery = min(_jit(rng, c.portal_recovery_m, j), tunnel)
        speed = max(cruise_mps - drop, 5.0 * KMH)
        # The recovery after the adaptation distance is gentle (drivers speed up again inside).
        zone = SpeedZone(entrance_m, entrance_m + recovery, speed, decel=c.portal_brake, accel=0.5)
        return TrafficPlan(zones=(zone,))
    if c.scenario == "speed_limit":
        compliance = _jit(rng, 1.0, 0.1 * j)  # drivers drive near, not exactly at, the limit
        zone = SpeedZone(entrance_m, exit_m, c.speed_limit_kmh * KMH * compliance, decel=1.0, accel=1.0)
        return TrafficPlan(zones=(zone,))
    if c.scenario == "stop_and_go":
        moving = _jit(rng, c.moving_speed_kmh, j) * KMH
        zone = SpeedZone(entrance_m, exit_m, moving, c.brake_decel, c.go_accel, variation_mps=0.15 * moving,
                         variation_seed=int(rng.integers(2**31)))  # fmt: skip
        at = _stop_positions(rng, entrance_m, exit_m, c.stop_count, j, margin=min(100.0, 0.1 * tunnel))
        stops = tuple(Stop(a, d) for a, d in zip(at, durations(len(at)), strict=True))
        return TrafficPlan(zones=(zone,), stops=stops, stop_decel=c.brake_decel, go_accel=c.go_accel)
    if c.scenario == "exit_queue":
        length = min(_jit(rng, c.queue_length_m, j), tunnel)
        start = exit_m - length
        zone = SpeedZone(start, exit_m, _jit(rng, c.queue_speed_kmh, j) * KMH, c.brake_decel, c.go_accel)
        at = _stop_positions(rng, start, exit_m, c.queue_stops, j, margin=min(30.0, 0.1 * length))
        stops = tuple(Stop(a, d) for a, d in zip(at, durations(len(at)), strict=True))
        return TrafficPlan(zones=(zone,), stops=stops, stop_decel=c.brake_decel, go_accel=c.go_accel)
    if c.scenario == "congested":
        speed = _jit(rng, c.congested_speed_kmh, j) * KMH
        variation, seed = c.congested_variation_kmh * KMH, int(rng.integers(2**31))
        zone = SpeedZone(entrance_m, exit_m, speed, c.brake_decel, c.go_accel, variation_mps=variation,
                         variation_seed=seed)  # fmt: skip
        return TrafficPlan(zones=(zone,))
    raise ValueError(f"unknown traffic scenario {c.scenario!r}")


def zone_speed_cap(
    s: NDArray[np.float64], zone: SpeedZone, variation: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Speed cap of one zone on the grid ``s``: inside the zone (incl. variation), a braking ramp
    before it and an acceleration ramp after it (v² linear in distance, i.e. constant de/acceleration)."""
    inside = np.clip(zone.speed_mps + variation, zone.min_speed_mps, None)
    cap = np.full_like(s, np.inf)
    m = (s >= zone.start_m) & (s <= zone.end_m)
    cap[m] = inside[m]
    v_in = float(np.interp(zone.start_m, s, inside)) if zone.start_m <= s[-1] else zone.speed_mps
    v_out = float(np.interp(zone.end_m, s, inside)) if zone.end_m >= s[0] else zone.speed_mps
    before, after = s < zone.start_m, s > zone.end_m
    cap[before] = np.sqrt(v_in**2 + 2.0 * zone.decel * (zone.start_m - s[before]))
    cap[after] = np.sqrt(v_out**2 + 2.0 * zone.accel * (s[after] - zone.end_m))
    return cap


def stop_approach_speed(distance_to_stop: float, decel: float) -> float:
    """Speed on the constant-deceleration braking curve ``distance_to_stop`` before a stop."""
    return math.sqrt(2.0 * decel * max(distance_to_stop, 0.0))
