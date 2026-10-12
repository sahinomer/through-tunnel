import numpy as np
import pytest

from throughtunnel.geodesy import LocalFrame, ecef_to_geodetic, geodetic_to_ecef, haversine_m


@pytest.mark.parametrize(("lat", "lon", "alt"), [(47.6, -122.33, 30.0), (-33.9, 151.2, 0.0), (0.0, 0.0, 0.0)])
def test_ecef_round_trip(lat, lon, alt):
    la, lo, h = ecef_to_geodetic(geodetic_to_ecef(lat, lon, alt))
    assert la == pytest.approx(lat, abs=1e-10)
    assert lo == pytest.approx(lon, abs=1e-10)
    assert h == pytest.approx(alt, abs=1e-5)


def test_enu_round_trip_and_origin():
    frame = LocalFrame(47.5957, -122.3355)
    rng = np.random.default_rng(0)
    lat = 47.5957 + rng.uniform(-0.05, 0.05, 50)
    lon = -122.3355 + rng.uniform(-0.05, 0.05, 50)
    enu = frame.to_enu(lat, lon)
    la, lo, _ = frame.to_geodetic(enu)
    assert np.abs(la - lat).max() < 1e-10  # ~0.01 mm
    assert np.abs(lo - lon).max() < 1e-10
    assert np.allclose(frame.to_enu(47.5957, -122.3355), 0.0, atol=1e-9)


def test_enu_axes_and_distances():
    frame = LocalFrame(40.0, -74.0)
    north = frame.to_enu(40.01, -74.0)
    east = frame.to_enu(40.0, -73.99)
    assert north[1] > 1000 and abs(north[0]) < 1e-6
    assert east[0] > 800 and abs(east[1]) < 1.0  # meridian convergence: tiny northing
    # ENU is a rigid rotation of ECEF: straight-line distances are preserved exactly.
    p = frame.to_enu(40.02, -73.97)
    chord = np.linalg.norm(geodetic_to_ecef(40.02, -73.97) - geodetic_to_ecef(40.0, -74.0))
    assert np.linalg.norm(p) == pytest.approx(chord, rel=1e-12)
    # ...and agree with an independent great-circle formula to the sphere/ellipsoid difference.
    assert np.linalg.norm(p[:2]) == pytest.approx(haversine_m(40.0, -74.0, 40.02, -73.97), rel=5e-3)
