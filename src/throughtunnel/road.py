"""Road centreline processing: map polyline -> smooth, arc-length-parametrised path.

Why this is needed
------------------
An OpenStreetMap way is a *polyline*: straight chords between nodes. Driving it
literally means heading jumps at every node (infinite yaw rate and lateral
acceleration) and zero curvature in between. Nodes are also unevenly spaced
and slightly jittered, so a naive smoothing (e.g. Gaussian) leaves a curvature
ripple at the node spacing that would show up as a fake oscillating yaw rate.

Pipeline (each step is a pure function of the input + :class:`RoadConfig`)
--------------------------------------------------------------------------
1. lat/lon -> local ENU (metres), origin at the first vertex.
2. Clean: drop near-duplicate vertices and short direction-reversal "spikes"
   (typical snapping/digitising artefacts).
3. Corner filleting: every vertex is replaced by a tangent circular arc. The arc
   radius is the largest one that (a) cuts the corner by at most
   ``max_corner_cut_m`` and (b) fits within half of each adjacent segment.
   For a curve sampled by evenly spaced nodes, the fillets meet at the segment
   midpoints and reproduce the original arc radius; for an isolated sharp
   corner (an intersection) the turn radius is bounded by the corner cut.
4. Uniform resampling (1 m) + Whittaker smoothing with a third-difference
   penalty: minimise  sum w_i |p_i - r_i|^2 + lambda sum |D^3 p_i|^2.
   D^3 p ~ d^3r/ds^3, whose normal component is dκ/ds, so the smoother prefers
   clothoid-like curvature transitions (as in real road design) and removes
   node-spacing ripple and jitter. It acts as a ~6th-order low-pass with cutoff
   wavelength ``smoothing_wavelength_m``. A corridor constraint is enforced by
   iterative reweighting: points that drift more than ``smoothing_corridor_m``
   from the filleted path get heavier weights until they comply.
5. Quintic spline re-parametrised by true arc length (|dr/ds| = 1), giving
   continuous heading, curvature and curvature rate dκ/ds.

Diagnostics (lengths, deviation from the map polyline, minimum radius) are
reported so the approximation is always visible.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp
from numpy.typing import ArrayLike, NDArray
from pydantic import BaseModel, ConfigDict, Field
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import BSpline, make_interp_spline
from scipy.ndimage import maximum_filter1d
from scipy.sparse.linalg import spsolve

from throughtunnel.geodesy import LocalFrame
from throughtunnel.routing.base import RawRoute

MIN_ROAD_LENGTH_M = 20.0


class RoadConfig(BaseModel):
    """Parameters of the map-polyline -> drivable-path conversion."""

    model_config = ConfigDict(frozen=True)

    min_vertex_spacing_m: float = Field(0.5, gt=0, description="Vertices closer than this are merged")
    spike_angle_deg: float = Field(150.0, gt=90, le=180, description="Turn angle treated as a reversal spike")
    spike_max_segment_m: float = Field(25.0, gt=0, description="Spikes are only removed if a leg is shorter")
    max_corner_cut_m: float = Field(4.0, gt=0, description="Max distance a fillet may cut inside a vertex")
    smoothing_wavelength_m: float = Field(
        150.0, ge=0, description="Cutoff wavelength of the curvature smoother (0 disables smoothing)"
    )
    smoothing_corridor_m: float = Field(
        1.0, gt=0, description="Max distance the smoothed path may move away from the filleted path"
    )
    resample_step_m: float = Field(1.0, gt=0, le=5, description="Arc-length grid spacing")


@dataclass(frozen=True)
class RoadDiagnostics:
    raw_vertices: int
    removed_duplicates: int
    removed_spikes: int
    raw_length_m: float
    length_m: float
    max_deviation_m: float
    rms_deviation_m: float
    min_radius_m: float
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PathState:
    """Path geometry evaluated at arc lengths ``s`` (all arrays share the shape of ``s``)."""

    s: NDArray[np.float64]
    xy: NDArray[np.float64]  # (N, 2) ENU east/north [m]
    yaw: NDArray[np.float64]  # ENU yaw, CCW from East, continuous (unwrapped) [rad]
    curvature: NDArray[np.float64]  # signed, positive = left [1/m]
    curvature_rate: NDArray[np.float64]  # dκ/ds [1/m^2]


class RoadPath:
    """A smooth, arc-length-parametrised road centreline in a local ENU frame."""

    def __init__(
        self,
        frame: LocalFrame,
        spline: BSpline,
        length_m: float,
        reference_enu: NDArray[np.float64],
        diagnostics: RoadDiagnostics,
        grid_step_m: float,
    ) -> None:
        self.frame = frame
        self._spline = spline
        self.length_m = float(length_m)
        self.reference_enu = reference_enu  # cleaned map polyline (for display / deviation)
        self.diagnostics = diagnostics
        n = max(2, math.ceil(self.length_m / grid_step_m) + 1)
        self.grid_s = np.linspace(0.0, self.length_m, n)
        d1 = self._spline(self.grid_s, 1)
        self._grid_yaw = np.unwrap(np.arctan2(d1[:, 1], d1[:, 0]))

    # ------------------------------------------------------------------ construction
    @classmethod
    def from_route(cls, route: RawRoute, config: RoadConfig | None = None) -> RoadPath:
        coords = np.asarray(route.coordinates, dtype=float)
        frame = LocalFrame(lat0=float(coords[0, 0]), lon0=float(coords[0, 1]))
        enu = frame.to_enu(coords[:, 0], coords[:, 1])[:, :2]
        return cls.from_enu(enu, frame, config)

    @classmethod
    def from_enu(cls, points: ArrayLike, frame: LocalFrame, config: RoadConfig | None = None) -> RoadPath:
        cfg = config or RoadConfig()
        raw = np.asarray(points, dtype=float)
        raw_length = _polyline_length(raw)

        pts, n_dupes = _remove_duplicates(raw, cfg.min_vertex_spacing_m)
        pts, n_spikes = _remove_spikes(pts, cfg.spike_angle_deg, cfg.spike_max_segment_m)
        reference = pts
        if _polyline_length(reference) < MIN_ROAD_LENGTH_M:
            raise ValueError(f"road is too short (< {MIN_ROAD_LENGTH_M:.0f} m) to simulate")

        filleted = _fillet_corners(pts, cfg.max_corner_cut_m)
        dense = _resample(filleted, cfg.resample_step_m)
        smooth = whittaker_smooth(
            dense, cfg.smoothing_wavelength_m, cfg.smoothing_corridor_m, cfg.resample_step_m
        )
        spline, length = _arc_length_spline(smooth, cfg.resample_step_m)

        diag = _diagnostics(spline, length, reference, raw, n_dupes, n_spikes, raw_length, cfg)
        return cls(frame, spline, length, reference, diag, cfg.resample_step_m)

    # ------------------------------------------------------------------ evaluation
    def evaluate(self, s: ArrayLike) -> PathState:
        s_arr = np.clip(np.asarray(s, dtype=float), 0.0, self.length_m)
        xy = self._spline(s_arr)
        d1 = self._spline(s_arr, 1)
        d2 = self._spline(s_arr, 2)
        d3 = self._spline(s_arr, 3)
        x1, y1 = d1[..., 0], d1[..., 1]
        x2, y2 = d2[..., 0], d2[..., 1]
        x3, y3 = d3[..., 0], d3[..., 1]
        n = x1**2 + y1**2  # |r'|^2 (== 1 up to spline accuracy)
        c = x1 * y2 - y1 * x2
        kappa = c / n**1.5
        dc = x1 * y3 - y1 * x3
        dn = 2.0 * (x1 * x2 + y1 * y2)
        dkappa = dc / n**1.5 - 1.5 * c * dn / n**2.5

        yaw_wrapped = np.arctan2(y1, x1)
        yaw_ref = np.interp(s_arr, self.grid_s, self._grid_yaw)
        yaw = yaw_wrapped + 2.0 * np.pi * np.round((yaw_ref - yaw_wrapped) / (2.0 * np.pi))
        return PathState(s=s_arr, xy=xy, yaw=yaw, curvature=kappa, curvature_rate=dkappa)

    def project(self, east: float, north: float, s_lo: float = 0.0, s_hi: float | None = None) -> float:
        """Arc length of the path point closest to (east, north), searched within [s_lo, s_hi]."""
        hi = self.length_m if s_hi is None else min(s_hi, self.length_m)
        mask = (self.grid_s >= s_lo - 1e-9) & (self.grid_s <= hi + 1e-9)
        grid = self.grid_s[mask]
        xy = self._spline(grid)
        s = float(grid[int(np.argmin((xy[:, 0] - east) ** 2 + (xy[:, 1] - north) ** 2))])
        for _ in range(8):  # Newton on d/ds |r(s) - p|^2 / 2 = (r - p) . r'
            r, d1, d2 = self._spline(s), self._spline(s, 1), self._spline(s, 2)
            diff = r - np.array([east, north])
            step = float(diff @ d1) / max(float(d1 @ d1 + diff @ d2), 1e-9)
            s = min(max(s - step, s_lo), hi)
            if abs(step) < 1e-9:
                break
        return s

    def tangent_norm(self, s: ArrayLike) -> NDArray[np.float64]:
        """|dr/ds| — equals 1 for a perfect arc-length parametrisation."""
        return np.linalg.norm(self._spline(np.asarray(s, dtype=float), 1), axis=-1)

    def latlon(self, step_m: float = 5.0) -> NDArray[np.float64]:
        """Centreline as (N, 2) lat/lon for display."""
        s = np.linspace(0.0, self.length_m, max(2, math.ceil(self.length_m / step_m) + 1))
        xy = self._spline(s)
        lat, lon, _ = self.frame.to_geodetic(np.column_stack([xy, np.zeros(len(s))]))
        return np.column_stack([lat, lon])

    def reference_latlon(self) -> NDArray[np.float64]:
        ref = self.reference_enu
        lat, lon, _ = self.frame.to_geodetic(np.column_stack([ref, np.zeros(len(ref))]))
        return np.column_stack([lat, lon])


# ---------------------------------------------------------------------- pipeline steps
def _polyline_length(pts: NDArray[np.float64]) -> float:
    return float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())


def _remove_duplicates(pts: NDArray[np.float64], min_spacing: float) -> tuple[NDArray[np.float64], int]:
    keep = [0]
    for i in range(1, len(pts)):
        if np.linalg.norm(pts[i] - pts[keep[-1]]) >= min_spacing:
            keep.append(i)
    if keep[-1] != len(pts) - 1:  # always end exactly at the last vertex
        if len(keep) > 1:
            keep[-1] = len(pts) - 1
        else:
            keep.append(len(pts) - 1)
    return pts[keep], len(pts) - len(keep)


def _turn_angles(pts: NDArray[np.float64]) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Signed turn angle at each interior vertex and the segment lengths."""
    seg = np.diff(pts, axis=0)
    lengths = np.linalg.norm(seg, axis=1)
    a, b = seg[:-1], seg[1:]
    cross = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
    dot = (a * b).sum(axis=1)
    return np.arctan2(cross, dot), lengths


