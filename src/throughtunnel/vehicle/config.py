"""Driver / vehicle behaviour parameters.

Values are comfort-oriented passenger-car figures (SI units unless the name
says otherwise). References for the defaults: typical comfortable lateral
acceleration 1.5-3 m/s^2, comfortable acceleration ~1-2 m/s^2, comfortable
braking ~2-3 m/s^2, comfortable longitudinal jerk ~1-2.5 m/s^3.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

KMH = 1.0 / 3.6  # km/h -> m/s


class DriverConfig(BaseModel):
    """How the (reasonable) driver chooses speed along the road."""

    model_config = ConfigDict(frozen=True)

    style: str = Field("normal", description="Label of the preset this config came from")
    cruise_speed_kmh: float = Field(70.0, gt=0, le=200, description="Preferred speed on straight road")
    speed_variability_kmh: float = Field(
        4.0, ge=0, le=30, description="Std-dev of slow random variation of the preferred speed"
    )
    speed_correlation_length_m: float = Field(
        400.0, gt=0, description="Correlation length of the preferred-speed variation"
    )
    initial_speed_kmh: float | None = Field(
        None, gt=0, description="Speed at the start of the route; None = the planned reference speed"
    )
    min_speed_kmh: float = Field(10.0, gt=0, description="Speed floor: the vehicle never stops in the tunnel")
    max_speed_kmh: float = Field(130.0, gt=0, le=250)
    max_lateral_accel: float = Field(2.0, gt=0, le=8, description="Curve speed limit: v^2 * |κ| <= this")
    max_accel: float = Field(1.5, gt=0, le=6)
    max_decel: float = Field(2.5, gt=0, le=9)
    max_jerk: float = Field(2.0, gt=0, le=20, description="Longitudinal jerk limit")
    curve_preview_m: float = Field(
        15.0, ge=0, description="Curve speed limits are applied this far before/after the curvature peak"
    )
    speed_tracking_gain: float = Field(0.8, gt=0, description="P-gain on speed error [1/s]")
    accel_response_rate: float = Field(4.0, gt=0, description="Bandwidth of the acceleration actuator [1/s]")

    @model_validator(mode="after")
    def _consistent_speeds(self) -> Self:
        if not self.min_speed_kmh < self.max_speed_kmh:
            raise ValueError("min_speed_kmh must be below max_speed_kmh")
        if self.cruise_speed_kmh < self.min_speed_kmh:
            raise ValueError("cruise_speed_kmh must be at least min_speed_kmh")
        return self

    @property
    def preview_time_s(self) -> float:
        """Anticipation that centres the jerk-limited ramp on the reference profile corner."""
        return 0.5 * max(self.max_accel, self.max_decel) / self.max_jerk


DRIVER_PRESETS: dict[str, DriverConfig] = {
    "calm": DriverConfig(
        style="calm",
        cruise_speed_kmh=60.0,
        speed_variability_kmh=2.0,
        max_lateral_accel=1.5,
        max_accel=1.0,
        max_decel=2.0,
        max_jerk=1.2,
    ),
    "normal": DriverConfig(style="normal"),
    "sporty": DriverConfig(
        style="sporty",
        cruise_speed_kmh=85.0,
        speed_variability_kmh=6.0,
        speed_correlation_length_m=300.0,
        max_lateral_accel=3.0,
        max_accel=2.5,
        max_decel=3.5,
        max_jerk=3.5,
    ),
}
