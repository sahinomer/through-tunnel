"""Causal, timestamp-ordered replay of observations through the positioning pipeline (D17, D40).

Pipeline: observations → alignment stage → estimator. The runner is the only component that sees
whole streams. It hands each stage, then each estimator, one observation at a time in time order
(ties: the IMU sample before the GPS fix with the same timestamp) and samples the estimator's state at
a fixed output rate. Nothing can look ahead. Execution is offline (faster than real time), but
information flow is strictly causal.

Each alignment stage runs once per run; its vehicle-axis samples are shared by every estimator that
uses it (a stage depends only on the observations, not on the estimator). The calibration error is an
experiment setting applied inside the stage (``alignment.py``); estimators never receive it.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from throughtunnel.observations import Observations, RouteMap
from throughtunnel.positioning.alignment import ALIGNMENTS, AlignmentStage, VehicleImu
from throughtunnel.positioning.base import Estimator, StateEstimate

DEFAULT_OUTPUT_RATE_HZ = 20.0


class Announcer:
    """Shared exit-announcement logic (PD8, D32): fires once, the first time the estimated distance along
    the route reaches the announcement point (``RouteMap.announcement_m``, a set distance before the
    tunnel exit C). Estimators without an along-route state are map-matched by projection onto the
    route, searched in a window around the previous projection so a drifting estimate cannot jump."""

    def __init__(self, route: RouteMap, search_back_m: float = 100.0, search_ahead_m: float = 500.0) -> None:
        self.route = route
        self.target_m = route.announcement_m
        self.fired_t = math.nan  # estimate time of the announcement; NaN = not (yet) announced
        self._last_d: float | None = None
        self._back, self._ahead = search_back_m, search_ahead_m

    def update(self, est: StateEstimate) -> float:
        if est.route_distance is not None:
            d = est.route_distance
        elif self._last_d is None:
            d = self.route.project_enu(est.east, est.north)[0]
        else:
            lo, hi = self._last_d - self._back, self._last_d + self._ahead
            d = self.route.project_enu(est.east, est.north, lo_m=lo, hi_m=hi)[0]
        self._last_d = d
        if self.target_m is not None and math.isnan(self.fired_t) and d >= self.target_m:
            self.fired_t = est.t
        return d


@dataclass(frozen=True)
class EstimateTrack:
    """An estimator's output over time, plus the time it announced the tunnel exit."""

    name: str
    label: str
    t: NDArray[np.float64]
    east: NDArray[np.float64]
    north: NDArray[np.float64]
    speed: NDArray[np.float64]
    heading: NDArray[np.float64]
    mode: NDArray[np.str_]
    route_distance: NDArray[np.float64]  # estimator's own, or the announcer's map-matched value
    position_std_m: NDArray[np.float64]  # NaN where not provided
    announcement_t: float = math.nan  # NaN = never announced

    def __len__(self) -> int:
        return len(self.t)


def align_imu(stage: AlignmentStage, obs: Observations) -> list[VehicleImu | None]:
    """Feed the observations through an alignment stage in time order; one output per IMU sample."""
    imu_t = obs.imu.t.tolist()
    accel = obs.imu.accel.tolist()
    gyro = obs.imu.gyro.tolist()
    fixes = [obs.gnss.fix(i) for i in range(len(obs.gnss))]
    out: list[VehicleImu | None] = []
    j = 0
    for i, t in enumerate(imu_t):
        while j < len(fixes) and fixes[j].t < t:  # fixes strictly before this sample
            stage.on_gnss(fixes[j])
            j += 1
        out.append(stage.on_imu(t, accel[i], gyro[i]))
        while j < len(fixes) and fixes[j].t <= t:  # fixes at the same timestamp come after the IMU sample
            stage.on_gnss(fixes[j])
            j += 1
    return out


def aligned_streams(
    names: Sequence[str | None], obs: Observations, calibration_error: NDArray[np.float64] | None = None
) -> dict[str | None, list[VehicleImu | None]]:
    """One vehicle-axis stream per alignment stage name (None = no stage: no IMU, time ticks only)."""
    streams: dict[str | None, list[VehicleImu | None]] = {}
    for name in names:
        if name not in streams:
            streams[name] = (
                [None] * len(obs.imu)
                if name is None
                else align_imu(ALIGNMENTS[name](obs.route, calibration_error), obs)
            )
    return streams


def run_estimator(
    estimator: Estimator,
    obs: Observations,
    output_rate_hz: float = DEFAULT_OUTPUT_RATE_HZ,
    calibration_error: NDArray[np.float64] | None = None,
) -> EstimateTrack:
    """Run one estimator behind its alignment stage (``estimator.alignment``)."""
    return run_estimators([estimator], obs, output_rate_hz, calibration_error)[0]


def run_estimators(
    estimators: Sequence[Estimator],
    obs: Observations,
    output_rate_hz: float = DEFAULT_OUTPUT_RATE_HZ,
    calibration_error: NDArray[np.float64] | None = None,
) -> list[EstimateTrack]:
    """Run several estimators on the *same* observations (D19), each alignment stage once."""
    streams = aligned_streams([e.alignment for e in estimators], obs, calibration_error)
    return [replay(e, obs, streams[e.alignment], output_rate_hz) for e in estimators]


def replay(
    estimator: Estimator,
    obs: Observations,
    imu: Sequence[VehicleImu | None],
    output_rate_hz: float = DEFAULT_OUTPUT_RATE_HZ,
) -> EstimateTrack:
    """Feed one estimator its vehicle-axis IMU stream and the GPS fixes in time order."""
    imu_t = obs.imu.t.tolist()
    fixes = [obs.gnss.fix(i) for i in range(len(obs.gnss))]
    announcer = Announcer(obs.route)

    rows: list[tuple] = []
    out_dt = 1.0 / output_rate_hz
    next_out = imu_t[0] if imu_t else 0.0
    j = 0
    for i, t in enumerate(imu_t):
        while j < len(fixes) and fixes[j].t < t:  # fixes strictly before this sample
            estimator.on_gnss(fixes[j])
            j += 1
        estimator.on_imu(t, imu[i])
        while j < len(fixes) and fixes[j].t <= t:  # fixes at the same timestamp come after the IMU sample
            estimator.on_gnss(fixes[j])
            j += 1
        if t >= next_out - 1e-9:
            next_out += out_dt
            est = estimator.state()
            if est is not None:
                d = announcer.update(est)
                rows.append(
                    (
                        est.t,
                        est.east,
                        est.north,
                        est.speed,
                        est.heading,
                        est.mode,
                        d,
                        math.nan if est.position_std_m is None else est.position_std_m,
                    )
                )
    cols = list(zip(*rows, strict=True)) if rows else [[]] * 8
    return EstimateTrack(
        name=estimator.name,
        label=estimator.label,
        t=np.asarray(cols[0], dtype=float),
        east=np.asarray(cols[1], dtype=float),
        north=np.asarray(cols[2], dtype=float),
        speed=np.asarray(cols[3], dtype=float),
        heading=np.asarray(cols[4], dtype=float),
        mode=np.asarray(cols[5], dtype=str),
        route_distance=np.asarray(cols[6], dtype=float),
        position_std_m=np.asarray(cols[7], dtype=float),
        announcement_t=announcer.fired_t,
    )
