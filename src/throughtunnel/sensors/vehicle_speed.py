"""Vehicle speed sensor (OBD wheel speed / speedometer): reference information only (D41).

Not a phone sensor: the car's own speed reading, as an app could get it through an OBD dongle or the
car's interface. It is used only by the reference estimator; the runner never hands it to the main
estimators (D20).

Model: the true speed along the road (wheels roll along the slope: horizontal speed · √(1 + grade²))
times a fixed scale error, sampled at ``rate_hz``. The scale error stands for tyre wear and pressure,
load and speedometer calibration (+ = reads high). It keeps standstill at exactly zero, and its effect
on position grows with distance travelled, not with time. Not modelled (limitations.md): the 1 km/h
quantisation of the OBD value, noise, latency, dropouts.
"""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from throughtunnel.observations import VehicleSpeedStream
from throughtunnel.vehicle.truth import GroundTruth

DEFAULT_SCALE_ERROR_PCT = 2.0


class VehicleSpeedConfig(BaseModel):
    """The car's speed reading: a fixed scale error (no noise, no offset)."""

    model_config = ConfigDict(frozen=True)

    scale_error_pct: float = Field(
        DEFAULT_SCALE_ERROR_PCT, ge=-10.0, le=10.0, description="Fixed scale error [%], + = reads high"
    )
    rate_hz: float = Field(10.0, gt=0.0, le=100.0, description="Readings per second")


def simulate_vehicle_speed(truth: GroundTruth, config: VehicleSpeedConfig) -> VehicleSpeedStream:
    """Readings at ``rate_hz`` from t = 0 to the end of the drive."""
    t = np.arange(0.0, truth.duration_s + 1e-9, 1.0 / config.rate_hz)
    horizontal = np.interp(t, truth.t, truth.speed)
    grade = np.interp(t, truth.t, truth.grade)
    along_road = horizontal * np.sqrt(1.0 + grade**2)
    return VehicleSpeedStream(t=t, speed_mps=along_road * (1.0 + config.scale_error_pct / 100.0))
