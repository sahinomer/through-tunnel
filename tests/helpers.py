import numpy as np

from throughtunnel.geodesy import LocalFrame
from throughtunnel.routing.base import RawRoute


def enu_to_route(points: np.ndarray, name: str = "test") -> RawRoute:
    """Wrap an ENU polyline (metres, origin at 0°N 0°E) as a RawRoute."""
    frame = LocalFrame(0.0, 0.0)
    lat, lon, _ = frame.to_geodetic(np.column_stack([points, np.zeros(len(points))]))
    return RawRoute(coordinates=list(zip(lat.tolist(), lon.tolist(), strict=True)), source=f"test:{name}")


def stationary_truth(
    n: int = 200, lat: float = 47.6, lon: float = -122.3, yaw_deg: float = 0.0, rate: float = 100.0
):
    """Ground truth of a parked vehicle (the vehicle simulator itself never stops)."""
    from throughtunnel.vehicle.truth import GroundTruth

    z = np.zeros(n)
    return GroundTruth(
        frame=LocalFrame(lat, lon),
        t=np.arange(n) / rate,
        s=z, x=z, y=z, z=z, lat=np.full(n, lat), lon=np.full(n, lon), alt=z,
        speed=z, accel_long=z, accel_lat=z, jerk=z, yaw=np.full(n, np.radians(yaw_deg)),
        yaw_rate=z, yaw_accel=z, curvature=z, roll=z, pitch=z,
        acc_enu=np.zeros((n, 3)), acc_body=np.zeros((n, 3)), omega_body=np.zeros((n, 3)),
    )  # fmt: skip
