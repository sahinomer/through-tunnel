"""Positioning: estimators that see only ``throughtunnel.observations`` (never the simulator's truth).

Import rule (tested): nothing in this package may import ``throughtunnel.vehicle``, ``road``,
``scenario``, ``sensors``, ``routing``, ``app`` or ``evaluation``.
"""

from throughtunnel.positioning.alignment import ALIGNMENTS, AlignmentStage, VehicleImu
from throughtunnel.positioning.base import Estimator, StateEstimate
from throughtunnel.positioning.dead_reckoning import (
    CalibratedDeadReckoning,
    FilteredDeadReckoning,
    RawDeadReckoning,
)
from throughtunnel.positioning.route_constrained import (
    RouteImuDeadReckoning,
    RouteImuStandstill,
    RouteImuZeroVelocity,
    RouteSpeedHold,
    RouteVehicleSpeed,
)
from throughtunnel.positioning.runner import EstimateTrack, align_imu, run_estimator, run_estimators

# Registry used by the UI and experiments: name -> estimator class (constructed with the route map).
# Each class names its alignment stage (``Estimator.alignment``; registry ``ALIGNMENTS``), D40.
ESTIMATORS: dict[str, type[Estimator]] = {
    cls.name: cls
    for cls in (
        RawDeadReckoning,
        CalibratedDeadReckoning,
        FilteredDeadReckoning,
        RouteImuDeadReckoning,
        RouteSpeedHold,
        RouteVehicleSpeed,
        RouteImuStandstill,
        RouteImuZeroVelocity,
    )
}
# The phone-only solution (D20) vs. reference estimators that use the car's speed reading (D41) and
# oracle estimators that get standstill from the true motion (D49).
MAIN_ESTIMATORS: dict[str, type[Estimator]] = {
    n: cls for n, cls in ESTIMATORS.items() if not (cls.uses_vehicle_speed or cls.uses_standstill)
}
REFERENCE_ESTIMATORS: dict[str, type[Estimator]] = {
    n: cls for n, cls in ESTIMATORS.items() if cls.uses_vehicle_speed
}
ORACLE_ESTIMATORS: dict[str, type[Estimator]] = {
    n: cls for n, cls in ESTIMATORS.items() if cls.uses_standstill
}

__all__ = [
    "ALIGNMENTS",
    "ESTIMATORS",
    "MAIN_ESTIMATORS",
    "ORACLE_ESTIMATORS",
    "REFERENCE_ESTIMATORS",
    "AlignmentStage",
    "EstimateTrack",
    "Estimator",
    "StateEstimate",
    "VehicleImu",
    "align_imu",
    "run_estimator",
    "run_estimators",
]
