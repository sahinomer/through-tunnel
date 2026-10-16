"""Benchmark (D43): one fixed scenario set and seeds for judging every estimator, with saved baselines.

Scenarios (48): 8 geometries × 3 road profiles × 2 traffic cases.
* Geometries:
  * a length ladder of synthetic routes with tunnels of 0.5, 1, 2, 3 and 5 km (the synthetic preset's
    1.6 km approach with turns and 0.8 km recovery; the tunnel is a gentle S-curve);
  * the three presets, with their real (or demo) geometry and 2.0–3.0 km tunnels.
* Road: flat; a 3 % climb inside the tunnel; an underwater V (−4 % / +4 %).
* Traffic: free flow; stop-and-go (T3).

Sensors are realistic, with the realism options on: the preset IMU noise and bias, *bias drift*, the GPS
error model with *degradation before the portal*, and the car-speed reading (+2 % scale error, for the
reference estimator only). The calibration error is the natural one, none injected. Run k uses seed k
for the drive, the sensors, the GPS and the traffic, so it differs between runs but is the same for
every estimator and every code version. Sloped roads are evaluated twice, with the map grade off and
on (two information levels); flat roads once.

Every registered estimator runs, the reference ``route_vspeed`` included (marked as reference in the
tables). Per run and estimator, two failure states and one data-quality flag (D44):
* **gross error**: the estimate was more than ``GROSS_ERROR_M`` (200 m) from the true position at some
  time in the tunnel or at C, ahead or behind;
* **announcement off**: the exit announcement was more than ``ANNOUNCE_OFF_S`` (15 s) early or late,
  or never fired;
* **capped** (not a failure): the estimate reached the route end D before the vehicle reached C. A
  route estimate stops at D, so its error is then a lower bound. Such a run is always also a gross
  error (it was at least the C–D distance, 0.8–0.9 km, ahead).

    uv run python -m throughtunnel.evaluation.benchmark --seeds 20 --out docs/benchmark/baseline
    uv run python -m throughtunnel.evaluation.benchmark --quick --out <dir> --compare docs/benchmark/baseline

``--dev`` = the development subset (agreed 2026-10-16): the guard scenarios ``DEV_CASES`` (short and long
flat tunnel, the long tunnel with a climb and underwater, both traffic cases), sloped roads with the map
grade on only (map grade is a settled requirement), and only the estimators an estimator change can
affect (``DEV_ESTIMATORS``). The full set is rerun at milestones, not after every change.
``--quick`` = 5 seeds. ``--compare`` writes ``compare.md``: per estimator and scenario
family, the median change of the error at C against the baseline on the shared runs, with regressions
flagged. ``--from-csv`` regenerates the tables of an existing output directory.

Every run also writes its configuration next to its results: ``config.md`` (readable: shared settings,
the ones that differ by scenario, where the setup is optimistic) and ``config.json`` (the complete
effective scenario configuration of every scenario). ``--write-config`` (with ``--from-csv``) rewrites
them for an existing run.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from throughtunnel.evaluation.experiment import compare_estimators, markdown_table
from throughtunnel.evaluation.slope_study import Profile, profile_config
from throughtunnel.positioning import ESTIMATORS, REFERENCE_ESTIMATORS
from throughtunnel.road_profile import ElevationProfile
from throughtunnel.routing.synthetic import (
    DEMO_APPROACH,
    DEMO_RECOVERY,
    Arc,
    Straight,
    build_enu_polyline,
    synthetic_route,
)
from throughtunnel.scenario import (
    MapDataConfig,
    ScenarioConfig,
    TunnelConfig,
    list_presets,
    load_preset,
    run_scenario,
    with_map_data,
)
from throughtunnel.sensors.errors import DEG, MDPS, MG, UG
from throughtunnel.vehicle.traffic import TrafficConfig

LADDER_KM = (0.5, 1.0, 2.0, 3.0, 5.0)
PRESETS = tuple(list_presets())
ROADS: dict[str, Profile | None] = {
    "flat": None,
    "climb3": Profile("climb3", "Climb in the tunnel +3 %", "tunnel_climb", 1.0),
    "underwater": Profile("underwater", "Underwater V −4 % / +4 %", "underwater", 1.0),
}
TRAFFIC = ("free", "stop_and_go")
QUICK_SEEDS = 5
ANNOUNCE_OK_S = 3.0  # "good" announcement: within ±3 s of the ideal time
ANNOUNCE_OFF_S = 15.0  # failure: announcement more than 15 s early or late (or never)
GROSS_ERROR_M = 200.0  # failure: the estimate more than 200 m off at some time in the tunnel or at C
REGRESSION_REL, REGRESSION_ABS_M = 0.10, 5.0  # flagged if the median gets worse by both
# Development subset (--dev): guard scenarios, map grade on, the calibrated estimators + the reference.
DEV_CASES = tuple(
    f"ladder_{km}/{road}/{traffic}"
    for km, road in (("0.5km", "flat"), ("5km", "flat"), ("5km", "climb3"), ("5km", "underwater"))
    for traffic in ("free", "stop_and_go")
)
DEV_ESTIMATORS = ("dr_calibrated", "dr_filtered", "route_imu", "route_vspeed")
VERTEX_SPACING_M = 15.0


@dataclass(frozen=True)
class Case:
    geometry: str  # "ladder_2km" or a preset id
    road: str
    traffic: str

    @property
    def key(self) -> str:
        return f"{self.geometry}/{self.road}/{self.traffic}"


def cases() -> list[Case]:
    geometries = [f"ladder_{km:g}km" for km in LADDER_KM] + list(PRESETS)
    return [Case(g, r, t) for g in geometries for r in ROADS for t in TRAFFIC]


# ---------------------------------------------------------------------- scenario construction
def _polyline_length(segments) -> float:
    pts = build_enu_polyline(segments, VERTEX_SPACING_M)
    return float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())


def ladder_config(tunnel_km: float) -> ScenarioConfig:
    """The synthetic preset's approach and recovery around a gently S-curved tunnel of the given length."""
    length = 1000.0 * tunnel_km
    radius = 800.0
    arc_deg = math.degrees(0.15 * length / radius)  # two opposite arcs of 15 % each; straights 70 %
    tunnel = (Straight(0.3 * length), Arc(radius, arc_deg), Straight(0.2 * length), Arc(radius, -arc_deg),
              Straight(0.2 * length))  # fmt: skip
    entrance = _polyline_length(DEMO_APPROACH)
    exit_ = _polyline_length((*DEMO_APPROACH, *tunnel))
    route = synthetic_route(
        [*DEMO_APPROACH, *tunnel, *DEMO_RECOVERY],
        f"ladder-{tunnel_km:g}km",
        vertex_spacing_m=VERTEX_SPACING_M,
    )
    base = load_preset("synthetic_demo_track")
    return base.model_copy(update={
        "name": f"Benchmark ladder, {tunnel_km:g} km tunnel", "route": route,
        "tunnel": TunnelConfig(entrance_m=entrance, exit_m=exit_, announce_before_exit_m=300.0),
    })  # fmt: skip


