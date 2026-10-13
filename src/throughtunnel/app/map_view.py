"""The Leaflet map: route, tunnel band, A–D points, true path, GPS fixes, estimate overlays.

Vehicle and estimate markers are animated in the browser (`static/track_player.js`) from decimated
tracks, interpolated every animation frame and re-anchored to the server playback clock by
``sync_player``. Server-pushed marker positions made the vehicle hold still and then jump.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np
from nicegui import context, ui

from throughtunnel.app.positioning_view import color_of, track_payload
from throughtunnel.app.track import playback_track
from throughtunnel.observations import RouteMap
from throughtunnel.positioning.runner import EstimateTrack
from throughtunnel.routing import RawRoute
from throughtunnel.scenario import SimulationResult, TunnelConfig

TRACK_PLAYER_JS = (Path(__file__).parent / "static" / "track_player.js").read_text(encoding="utf-8")

ROUTE_STYLE_RAW = {"color": "#555555", "weight": 2, "dashArray": "4 6", "opacity": 0.9}
ROUTE_STYLE_PATH = {"color": "#1565c0", "weight": 5, "opacity": 0.55}
TRAIL_STYLE = {"color": "#e65100", "weight": 4, "opacity": 0.9}
TUNNEL_STYLE = {"color": "#616161", "weight": 18, "opacity": 0.35, "lineCap": "butt"}
GPS_STYLE = {"color": "#00897b", "weight": 4, "opacity": 0.9, "dashArray": "1 9", "lineCap": "round"}
POINT_COLORS = {"A": "#2e7d32", "B": "#ef6c00", "C": "#6a1b9a", "D": "#c62828"}
VEHICLE_STYLE = {"radius": 9, "color": "#000000", "weight": 2, "fillColor": "#ffb300", "fillOpacity": 1.0}
PICK_PREFIX = "pick"  # layers of the A–D click selection survive route changes


class MapView:
    def __init__(self) -> None:
        ui.add_body_html(f"<script>{TRACK_PLAYER_JS}</script>")
        self.client = context.client
        self.map = ui.leaflet(center=(47.6086, -122.3398), zoom=13).classes("w-full")
        self.map.style("height: 62vh")
        self.layers: dict[str, Any] = {}

    # ------------------------------------------------------------------ layers
    def remove(self, *names: str) -> None:
        for name in names:
            layer = self.layers.pop(name, None)
            if layer is not None:
                self.map.remove_layer(layer)

    def remove_prefixed(self, prefix: str) -> None:
        self.remove(*[k for k in self.layers if k.startswith(prefix)])

    def draw_point(self, name: str, latlng: list[float], label: str) -> None:
        self.remove(name)
        color = POINT_COLORS.get(label, "#ff6f00")
        style = {"radius": 7, "color": "#ffffff", "weight": 2, "fillColor": color, "fillOpacity": 1.0}
        layer = self.map.generic_layer(name="circleMarker", args=[latlng, style])
        layer.run_method("bindTooltip", label, {"permanent": True, "direction": "top", "offset": [0, -6]})
        self.layers[name] = layer

    def _polyline(self, name: str, points: list, style: dict) -> None:
        self.layers[name] = self.map.generic_layer(name="polyline", args=[points, style])

    # ------------------------------------------------------------------ scene
    def show_route(self, route: RawRoute, tunnel: TunnelConfig | None) -> None:
        """Map route, tunnel band B–C and points A–D; clears everything except the click selection."""
        self.remove(*[k for k in self.layers if not k.startswith(PICK_PREFIX)])
        coords = [list(c) for c in route.coordinates]
        rm = RouteMap(lat=np.array([c[0] for c in coords]), lon=np.array([c[1] for c in coords]),
                      tunnel_entrance_m=0.0, tunnel_exit_m=0.0)  # fmt: skip
        points = {"A": 0.0, "D": rm.length_m}
        if tunnel is not None:  # drawn first, so it stays underneath the route
            b, c = min(tunnel.entrance_m, rm.length_m), min(tunnel.exit_m, rm.length_m)
            inner = [list(x) for x, d in zip(coords, rm.distance_m, strict=True) if b < d < c]
            self._polyline("tunnel", [list(rm.latlon_at(b)), *inner, list(rm.latlon_at(c))], TUNNEL_STYLE)
            points.update(B=b, C=c)
        self._polyline("raw", coords, ROUTE_STYLE_RAW)
        for label, d in points.items():
            self.draw_point(f"pt_{label}", list(rm.latlon_at(d)), label)
        lats, lons = [c[0] for c in coords], [c[1] for c in coords]
        self.map.run_map_method(
            "fitBounds", [[min(lats), min(lons)], [max(lats), max(lons)]], {"padding": [30, 30]}
        )

    def show_result(self, result: SimulationResult) -> None:
        """True path, GPS fixes, announcement point and the animated vehicle of a new simulation."""
        self.remove("path", "vehicle", "heading", "trail", "link", "gps", "announce")
        self.remove_prefixed("est_")
        path_ll = result.path.latlon(step_m=5.0).tolist()
        self._polyline("path", path_ll, ROUTE_STYLE_PATH)
        self.show_gps(result)
        rm = result.route_map
        if rm.announcement_m is not None:
            self.draw_point("announce", list(rm.latlon_at(rm.announcement_m)), "announce")
        self._polyline("trail", [], TRAIL_STYLE)
        self._polyline("link", [], TRAIL_STYLE)
        self._polyline("heading", [path_ll[0], path_ll[0]], {"color": "#000000", "weight": 3})
        self.layers["vehicle"] = self.map.generic_layer(name="circleMarker", args=[path_ll[0], VEHICLE_STYLE])
        ids = {k: self.layers[k].id for k in ("vehicle", "heading", "trail", "link")}
        track = json.dumps(playback_track(result.truth))
        self.client.run_javascript(f"ttPlayer.load({self.map.id}, {track}, {json.dumps(ids)})")

    def show_gps(self, result: SimulationResult) -> None:
        """Measured GPS fixes as a dotted line, split where fixes are missing (the tunnel gap)."""
        self.remove("gps")
        g = result.gnss
        if len(g) < 2:
            return
        breaks = np.flatnonzero(np.diff(g.t) > 1.5 / result.config.gnss.rate_hz) + 1
        segments = [
            np.column_stack([lat, lon]).tolist()
            for lat, lon in zip(np.split(g.lat, breaks), np.split(g.lon, breaks), strict=True)
        ]
        self._polyline("gps", segments, GPS_STYLE)
        if "vehicle" in self.layers:
            self.layers["vehicle"].run_method("bringToFront")

    def show_estimates(
        self, tracks: Iterable[EstimateTrack], result: SimulationResult, visible: set[str]
    ) -> None:
        """One line and one animated marker per estimator (hidden ones transparent, for quick toggling)."""
        self.remove_prefixed("est_")
        extras = []
        for track in tracks:
            payload = track_payload(track, result)
            shown = track.name in visible
            color = color_of(track.name)
            line = {"color": color, "weight": 3, "opacity": 0.85 if shown else 0.0}
            pts = np.column_stack([payload["lat"], payload["lon"]]).tolist()
            self._polyline(f"est_line_{track.name}", pts, line)
            marker = {"radius": 6, "color": "#ffffff", "weight": 1.5, "fillColor": color,
                      "fillOpacity": 1.0 if shown else 0.0, "opacity": 1.0 if shown else 0.0}  # fmt: skip
            layer = self.map.generic_layer(name="circleMarker", args=[pts[0], marker])
            self.layers[f"est_marker_{track.name}"] = layer
            extras.append({"id": layer.id, **payload})
        self.layers["vehicle"].run_method("bringToFront")
        self.client.run_javascript(f"window.ttPlayer && ttPlayer.setExtras({json.dumps(extras)})")

    def set_estimate_visibility(self, names: Iterable[str], visible: set[str]) -> None:
        for name in names:
            shown = name in visible
            if f"est_line_{name}" in self.layers:
                self.layers[f"est_line_{name}"].run_method("setStyle", {"opacity": 0.85 if shown else 0.0})
                self.layers[f"est_marker_{name}"].run_method(
                    "setStyle", {"opacity": 1.0 if shown else 0.0, "fillOpacity": 1.0 if shown else 0.0}
                )

    def sync_player(self, t: float, speed: float, playing: bool, soft: bool = False) -> None:
        """Re-anchor the browser's map animation to the server playback clock."""
        args = f"{t:.4f}, {speed}, {'true' if playing else 'false'}, {'true' if soft else 'false'}"
        self.client.run_javascript(f"window.ttPlayer && ttPlayer.sync({args})")
