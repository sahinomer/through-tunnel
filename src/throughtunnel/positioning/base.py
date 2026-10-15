"""Estimator contract (inheritance, D18) and the state it reports."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

from throughtunnel.observations import GnssFix, RouteMap
from throughtunnel.positioning.alignment import VehicleImu


@dataclass(frozen=True)
class StateEstimate:
    """An estimator's belief at time ``t`` (route-local ENU frame, i.e. ``RouteMap.frame``)."""

    t: float
    east: float  # [m]
    north: float  # [m]
    speed: float  # [m/s]
    heading: float  # ENU yaw, CCW from east [rad]
    mode: str  # "gnss" (fixes arriving) or "dead_reckoning" (no fixes)
    route_distance: float | None = None  # along the route map, if the estimator tracks it
    position_std_m: float | None = None  # 1-sigma horizontal uncertainty, if the estimator has one


class Estimator(ABC):
    """A live positioning algorithm: receives observations one at a time, in time order (D17).

    Pipeline (D40): observations → alignment stage → estimator. The IMU reaches the estimator only
    through its alignment stage, as vehicle-axis samples (``VehicleImu``, or None while the stage has
    no orientation yet). GPS fixes and the route map arrive unchanged. An estimator gets the route map
    at construction and must not use any other information (D15). Reusable processing (map matching,
    grade compensation) is composed in as plain objects (D18).

    ``alignment`` names the stage that feeds the estimator (``alignment.ALIGNMENTS``); None = the
    estimator uses no IMU and receives None samples (time ticks only). Experiments may set another
    stage on an instance to compare alignment methods on the same estimator.
    """

    name: str = "estimator"
    label: str = "Estimator"
    alignment: str | None = "gps_imu"

    def __init__(self, route: RouteMap) -> None:
        self.route = route
        self.frame = route.frame

    @abstractmethod
    def on_imu(self, t: float, imu: VehicleImu | None) -> None:
        """One IMU sample from the alignment stage (vehicle axes), or None (no orientation yet)."""

    @abstractmethod
    def on_gnss(self, fix: GnssFix) -> None:
        """One GPS fix."""

    @abstractmethod
    def state(self) -> StateEstimate | None:
        """Current estimate, or None before the estimator is initialised."""

    # ------------------------------------------------------------------ helpers for subclasses
    def fix_enu(self, fix: GnssFix) -> tuple[float, float]:
        e, n, _ = self.frame.to_enu(fix.lat, fix.lon)
        return float(e), float(n)

    @staticmethod
    def bearing_to_yaw(bearing_deg: float) -> float:
        """Compass bearing (clockwise from north) -> ENU yaw (counter-clockwise from east)."""
        return math.radians(90.0 - bearing_deg)
