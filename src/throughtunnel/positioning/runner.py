"""Causal, timestamp-ordered replay of observations into estimators (D17).

The runner is the only component that sees whole streams. It hands each estimator one observation
at a time in time order (ties: the IMU sample before the GPS fix with the same timestamp) and samples
the estimator's state at a fixed output rate. Estimators therefore cannot look ahead. Execution is
offline (faster than real time), but information flow is strictly causal.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from throughtunnel.observations import Observations, RouteMap
from throughtunnel.positioning.base import Estimator, StateEstimate

DEFAULT_OUTPUT_RATE_HZ = 20.0


class Announcer:
    """Shared navigation-announcement logic (PD8): fires each target when the estimated distance along
    the route reaches it. Estimators without an along-route state are map-matched by projection onto the
    route, searched in a window around the previous projection so a drifting estimate cannot jump."""

    def __init__(self, route: RouteMap, search_back_m: float = 100.0, search_ahead_m: float = 500.0) -> None:
        self.route = route
        self.targets = dict(sorted(route.announcement_targets().items(), key=lambda kv: kv[1]))
        self.fired: dict[str, float] = {}
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
        for name, target in self.targets.items():
            if name not in self.fired and d >= target:
                self.fired[name] = est.t
        return d


@dataclass(frozen=True)
class EstimateTrack:
    """An estimator's output over time, plus the times it announced each navigation target."""

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
    announcements: dict[str, float] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.t)


def run_estimator(
    estimator: Estimator, obs: Observations, output_rate_hz: float = DEFAULT_OUTPUT_RATE_HZ
) -> EstimateTrack:
    imu_t = obs.imu.t.tolist()
    accel = obs.imu.accel.tolist()
    gyro = obs.imu.gyro.tolist()
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
        estimator.on_imu(t, accel[i], gyro[i])
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
        announcements=dict(announcer.fired),
    )


def run_estimators(
    factories: Sequence[Callable[[RouteMap], Estimator]],
    obs: Observations,
    output_rate_hz: float = DEFAULT_OUTPUT_RATE_HZ,
) -> list[EstimateTrack]:
    """Run several estimators on the *same* observations (D19)."""
    return [run_estimator(make(obs.route), obs, output_rate_hz) for make in factories]
