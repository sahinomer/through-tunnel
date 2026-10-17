"""Map heading as a smooth function of route distance (step 5, map-feature fixes; estimator_plan.md).

``RouteMap.heading_at`` is the heading of the polyline segment containing a distance: piecewise constant,
with a jump at every vertex (on an 800 m arc with 15 m vertex spacing, ~1° every 15 m). For matching the
gyro's integrated heading against the map, the heading is taken at the segment midpoints (unwrapped) and
interpolated linearly between them, then averaged over a short window. The curvature is the slope of that
heading. Shared component (composition, D18), like ``map_grade``; plain Python per call, as estimators call it
at a few Hz.
"""

from __future__ import annotations

import math

import numpy as np

from throughtunnel.observations import RouteMap

GRID_M = 5.0  # resampling step [m]
SMOOTH_M = 60.0  # moving-average window [m]: the polyline's vertex spacing is ~15 m


class MapHeading:
    """Smoothed map heading ψ_map(d) [rad, unwrapped, ENU CCW from east] and curvature κ(d) = dψ/dd [1/m]."""

    def __init__(self, route: RouteMap, grid_m: float = GRID_M, smooth_m: float = SMOOTH_M) -> None:
        d, xy = route.distance_m, route.enu
        seg = np.diff(xy, axis=0)
        mid = 0.5 * (d[:-1] + d[1:])
        psi = np.unwrap(np.arctan2(seg[:, 1], seg[:, 0]))
        grid = np.arange(0.0, float(d[-1]) + grid_m, grid_m)
        h = np.interp(grid, mid, psi)
        n = max(1, round(smooth_m / grid_m))
        if n > 1:
            kernel = np.ones(n) / n
            padded = np.concatenate([np.full(n // 2, h[0]), h, np.full(n - 1 - n // 2, h[-1])])
            h = np.convolve(padded, kernel, mode="valid")
        self._step = grid_m
        self._h = h.tolist()
        self._k = (np.gradient(h, grid_m)).tolist()

    def _interp(self, values: list[float], distance_m: float) -> float:
        x = distance_m / self._step
        if x <= 0.0:
            return values[0]
        i = int(x)
        if i >= len(values) - 1:
            return values[-1]
        return values[i] + (x - i) * (values[i + 1] - values[i])

    def heading(self, distance_m: float) -> float:
        return self._interp(self._h, distance_m)

    def curvature(self, distance_m: float) -> float:
        return self._interp(self._k, distance_m)


def wrap(angle: float) -> float:
    """Angle wrapped to (−π, π]."""
    return math.remainder(angle, 2.0 * math.pi)
