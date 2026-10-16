"""Standstill oracle (D49): when the car stands still, taken from the true motion. Not a sensor.

Step 3 of estimator_plan.md measures what knowing standstill is worth before anyone builds a detector.
A phone detector would need vehicle vibration or engine audio, which the simulator does not model and
this study could not validate (limitations.md, roadmap R12). So the information is given directly,
labelled as an oracle, and only estimators that declare ``uses_standstill`` receive it.

Perfect version: the car stands when its true speed is exactly zero (traffic stops, D37). Transitions are
at the simulation rate (100 Hz). A later sensitivity study adds delays, missed stops and false
standstills during real slow-downs (user: "false standstill should be logical like when slow down").
"""

from __future__ import annotations

import numpy as np

from throughtunnel.observations import StandstillStream
from throughtunnel.vehicle.truth import GroundTruth


def standstill_oracle(truth: GroundTruth) -> StandstillStream:
    """Exact transitions between moving and standing (speed == 0) in the true motion."""
    standing = truth.speed <= 0.0
    change = np.flatnonzero(np.diff(standing.astype(np.int8))) + 1
    idx = np.concatenate([[0], change]) if standing[0] else change
    return StandstillStream(t=truth.t[idx].astype(float), standing=standing[idx].copy())
