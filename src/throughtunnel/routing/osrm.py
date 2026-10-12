"""OSRM (Open Source Routing Machine) route provider.

OSRM routes on OpenStreetMap data and snaps the requested points to the
nearest drivable road. The public demo server (default) is meant for light
development use only (~1 request/s, no SLA); point ``base_url`` to a
self-hosted OSRM instance for anything heavier.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from throughtunnel.routing.base import LatLon, RawRoute, RoutingError

DEFAULT_OSRM_URL = "https://router.project-osrm.org"
USER_AGENT = "ThroughTunnel/0.1 (vehicle sensor simulator; research use)"


@dataclass(frozen=True)
class OsrmRouteProvider:
    base_url: str = DEFAULT_OSRM_URL
    profile: str = "driving"
    timeout_s: float = 20.0

    def route(self, start: LatLon, end: LatLon) -> RawRoute:
        return self.route_via([start, end])

    def route_via(self, points: list[LatLon]) -> RawRoute:
        """Route through all points in order (e.g. A, B, C, D). Snapped points are in metadata."""
        if len(points) < 2:
            raise RoutingError("need at least two points")
        start, end = points[0], points[-1]
        coords = ";".join(f"{p.lon:.7f},{p.lat:.7f}" for p in points)
        url = f"{self.base_url.rstrip('/')}/route/v1/{self.profile}/{coords}"
        params = {"overview": "full", "geometries": "geojson", "steps": "true"}
        try:
            resp = httpx.get(url, params=params, timeout=self.timeout_s, headers={"User-Agent": USER_AGENT})
        except httpx.HTTPError as exc:
            raise RoutingError(f"OSRM request failed: {exc}") from exc
        if resp.status_code != 200:
            raise RoutingError(f"OSRM returned HTTP {resp.status_code}: {resp.text[:200]}")
        return parse_osrm_response(resp.json(), start=start, end=end, base_url=self.base_url)


def parse_osrm_response(
    data: dict, *, start: LatLon | None = None, end: LatLon | None = None, base_url: str = ""
) -> RawRoute:
    """Convert an OSRM ``/route`` JSON response into a :class:`RawRoute`."""
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingError(
            f"OSRM could not find a route: {data.get('code')} {data.get('message', '')}".strip()
        )
    route = data["routes"][0]
    coordinates = [(lat, lon) for lon, lat in route["geometry"]["coordinates"]]
    snapped = [{"lat": w["location"][1], "lon": w["location"][0]} for w in data.get("waypoints", [])]

    # Keep intersection classes (e.g. 'tunnel', 'motorway', 'toll') and road names:
    # cheap to store now, useful later for marking tunnel sections without refetching.
    intersections: list[dict] = []
    road_names: list[str] = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            name = step.get("name") or step.get("ref") or ""
            if name and (not road_names or road_names[-1] != name):
                road_names.append(name)
            for inter in step.get("intersections", []):
                lon, lat = inter["location"]
                intersections.append({"lat": lat, "lon": lon, "classes": inter.get("classes", [])})

    return RawRoute(
        coordinates=coordinates,
        source="osrm",
        start=start,
        end=end,
        provider_distance_m=route.get("distance"),
        provider_duration_s=route.get("duration"),
        metadata={
            "base_url": base_url,
            "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "road_names": road_names,
            "intersections": intersections,
            "waypoints": snapped,
            "leg_distances_m": [leg.get("distance") for leg in route.get("legs", [])],
        },
    )