def _remove_spikes(
    pts: NDArray[np.float64], angle_deg: float, max_seg: float
) -> tuple[NDArray[np.float64], int]:
    removed = 0
    limit = np.radians(angle_deg)
    while len(pts) > 2:
        theta, lengths = _turn_angles(pts)
        short_leg = np.minimum(lengths[:-1], lengths[1:]) < max_seg
        candidates = np.flatnonzero((np.abs(theta) > limit) & short_leg)
        if candidates.size == 0:
            break
        worst = candidates[np.argmax(np.abs(theta[candidates]))]
        pts = np.delete(pts, worst + 1, axis=0)
        removed += 1
    return pts, removed


def _fillet_corners(pts: NDArray[np.float64], max_cut: float, arc_step: float = 0.5) -> NDArray[np.float64]:
    """Replace every interior vertex by a tangent circular arc (see module docstring)."""
    if len(pts) < 3:
        return pts
    theta, lengths = _turn_angles(pts)
    out = [pts[0]]
    n_seg = len(lengths)
    for k, th in enumerate(theta):
        p = pts[k + 1]
        abs_th = abs(th)
        if abs_th < 1e-9:
            out.append(p)
            continue
        # Tangent length available on each adjacent segment: the whole segment if
        # the other end is a route endpoint, otherwise half (shared with the next fillet).
        avail_in = lengths[k] if k == 0 else 0.5 * lengths[k]
        avail_out = lengths[k + 1] if k + 1 == n_seg - 1 else 0.5 * lengths[k + 1]
        tan_half = math.tan(abs_th / 2.0)
        cut_factor = 1.0 / math.cos(abs_th / 2.0) - 1.0  # vertex-to-arc distance per unit radius
        r_cut = max_cut / cut_factor if cut_factor > 0 else math.inf
        r_fit = min(avail_in, avail_out) / tan_half
        radius = min(r_cut, r_fit)
        t_len = radius * tan_half

        u_in = (pts[k + 1] - pts[k]) / lengths[k]
        u_out = (pts[k + 2] - pts[k + 1]) / lengths[k + 1]
        a = p - u_in * t_len
        normal_left = np.array([-u_in[1], u_in[0]])
        centre = a + math.copysign(radius, th) * normal_left
        a0 = math.atan2(a[1] - centre[1], a[0] - centre[0])
        n = max(2, math.ceil(radius * abs_th / arc_step) + 1)
        phi = a0 + np.linspace(0.0, th, n)
        arc = centre + radius * np.column_stack([np.cos(phi), np.sin(phi)])
        arc[-1] = p + u_out * t_len  # exact tangent point
        out.extend(arc)
    out.append(pts[-1])
    res, _ = _remove_duplicates(np.asarray(out), 1e-6)
    return res