def base_config(geometry: str) -> ScenarioConfig:
    if geometry.startswith("ladder_"):
        return ladder_config(float(geometry.removeprefix("ladder_").removesuffix("km")))
    return load_preset(geometry)


def run_config(case: Case, seed: int) -> ScenarioConfig:
    """The scenario of one benchmark run: realism options on, seed k for drive, sensors, GPS, traffic."""
    cfg = base_config(case.geometry)
    errors = cfg.imu.errors
    errors = errors.model_copy(update={
        "seed": seed,
        "accel": errors.accel.model_copy(update={"drift_enabled": True}),
        "gyro": errors.gyro.model_copy(update={"drift_enabled": True}),
    })  # fmt: skip
    profile = ROADS[case.road]
    return cfg.model_copy(update={
        "seed": 1000 + seed,
        "imu": cfg.imu.model_copy(update={"errors": errors}),
        "gnss": cfg.gnss.model_copy(update={"seed": seed, "portal_degradation": True}),
        "traffic": TrafficConfig(scenario=case.traffic, seed=seed),
        "road_profile": profile_config(cfg, profile) if profile is not None else cfg.road_profile,
    })  # fmt: skip


# ---------------------------------------------------------------------- running
def run_case(case: Case, seeds: list[int], dev: bool = False) -> list[dict]:
    """All runs of one scenario; ``dev``: map grade on only (sloped roads), ``DEV_ESTIMATORS`` only."""
    records = []
    grades = (False,) if case.road == "flat" else ((True,) if dev else (False, True))
    names = list(DEV_ESTIMATORS) if dev else None
    for seed in seeds:
        res = run_scenario(run_config(case, seed))
        c_t, length = res.sections.exit_t, res.route_map.length_m
        outage = res.gnss_events.reacquire_t - res.gnss_events.loss_t
        for grade in grades:
            cmp = compare_estimators(with_map_data(res, MapDataConfig(road_grade=grade)), names)
            for track, ev in zip(cmp.tracks, cmp.evaluations, strict=True):
                rd = track.route_distance[track.t < c_t]
                s = ev.summary
                ann = ev.announcement_time_error_s
                records.append({
                    "case": case.key, "geometry": case.geometry, "road": case.road, "traffic": case.traffic,
                    "map_grade": grade, "seed": seed, "estimator": ev.name,
                    "tunnel_m": res.route_map.tunnel_exit_m - res.route_map.tunnel_entrance_m,
                    "outage_s": outage, "exit_total_m": s["exit_total_m"], "exit_along_m": s["exit_along_m"],
                    "tunnel_max_m": s["tunnel_max_m"], "announcement_error_s": ann,
                    "announcement_missed": bool(math.isnan(ann)),
                    "route_end_reached": bool(len(rd) and rd.max() >= length - 1.0),
                })  # fmt: skip
    print(f"{case.key}: {len(seeds)} runs", flush=True)
    return records


