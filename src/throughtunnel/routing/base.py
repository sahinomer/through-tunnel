"""Route data model shared by all route providers.

A ``RawRoute`` is the *unprocessed* road centreline exactly as a provider
returned it (WGS84 lat/lon polyline). It is stored verbatim inside scenario
files so that a scenario can be replayed offline and bit-for-bit, independent
of later changes to OpenStreetMap or to the routing service.
"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LatLon(BaseModel):
    model_config = ConfigDict(frozen=True)

    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)


class RawRoute(BaseModel):
    """Unprocessed road polyline from a route provider."""

    model_config = ConfigDict(frozen=True)

    coordinates: list[tuple[float, float]] = Field(description="Polyline vertices as (lat, lon) in degrees")
    source: str = Field(description="Provider identifier, e.g. 'osrm' or 'synthetic:circle'")
    start: LatLon | None = Field(default=None, description="Requested start point (before road snapping)")
    end: LatLon | None = Field(default=None, description="Requested end point (before road snapping)")
    provider_distance_m: float | None = Field(default=None, description="Length reported by the provider")
    provider_duration_s: float | None = Field(
        default=None, description="Travel time reported by the provider"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Provider-specific extras")

    @field_validator("coordinates")
    @classmethod
    def _at_least_two_points(cls, v: list[tuple[float, float]]) -> list[tuple[float, float]]:
        if len(v) < 2:
            raise ValueError("a route needs at least two vertices")
        return v


class RoutingError(RuntimeError):
    """Raised when a route provider cannot produce a route."""


class RouteProvider(Protocol):
    """Anything that can turn a start/end pair into a drivable road polyline."""

    def route(self, start: LatLon, end: LatLon) -> RawRoute: ...

    def route_via(self, points: list[LatLon]) -> RawRoute: ...
