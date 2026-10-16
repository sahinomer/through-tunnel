"""Portal freeze (D46, solutions 1a + 2a of docs/estimator_plan.md): no GPS learning right before a tunnel.

GPS degrades in the last few hundred metres before a tunnel portal (walls, slopes, multipath), but the
phone's reported accuracy does not always show it. The handover diagnostic (docs/handover_study.md)
showed why that matters: the levelling's forward offset is set by the GPS speed error of the *last*
approach fix, and the 5 s speed blend hands over the last few fixes' speed errors. Both then grow
with the outage (½·b·t² + δv·t).

The route map knows where the tunnel is (B, C). Inside the freeze zone, from ``before_m`` before B to
the tunnel exit C:
* the GPS + IMU alignment stops calibrating: it keeps the orientation solved from the fixes before
  the zone (1a);
* the GPS-blending estimators stop pulling speed (and heading) towards the fixes and carry them with
  the IMU, so they hand over the last state they trusted (2a). Position still follows the fixes.

The zone is looked up at the estimator's own along-route distance (each fix projected onto the route).
After C everything works as before. ``FREEZE_BEFORE_ENTRANCE_M`` is the default; None switches the
freeze off (the behaviour before D46). It is read when a stage or estimator is built, so an experiment
can change it per process.
"""

from __future__ import annotations

from throughtunnel.observations import RouteMap

FREEZE_BEFORE_ENTRANCE_M: float | None = 200.0


class PortalFreeze:
    """The freeze zone [B − before_m, C] of one route, in route distance from A."""

    def __init__(self, route: RouteMap, before_m: float) -> None:
        self.start_m = route.tunnel_entrance_m - before_m
        self.end_m = route.tunnel_exit_m

    def active(self, distance_m: float | None) -> bool:
        return distance_m is not None and self.start_m <= distance_m <= self.end_m


def portal_freeze(route: RouteMap) -> PortalFreeze | None:
    """The route's freeze zone, or None if the freeze is off or the route has no tunnel."""
    before = FREEZE_BEFORE_ENTRANCE_M
    if before is None or route.tunnel_exit_m <= route.tunnel_entrance_m:
        return None
    return PortalFreeze(route, before)
