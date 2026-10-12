"""Reproducibility, persistence and route-provider parsing."""

import numpy as np
import pytest

from throughtunnel.routing.base import LatLon, RoutingError
from throughtunnel.routing.osrm import parse_osrm_response
from throughtunnel.scenario import (
    SCHEMA_VERSION,
    list_presets,
    load_preset,
    load_scenario,
    rng_stream,
    run_scenario,
    save_scenario,
)


def truth_arrays(result) -> dict[str, np.ndarray]:
    tr = result.truth
    cols = tr.scalar_columns()
    cols.update(acc_enu=tr.acc_enu, acc_body=tr.acc_body, omega_body=tr.omega_body)
    return cols


def assert_identical(a, b):
    ta, tb = truth_arrays(a), truth_arrays(b)
    assert ta.keys() == tb.keys()
    for k in ta:
        assert np.array_equal(ta[k], tb[k]), k


def test_same_seed_reproduces_bit_identical_truth():
    cfg = load_preset("synthetic_demo_track")
    assert_identical(run_scenario(cfg), run_scenario(cfg))


def test_different_seed_changes_driver_behaviour():
    cfg = load_preset("synthetic_demo_track")
    a = run_scenario(cfg)
    b = run_scenario(cfg.model_copy(update={"seed": cfg.seed + 1}))
    assert not np.array_equal(a.profile.v_preferred, b.profile.v_preferred)
    assert np.abs(a.truth.speed[:1000] - b.truth.speed[:1000]).max() > 0.1
    # The road itself does not depend on the seed.
    assert a.path.length_m == b.path.length_m


def test_json_round_trip_reproduces_run(tmp_path):
    cfg = load_preset("seattle_sr99_tunnel")
    file = tmp_path / "scenario.json"
    save_scenario(cfg, file)
    loaded = load_scenario(file)
    assert loaded == cfg
    assert loaded.schema_version == SCHEMA_VERSION
    assert_identical(run_scenario(cfg), run_scenario(loaded))


def test_named_rng_streams_are_independent_and_stable():
    a1 = rng_stream(7, "driver").standard_normal(5)
    a2 = rng_stream(7, "driver").standard_normal(5)
    b = rng_stream(7, "accelerometer").standard_normal(5)
    assert np.array_equal(a1, a2)
    assert not np.array_equal(a1, b)


def test_presets_load_and_run():
    presets = list_presets()
    assert {"seattle_sr99_tunnel", "eisenhower_tunnel", "synthetic_demo_track"} <= presets.keys()
    for pid in presets:
        res = run_scenario(load_preset(pid))
        assert 500.0 <= res.path.length_m <= 5000.0
        assert res.truth.duration_s > 30.0


def test_parse_osrm_response():
    data = {
        "code": "Ok",
        "routes": [
            {
                "distance": 123.4,
                "duration": 9.8,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[10.0, 50.0], [10.001, 50.0], [10.002, 50.001]],
                },
                "legs": [
                    {
                        "steps": [
                            {
                                "name": "Tunnel Road",
                                "intersections": [{"location": [10.0, 50.0], "classes": ["tunnel"]}],
                            }
                        ]
                    }
                ],
            }
        ],
    }
    route = parse_osrm_response(data, start=LatLon(lat=50.0, lon=10.0), end=LatLon(lat=50.001, lon=10.002))
    assert route.coordinates[0] == (50.0, 10.0)  # (lat, lon) order
    assert route.provider_distance_m == 123.4
    assert route.metadata["road_names"] == ["Tunnel Road"]
    assert route.metadata["intersections"][0]["classes"] == ["tunnel"]


def test_parse_osrm_error():
    with pytest.raises(RoutingError, match="NoRoute"):
        parse_osrm_response({"code": "NoRoute", "message": "Impossible route"})
