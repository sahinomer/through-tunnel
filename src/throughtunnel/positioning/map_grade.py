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

Gravity (F1, D48): the normal gravity of the WGS84 ellipsoid at the route's latitude (the phone knows
it from GPS), as inertial navigation does. The standard value 9.80665 m/s² was 0.05 % off at 40° N and
scaled the grade correction wrongly: −11 m (Eisenhower +2 %) and +23–29 m (synthetic −2 %) after
stop-and-go outages with ideal sensors (residual_study.md). Taking g from the calibration's measured
|f| would be worse: an accelerometer bias along the up axis (~10 mg) is not calibrated away. Not
modelled: altitude (−0.03 % per km) and local anomalies (~0.01 %); the simulator uses the same
formula without altitude, so here the value is exact (limitations.md).
"""

from __future__ import annotations

import math

from throughtunnel.observations import RouteMap

GRAVITY = 9.80665  # m/s^2, standard gravity (used only with use_normal_gravity = False)
GAMMA_EQUATOR, K_SOMIGLIANA, E2 = 9.7803253359, 0.00193185265241, 6.69437999014e-3  # WGS84


def normal_gravity(lat_deg: float) -> float:
    """WGS84 normal gravity on the ellipsoid [m/s^2] (Somigliana)."""
    s2 = math.sin(math.radians(lat_deg)) ** 2
    return GAMMA_EQUATOR * (1.0 + K_SOMIGLIANA * s2) / math.sqrt(1.0 - E2 * s2)


class GradeCompensation:
    """Gravity leakage on the forward axis predicted from the map's road grade."""

    use_normal_gravity = True  # False: the standard value (the behaviour before D48, for comparisons)

    def __init__(self, route: RouteMap) -> None:
        if not route.has_grade:
            raise ValueError("the route map has no grade data")
        self.route = route
        self.gravity = normal_gravity(float(route.lat[0])) if self.use_normal_gravity else GRAVITY

    def angle_at(self, distance_m: float) -> float:
        """Road grade angle [rad] at ``distance_m`` along the route (+ = uphill)."""
        return math.atan(self.route.grade_at(distance_m))

    def forward_gravity(self, distance_m: float, calibration_angle: float) -> float:
        """Specific force [m/s^2] that gravity adds to the levelled forward axis at ``distance_m``."""
        return self.gravity * math.sin(self.angle_at(distance_m) - calibration_angle)


def grade_compensation(route: RouteMap) -> GradeCompensation | None:
    """The compensation if the map provides the grade, else None (the estimator runs unchanged)."""
    return GradeCompensation(route) if route.has_grade else None