# ---------------------------------------------------------------------- tables
def _sel(records, **kw):
    return [r for r in records if all(r[k] == v for k, v in kw.items())]


def _med_p90(vals) -> str:
    v = np.asarray(vals, dtype=float)
    v = v[np.isfinite(v)]
    return f"{np.median(v):.0f} ({np.percentile(v, 90):.0f})" if len(v) else "–"


def gross_error(r) -> bool:
    """More than GROSS_ERROR_M off, ahead or behind, at some time in the tunnel or at C."""
    return max(r["tunnel_max_m"], r["exit_total_m"]) > GROSS_ERROR_M


def announcement_off(r) -> bool:
    """Announced more than ANNOUNCE_OFF_S early or late, or never."""
    return r["announcement_missed"] or abs(r["announcement_error_s"]) > ANNOUNCE_OFF_S


def _pct(flags) -> str:
    return f"{100 * np.mean(list(flags)):.0f} %"


def _label(name: str) -> str:
    return ESTIMATORS[name].label if name in ESTIMATORS else name


def _estimators(records) -> list[str]:
    present = {r["estimator"] for r in records}
    return [n for n in ESTIMATORS if n in present] + sorted(present - set(ESTIMATORS))


def overall_table(records, map_grade: bool) -> list[dict[str, str]]:
    """All 48 scenarios at one information level (flat roads, where the map grade changes nothing,
    are in both)."""
    rows = []
    for name in _estimators(records):
        sel = [r for r in _sel(records, estimator=name) if r["road"] == "flat" or r["map_grade"] == map_grade]
        ann = np.array([r["announcement_error_s"] for r in sel], dtype=float)
        rows.append({
            "estimator": _label(name) + (" †" if name in REFERENCE_ESTIMATORS else ""),
            "error at C [m]": _med_p90([r["exit_total_m"] for r in sel]),
            "max in tunnel [m]": _med_p90([r["tunnel_max_m"] for r in sel]),
            f"gross error (> {GROSS_ERROR_M:g} m)": _pct(gross_error(r) for r in sel),
            f"announcement off (> ±{ANNOUNCE_OFF_S:g} s)": _pct(announcement_off(r) for r in sel),
            f"announcement good (±{ANNOUNCE_OK_S:g} s)": _pct(np.abs(ann) <= ANNOUNCE_OK_S),
            "capped at D": _pct(r["route_end_reached"] for r in sel),
        })  # fmt: skip
    return rows


