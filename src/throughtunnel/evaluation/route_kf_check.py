"""Paired check of the two route Kalman filters on fresh seeds (step 4.1): ``route_kf`` vs. ``route_kf_yaw``.

The development subsets (D47) use seeds 0–19, and a stop-and-go median over 20 runs is fragile: the v ≥ 0
clamp (P5) makes the outcome depend on the sign of a small offset error. This reruns error-source
conditions on another seed range with both filters on identical observations:
* ``first``: ``route_kf`` (D51);
* ``yaw``: ``route_kf_yaw`` (yaw state, D52).

    uv run python -m throughtunnel.evaluation.route_kf_check --out docs/route_kalman_yaw/fresh_seeds \
        --conditions realistic --first-seed 20 --seeds 60
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
from throughtunnel.evaluation.benchmark import _med_p90, git_commit, gross_error, read_runs, write_runs
from throughtunnel.evaluation.experiment import markdown_table
from throughtunnel.evaluation.metrics import evaluate_track
from throughtunnel.positioning.alignment import GpsImuAlignment
from throughtunnel.positioning.route_kalman import RouteKalman, RouteKalmanYaw
from throughtunnel.positioning.runner import align_imu, replay
from throughtunnel.scenario import run_scenario

TEXT = ("case", "condition", "traffic", "variant")

VARIANTS = {"first": RouteKalman, "yaw": RouteKalmanYaw}


def _job(args: tuple[str, str, list[int]]) -> list[dict]:
    key, traffic, seeds = args
    out = []
    for seed in seeds:
        res = run_scenario(es.run_config(es.BY_KEY[key], seed, traffic))
        obs = res.observations()
        stream = align_imu(GpsImuAlignment(obs.route, res.config.calibration.rotation_error()), obs)
        for name, cls in VARIANTS.items():
            ev = evaluate_track(replay(cls(obs.route), obs, stream), res)
            out.append({
                "case": f"{key}/{traffic}", "condition": key, "traffic": traffic, "seed": seed,
                "variant": name,
                "exit_total_m": ev.summary["exit_total_m"], "exit_along_m": ev.summary["exit_along_m"],
                "tunnel_max_m": ev.summary["tunnel_max_m"],
            })  # fmt: skip
    print(f"{key}/{traffic}: {len(seeds)} runs", flush=True)
    return out


def tables_markdown(records: list[dict], meta: dict) -> str:
    out = [
        "# Route Kalman filters on fresh seeds: route_kf (first) vs. route_kf_yaw (yaw)\n",
        f"Commit `{meta['commit']}`, {meta['date']}; seeds {meta['seeds'][0]}–{meta['seeds'][-1]}. "
        "Error at C, median (p90) [m], ✗ = gross errors (> 200 m). Paired: runs where the yaw state is "
        "worse / better / within 1 m (capped runs end at the same point).\n",
    ]
    rows = []
    for case in dict.fromkeys(r["case"] for r in records):
        by = {v: {r["seed"]: r for r in records if r["case"] == case and r["variant"] == v} for v in VARIANTS}
        seeds = sorted(by["first"])
        diff = np.array([by["yaw"][s]["exit_total_m"] - by["first"][s]["exit_total_m"] for s in seeds])
        worse, better = int(np.sum(diff > 1.0)), int(np.sum(diff < -1.0))
        # two-sided sign test on the runs that differ
        n = worse + better
        p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(worse, better) + 1)) / 2**n) if n else 1.0
        row = {"case": case, "runs": str(len(seeds))}
        for v in VARIANTS:
            rs = list(by[v].values())
            row[v] = f"{_med_p90([r['exit_total_m'] for r in rs])} ✗{sum(gross_error(r) for r in rs)}"
        row["paired worse / better / same"] = f"{worse} / {better} / {len(seeds) - n}"
        row["sign test p"] = f"{p:.2f}"
        row["median paired change [m]"] = f"{np.median(diff):+.0f}"
        rows.append(row)
    out.append(markdown_table(rows) + "\n")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--conditions", default="realistic", help="comma-separated error-source conditions")
    parser.add_argument("--first-seed", type=int, default=20)
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--from-csv", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if args.from_csv:
        records = read_runs(args.out / "runs.csv", text=TEXT)
        meta = json.loads((args.out / "meta.json").read_text(encoding="utf-8"))
    else:
        seeds = list(range(args.first_seed, args.first_seed + args.seeds))
        chunks = [seeds[i : i + 10] for i in range(0, len(seeds), 10)]
        jobs = [(c, t, ch) for c in args.conditions.split(",") for t in es.TRAFFIC for ch in chunks]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            records = [r for recs in pool.map(_job, jobs) for r in recs]
        records.sort(key=lambda r: (r["case"], r["seed"], r["variant"]))
        meta = {
            "commit": git_commit(),
            "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "seeds": seeds,
            "conditions": args.conditions.split(","),
            "runtime_s": round(time.perf_counter() - t0),
        }
        write_runs(records, args.out / "runs.csv")
        (args.out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    (args.out / "tables.md").write_text(tables_markdown(records, meta), encoding="utf-8")
    print(f"wrote {args.out / 'tables.md'}; {len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
