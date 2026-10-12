"""Synthetic road geometries for controlled validation scenarios.

Roads are built from analytic primitives (straights and circular arcs, heading
changes positive to the left) in a local ENU frame and then converted to
lat/lon, so they flow through exactly the same pipeline as OSM routes.
``vertex_spacing_m`` controls how coarsely arcs are sampled, which lets tests
mimic the chord artefacts of real map polylines.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from throughtunnel.geodesy import LocalFrame
from throughtunnel.routing.base import LatLon, RawRoute

# Synthetic roads are placed at "Null Island" so they are visibly not real roads on the map.
SYNTHETIC_ORIGIN = LocalFrame(lat0=0.0, lon0=0.0)


@dataclass(frozen=True)
class Straight:
    length_m: float


@dataclass(frozen=True)
class Arc:
    radius_m: float
    angle_deg: float  # signed: positive = left turn


@dataclass(frozen=True)
class Corner:
    """Instantaneous heading change at a single vertex (a raw polyline corner)."""

    angle_deg: float


Segment = Straight | Arc | Corner


def build_enu_polyline(
    segments: Sequence[Segment], vertex_spacing_m: float = 1.0, initial_heading_deg: float = 0.0
) -> np.ndarray:
    """Return ENU vertices (N, 2) for a chain of segments starting at the origin.

    ``initial_heading_deg`` is the ENU yaw (counter-clockwise from East).
    """
    pts = [np.zeros(2)]
    pos = np.zeros(2)
    yaw = np.radians(initial_heading_deg)
    for seg in segments:
        match seg:
            case Straight(length_m=length):
                n = max(1, round(length / vertex_spacing_m))
                d = np.linspace(0.0, length, n + 1)[1:]
                new = pos + np.outer(d, [np.cos(yaw), np.sin(yaw)])
                pts.extend(new)
                pos = new[-1]
            case Arc(radius_m=r, angle_deg=ang):
                dpsi = np.radians(ang)
                arc_len = abs(dpsi) * r
                n = max(1, round(arc_len / vertex_spacing_m))
                sign = np.sign(dpsi)
                centre = pos + sign * r * np.array([-np.sin(yaw), np.cos(yaw)])
                phi = yaw + np.linspace(0.0, dpsi, n + 1)[1:]
                new = centre + sign * r * np.column_stack([np.sin(phi), -np.cos(phi)])
                pts.extend(new)
                pos = new[-1]
                yaw += dpsi
            case Corner(angle_deg=ang):
                yaw += np.radians(ang)
    return np.asarray(pts)


def synthetic_route(
    segments: Sequence[Segment],
    name: str,
    vertex_spacing_m: float = 1.0,
    initial_heading_deg: float = 0.0,
    frame: LocalFrame = SYNTHETIC_ORIGIN,
) -> RawRoute:
    enu = build_enu_polyline(segments, vertex_spacing_m, initial_heading_deg)
    lat, lon, _ = frame.to_geodetic(np.column_stack([enu, np.zeros(len(enu))]))
    coords = [(float(a), float(b)) for a, b in zip(lat, lon, strict=True)]
    return RawRoute(
        coordinates=coords,
        source=f"synthetic:{name}",
        start=LatLon(lat=coords[0][0], lon=coords[0][1]),
        end=LatLon(lat=coords[-1][0], lon=coords[-1][1]),
        metadata={"segments": [repr(s) for s in segments], "vertex_spacing_m": vertex_spacing_m},
    )


def straight_road(length_m: float = 1000.0, heading_deg: float = 30.0) -> RawRoute:
    return synthetic_route(
        [Straight(length_m)], "straight", vertex_spacing_m=50.0, initial_heading_deg=heading_deg
    )


def circle_road(
    radius_m: float = 200.0, angle_deg: float = 270.0, lead_m: float = 200.0, spacing_m: float = 2.0
):
    return synthetic_route(
        [Straight(lead_m), Arc(radius_m, angle_deg), Straight(lead_m)], "circle", vertex_spacing_m=spacing_m
    )


def s_curve_road(radius_m: float = 150.0, angle_deg: float = 60.0, spacing_m: float = 10.0) -> RawRoute:
    return synthetic_route(
        [Straight(300.0), Arc(radius_m, angle_deg), Arc(radius_m, -angle_deg), Straight(300.0)],
        "s-curve",
        vertex_spacing_m=spacing_m,
    )


def segment_length(seg: Segment) -> float:
    match seg:
        case Straight(length_m=length):
            return length
        case Arc(radius_m=r, angle_deg=ang):
            return r * abs(np.radians(ang))
    return 0.0


# Synthetic A–D demo route: approach with turns (GPS available; also excites the phone-mount
# alignment), a curvy "tunnel" with left and right curves of different radii, and a recovery section.
DEMO_APPROACH: tuple[Segment, ...] = (
    Straight(300.0),
    Arc(250.0, 35.0),
    Straight(250.0),
    Arc(150.0, -60.0),
    Straight(300.0),
    Arc(400.0, 20.0),
    Straight(300.0),
)
DEMO_TUNNEL: tuple[Segment, ...] = (
    Arc(600.0, -25.0),
    Straight(450.0),
    Arc(300.0, 45.0),
    Straight(350.0),
    Arc(200.0, -60.0),
    Straight(450.0),
)
DEMO_RECOVERY: tuple[Segment, ...] = (Straight(300.0), Arc(250.0, 40.0), Straight(350.0))
DEMO_TUNNEL_ENTRANCE_M = sum(segment_length(s) for s in DEMO_APPROACH)
DEMO_TUNNEL_EXIT_M = DEMO_TUNNEL_ENTRANCE_M + sum(segment_length(s) for s in DEMO_TUNNEL)


def demo_track_road() -> RawRoute:
    """~4.4 km synthetic A–D route (1.6 km approach, 2.0 km tunnel, 0.8 km recovery)."""
    return synthetic_route(
        [*DEMO_APPROACH, *DEMO_TUNNEL, *DEMO_RECOVERY], "demo-track", vertex_spacing_m=15.0
    )