def family_table(records, column: str, values, label=str, **fixed) -> list[dict[str, str]]:
    """Median (p90) error at C per estimator for each value of ``column`` (other columns fixed)."""
    rows = []
    for name in _estimators(records):
        row = {"estimator": _label(name) + (" †" if name in REFERENCE_ESTIMATORS else "")}
        for v in values:
            sel = _sel(records, estimator=name, **{column: v}, **fixed)
            cell = _med_p90([r["exit_total_m"] for r in sel])
            gross = sum(gross_error(r) for r in sel)
            capped = sum(r["route_end_reached"] for r in sel)
            row[label(v)] = cell + (f" ✗{gross}" if gross else "") + (f" §{capped}" if capped else "")
        rows.append(row)
    return rows


def tables_markdown(records, meta: dict) -> str:
    n_seeds = len({r["seed"] for r in records})
    out = [
        "# Benchmark: generated tables\n",
        f"{meta.get('label', '')} · commit `{meta.get('commit', '?')}` · {meta.get('date', '')} · "
        f"{len({r['case'] for r in records})} scenarios × {n_seeds} runs"
        + (" (**development subset**: map grade on, calibrated estimators only)" if meta.get("dev") else "")
        + ". † = reference estimator (uses "
        "the car's speed reading; not a phone-only solution). Realism options on (bias drift, GPS "
        "degradation before the portal).\n",
        "## How to read the failure states\n",
        f"* **Gross error**: the estimate was more than {GROSS_ERROR_M:g} m from the true position at some "
        "time in the tunnel or at C, ahead *or* behind. The position is unusable for guidance.\n"
        f"* **Announcement off**: the exit announcement came more than {ANNOUNCE_OFF_S:g} s early or late "
        "(or never). The driver gets the instruction at the wrong time. Never-fired does not happen in "
        "practice: a late estimate is pushed past the announcement point when GPS returns, so the "
        "announcement is late, not missing.\n"
        "* **Capped at D** (a data-quality flag, not a third failure): the estimate reached the route end D "
        "before the vehicle reached C. A route estimate stops at D, so its error is a lower bound (cells of "
        "exactly 782 / 881 / 889 m are the C–D distances). Every capped run is also a gross error.\n"
        "* In the scenario tables, cells are the error at C [m], median (p90); ✗n = n runs with a gross "
        "error, §n = n of them capped at D.\n",
        "## Overall, without map grade\n",
        markdown_table(overall_table(records, map_grade=False)) + "\n",
        "## Overall, with map grade\n",
        "Flat roads (where the map grade changes nothing) are in both overall tables.\n",
        markdown_table(overall_table(records, map_grade=True)) + "\n",
    ]
    ladder = [f"ladder_{km:g}km" for km in LADDER_KM]
    km = lambda g: g.removeprefix("ladder_").replace("km", " km")  # noqa: E731
    for traffic in TRAFFIC:
        t_label = "free flow" if traffic == "free" else "stop-and-go"
        out.append(f"## Tunnel length, flat road, {t_label}\n")
        out.append(
            markdown_table(family_table(records, "geometry", ladder, km, road="flat", traffic=traffic))
        )
        out.append("")
    for traffic in TRAFFIC:
        t_label = "free flow" if traffic == "free" else "stop-and-go"
        for grade in (False, True):
            out.append(f"## Road profile, all geometries, {t_label}, map grade {'on' if grade else 'off'}\n")
            rows_by_road = {}
            for road in ROADS:
                fixed = {"traffic": traffic} | ({} if road == "flat" else {"map_grade": grade})
                rows_by_road[road] = family_table(records, "road", [road], lambda r: r, **fixed)
            rows = [{"estimator": rows_by_road["flat"][i]["estimator"],
                     **{road: rows_by_road[road][i][road] for road in ROADS}}
                    for i in range(len(rows_by_road["flat"]))]  # fmt: skip
            out.append(markdown_table(rows) + "\n")
    names = {p: load_preset(p).name.split(",")[0].split("(")[0].strip() for p in PRESETS}
    for traffic in TRAFFIC:
        t_label = "free flow" if traffic == "free" else "stop-and-go"
        out.append(f"## Presets (real / demo geometry), flat road, {t_label}\n")
        rows = family_table(records, "geometry", PRESETS, names.get, road="flat", traffic=traffic)
        out.append(markdown_table(rows) + "\n")
    return "\n".join(out)


