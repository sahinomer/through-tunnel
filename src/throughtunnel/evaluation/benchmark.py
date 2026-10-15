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
tables). A run "fails" if the estimate reaches the route end D before C (its error is then capped by
the route length) or the exit announcement is missed.

    uv run python -m throughtunnel.evaluation.benchmark --seeds 20 --out docs/benchmark/baseline
    uv run python -m throughtunnel.evaluation.benchmark --quick --out <dir> --compare docs/benchmark/baseline

``--quick`` = 5 seeds (development). ``--compare`` writes ``compare.md``: per estimator and scenario
family, the median change of the error at C against the baseline on the shared runs, with regressions
flagged. ``--from-csv`` regenerates the tables of an existing output directory.
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
REGRESSION_REL, REGRESSION_ABS_M = 0.10, 5.0  # flagged if the median gets worse by both
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
def run_case(case: Case, seeds: list[int]) -> list[dict]:
    records = []
    grades = (False,) if case.road == "flat" else (False, True)
    for seed in seeds:
        res = run_scenario(run_config(case, seed))
        c_t, length = res.sections.exit_t, res.route_map.length_m
        outage = res.gnss_events.reacquire_t - res.gnss_events.loss_t
        for grade in grades:
            cmp = compare_estimators(with_map_data(res, MapDataConfig(road_grade=grade)))
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


def _failed(r) -> bool:
    return r["route_end_reached"] or r["announcement_missed"]


def _label(name: str) -> str:
    return ESTIMATORS[name].label if name in ESTIMATORS else name


def _estimators(records) -> list[str]:
    present = {r["estimator"] for r in records}
    return [n for n in ESTIMATORS if n in present] + sorted(present - set(ESTIMATORS))


def overall_table(records) -> list[dict[str, str]]:
    rows = []
    for name in _estimators(records):
        sel = _sel(records, estimator=name)
        off = [r for r in sel if not r["map_grade"]]  # flat runs + sloped runs without map grade
        on = [r for r in sel if r["road"] == "flat" or r["map_grade"]]
        ann = np.array([r["announcement_error_s"] for r in off], dtype=float)
        row = {"estimator": _label(name) + (" †" if name in REFERENCE_ESTIMATORS else "")}
        row["error at C, map grade off [m]"] = _med_p90([r["exit_total_m"] for r in off])
        row["error at C, map grade on [m]"] = _med_p90([r["exit_total_m"] for r in on])
        row["max in tunnel [m]"] = _med_p90([r["tunnel_max_m"] for r in off])
        row["announcement within ±3 s"] = f"{100 * np.mean(np.abs(ann) <= ANNOUNCE_OK_S):.0f} %"
        row["failed runs"] = f"{100 * np.mean([_failed(r) for r in off]):.1f} %"
        rows.append(row)
    return rows


def family_table(records, column: str, values, label=str, **fixed) -> list[dict[str, str]]:
    """Median (p90) error at C per estimator for each value of ``column`` (other columns fixed)."""
    rows = []
    for name in _estimators(records):
        row = {"estimator": _label(name) + (" †" if name in REFERENCE_ESTIMATORS else "")}
        for v in values:
            sel = _sel(records, estimator=name, **{column: v}, **fixed)
            cell = _med_p90([r["exit_total_m"] for r in sel])
            failed = sum(_failed(r) for r in sel)
            row[label(v)] = cell + (f" ✗{failed}" if failed else "")
        rows.append(row)
    return rows


def tables_markdown(records, meta: dict) -> str:
    n_seeds = len({r["seed"] for r in records})
    out = [
        "# Benchmark: generated tables\n",
        f"{meta.get('label', '')} · commit `{meta.get('commit', '?')}` · {meta.get('date', '')} · "
        f"{len({r['case'] for r in records})} scenarios × {n_seeds} runs. Cells: error at C [m], median "
        "(p90). ✗n = n failed runs (route end reached before C, or announcement missed). † = reference "
        "estimator (uses the car's speed reading; not a phone-only solution). Realism options on (bias "
        "drift, GPS degradation before the portal).\n",
        "## Overall\n",
        "Flat roads are counted in both error columns (the map grade changes nothing there); the other "
        "columns use the runs without map grade.\n",
        markdown_table(overall_table(records)) + "\n",
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
    return "\n".join(head)


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


def read_runs(path: Path) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rec: dict = {}
            for k, v in row.items():
                if k in TEXT:
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
    parser.add_argument("--cases", default="", help="only scenarios whose key contains this text")
    parser.add_argument("--workers", type=int, default=2, help="parallel processes (memory: ~0.5 GB each)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", default="", help="free text recorded with the run")
    parser.add_argument("--compare", type=Path, default=None, help="baseline directory to compare against")
    parser.add_argument("--from-csv", action="store_true", help="regenerate the tables from --out/runs.csv")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if args.from_csv:
        records = read_runs(args.out / "runs.csv")
        meta = json.loads((args.out / "meta.json").read_text(encoding="utf-8"))
    else:
        seeds = list(range(QUICK_SEEDS if args.quick else args.seeds))
        selected = [c for c in cases() if args.cases in c.key]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(run_case, selected, [seeds] * len(selected)))
        records = [r for recs in results for r in recs]
        meta = {
            "commit": git_commit(), "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "label": args.label, "seeds": seeds, "cases": [c.key for c in selected],
            "estimators": list(ESTIMATORS), "runtime_s": round(time.perf_counter() - t0),
        }  # fmt: skip
        write_runs(records, args.out / "runs.csv")
        (args.out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
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
