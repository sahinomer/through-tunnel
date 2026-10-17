"""Uncertainty consistency check (step 6.1 of docs/estimator_plan.md): is ``position_std_m`` honest?

Diagnostic only, no estimator change. The Kalman filters report a 1σ along-route uncertainty; an
uncertainty-aware announcement (3d) can only rely on it if the true along-track error stays within ±1σ
about 68 % of the time and within ±2σ about 95 %. Checked for ``route_kf`` and ``route_kf_yaw``:
* at the true announcement time (300 m before C: what the announcement would rely on), at C, at fixed
  distances into the tunnel, and over all output samples of the GPS outage;
* on error-source conditions (5 km flat tunnel: floor, realistic, GPS speed noise, accelerometer bias
  drift, calibration pitch 0.1° and yaw 2°) and benchmark scenarios (2 km flat, 5 km climb and
  underwater with map grade), free flow and stop-and-go, 20 seeds.

Per run and estimator, ``runs.csv`` holds the along-track error and σ at each checkpoint and the outage
coverage, so other summaries can be produced with ``--from-csv``.

    uv run python -m throughtunnel.evaluation.uncertainty_study --out docs/uncertainty_study
"""

from __future__ import annotations

import argparse
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from throughtunnel.evaluation import error_sources as es
from throughtunnel.evaluation.benchmark import Case, git_commit, read_runs, write_runs
from throughtunnel.evaluation.benchmark import run_config as benchmark_run_config
from throughtunnel.evaluation.experiment import compare_estimators, markdown_table
from throughtunnel.scenario import MapDataConfig, run_scenario, with_map_data

ESTIMATORS = ("route_kf", "route_kf_yaw", "route_kf_map")  # default; --estimators to choose
ES_CONDITIONS = ("floor", "realistic", "gps_speed", "acc_drift", "cal_pitch_0.1", "cal_yaw_2")
BENCH_CASES = (("ladder_2km", "flat"), ("ladder_5km", "climb3"), ("ladder_5km", "underwater"))
TRAFFIC = ("free", "stop_and_go")
CHECKPOINTS_KM = (0.5, 1.0, 2.0, 3.0, 4.0)
TEXT = ("case", "source", "scenario", "traffic", "estimator")


def _records(res, source: str, scenario: str, traffic: str, seed: int, names: list[str]) -> list[dict]:
    sec, ev_gnss, motion = res.sections, res.gnss_events, res.motion
    points = {"announce": sec.announcement_t, "exit": sec.exit_t}
    for km in CHECKPOINTS_KM:
        s = sec.entrance_s + 1000.0 * km
        if s < sec.exit_s:
            points[f"{km:g}km"] = float(np.interp(s, motion.s, motion.t))
    out = []
    cmp = compare_estimators(res, names)
    for ev in cmp.evaluations:
        std = ev.position_std_m
        rec = {
            "case": f"{scenario}/{traffic}", "source": source, "scenario": scenario, "traffic": traffic,
            "seed": seed, "estimator": ev.name, "outage_s": ev_gnss.reacquire_t - ev_gnss.loss_t,
        }  # fmt: skip
        for key in ("announce", "exit", *(f"{km:g}km" for km in CHECKPOINTS_KM)):
            t = points.get(key, math.nan)
            ok = math.isfinite(t) and ev.t[0] <= t <= ev.t[-1]
            rec[f"along_{key}_m"] = float(np.interp(t, ev.t, ev.along)) if ok else math.nan
            rec[f"std_{key}_m"] = float(np.interp(t, ev.t, std)) if ok else math.nan
        outage = (ev.t >= ev_gnss.loss_t) & (ev.t < ev_gnss.reacquire_t)
        z = np.abs(ev.along[outage]) / np.maximum(std[outage], 1e-9)
        rec["outage_cov1"] = float(np.mean(z <= 1.0))
        rec["outage_cov2"] = float(np.mean(z <= 2.0))
        out.append(rec)
    return out


def _job(args: tuple[str, str, str, str, list[int], list[str]]) -> list[dict]:
    source, scenario, road, traffic, seeds, names = args
    out = []
    for seed in seeds:
        if source == "error_sources":
            res = run_scenario(es.run_config(es.BY_KEY[scenario], seed, traffic))
        else:
            res = run_scenario(benchmark_run_config(Case(scenario, road, traffic), seed))
            res = with_map_data(res, MapDataConfig(road_grade=road != "flat"))
            scenario_key = f"{scenario}/{road}"
        key = scenario if source == "error_sources" else scenario_key
        out += _records(res, source, key, traffic, seed, names)
    print(f"{source}: {scenario}/{road}/{traffic}: {len(seeds)} runs", flush=True)
    return out