# ---------------------------------------------------------------------- comparison with a baseline
def compare_markdown(records, baseline, meta: dict, base_meta: dict) -> str:
    """Median change of the error at C on the runs both share (same case, information, seed, estimator)."""
    key = lambda r: (r["case"], r["map_grade"], r["seed"], r["estimator"])  # noqa: E731
    base = {key(r): r for r in baseline}
    shared = [(r, base[key(r)]) for r in records if key(r) in base]
    families = [(road, traffic) for road in ROADS for traffic in TRAFFIC]
    rows, regressions = [], []
    for name in _estimators([r for r, _ in shared]):
        row = {"estimator": _label(name)}
        for road, traffic in families:
            pairs = [(r, b) for r, b in shared if r["estimator"] == name and r["road"] == road
                     and r["traffic"] == traffic]  # fmt: skip
            if not pairs:
                row[f"{road} / {traffic}"] = "–"
                continue
            new = np.median([r["exit_total_m"] for r, _ in pairs])
            old = np.median([b["exit_total_m"] for _, b in pairs])
            worse = new - old > max(REGRESSION_ABS_M, REGRESSION_REL * old)
            row[f"{road} / {traffic}"] = f"{old:.0f} → {new:.0f}" + (" ⚠" if worse else "")
            if worse:
                regressions.append(f"{_label(name)}, {road} / {traffic}: {old:.0f} → {new:.0f} m")
        rows.append(row)
    head = [
        "# Benchmark comparison\n",
        f"Baseline: commit `{base_meta.get('commit', '?')}` ({base_meta.get('date', '')}). This run: commit "
        f"`{meta.get('commit', '?')}`. {len(shared)} shared runs. Cells: median error at C [m], baseline → "
        f"this run. ⚠ = worse by more than {100 * REGRESSION_REL:.0f} % and {REGRESSION_ABS_M:g} m.\n",
        markdown_table(rows) + "\n",
        "**Regressions:** " + ("; ".join(regressions) if regressions else "none") + "\n",
    ]
    cases_ = list(dict.fromkeys((r["case"], r["map_grade"]) for r, _ in shared))
    if len(cases_) <= PER_SCENARIO_MAX:
        head += [
            "## Per scenario\n",
            "Error at C [m], median (p90) ✗gross errors, baseline → this run.\n",
            markdown_table(per_scenario_rows(shared, cases_)) + "\n",
        ]
    return "\n".join(head)


PER_SCENARIO_MAX = 12  # compare.md lists every scenario for runs up to this size (development subsets)


def per_scenario_rows(shared, cases_) -> list[dict[str, str]]:
    def cell(rs) -> str:
        gross = sum(gross_error(r) for r in rs)
        return _med_p90([r["exit_total_m"] for r in rs]) + (f" ✗{gross}" if gross else "")

    rows = []
    for name in _estimators([r for r, _ in shared]):
        row = {"estimator": _label(name)}
        for case, grade in cases_:
            pairs = [(r, b) for r, b in shared if r["estimator"] == name and r["case"] == case
                     and r["map_grade"] == grade]  # fmt: skip
            label = case.removeprefix("ladder_").replace("stop_and_go", "s&g") + (" (grade)" if grade else "")
            row[label] = f"{cell([b for _, b in pairs])} → {cell([r for r, _ in pairs])}" if pairs else "–"
        rows.append(row)
    return rows


# ---------------------------------------------------------------------- configuration snapshot
OPTIMISTIC_NOTES = (
    "**The phone is mounted perfectly aligned** with the vehicle (and lever arm 0). Real holders tilt the "
    "phone. This mainly flatters `dr_raw`, whose aligned assumption is then exactly true; the calibrated "
    "estimators estimate the mount anyway.",
    "**No calibration error is injected**: only the natural residual of the approach calibration (from "
    "noise, bias and GPS errors) remains. Real calibrations leave more, and a 0.1° pitch residual costs "
    "hundreds of metres in long outages (calibration_error.md), so the phone-only numbers are likely "
    "optimistic.",
    "**The map is exact** (geometry and grade, user decision): this flatters the route-constrained and "
    "map-grade results (limitations.md).",
    "Earth rotation is off.",
)


