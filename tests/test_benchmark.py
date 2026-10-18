"""Benchmark (D43): the scenario set is what it says, runs are reproducible, comparisons flag regressions."""

import math

import pytest

from throughtunnel.evaluation.benchmark import (
    LADDER_KM,
    PRESETS,
    Case,
    cases,
    compare_markdown,
    ladder_config,
    read_runs,
    run_case,
    run_config,
    write_runs,
)
from throughtunnel.positioning import ESTIMATORS
from throughtunnel.scenario import build_route_map


def test_scenario_set():
    all_cases = cases()
    assert len(all_cases) == (len(LADDER_KM) + len(PRESETS)) * 3 * 2 == 48
    assert len({c.key for c in all_cases}) == 48


@pytest.mark.parametrize("km", LADDER_KM)
def test_ladder_tunnel_lengths(km):
    rm = build_route_map(ladder_config(km))
    assert rm.tunnel_exit_m - rm.tunnel_entrance_m == pytest.approx(1000.0 * km, rel=0.01)
    assert rm.tunnel_entrance_m == pytest.approx(1600.0, abs=10.0)


def test_run_config_turns_the_realism_options_on_and_seeds_everything():
    cfg = run_config(Case("ladder_1km", "underwater", "stop_and_go"), seed=7)
    assert cfg.imu.errors.accel.drift_enabled and cfg.imu.errors.gyro.drift_enabled
    assert cfg.gnss.portal_degradation
    assert (cfg.imu.errors.seed, cfg.gnss.seed, cfg.traffic.seed, cfg.seed) == (7, 7, 7, 1007)
    assert cfg.traffic.scenario == "stop_and_go" and not cfg.road_profile.is_flat


def _same(a: list[dict], b: list[dict]) -> bool:
    """Records equal, NaN = NaN (e.g. the uncertainty-aware announcement of estimators without σ)."""

    def norm(r: dict) -> dict:
        return {k: "nan" if isinstance(v, float) and math.isnan(v) else v for k, v in r.items()}

    return [norm(r) for r in a] == [norm(r) for r in b]


def test_run_case_records_and_csv_round_trip(tmp_path):
    case = Case("ladder_0.5km", "climb3", "free")
    records = run_case(case, [0])
    assert len(records) == 2 * len(ESTIMATORS)  # map grade off and on
    write_runs(records, tmp_path / "runs.csv")
    again = read_runs(tmp_path / "runs.csv")
    assert _same(again, records)  # full precision, so a baseline compares exactly
    assert _same(run_case(case, [0]), records)  # reproducible


def test_comparison_flags_regressions_only():
    base = [{"case": "g/flat/free", "road": "flat", "traffic": "free", "map_grade": False, "seed": s,
             "tunnel_max_m": 20.0,
             "estimator": "route_imu", "exit_total_m": 20.0} for s in range(5)]  # fmt: skip
    same = compare_markdown(base, base, {"commit": "b"}, {"commit": "a"})
    assert "**Regressions:** none" in same
    worse = [r | {"exit_total_m": 30.0} for r in base]
    text = compare_markdown(worse, base, {"commit": "b"}, {"commit": "a"})
    assert "20 → 30 ⚠" in text and "Route + filtered IMU speed, flat / free" in text
    assert "## Per scenario" in text and "20 (20) → 30 (30)" in text
    slightly = [r | {"exit_total_m": 23.0} for r in base]  # 3 m worse: below the 5 m threshold
    assert "**Regressions:** none" in compare_markdown(slightly, base, {}, {})


def test_failure_states_are_symmetric_and_explained():
    from throughtunnel.evaluation.benchmark import announcement_off, gross_error

    run = {"tunnel_max_m": 50.0, "exit_total_m": 40.0}
    run |= {"announcement_error_s": 2.0, "announcement_missed": False}
    assert not gross_error(run) and not announcement_off(run)
    assert gross_error(run | {"tunnel_max_m": 250.0})  # 250 m off in the tunnel, ahead or behind
    assert gross_error(run | {"exit_total_m": 201.0})
    assert announcement_off(run | {"announcement_error_s": -16.0})  # 16 s early
    assert announcement_off(run | {"announcement_error_s": 20.0})  # 20 s late
    assert announcement_off(run | {"announcement_error_s": float("nan"), "announcement_missed": True})


def test_configuration_snapshot_lists_shared_and_varying_settings():
    from throughtunnel.evaluation.benchmark import config_markdown, config_snapshot

    selected = [Case("ladder_0.5km", "flat", "free"), Case("eisenhower_tunnel", "underwater", "stop_and_go")]
    snap = config_snapshot(selected, [3, 4])
    assert set(snap["cases"]) == {c.key for c in selected} and snap["shown_for_seed"] == 3
    assert snap["cases"]["ladder_0.5km/flat/free"]["imu"]["errors"]["accel"]["drift_enabled"] is True
    assert "coordinates" not in snap["cases"]["ladder_0.5km/flat/free"]["route"]
    text = config_markdown(snap, {"commit": "abc"})
    assert "| Accelerometer bias | 10 mg, direction random per seed |" in text  # shared
    assert "### Traffic by scenario" in text and "### Driver by scenario" in text  # varying
    assert "## Where this setup is optimistic" in text


def test_development_subset_is_part_of_the_full_set():
    from throughtunnel.evaluation.benchmark import DEV_CASES, DEV_ESTIMATORS
    from throughtunnel.evaluation.error_sources import BY_KEY, DEV_CONDITIONS

    keys = {c.key for c in cases()}
    assert set(DEV_CASES) <= keys and len(DEV_CASES) == 10  # 4 ladder roads + Eisenhower (D54), both traffic
    assert set(DEV_ESTIMATORS) <= set(ESTIMATORS)
    assert set(DEV_CONDITIONS) <= set(BY_KEY)


def test_nearly_straight_tunnel_has_no_curve_fixes():
    """The UI's long tunnel: the requested length; every bend gentler than route_kf_map's curve threshold."""
    import numpy as np

    from throughtunnel.evaluation.benchmark import straight_tunnel_config
    from throughtunnel.positioning.route_kalman import MIN_CURVATURE
    from throughtunnel.scenario import build_route_map

    cfg = straight_tunnel_config(10.0)
    assert cfg.tunnel.exit_m - cfg.tunnel.entrance_m == pytest.approx(10_000.0, abs=1.0)
    rm = build_route_map(cfg)
    d = np.arange(rm.tunnel_entrance_m + 100.0, rm.tunnel_exit_m - 100.0, 25.0)
    heading = np.unwrap([rm.heading_at(x) for x in d])
    turned = np.degrees(np.abs(np.diff(heading)).sum())
    assert turned < 8.0  # two 3° bends (plus polyline discretisation)
    assert (np.abs(np.diff(heading)) / 25.0).max() < MIN_CURVATURE  # radius above 2 km everywhere