def _resample(pts: NDArray[np.float64], step: float) -> NDArray[np.float64]:
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    n = max(7, math.ceil(s[-1] / step) + 1)
    grid = np.linspace(0.0, s[-1], n)
    return np.column_stack([np.interp(grid, s, pts[:, 0]), np.interp(grid, s, pts[:, 1])])


def whittaker_smooth(
    pts: NDArray[np.float64], wavelength_m: float, corridor_m: float, step: float, max_iter: int = 30
) -> NDArray[np.float64]:
    """Third-difference Whittaker smoother with an iteratively reweighted deviation corridor.

    ``pts`` must be (approximately) uniformly spaced by ``step``. The penalty weight
    is chosen so the half-power wavelength of the equivalent low-pass filter
    H(w) = 1 / (1 + lambda * (2 sin(w/2))^6) equals ``wavelength_m``.
    """
    n = len(pts)
    if wavelength_m <= 0 or n < 8:
        return pts
    lam = (wavelength_m / (2.0 * math.pi * step)) ** 6
    d3 = sp.diags([-1.0, 3.0, -3.0, 1.0], [0, 1, 2, 3], shape=(n - 3, n))
    penalty = (lam * (d3.T @ d3)).tocsc()
    # Solve for the correction d = p - r: (W + P) d = -P r. Equivalent to (W + P) p = W r, but
    # keeps precision relative to |d| (metres) rather than |p| (kilometres), which matters as
    # lambda makes the system badly conditioned. -P r is evaluated as -lambda D^T (D r): taking
    # differences first avoids cancellation and keeps the RHS orthogonal to the free (quadratic) modes.
    rhs = -lam * (d3.T @ (d3 @ pts))
    w = np.ones(n)
    d = np.zeros_like(pts)
    for _ in range(max_iter):
        system = (sp.diags(w) + penalty).tocsc()
        d = np.column_stack([spsolve(system, rhs[:, k]) for k in range(2)])
        dev = np.linalg.norm(d, axis=1)
        if dev.max() <= corridor_m * 1.02:
            break
        # Stiffen violating points (and their neighbours, to avoid kinks).
        w *= maximum_filter1d(np.maximum(dev / corridor_m, 1.0), size=5) ** 2
    return pts + d


