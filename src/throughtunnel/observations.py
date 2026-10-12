"""Observation types: everything a phone navigation app can see, and nothing else.

This module is the boundary between the simulator, which knows the ground truth, and positioning,
which must not (decisions D15, PD1). It depends only on numpy and the pure geodesy helpers and must
never import simulator modules (vehicle, road, scenario, sensors, routing, app). A test enforces
this.

Contents:
* ``ImuStream``: accelerometer and gyroscope samples in Android phone axes.
* ``GnssStream`` / ``GnssFix``: phone-style location fixes (Android ``Location``-like fields).
* ``RouteMap``: the navigation route as the app knows it. Map geometry, not the driven path. It
  includes the tunnel entrance/exit and navigation events as distances along the route.
* ``Observations``: the bundle handed to estimators.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import cached_property

import numpy as np
from numpy.typing import NDArray

from throughtunnel.geodesy import LocalFrame

ANDROID_FRAME = "android"  # x: right edge, y: top edge, z: out of the screen; m/s^2 and rad/s


@dataclass(frozen=True)
class ImuStream:
    """Timestamped accelerometer and gyroscope samples in the phone's sensor frame.

    Deliberately carries no simulation truth: in particular not the phone mounting, which a real
    app does not know (estimating the phone-to-vehicle rotation is part of the positioning problem).
    """

    t: NDArray[np.float64]  # [s], strictly increasing
    accel: NDArray[np.float64]  # (N, 3) specific force [m/s^2]
    gyro: NDArray[np.float64]  # (N, 3) angular rate [rad/s]
    frame: str = ANDROID_FRAME
    source: str = "simulated:ideal"
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        n = len(self.t)
        if self.accel.shape != (n, 3) or self.gyro.shape != (n, 3):
            raise ValueError("accel and gyro must have shape (len(t), 3)")
        if n > 1 and not np.all(np.diff(self.t) > 0):
            raise ValueError("timestamps must be strictly increasing")

    def __len__(self) -> int:
        return len(self.t)

    @property
    def rate_hz(self) -> float:
        return (len(self.t) - 1) / float(self.t[-1] - self.t[0])

    def at(self, t: float) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Linearly interpolated (accel, gyro) at time ``t`` (display helper)."""
        tc = min(max(t, float(self.t[0])), float(self.t[-1]))
        accel = np.array([np.interp(tc, self.t, self.accel[:, k]) for k in range(3)])
        gyro = np.array([np.interp(tc, self.t, self.gyro[:, k]) for k in range(3)])
        return accel, gyro


@dataclass(frozen=True)
class GnssFix:
    """One phone location fix (fields modelled on Android ``Location``)."""

    t: float  # [s] on the same clock as the IMU
    lat: float  # [deg]
    lon: float  # [deg]
    horizontal_accuracy_m: float  # 68 % radius
    speed_mps: float
    bearing_deg: float  # direction of travel, clockwise from north
    speed_accuracy_mps: float
    bearing_accuracy_deg: float


_GNSS_FIELDS = (
    "lat",
    "lon",
    "horizontal_accuracy_m",
    "speed_mps",
    "bearing_deg",
    "speed_accuracy_mps",
    "bearing_accuracy_deg",
)


@dataclass(frozen=True)
class GnssStream:
    """Time-ordered location fixes. Gaps (e.g. inside a tunnel) are simply missing fixes."""

    t: NDArray[np.float64]
    lat: NDArray[np.float64]
    lon: NDArray[np.float64]
    horizontal_accuracy_m: NDArray[np.float64]
    speed_mps: NDArray[np.float64]
    bearing_deg: NDArray[np.float64]
    speed_accuracy_mps: NDArray[np.float64]
    bearing_accuracy_deg: NDArray[np.float64]
    source: str = "simulated:measured"

    def __post_init__(self) -> None:
        n = len(self.t)
        if any(len(getattr(self, f)) != n for f in _GNSS_FIELDS):
            raise ValueError("all GNSS fields must have the same length")
        if n > 1 and not np.all(np.diff(self.t) > 0):
            raise ValueError("timestamps must be strictly increasing")

    def __len__(self) -> int:
        return len(self.t)

    def fix(self, i: int) -> GnssFix:
        return GnssFix(float(self.t[i]), *(float(getattr(self, f)[i]) for f in _GNSS_FIELDS))

    def select(self, mask: NDArray[np.bool_]) -> GnssStream:
        return GnssStream(
            t=self.t[mask], **{f: getattr(self, f)[mask] for f in _GNSS_FIELDS}, source=self.source
        )


@dataclass(frozen=True)
class NavigationEvent:
    """A navigation target the app knows about, e.g. an exit inside the tunnel (D14)."""

    name: str
    distance_m: float  # along the route map, from the route start A
    announce_leads_m: tuple[float, ...] = (300.0, 0.0)  # announce this far before the event


@dataclass(frozen=True)
class RouteMap:
    """The navigation route as the app knows it: original map geometry (D21), not the driven path."""

    lat: NDArray[np.float64]
    lon: NDArray[np.float64]
    tunnel_entrance_m: float  # point B, distance from A along this polyline
    tunnel_exit_m: float  # point C
    events: tuple[NavigationEvent, ...] = ()

    def __post_init__(self) -> None:
        if len(self.lat) < 2 or len(self.lat) != len(self.lon):
            raise ValueError("route needs at least two (lat, lon) vertices")
        if not 0.0 <= self.tunnel_entrance_m <= self.tunnel_exit_m <= self.length_m + 1e-6:
            raise ValueError("require 0 <= tunnel entrance <= tunnel exit <= route length")

    @cached_property
    def frame(self) -> LocalFrame:
        """Local ENU frame anchored at the route start (A)."""
        return LocalFrame(float(self.lat[0]), float(self.lon[0]))

    @cached_property
    def enu(self) -> NDArray[np.float64]:
        """Polyline vertices (N, 2) east/north [m] in ``frame``."""
        return self.frame.to_enu(self.lat, self.lon)[:, :2]

    @cached_property
    def distance_m(self) -> NDArray[np.float64]:
        """Cumulative along-route distance at each vertex [m]."""
        seg = np.linalg.norm(np.diff(self.enu, axis=0), axis=1)
        return np.concatenate([[0.0], np.cumsum(seg)])

    @property
    def length_m(self) -> float:
        return float(self.distance_m[-1])

    def enu_at(self, distance_m: float) -> tuple[float, float]:
        d = self.distance_m
        xy = self.enu
        s = min(max(distance_m, 0.0), float(d[-1]))
        return float(np.interp(s, d, xy[:, 0])), float(np.interp(s, d, xy[:, 1]))

    def latlon_at(self, distance_m: float) -> tuple[float, float]:
        e, n = self.enu_at(distance_m)
        lat, lon, _ = self.frame.to_geodetic(np.array([e, n, 0.0]))
        return float(lat), float(lon)

    def heading_at(self, distance_m: float) -> float:
        """ENU yaw (CCW from east) of the polyline segment containing ``distance_m``."""
        d = self.distance_m
        i = int(np.clip(np.searchsorted(d, distance_m, side="right") - 1, 0, len(d) - 2))
        dx, dy = np.diff(self.enu[i : i + 2], axis=0)[0]
        return math.atan2(dy, dx)


@dataclass(frozen=True)
class Observations:
    """Everything an estimator is allowed to use (D15)."""

    imu: ImuStream
    gnss: GnssStream
    route: RouteMap