# ---------------------------------------------------------------------- analysis
def _cov(records, key: str) -> tuple[str, str, str, str]:
    """Coverage within 1σ and 2σ, rms of error/σ, and median |error| / median σ at one checkpoint."""
    a = np.array([r[f"along_{key}_m"] for r in records], float)
    s = np.array([r[f"std_{key}_m"] for r in records], float)
    ok = np.isfinite(a) & np.isfinite(s)
    if not ok.any():
        return "–", "–", "–", "–"
    a, s = a[ok], s[ok]
    z = np.abs(a) / np.maximum(s, 1e-9)
    return (
        f"{100 * np.mean(z <= 1):.0f} %",
        f"{100 * np.mean(z <= 2):.0f} %",
        f"{np.sqrt(np.mean(z**2)):.1f}",
        f"{np.median(np.abs(a)):.0f} / {np.median(s):.0f}",
    )


def tables_markdown(records: list[dict], meta: dict) -> str:
    out = [
        "# Uncertainty consistency: tables\n",
        f"Commit `{meta['commit']}`, {meta['date']}; {len(meta['seeds'])} seeds per case. Coverage = "
        "share of runs whose along-track error lies within ±1σ / ±2σ of the filter's own uncertainty "
        "(honest: ~68 % / ~95 %). rms z = rms of error/σ (honest: ~1; > 1 = overconfident). "
        "|err| / σ: medians [m].\n",
    ]
    cases = list(dict.fromkeys(r["case"] for r in records))
    for name in dict.fromkeys(r["estimator"] for r in records):
        out.append(f"## {name}\n")
        out.append("### At the announcement point (true time) and at C\n")
        rows = []
        for case in cases:
            sel = [r for r in records if r["case"] == case and r["estimator"] == name]
            a1, a2, az, am = _cov(sel, "announce")
            c1, c2, cz, cm = _cov(sel, "exit")
            rows.append({
                "case": case, "announce 1σ / 2σ": f"{a1} / {a2}", "announce rms z": az,
                "announce |err| / σ": am,
                "C 1σ / 2σ": f"{c1} / {c2}", "C rms z": cz, "C |err| / σ": cm,
                "outage samples 1σ / 2σ": f"{100 * np.mean([r['outage_cov1'] for r in sel]):.0f} % / "
                f"{100 * np.mean([r['outage_cov2'] for r in sel]):.0f} %",
            })  # fmt: skip
        out.append(markdown_table(rows) + "\n")
        out.append("### Growth: rms z by distance into the tunnel\n")
        rows = []
        for case in cases:
            sel = [r for r in records if r["case"] == case and r["estimator"] == name]
            row = {"case": case}
            for km in CHECKPOINTS_KM:
                row[f"{km:g} km"] = _cov(sel, f"{km:g}km")[2]
            row["C"] = _cov(sel, "exit")[2]
            rows.append(row)
        out.append(markdown_table(rows) + "\n")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--from-csv", action="store_true")
    parser.add_argument("--estimators", default=",".join(ESTIMATORS), help="comma-separated")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if args.from_csv:
        records = read_runs(args.out / "runs.csv", text=TEXT)
        meta = json.loads((args.out / "meta.json").read_text(encoding="utf-8"))
    else:
        seeds = list(range(args.seeds))
        names = args.estimators.split(",")
        jobs = [("error_sources", c, "flat", t, seeds, names) for c in ES_CONDITIONS for t in TRAFFIC]
        jobs += [("benchmark", g, road, t, seeds, names) for g, road in BENCH_CASES for t in TRAFFIC]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            records = [r for recs in pool.map(_job, jobs) for r in recs]
        meta = {
            "commit": git_commit(),
            "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "seeds": seeds,
            "error_sources": list(ES_CONDITIONS),
            "benchmark": [f"{g}/{road}" for g, road in BENCH_CASES],
            "estimators": names,
            "runtime_s": round(time.perf_counter() - t0),
        }
        write_runs(records, args.out / "runs.csv")
        (args.out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    (args.out / "tables.md").write_text(tables_markdown(records, meta), encoding="utf-8")
    print(f"wrote {args.out / 'tables.md'}; {len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