def _arc_length_spline(pts: NDArray[np.float64], step: float) -> tuple[BSpline, float]:
    u = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    spl_u = make_interp_spline(u, pts, k=5)
    u_dense = np.linspace(0.0, u[-1], 4 * len(u))
    speed = np.linalg.norm(spl_u(u_dense, 1), axis=1)
    s_dense = cumulative_trapezoid(speed, u_dense, initial=0.0)
    length = float(s_dense[-1])
    s_grid = np.linspace(0.0, length, max(7, math.ceil(length / step) + 1))
    resampled = spl_u(np.interp(s_grid, s_dense, u_dense))
    return make_interp_spline(s_grid, resampled, k=5), length


def point_to_polyline_distance(q: ArrayLike, poly: ArrayLike, chunk: int = 512) -> NDArray[np.float64]:
    """Euclidean distance from each point in ``q`` (M, 2) to the polyline ``poly`` (N, 2)."""
    q = np.asarray(q, dtype=float)
    poly = np.asarray(poly, dtype=float)
    a = poly[:-1]
    ab = poly[1:] - a
    ab2 = np.maximum((ab**2).sum(axis=1), 1e-18)
    out = np.empty(len(q))
    for i in range(0, len(q), chunk):
        ap = q[i : i + chunk, None, :] - a[None, :, :]
        t = np.clip((ap * ab).sum(axis=2) / ab2, 0.0, 1.0)
        d = np.linalg.norm(ap - t[..., None] * ab, axis=2)
        out[i : i + chunk] = d.min(axis=1)
    return out


