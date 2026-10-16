"""Standstill oracle (D49): when the car stands still, taken from the true motion. Not a sensor.

Step 3 of estimator_plan.md measures what knowing standstill is worth before anyone builds a detector.
A phone detector would need vehicle vibration or engine audio, which the simulator does not model and
this study could not validate (limitations.md, roadmap R12). So the information is given directly,
labelled as an oracle, and only estimators that declare ``uses_standstill`` receive it.

Default (perfect): the car stands when its true speed is exactly zero (traffic stops, D37); transitions
at the simulation rate (100 Hz). The error model (D50, step 3b) degrades it the way a detector would
fail, tied to the real motion, not at random times (user: "false standstill should be logical like
when slow down"):
1. ``false_standstill_kmh``: standstill is reported whenever the true speed is below this threshold. A
   detector cannot tell creeping from standing, so it fires early while braking into a stop and
   releases late while pulling away (and reports any slow phase without a stop).
2. ``miss_probability``: each reported standstill is dropped with this probability (a stop the detector
   never notices), drawn per stop from the run's seed (stream "standstill.miss").
3. ``delay_s``: every report starts and ends this much late (the detector needs time to decide).
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from throughtunnel.observations import StandstillStream
from throughtunnel.randomness import rng_stream
from throughtunnel.vehicle.truth import GroundTruth

KMH = 1.0 / 3.6


class StandstillOracleConfig(BaseModel):
    """Errors of the standstill oracle (D50). All zero = the perfect oracle."""

    model_config = ConfigDict(frozen=True)

    delay_s: float = Field(0.0, ge=0.0, le=10.0, description="Each report starts and ends this late [s]")
    miss_probability: float = Field(0.0, ge=0.0, le=1.0, description="Probability a stop is not reported")
    false_standstill_kmh: float = Field(
        0.0, ge=0.0, le=20.0, description="Report standstill below this true speed [km/h] (0: exactly zero)"
    )

    @property
    def perfect(self) -> bool:
        return self.delay_s == 0.0 and self.miss_probability == 0.0 and self.false_standstill_kmh == 0.0


def standstill_oracle(
    truth: GroundTruth, config: StandstillOracleConfig | None = None, seed: int = 0
) -> StandstillStream:
    """Transitions between moving and reported standing, from the true motion and the error model."""
    config = config or StandstillOracleConfig()
    threshold = config.false_standstill_kmh * KMH
    standing = truth.speed <= 0.0 if threshold <= 0.0 else truth.speed < threshold
    change = np.flatnonzero(np.diff(standing.astype(np.int8))) + 1
    edges = np.concatenate([[0], change, [len(standing)]])
    t = truth.t
    intervals = [
        (float(t[a]), float(t[b]) if b < len(t) else np.inf) for a, b in pairwise(edges) if standing[a]
    ]
    if config.miss_probability > 0.0:
        u = rng_stream(seed, "standstill.miss").random(len(intervals))
        intervals = [iv for iv, x in zip(intervals, u, strict=True) if x >= config.miss_probability]
    if config.delay_s > 0.0:
        intervals = [(a + config.delay_s, b + config.delay_s) for a, b in intervals]
    times: list[float] = []
    states: list[bool] = []
    for a, b in intervals:
        if times and a <= times[-1]:  # overlaps the previous report after the delay: merge
            times.pop()
            states.pop()
        else:
            times.append(a)
            states.append(True)
        if np.isfinite(b):
            times.append(b)
            states.append(False)
    return StandstillStream(t=np.array(times, dtype=float), standing=np.array(states, dtype=bool))
