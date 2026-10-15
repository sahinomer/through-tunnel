"""Alignment stage (D40): the first positioning step, between the observations and the estimators.

Pipeline: observations (measured phone IMU, GPS fixes, route map) → **alignment** → estimators.

An alignment stage receives the raw phone IMU and the GPS fixes in time order and turns every IMU
sample into a vehicle-axis sample (``VehicleImu``): the same measured values, noise and bias
included, rotated from phone axes into the vehicle axes the stage believes in, with the gyro bias it
estimated removed from the yaw rate. Nothing is filtered or averaged, and all three axes are kept, so
no information is lost. Before the stage has an orientation it yields ``None``.

Methods (``ALIGNMENTS``), swappable per estimator:
* ``DeclaredAlignment``: phone axes taken as vehicle axes, no gyro bias (an explicit assumption,
  valid only for an aligned mount).
* ``GpsImuAlignment``: levelling, yaw and gyro bias from approach GPS and IMU
  (``mount_estimation.MountAlignmentEstimator``). If the map provides the grade (D39), the grade
  angle at each fix goes into the calibration, and every sample carries the mean grade the calibration
  absorbed (``calibration_grade_angle``).

Calibration error (D34, D40): an experiment setting, not information. The orientation the stage uses
is rotated by it before any sample leaves the stage, so it acts on every method alike, and the
estimators only ever see finished data. A fixed rotation in the *sensor* data would not work: the
calibration would measure it as part of the mount and remove it.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, replace

import numpy as np
from numpy.typing import NDArray

from throughtunnel.observations import GnssFix, RouteMap
from throughtunnel.positioning.map_grade import grade_compensation
from throughtunnel.positioning.mount_estimation import ALIGNED, Alignment, MountAlignmentEstimator

GNSS_TIMEOUT_S = 1.5  # calibration data only while fixes arrive at least this often
SEARCH_BACK_M = 50.0  # window for projecting a fix onto the route near the previous fix ...
SEARCH_AHEAD_M = 200.0
MAX_SPEED_MPS = 70.0  # ... widened ahead by this speed times the time since that fix (after an outage)


@dataclass(frozen=True, slots=True)
class VehicleImu:
    """One IMU sample in vehicle axes (ISO 8855: x forward, y left, z up)."""

    t: float
    accel: tuple[float, float, float]  # specific force [m/s^2]
    gyro: tuple[float, float, float]  # angular rate [rad/s]; z with the estimated gyro bias removed
    calibration_grade_angle: float = 0.0  # map grade angle absorbed by the levelling [rad] (D39)


def with_orientation_error(alignment: Alignment, rotation: NDArray[np.float64] | None) -> Alignment:
    """The alignment with its vehicle axes rotated by ``rotation`` (in vehicle axes, D34).

    ``A = [forward left up]`` maps vehicle to phone coordinates; the erroneous axes are ``A @ rotation``.
    ``None`` returns the alignment unchanged.
    """
    if rotation is None:
        return alignment
    axes = np.column_stack([alignment.forward, alignment.left, alignment.up]) @ rotation
    return replace(alignment, forward=axes[:, 0], left=axes[:, 1], up=axes[:, 2])


class AlignmentStage(ABC):
    """Turns raw phone IMU samples into vehicle-axis samples; causal, fed in time order."""

    name: str = "alignment"
    label: str = "Alignment"

    def __init__(self, route: RouteMap, calibration_error: NDArray[np.float64] | None = None) -> None:
        self.route = route
        self.calibration_error = calibration_error
        self._axes: Alignment | None = None
        self._rows: tuple | None = None  # the axes as plain floats (per-sample arithmetic)

    @abstractmethod
    def on_gnss(self, fix: GnssFix) -> None:
        """One GPS fix."""

    @abstractmethod
    def on_imu(self, t: float, accel: Sequence[float], gyro: Sequence[float]) -> VehicleImu | None:
        """One raw phone sample → the vehicle-axis sample, or None while no orientation is known."""

    @property
    def alignment(self) -> Alignment | None:
        """Orientation in use, calibration error included (diagnostics)."""
        return self._axes

    def _use(self, axes: Alignment) -> None:
        axes = with_orientation_error(axes, self.calibration_error)
        self._axes = axes
        self._rows = (
            *(tuple(float(x) for x in a) for a in (axes.forward, axes.left, axes.up)),
            axes.gyro_bias_up,
            axes.calibration_grade_angle,
        )

    def _rotate(self, t: float, accel: Sequence[float], gyro: Sequence[float]) -> VehicleImu | None:
        if self._rows is None:
            return None
        f, lf, u, bias, grade_angle = self._rows
        return VehicleImu(
            t,
            (
                f[0] * accel[0] + f[1] * accel[1] + f[2] * accel[2],
                lf[0] * accel[0] + lf[1] * accel[1] + lf[2] * accel[2],
                u[0] * accel[0] + u[1] * accel[1] + u[2] * accel[2],
            ),
            (
                f[0] * gyro[0] + f[1] * gyro[1] + f[2] * gyro[2],
                lf[0] * gyro[0] + lf[1] * gyro[1] + lf[2] * gyro[2],
                u[0] * gyro[0] + u[1] * gyro[1] + u[2] * gyro[2] - bias,
            ),
            grade_angle,
        )


class DeclaredAlignment(AlignmentStage):
    name = "declared"
    label = "Declared (phone axes = vehicle axes)"

    def __init__(self, route: RouteMap, calibration_error: NDArray[np.float64] | None = None) -> None:
        super().__init__(route, calibration_error)
        self._use(ALIGNED)

    def on_gnss(self, fix: GnssFix) -> None:
        pass

    def on_imu(self, t: float, accel: Sequence[float], gyro: Sequence[float]) -> VehicleImu | None:
        return self._rotate(t, accel, gyro)


class GpsImuAlignment(AlignmentStage):
    name = "gps_imu"
    label = "GPS + IMU calibration (levelling, yaw, gyro bias)"

    def __init__(self, route: RouteMap, calibration_error: NDArray[np.float64] | None = None) -> None:
        super().__init__(route, calibration_error)
        self._solver = MountAlignmentEstimator()
        self._grade = grade_compensation(route)
        self._d: float | None = None  # last fix projected onto the route (grade lookup only)
        self._last_fix_t = -math.inf

    def on_gnss(self, fix: GnssFix) -> None:
        grade_angle = 0.0
        if self._grade is not None:
            e, n, _ = self.route.frame.to_enu(fix.lat, fix.lon)
            if self._d is None:
                self._d = self.route.project_enu(float(e), float(n))[0]
            else:
                ahead = SEARCH_AHEAD_M + MAX_SPEED_MPS * (fix.t - self._last_fix_t)
                lo, hi = self._d - SEARCH_BACK_M, self._d + ahead
                self._d = self.route.project_enu(float(e), float(n), lo_m=lo, hi_m=hi)[0]
            grade_angle = self._grade.angle_at(self._d)
        self._last_fix_t = fix.t
        self._solver.add_fix(fix, grade_angle)
        solved = self._solver.solve()
        if solved is not None and solved.ready:
            self._use(solved)

    def on_imu(self, t: float, accel: Sequence[float], gyro: Sequence[float]) -> VehicleImu | None:
        if t - self._last_fix_t <= GNSS_TIMEOUT_S:
            self._solver.add_imu(accel, gyro)  # calibration data only while GPS is available
        return self._rotate(t, accel, gyro)


ALIGNMENTS: dict[str, type[AlignmentStage]] = {cls.name: cls for cls in (DeclaredAlignment, GpsImuAlignment)}