def config_snapshot(selected: list[Case], seeds: list[int]) -> dict:
    """The effective scenario configuration of every scenario (run ``seeds[0]``; the seed rule gives
    the others). Route coordinates are left out (source and vertex count instead)."""
    out = {}
    for case in selected:
        cfg = run_config(case, seeds[0])
        d = cfg.model_dump(mode="json")
        d["route"] = {"source": cfg.route.source, "vertices": len(cfg.route.coordinates)}
        out[case.key] = d
    return {
        "seed_rule": "run k: scenario seed 1000 + k; IMU, GPS and traffic seed k",
        "seeds": seeds,
        "shown_for_seed": seeds[0],
        "cases": out,
    }


def _get(d: dict, path: str):
    for part in path.split("."):
        d = d[part]
    return d


def _mount(m: dict) -> str:
    angles = f"yaw {m['yaw_deg']:g}°, pitch {m['pitch_deg']:g}°, roll {m['roll_deg']:g}°"
    return f"{m['label']} ({angles}), lever arm {tuple(m['lever_arm_m'])} m"


def _noise(unit: float, name: str):
    return lambda e: f"{e['noise_density'] / unit:g} {name}" if e["noise_enabled"] else "off"


def _bias(unit: float, name: str):
    def fmt(e: dict) -> str:
        if not e["bias_enabled"]:
            return "off"
        return f"{e['bias_magnitude'] / unit:g} {name}, direction random per seed"

    return fmt


def _drift(unit: float, name: str):
    def fmt(e: dict) -> str:
        if not e["drift_enabled"]:
            return "off"
        return f"on: {e['drift_sigma'] / unit:g} {name}, τ {e['drift_tau_s']:g} s"

    return fmt


def _calibration(c: dict) -> str:
    if not c["enabled"]:
        return "none (only the natural residual of the approach calibration)"
    return f"yaw {c['yaw_deg']:g}°, pitch {c['pitch_deg']:g}°, roll {c['roll_deg']:g}°"


def _gps_position(g: dict) -> str:
    correlated = f"{g['position_sigma_m']:g} m correlated (τ {g['position_tau_s']:g} s)"
    return f"{correlated} + {g['white_sigma_m']:g} m white"


def _degradation(g: dict) -> str:
    if not g["portal_degradation"]:
        return "off"
    return (
        f"on: last {g['degradation_length_m']:g} m before B, up to {g['degradation_sigma_m']:g} m extra "
        f"error at B, {100 * g['outlier_probability']:g} % jump probability"
    )


def _traffic(t: dict) -> str:
    if t["scenario"] == "free":
        return "free flow"
    return (
        f"stop-and-go: {t['stop_count']} stops of {t['stop_min_s']:g}–{t['stop_max_s']:g} s, "
        f"{t['moving_speed_kmh']:g} km/h between, ±{100 * t['jitter']:g} % variation"
    )


def _profile(r: dict) -> str:
    if not r["points"]:
        return "flat"
    profile = ElevationProfile.from_points(r["points"])
    heights = [h for _, h in r["points"]]
    steepest = 100 * profile.max_grade()
    return f"steepest grade {steepest:.1f} %, height {min(heights):+.0f} … {max(heights):+.0f} m"


