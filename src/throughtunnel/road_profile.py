"""Road elevation profile: heights at points along the route, joined by a smooth curve (D36).

The profile is defined by heights at a few points along the route (distance from A along the map
route, metres). Between the points the road follows a curve that
* passes exactly through every point, so a dragged point is where the road goes;
* does not overshoot: the slopes at the points are those of a shape-preserving (PCHIP) interpolation,
  so there are no invented hills or dips between points;
* is C2: each interval is a quintic with zero vertical curvature at the points, so grade and
  vertical curvature are continuous. This keeps the vehicle's pitch rate continuous; a plain PCHIP
  curve would make it jump at every point, which a real suspension does not do.

The grade (dz/ds, + = uphill) is limited to ``max_grade_pct`` along the whole curve; the editor clamps
dragged points to stay within it (``clamp_height``). Outside the points the road continues with the
end grade. The profile is a function of the horizontal distance along the road: the map, B, C and the
driver's speed profile are unchanged; the vehicle's height, pitch and vertical motion follow from it.
"""

from __future__ import annotations

import itertools
import math

import numpy as np
from numpy.typing import ArrayLike, NDArray
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from scipy.interpolate import BPoly, PchipInterpolator

DEFAULT_MAX_GRADE_PCT = 6.0
DEFAULT_POINT_SPACING_M = 200.0
VERTICAL_ACCEL_WARNING = 0.5  # m/s^2: dips and crests sharper than this feel abrupt
_GRADE_CHECK_STEP_M = 1.0


class RoadProfileConfig(BaseModel):
    """Heights at points along the route. No points (the default) = flat road."""

    model_config = ConfigDict(frozen=True)

    points: tuple[tuple[float, float], ...] = Field(
        (), description="(distance along the route from A [m], height relative to A [m]), increasing distance"
    )
    max_grade_pct: float = Field(DEFAULT_MAX_GRADE_PCT, gt=0.0, le=15.0, description="Steepest allowed grade")

    @field_validator("points")
    @classmethod
    def _ordered(cls, points: tuple[tuple[float, float], ...]) -> tuple[tuple[float, float], ...]:
        if len(points) == 1:
            raise ValueError("a road profile needs at least two points")
        d = [p[0] for p in points]
        if any(b <= a for a, b in itertools.pairwise(d)) or (d and d[0] < 0.0):
            raise ValueError("profile points must have increasing, non-negative distances")
        return points

    @model_validator(mode="after")
    def _within_grade_limit(self) -> RoadProfileConfig:
        if self.points:
            g = ElevationProfile.from_points(self.points).max_grade()
            if g > self.max_grade_pct / 100.0 * (1.0 + 1e-6):
                raise ValueError(
                    f"the profile reaches {100 * g:.2f}% grade, above the {self.max_grade_pct:g}% limit"
                )
        return self

    @property
    def is_flat(self) -> bool:
        return not self.points or len({h for _, h in self.points}) == 1


class ElevationProfile:
    """Height z(s) and its derivatives along the road (s = horizontal distance from A)."""

    def __init__(self, distances: ArrayLike, heights: ArrayLike) -> None:
        x = np.asarray(distances, dtype=float)
        z = np.asarray(heights, dtype=float)
        if len(x) < 2 or len(x) != len(z) or np.any(np.diff(x) <= 0):
            raise ValueError("need at least two points with increasing distances")
        slopes = PchipInterpolator(x, z).derivative()(x)
        self.distances, self.heights, self._slopes = x, z, slopes
        self._z = BPoly.from_derivatives(x, np.column_stack([z, slopes, np.zeros_like(z)]), orders=5)
        self._d = [self._z.derivative(k) for k in (1, 2, 3)]

    @classmethod
    def from_points(cls, points: ArrayLike) -> ElevationProfile:
        p = np.asarray(points, dtype=float)
        return cls(p[:, 0], p[:, 1])

    @classmethod
    def from_config(cls, config: RoadProfileConfig) -> ElevationProfile | None:
        """None for a flat road (keeps flat-road results bit-identical)."""
        return None if config.is_flat else cls.from_points(config.points)

    def evaluate(self, s: ArrayLike) -> tuple[NDArray, NDArray, NDArray, NDArray]:
        """Height z, grade z', vertical curvature z'' and its rate z''' at distances ``s``.

        Beyond the first and last point the road continues straight with the end grade (z'' = 0 there,
        so the transition is still C2)."""
        s = np.asarray(s, dtype=float)
        x0, x1 = self.distances[0], self.distances[-1]
        sc = np.clip(s, x0, x1)
        z, g, c, r = self._z(sc), self._d[0](sc), self._d[1](sc), self._d[2](sc)
        outside = (s < x0) | (s > x1)
        z = z + g * (s - sc)
        c = np.where(outside, 0.0, c)
        r = np.where(outside, 0.0, r)
        return z, g, c, r

    def max_grade(self) -> float:
        s = np.union1d(np.arange(self.distances[0], self.distances[-1], _GRADE_CHECK_STEP_M), self.distances)
        return float(np.abs(self._d[0](s)).max())

    def max_vertical_curvature(self) -> float:
        """Largest |z''| [1/m]; times speed² gives the vertical acceleration in dips and crests."""
        s = np.union1d(np.arange(self.distances[0], self.distances[-1], _GRADE_CHECK_STEP_M), self.distances)
        return float(np.abs(self._d[1](s)).max())


