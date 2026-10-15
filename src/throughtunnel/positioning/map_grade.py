"""Map-grade compensation of the forward accelerometer channel (D39).

A reusable component (composition, D18) for estimators that integrate the forward specific force.
On a grade φ the forward accelerometer axis picks up gravity, g·sin φ (+ uphill). The approach-phase
levelling has already absorbed the grade it was calibrated in (φ_cal, the mean over its GPS
intervals), so what leaks into the speed is

    a_fwd = a + g·sin(φ - φ_cal)

With the road grade from the map, the estimator subtracts this term at its *estimated* position along
the route. What it cannot remove:
* the grade mismatch caused by its own along-track error at a grade change,
  g·Δφ·(position error / speed), which feeds back into the speed;
* second-order terms: the forward axis measures the along-road rather than the horizontal
  acceleration (a factor √(1 + grade²), 0.08 % at 4 %), and the vertical acceleration in dips and
  crests leaks in multiplied by sin(φ - φ_cal).

Gravity is the standard value; the simulator uses normal gravity at the latitude. The difference
(≈0.05 % at 40° N) scales only the grade correction: ≈1·10⁻⁴ m/s² on a 2 % grade, i.e. ~14 m after a
7.6 min stop-and-go outage on Eisenhower +2 % (measured). Using the matched value there gives 56 m
instead of 42 m with ideal sensors: a second small term of opposite sign remains unidentified
(map_grade_study.md, open items).
"""

from __future__ import annotations

import math

from throughtunnel.observations import RouteMap

GRAVITY = 9.80665  # m/s^2


class GradeCompensation:
    """Gravity leakage on the forward axis predicted from the map's road grade."""

    def __init__(self, route: RouteMap) -> None:
        if not route.has_grade:
            raise ValueError("the route map has no grade data")
        self.route = route

    def angle_at(self, distance_m: float) -> float:
        """Road grade angle [rad] at ``distance_m`` along the route (+ = uphill)."""
        return math.atan(self.route.grade_at(distance_m))

    def forward_gravity(self, distance_m: float, calibration_angle: float) -> float:
        """Specific force [m/s^2] that gravity adds to the levelled forward axis at ``distance_m``."""
        return GRAVITY * math.sin(self.angle_at(distance_m) - calibration_angle)


def grade_compensation(route: RouteMap) -> GradeCompensation | None:
    """The compensation if the map provides the grade, else None (the estimator runs unchanged)."""
    return GradeCompensation(route) if route.has_grade else None
