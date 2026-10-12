import numpy as np
import pytest
from helpers import enu_to_route

from throughtunnel.routing.base import RawRoute
from throughtunnel.routing.synthetic import Arc, Straight, build_enu_polyline


@pytest.fixture
def uneven_jittered_circle() -> tuple[RawRoute, float, tuple[float, float]]:
    """R = 300 m arc mapped like a hand-digitised OSM way: node spacing 5-35 m, 0.3 m jitter.

    Returns the route, the true radius and the arc-length interval that is safely inside the arc.
    """
    radius, lead = 300.0, 300.0
    dense = build_enu_polyline([Straight(lead), Arc(radius, 100.0), Straight(lead)], 0.5)
    rng = np.random.default_rng(1)
    idx = [0]
    while idx[-1] < len(dense) - 1:
        idx.append(min(len(dense) - 1, idx[-1] + int(rng.uniform(10, 70))))
    pts = dense[idx] + rng.normal(0.0, 0.3, (len(idx), 2))
    pts[0] = dense[0]
    arc_len = radius * np.radians(100.0)
    return enu_to_route(pts, "uneven-circle"), radius, (lead + 80.0, lead + arc_len - 80.0)
