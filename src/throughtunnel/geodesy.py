"""WGS84 geodetic <-> ECEF <-> local ENU conversions.

The simulation runs in a local East-North-Up (ENU) tangent plane anchored at a
reference point (normally the route start). Conversions are exact on the WGS84
ellipsoid; the only approximation is treating the tangent plane as the "world"
frame for vehicle motion, which is accurate to well under a metre over the
<= 10 km extents used here (Earth-curvature drop ~ d^2 / 2R ~ 2 m vertical at
5 km is irrelevant on a flat-road model, horizontal distortion is ~mm).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

WGS84_A = 6_378_137.0  # semi-major axis [m]
WGS84_F = 1.0 / 298.257223563  # flattening
WGS84_B = WGS84_A * (1.0 - WGS84_F)
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)  # first eccentricity squared
WGS84_EP2 = WGS84_E2 / (1.0 - WGS84_E2)  # second eccentricity squared
EARTH_MEAN_RADIUS = 6_371_008.8  # [m], used only for the haversine helper


def geodetic_to_ecef(lat_deg: ArrayLike, lon_deg: ArrayLike, alt_m: ArrayLike = 0.0) -> NDArray[np.float64]:
    """Geodetic (deg, deg, m) -> ECEF (m), shape (..., 3)."""
    lat = np.radians(np.asarray(lat_deg, dtype=float))
    lon = np.radians(np.asarray(lon_deg, dtype=float))
    alt = np.asarray(alt_m, dtype=float)
    sin_lat = np.sin(lat)
    n = WGS84_A / np.sqrt(1.0 - WGS84_E2 * sin_lat**2)
    x = (n + alt) * np.cos(lat) * np.cos(lon)
    y = (n + alt) * np.cos(lat) * np.sin(lon)
    z = (n * (1.0 - WGS84_E2) + alt) * sin_lat
    return np.stack(np.broadcast_arrays(x, y, z), axis=-1)


def ecef_to_geodetic(ecef: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """ECEF (m), shape (..., 3) -> (lat_deg, lon_deg, alt_m). Bowring's method + 2 refinements."""
    p_ecef = np.asarray(ecef, dtype=float)
    x, y, z = p_ecef[..., 0], p_ecef[..., 1], p_ecef[..., 2]
    lon = np.arctan2(y, x)
    p = np.hypot(x, y)
    # Bowring initial guess via parametric latitude, then fixed-point refinement.
    beta = np.arctan2(WGS84_A * z, WGS84_B * p)
    lat = np.arctan2(z + WGS84_EP2 * WGS84_B * np.sin(beta) ** 3, p - WGS84_E2 * WGS84_A * np.cos(beta) ** 3)
    for _ in range(2):
        beta = np.arctan2((1.0 - WGS84_F) * np.sin(lat), np.cos(lat))
        lat = np.arctan2(
            z + WGS84_EP2 * WGS84_B * np.sin(beta) ** 3, p - WGS84_E2 * WGS84_A * np.cos(beta) ** 3
        )
    sin_lat = np.sin(lat)
    n = WGS84_A / np.sqrt(1.0 - WGS84_E2 * sin_lat**2)
    alt = p * np.cos(lat) + (z + WGS84_E2 * n * sin_lat) * sin_lat - n
    return np.degrees(lat), np.degrees(lon), alt


def _ecef_to_enu_matrix(lat0_deg: float, lon0_deg: float) -> NDArray[np.float64]:
    """Rotation matrix R such that enu = R @ (ecef - ecef0)."""
    lat0, lon0 = np.radians(lat0_deg), np.radians(lon0_deg)
    sl, cl = np.sin(lat0), np.cos(lat0)
    so, co = np.sin(lon0), np.cos(lon0)
    return np.array(
        [
            [-so, co, 0.0],
            [-sl * co, -sl * so, cl],
            [cl * co, cl * so, sl],
        ]
    )


@dataclass(frozen=True)
class LocalFrame:
    """A local ENU tangent-plane frame anchored at a geodetic origin."""

    lat0: float
    lon0: float
    alt0: float = 0.0

    @property
    def _origin_ecef(self) -> NDArray[np.float64]:
        return geodetic_to_ecef(self.lat0, self.lon0, self.alt0)

    @property
    def _rotation(self) -> NDArray[np.float64]:
        return _ecef_to_enu_matrix(self.lat0, self.lon0)

    def to_enu(self, lat_deg: ArrayLike, lon_deg: ArrayLike, alt_m: ArrayLike = 0.0) -> NDArray[np.float64]:
        """Geodetic -> ENU (m), shape (..., 3)."""
        d = geodetic_to_ecef(lat_deg, lon_deg, alt_m) - self._origin_ecef
        return d @ self._rotation.T

    def to_geodetic(
        self, enu: ArrayLike
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """ENU (m), shape (..., 3) -> (lat_deg, lon_deg, alt_m)."""
        ecef = np.asarray(enu, dtype=float) @ self._rotation + self._origin_ecef
        return ecef_to_geodetic(ecef)


def haversine_m(lat1: ArrayLike, lon1: ArrayLike, lat2: ArrayLike, lon2: ArrayLike) -> NDArray[np.float64]:
    """Great-circle distance on a sphere of mean Earth radius (independent cross-check only)."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(np.asarray(lon2) - np.asarray(lon1))
    h = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * EARTH_MEAN_RADIUS * np.arcsin(np.sqrt(h))