SNAPSHOT_FIELDS = (
    # (section, label, path in the scenario config, formatter)
    ("Phone IMU", "Phone mount", "imu.mount", _mount),
    ("Phone IMU", "Sample rate", "imu.rate_hz", lambda v: f"{v:g} Hz"),
    ("Phone IMU", "Accelerometer noise", "imu.errors.accel", _noise(UG, "µg/√Hz")),
    ("Phone IMU", "Accelerometer bias", "imu.errors.accel", _bias(MG, "mg")),
    ("Phone IMU", "Accelerometer bias drift", "imu.errors.accel", _drift(MG, "mg")),
    ("Phone IMU", "Gyroscope noise", "imu.errors.gyro", _noise(MDPS, "mdps/√Hz")),
    ("Phone IMU", "Gyroscope bias", "imu.errors.gyro", _bias(DEG, "°/s")),
    ("Phone IMU", "Gyroscope bias drift", "imu.errors.gyro", _drift(MDPS, "mdps")),
    ("Phone IMU", "Gravity / Earth rotation", "imu",
     lambda i: f"{i['gravity_model']} / {'on' if i['earth_rotation'] else 'off'}"),
    ("Phone IMU", "Calibration error (injected)", "calibration", _calibration),
    ("Phone GPS", "Fix rate", "gnss.rate_hz", lambda v: f"{v:g} Hz"),
    ("Phone GPS", "Position error", "gnss", _gps_position),
    ("Phone GPS", "Speed noise", "gnss.speed_sigma_mps", lambda v: f"{v:g} m/s"),
    ("Phone GPS", "Loss before B", "gnss.loss_window_m", lambda v: f"random, up to {v:g} m before B"),
    ("Phone GPS", "Reacquisition after C", "gnss",
     lambda g: f"{g['reacquisition_delay_s']:g} s + 0–{g['reacquisition_jitter_s']:g} s random"),
    ("Phone GPS", "Degradation before the portal", "gnss", _degradation),
    ("Drive and traffic", "Driver", "driver",
     lambda d: f"{d['style']}, cruise {d['cruise_speed_kmh']:g} km/h, ±{d['speed_variability_kmh']:g} km/h"),
    ("Drive and traffic", "Traffic", "traffic", _traffic),
    ("Drive and traffic", "Simulation rate", "sample_rate_hz", lambda v: f"{v:g} Hz"),
    ("Route and map", "Tunnel B–C / announcement", "tunnel",
     lambda t: f"{t['exit_m'] - t['entrance_m']:.0f} m / {t['announce_before_exit_m']:g} m before C"),
    ("Route and map", "Road profile", "road_profile", _profile),
    ("Route and map", "Map", "map_data",
     lambda m: "route polyline, exact; map grade off and on for sloped roads (both evaluated)"),
    ("Route and map", "Car speed reading (reference only)", "vehicle_speed",
     lambda v: f"{v['scale_error_pct']:+g} % scale error, {v['rate_hz']:g} Hz"),
)  # fmt: skip


def _scenario_groups(keys: list[str]) -> str:
    """'ladder_2km, seattle_sr99_tunnel' (+ the roads/traffic if not all of them)."""
    geometries = ", ".join(sorted({k.split("/")[0] for k in keys}))
    roads = sorted({k.split("/")[1] for k in keys})
    traffic = sorted({k.split("/")[2] for k in keys})
    extra = [", ".join(roads)] if len(roads) < len(ROADS) else []
    extra += [", ".join(traffic)] if len(traffic) < len(TRAFFIC) else []
    return geometries + (f" ({'; '.join(extra)})" if extra else "")


def config_markdown(snapshot: dict, meta: dict, group=None, notes=OPTIMISTIC_NOTES, title="Benchmark") -> str:
    """Readable summary: values shared by all scenarios, then the ones that differ (by scenario).
    ``group`` turns a list of scenario keys into a short description (default: geometry/road/traffic)."""
    group = group or _scenario_groups
    cases_ = snapshot["cases"]
    out = [
        f"# {title} configuration\n",
        f"The settings behind `runs.csv` in this directory (commit `{meta.get('commit', '?')}`). "
        f"{len(cases_)} scenarios × {len(snapshot['seeds'])} runs. Seed rule: {snapshot['seed_rule']}. "
        "The complete effective configuration of every scenario is in `config.json`.\n",
    ]
    rows: list[dict[str, str]] = []
    varying: list[tuple[str, dict[str, str]]] = []
    section = None
    for sec, label, path, fmt in SNAPSHOT_FIELDS:
        if sec != section:
            if rows:
                out.append(markdown_table(rows) + "\n")
                rows = []
            section = sec
            out.append(f"## {sec}\n")
        values = {key: fmt(_get(cfg, path)) for key, cfg in cases_.items()}
        distinct = sorted(set(values.values()))
        if len(distinct) == 1:
            rows.append({"setting": label, "value": distinct[0]})
        else:
            rows.append({"setting": label, "value": "differs by scenario (below)"})
            varying.append((label, values))
    if rows:
        out.append(markdown_table(rows) + "\n")
    for label, values in varying:
        out.append(f"### {label} by scenario\n")
        groups: dict[str, list[str]] = {}
        for key, value in values.items():
            groups.setdefault(value, []).append(key)
        table = [{"value": v, "scenarios": group(keys)} for v, keys in groups.items()]
        out.append(markdown_table(table) + "\n")
    if notes:
        out.append("## Where this setup is optimistic\n")
        out += [f"{i}. {note}" for i, note in enumerate(notes, 1)]
        out.append("")
    return "\n".join(out)


