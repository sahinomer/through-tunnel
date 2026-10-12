"""Positioning: estimators that see only ``throughtunnel.observations`` (never the simulator's truth).

Import rule (tested): nothing in this package may import ``throughtunnel.vehicle``, ``road``,
``scenario``, ``sensors``, ``routing``, ``app`` or ``evaluation``.
"""

from throughtunnel.positioning.base import Estimator, StateEstimate
from throughtunnel.positioning.dead_reckoning import (
    CalibratedDeadReckoning,
    FilteredDeadReckoning,
    RawDeadReckoning,
)
from throughtunnel.positioning.route_constrained import RouteImuDeadReckoning, RouteSpeedHold
from throughtunnel.positioning.runner import EstimateTrack, run_estimator, run_estimators

# Registry used by the UI and experiments: name -> estimator class (constructed with the route map).
ESTIMATORS: dict[str, type[Estimator]] = {
    cls.name: cls
    for cls in (
        RawDeadReckoning,
        CalibratedDeadReckoning,
        FilteredDeadReckoning,
        RouteImuDeadReckoning,
        RouteSpeedHold,
    )
}

__all__ = [
    "ESTIMATORS",
    "EstimateTrack",
    "Estimator",
    "StateEstimate",
    "run_estimator",
    "run_estimators",
]
