"""Observation types: everything a phone navigation app can see, and nothing else.

This module is the boundary between the simulator, which knows the ground truth, and positioning,
which must not (decisions D15, PD1). It depends only on numpy and the pure geodesy helpers and must
never import simulator modules (vehicle, road, scenario, sensors, routing, app). A test enforces
this.

Contents:
* ``ImuStream``: accelerometer and gyroscope samples in Android phone axes.
* ``GnssStream`` / ``GnssFix``: phone-style location fixes (Android ``Location``-like fields).
* ``RouteMap``: the navigation route as the app knows it. Map geometry, not the driven path. It
  includes the tunnel entrance/exit and the exit-announcement distance along the route.
* ``VehicleSpeedStream``: the car's own speed reading (OBD / speedometer), reference only (D41).
* ``StandstillStream``: when the car stands still, an oracle from the true motion (D49), not a sensor.
* ``Observations``: the bundle the runner feeds to the positioning pipeline.
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
class RouteMap:
    """The navigation route as the app knows it: original map geometry (D21), not the driven path."""

    lat: NDArray[np.float64]
    lon: NDArray[np.float64]
    tunnel_entrance_m: float  # point B, distance from A along this polyline
    tunnel_exit_m: float  # point C
    announce_before_exit_m: float | None = None  # announce the tunnel exit this far before C (D32)
    # Optional road grade from the map provider (D39): dz/ds (+ = uphill) every ``grade_step_m`` along
    # this polyline, starting at A. None = the map has no grade data.
    road_grade: NDArray[np.float64] | None = None
    grade_step_m: float = 10.0

    def __post_init__(self) -> None:
        if len(self.lat) < 2 or len(self.lat) != len(self.lon):
            raise ValueError("route needs at least two (lat, lon) vertices")
        if not 0.0 <= self.tunnel_entrance_m <= self.tunnel_exit_m <= self.length_m + 1e-6:
            raise ValueError("require 0 <= tunnel entrance <= tunnel exit <= route length")
        d = self.announce_before_exit_m
        if d is not None and not 0.0 <= d <= self.tunnel_exit_m - self.tunnel_entrance_m + 1e-6:
            raise ValueError("the announcement distance must lie within the tunnel length")
        if self.road_grade is not None and (len(self.road_grade) < 2 or self.grade_step_m <= 0.0):
            raise ValueError("grade data needs at least two samples and a positive step")

    @property
    def has_grade(self) -> bool:
        return self.road_grade is not None

    @cached_property
    def _grade_samples(self) -> list[float]:
        return np.asarray(self.road_grade, dtype=float).tolist()

    def grade_at(self, distance_m: float) -> float:
        """Road grade dz/ds (+ = uphill) at ``distance_m`` along the route, from the map's grade data.

        Linear interpolation on the uniform grid, in plain Python: estimators call it per IMU sample.
        Beyond the data the end values are held. Raises if the map has no grade data."""
        g = self._grade_samples
        x = distance_m / self.grade_step_m
        if x <= 0.0:
            return g[0]
        i = int(x)
        if i >= len(g) - 1:
            return g[-1]
        return g[i] + (x - i) * (g[i + 1] - g[i])

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

    @property
    def announcement_m(self) -> float | None:
        """Route distance from A at which the app announces the tunnel exit (None = no announcement)."""
        d = self.announce_before_exit_m
        return None if d is None else self.tunnel_exit_m - d

    def enu_at(self, distance_m: float) -> tuple[float, float]:
        d = self.distance_m
        xy = self.enu
        s = min(max(distance_m, 0.0), float(d[-1]))
        return float(np.interp(s, d, xy[:, 0])), float(np.interp(s, d, xy[:, 1]))

    def latlon_at(self, distance_m: float) -> tuple[float, float]:
        e, n = self.enu_at(distance_m)
        lat, lon, _ = self.frame.to_geodetic(np.array([e, n, 0.0]))
        return float(lat), float(lon)

    def project_enu(
        self, east: float, north: float, lo_m: float = 0.0, hi_m: float | None = None
    ) -> tuple[float, float]:
        """Closest point on the route (optionally searched only within [lo_m, hi_m] along it).

        Returns (distance along the route [m], signed lateral offset [m], + = left of travel).
        """
        xy, d = self.enu, self.distance_m
        a = xy[:-1]
        ab = xy[1:] - a
        seg_len2 = np.maximum((ab**2).sum(axis=1), 1e-12)
        ap = np.array([east, north]) - a
        frac = np.clip((ap * ab).sum(axis=1) / seg_len2, 0.0, 1.0)
        dist2 = ((ap - frac[:, None] * ab) ** 2).sum(axis=1)
        hi = self.length_m if hi_m is None else hi_m
        valid = (d[1:] >= lo_m) & (d[:-1] <= hi)
        dist2 = np.where(valid, dist2, np.inf)
        k = int(np.argmin(dist2))
        along = float(d[k] + frac[k] * np.sqrt(seg_len2[k]))
        cross = ab[k, 0] * ap[k, 1] - ab[k, 1] * ap[k, 0]
        return min(max(along, lo_m), hi), float(math.copysign(math.sqrt(dist2[k]), cross))

    def locate(self, lat: float, lon: float, lo_m: float = 0.0, hi_m: float | None = None) -> float:
        """Distance along the route of the point closest to (lat, lon)."""
        e, n, _ = self.frame.to_enu(lat, lon)
        return self.project_enu(float(e), float(n), lo_m, hi_m)[0]

    def heading_at(self, distance_m: float) -> float:
        """ENU yaw (CCW from east) of the polyline segment containing ``distance_m``."""
        d = self.distance_m
        i = int(np.clip(np.searchsorted(d, distance_m, side="right") - 1, 0, len(d) - 2))
        dx, dy = np.diff(self.enu[i : i + 2], axis=0)[0]
        return math.atan2(dy, dx)


@dataclass(frozen=True)
class VehicleSpeedStream:
    """The car's own speed reading (OBD wheel speed / speedometer): reference information only (D41).

    Not a phone sensor. The runner hands it only to estimators that declare ``uses_vehicle_speed``
    (the reference estimator); the main estimators never receive it (D20)."""

    t: NDArray[np.float64]  # [s], strictly increasing, same clock as the IMU
    speed_mps: NDArray[np.float64]  # [m/s], >= 0 (along the road)
    source: str = "simulated:vehicle"

    def __post_init__(self) -> None:
        if len(self.t) != len(self.speed_mps):
            raise ValueError("t and speed_mps must have the same length")
        if len(self.t) > 1 and not np.all(np.diff(self.t) > 0):
            raise ValueError("timestamps must be strictly increasing")

    def __len__(self) -> int:
        return len(self.t)


@dataclass(frozen=True)
class StandstillStream:
    """**Oracle** standstill information (D49): when the car stands still, as exact transitions.

    Not a phone sensor and not a validated detector. It is derived from the true motion to measure what
    knowing standstill is worth (step 3 of estimator_plan.md). A real source would be a detector from
    vibration or engine audio (roadmap R12) or the car itself. The runner hands it only to estimators
    that declare ``uses_standstill``; the phone-only estimators never receive it."""

    t: NDArray[np.float64]  # [s] transition times, strictly increasing, same clock as the IMU
    standing: NDArray[np.bool_]  # the state from t[k] on (alternating)
    source: str = "oracle:truth"

    def __post_init__(self) -> None:
        if len(self.t) != len(self.standing):
            raise ValueError("t and standing must have the same length")
        if len(self.t) > 1 and not np.all(np.diff(self.t) > 0):
            raise ValueError("timestamps must be strictly increasing")

    def __len__(self) -> int:
        return len(self.t)


@dataclass(frozen=True)
class Observations:
    """Everything the positioning pipeline may use (D15). ``vehicle_speed`` is reference information and
    ``standstill`` oracle information: the runner passes each only to estimators that declare it (D20,
    D41, D49)."""

    imu: ImuStream
    gnss: GnssStream
    route: RouteMap
    vehicle_speed: VehicleSpeedStream | None = None
    standstill: StandstillStream | None = None