def write_config(out_dir: Path, selected: list[Case], seeds: list[int], meta: dict) -> None:
    snapshot = config_snapshot(selected, seeds)
    (out_dir / "config.json").write_text(json.dumps(snapshot, indent=1), encoding="utf-8")
    (out_dir / "config.md").write_text(config_markdown(snapshot, meta), encoding="utf-8")


# ---------------------------------------------------------------------- I/O
TEXT = ("case", "geometry", "road", "traffic", "estimator")
FLAGS = ("map_grade", "announcement_missed", "route_end_reached")


def write_runs(records, path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        # full precision: a baseline must compare exactly against later runs
        for r in records:
            writer.writerow({k: (repr(float(v)) if isinstance(v, float) else v) for k, v in r.items()})


def read_runs(path: Path, text: tuple[str, ...] = TEXT) -> list[dict]:
    """Records of a ``runs.csv``; ``text`` = the columns kept as strings (others: flags, seed, floats)."""
    out = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rec: dict = {}
            for k, v in row.items():
                if k in text:
                    rec[k] = v
                elif k in FLAGS:
                    rec[k] = v == "True"
                elif k == "seed":
                    rec[k] = int(v)
                else:
                    rec[k] = float(v)
            out.append(rec)
    return out


def git_commit() -> str:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        )
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True,
                               text=True, check=True).stdout.strip()  # fmt: skip
        return sha.stdout.strip() + ("+dirty" if dirty else "")
    except OSError, subprocess.CalledProcessError:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=20, help="runs per scenario")
    parser.add_argument("--quick", action="store_true", help=f"{QUICK_SEEDS} runs per scenario")
    parser.add_argument("--dev", action="store_true", help="development subset: DEV_CASES, map grade on, "
                        "DEV_ESTIMATORS")  # fmt: skip
    parser.add_argument("--cases", default="", help="only scenarios whose key contains this text")
    parser.add_argument("--workers", type=int, default=2, help="parallel processes (memory: ~0.5 GB each)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", default="", help="free text recorded with the run")
    parser.add_argument("--compare", type=Path, default=None, help="baseline directory to compare against")
    parser.add_argument("--from-csv", action="store_true", help="regenerate the tables from --out/runs.csv")
    parser.add_argument(
        "--write-config", action="store_true", help="(re)write config.md / config.json for the run in --out"
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if args.from_csv:
        records = read_runs(args.out / "runs.csv")
        meta = json.loads((args.out / "meta.json").read_text(encoding="utf-8"))
    else:
        seeds = list(range(QUICK_SEEDS if args.quick else args.seeds))
        selected = [c for c in cases() if args.cases in c.key and (not args.dev or c.key in DEV_CASES)]
        n = len(selected)
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(run_case, selected, [seeds] * n, [args.dev] * n))
        records = [r for recs in results for r in recs]
        meta = {
            "commit": git_commit(), "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "label": args.label, "seeds": seeds, "cases": [c.key for c in selected], "dev": args.dev,
            "estimators": list(DEV_ESTIMATORS if args.dev else ESTIMATORS),
            "runtime_s": round(time.perf_counter() - t0),
        }  # fmt: skip
        write_runs(records, args.out / "runs.csv")
        (args.out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
        write_config(args.out, selected, seeds, meta)
    if args.write_config:
        selected = [c for c in cases() if c.key in set(meta["cases"])]
        write_config(args.out, selected, meta["seeds"], meta)
        print("wrote", args.out / "config.md")
    (args.out / "tables.md").write_text(tables_markdown(records, meta), encoding="utf-8")
    print("wrote", args.out / "tables.md")
    if args.compare is not None:
        baseline = read_runs(args.compare / "runs.csv")
        base_meta = json.loads((args.compare / "meta.json").read_text(encoding="utf-8"))
        (args.out / "compare.md").write_text(
            compare_markdown(records, baseline, meta, base_meta), encoding="utf-8"
        )
        print("wrote", args.out / "compare.md")
    print(f"{len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