def _diagnostics(
    spline: BSpline,
    length: float,
    reference: NDArray[np.float64],
    raw: NDArray[np.float64],
    n_dupes: int,
    n_spikes: int,
    raw_length: float,
    cfg: RoadConfig,
) -> RoadDiagnostics:
    s = np.linspace(0.0, length, max(7, math.ceil(length / cfg.resample_step_m) + 1))
    xy = spline(s)
    d1, d2 = spline(s, 1), spline(s, 2)
    kappa = (d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / np.linalg.norm(d1, axis=1) ** 3
    dev_path = point_to_polyline_distance(xy, reference)
    dev_vertices = point_to_polyline_distance(reference, xy)
    max_dev = float(max(dev_path.max(), dev_vertices.max()))
    max_kappa = float(np.abs(kappa).max())
    min_radius = 1.0 / max_kappa if max_kappa > 0 else math.inf

    warnings = []  # tunnel-section checks live in scenario.py (the road knows nothing about tunnels)
    if max_dev > cfg.max_corner_cut_m + cfg.smoothing_corridor_m + 0.5:
        warnings.append(f"Smoothed path deviates up to {max_dev:.1f} m from the map polyline.")
    if min_radius < 8.0:
        warnings.append(f"Very tight turn (min radius {min_radius:.1f} m): the vehicle will crawl there.")

    return RoadDiagnostics(
        raw_vertices=len(raw),
        removed_duplicates=n_dupes,
        removed_spikes=n_spikes,
        raw_length_m=raw_length,
        length_m=length,
        max_deviation_m=max_dev,
        rms_deviation_m=float(np.sqrt(np.mean(dev_path**2))),
        min_radius_m=min_radius,
        warnings=warnings,
    )
