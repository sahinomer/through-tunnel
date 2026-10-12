import numpy as np

from throughtunnel.geodesy import LocalFrame
from throughtunnel.routing.base import RawRoute


def enu_to_route(points: np.ndarray, name: str = "test") -> RawRoute:
    """Wrap an ENU polyline (metres, origin at 0°N 0°E) as a RawRoute."""
    frame = LocalFrame(0.0, 0.0)
    lat, lon, _ = frame.to_geodetic(np.column_stack([points, np.zeros(len(points))]))
    return RawRoute(coordinates=list(zip(lat.tolist(), lon.tolist(), strict=True)), source=f"test:{name}")