# ---------------------------------------------------------------------- editing helpers
def point_distances(
    length_m: float, entrance_m: float, exit_m: float, spacing_m: float = DEFAULT_POINT_SPACING_M
):
    """Editable point positions: an even grid along the route, plus B and C exactly (grid points too
    close to B or C are dropped so the spacing stays even)."""
    n = max(2, round(length_m / spacing_m) + 1)
    grid = np.linspace(0.0, length_m, n)
    step = length_m / (n - 1)
    keep = [d for d in grid if min(abs(d - entrance_m), abs(d - exit_m)) > 0.4 * step or d in (0.0, length_m)]
    return np.unique(np.concatenate([keep, [entrance_m, exit_m]]))


def max_grade_of(distances: ArrayLike, heights: ArrayLike) -> float:
    return ElevationProfile(distances, heights).max_grade()


def clamp_height(
    distances: ArrayLike, heights: ArrayLike, index: int, target: float, max_grade: float
) -> float:
    """The height closest to ``target`` for point ``index`` that keeps the whole profile within
    ``max_grade`` (a fraction, e.g. 0.06). Assumes the current profile is within the limit."""
    h = np.array(heights, dtype=float)

    def ok(value: float) -> bool:
        h[index] = value
        return max_grade_of(distances, h) <= max_grade * (1.0 + 1e-9)

    current = float(heights[index])
    if ok(target):
        return float(target)
    lo, hi = current, float(target)  # lo feasible, hi not
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if ok(mid) else (lo, mid)
    return lo


TEMPLATES = {
    "flat": "Flat",
    "climb": "Steady climb (2 %)",
    "tunnel_climb": "Climb inside the tunnel (3 %)",
    "underwater": "Underwater tunnel (−4 % / +4 %)",
}


TEMPLATE_TRANSITION_M = 400.0  # length of each grade change (vertical curve) in the templates


def template_heights(
    name: str, distances: ArrayLike, entrance_m: float, exit_m: float, max_grade: float
) -> NDArray[np.float64]:
    """Heights of a template shape at ``distances``, scaled down if needed to respect ``max_grade``.

    A template is a design grade line whose grade changes are spread over ``TEMPLATE_TRANSITION_M``
    (as real vertical curves are), integrated to heights. Sampling a sharp-cornered line instead
    would force the smooth curve through the points to overshoot the design grade near each corner."""
    d = np.asarray(distances, dtype=float)
    tunnel = exit_m - entrance_m
    initial, changes = 0.0, []  # grade at A, then (distance, grade after the change)
    if name == "flat":
        pass
    elif name == "climb":
        initial = 0.02
    elif name == "tunnel_climb":
        changes = [(entrance_m, 0.03), (exit_m, 0.0)]
    elif name == "underwater":  # descend over the first 40 %, flat bottom, climb over the last 40 %
        ramp = 0.4 * tunnel
        changes = [(entrance_m, -0.04), (entrance_m + ramp, 0.0), (exit_m - ramp, 0.04), (exit_m, 0.0)]
    else:
        raise ValueError(f"unknown profile template {name!r}")
    fine = np.arange(0.0, d.max() + 1.0, 1.0)
    grade = np.full_like(fine, initial)
    before = initial
    for at, after in changes:
        ramp_fraction = np.clip((fine - at) / TEMPLATE_TRANSITION_M + 0.5, 0.0, 1.0)
        grade += (after - before) * ramp_fraction
        before = after
    heights = np.interp(d, fine, np.concatenate([[0.0], np.cumsum(0.5 * (grade[1:] + grade[:-1]))]))
    g = max_grade_of(d, heights) if np.ptp(heights) > 0 else 0.0
    return heights * min(1.0, max_grade / g) if g > max_grade else heights


def vertical_accel(profile: ElevationProfile, speed_mps: float) -> float:
    return profile.max_vertical_curvature() * speed_mps**2


def grade_pct(g: float) -> str:
    return f"{100 * g:.1f} %" if math.isfinite(g) else "n/a"
