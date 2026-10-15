"""A–B–C–D route selection by four map clicks (D11, D28).

OSRM routes through the four points as waypoints. B and C are located on the returned polyline; a
route that reverses direction (snapped to the opposite carriageway or a dead end) is rejected, because
the vehicle model cannot drive a U-turn.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import numpy as np
from nicegui import events, run, ui

from throughtunnel.app.map_view import PICK_PREFIX, MapView
from throughtunnel.observations import RouteMap
from throughtunnel.routing import LatLon, OsrmRouteProvider, RawRoute, RoutingError
from throughtunnel.scenario import has_u_turn

POINT_NAMES = {"A": "start", "B": "tunnel entrance", "C": "tunnel exit", "D": "end"}
MIN_TUNNEL_M = 50.0  # C must come at least this far after B along the route

OnRoute = Callable[[RawRoute, float, float], Awaitable[None]]  # route, B and C along the route [m]


class RoutePicker:
    def __init__(self, map_view: MapView, provider: OsrmRouteProvider, on_route: OnRoute) -> None:
        self.map_view = map_view
        self.provider = provider
        self.on_route = on_route
        self.picks: list[LatLon] = []
        self._busy = False
        map_view.map.on("map-click", self._on_click)
        with ui.row().classes("items-center gap-3"):
            # Off by default: clicks while panning the map must not move the route points.
            self.switch = ui.switch("Select A–B–C–D by clicking the map", value=False)
            self.switch.on_value_change(lambda _: self._set_hint())
            ui.button("Clear selection", on_click=self.clear).props("flat dense")
        self.hint = ui.label().classes("text-xs text-gray-600")
        self._set_hint()

    def clear(self) -> None:
        self.picks = []
        self.map_view.remove_prefixed(PICK_PREFIX)
        self._set_hint()

    def _set_hint(self) -> None:
        if not self.switch.value:
            self.hint.text = "Turn on the switch to pick a new route (A, B, C, D) by clicking the map."
            return
        label = "ABCD"[len(self.picks)] if len(self.picks) < 4 else "A"
        self.hint.text = (
            f"Click the map to set point {label} ({POINT_NAMES[label]}). A–B: approach with GPS, "
            "B–C: simulated tunnel (0.5–5 km), C–D: recovery. Points snap to the nearest road (OSRM)."
        )

    async def _on_click(self, e: events.GenericEventArguments) -> None:
        if not self.switch.value or self._busy:
            return
        if len(self.picks) >= 4:
            self.clear()
        point = LatLon(lat=e.args["latlng"]["lat"], lon=e.args["latlng"]["lng"])
        label = "ABCD"[len(self.picks)]
        self.picks.append(point)
        self.map_view.draw_point(f"{PICK_PREFIX}_{label}", [point.lat, point.lon], label)
        self._set_hint()
        if len(self.picks) == 4:
            await self._route_from_picks()

    async def _route_from_picks(self) -> None:
        self._busy = True
        note = ui.notification("Computing route A–B–C–D (OSRM)…", spinner=True, timeout=None)
        try:
            route = await run.io_bound(self.provider.route_via, list(self.picks))
        except RoutingError as exc:
            ui.notify(str(exc), type="negative", multi_line=True)
            self.clear()
            return
        finally:
            note.dismiss()
            self._busy = False
        coords = np.asarray(route.coordinates)
        rm = RouteMap(lat=coords[:, 0], lon=coords[:, 1], tunnel_entrance_m=0.0, tunnel_exit_m=0.0)
        snapped = route.metadata.get("waypoints") or [{"lat": p.lat, "lon": p.lon} for p in self.picks]
        b = rm.locate(snapped[1]["lat"], snapped[1]["lon"])
        c = rm.locate(snapped[2]["lat"], snapped[2]["lon"], lo_m=b)
        if c - b < MIN_TUNNEL_M:
            ui.notify("Tunnel exit C must come after entrance B along the route.", type="negative")
            self.clear()
            return
        if has_u_turn(rm):
            ui.notify(
                "The route turns back at one of the points (snapped to the opposite carriageway or a dead "
                "end). Place the points along one driving direction, on the side of the road you drive on.",
                type="negative",
                multi_line=True,
                timeout=10000,
            )
            self.clear()
            return
        self.clear()
        await self.on_route(route, b, c)
