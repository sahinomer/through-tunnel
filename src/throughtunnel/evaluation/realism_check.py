"""Realism check (D38): do IMU bias drift and GPS degradation before the portal change the conclusions?

Paired runs on every preset: the realistic default sensors as the baseline, then + bias drift
(accelerometer and gyroscope, default σ and correlation time), + GPS portal degradation (defaults),
and both. Free flow and stop-and-go (long outage). Run k uses seed k for sensors, GPS and traffic in
every condition, so each difference is caused by the added effect alone.

    uv run python -m throughtunnel.evaluation.realism_check --seeds 10 --out docs/realism_check
"""

from __future__ import annotations

import argparse
import csv
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from throughtunnel.evaluation.experiment import markdown_table
from throughtunnel.evaluation.slope_study import realistic_sensors
from throughtunnel.evaluation.traffic_study import run_records
from throughtunnel.positioning import ESTIMATORS
from throughtunnel.scenario import list_presets, load_preset, run_scenario, with_sensor_config
from throughtunnel.vehicle.traffic import TrafficConfig

CONDITIONS = {
    "baseline": "Realistic defaults (noise, bias, GPS errors)",
    "drift": "+ IMU bias drift",
    "degradation": "+ GPS degradation before B",
    "both": "+ both",
}
TRAFFIC = ("free", "stop_and_go")


def condition_sensors(cfg, condition: str, seed: int):
    imu, gnss = realistic_sensors(cfg, seed)
    if condition in ("drift", "both"):
        e = imu.errors
        errors = e.model_copy(update={
            "accel": e.accel.model_copy(update={"drift_enabled": True}),
            "gyro": e.gyro.model_copy(update={"drift_enabled": True}),
        })  # fmt: skip
        imu = imu.model_copy(update={"errors": errors})
    if condition in ("degradation", "both"):
        gnss = gnss.model_copy(update={"portal_degradation": True})
    return imu, gnss


def study_preset(preset_id: str, seeds: list[int]) -> list[dict]:
    cfg = load_preset(preset_id)
    records = []
    for traffic in TRAFFIC:
        print(f"{preset_id}: {traffic}", flush=True)
        for k in seeds:
            base = run_scenario(cfg.model_copy(update={"traffic": TrafficConfig(scenario=traffic, seed=k)}))
            for condition in CONDITIONS:
                imu, gnss = condition_sensors(cfg, condition, k)
                res = with_sensor_config(base, imu=imu, gnss=gnss)
                tag = {"preset": preset_id, "traffic": traffic, "condition": condition, "seed": k}
                records.extend(run_records(res, tag))
    return records


def table(records, preset: str, traffic: str) -> list[dict[str, str]]:
    rows = []
    here = [r for r in records if r["preset"] == preset and r["traffic"] == traffic]
    base = {(r["seed"], r["estimator"]): r for r in here if r["condition"] == "baseline"}
    for cond, label in CONDITIONS.items():
        row = {"condition": label}
        for name in ESTIMATORS:
            sel = [r for r in records if r["preset"] == preset and r["traffic"] == traffic
                   and r["condition"] == cond and r["estimator"] == name]  # fmt: skip
            err = np.array([r["exit_total_m"] for r in sel])
            cell = f"{np.median(err):.0f}"
            if cond != "baseline":
                # Size of the paired shift of the error vector at C (along, cross): how far the added
                # effect moves each run's estimate, whatever the sign of the error it starts from.
                pairs = [(r, base[(r["seed"], name)]) for r in sel]
                d_along = [r["exit_along_m"] - q["exit_along_m"] for r, q in pairs]
                d_cross = [r["exit_cross_m"] - q["exit_cross_m"] for r, q in pairs]
                shift = np.hypot(d_along, d_cross)
                cell += f" (shift {np.median(shift):.0f} / {np.percentile(shift, 90):.0f})"
            if any(r["route_end_reached"] for r in sel):
                cell = "≥" + cell
            row[name] = cell
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--presets", nargs="*", default=list(list_presets()))
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--out", type=Path, default=Path("docs/realism_check"))
    args = parser.parse_args()
    seeds = list(range(args.seeds))
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(study_preset, args.presets, [seeds] * len(args.presets)))
    records = [r for recs in results for r in recs]
    out = [
        "# Realism check: bias drift and GPS degradation before the portal\n",
        f"Median error at C [m] over {len(seeds)} paired runs (seed k for sensors, GPS and traffic in every "
        "condition). In brackets: the size of the paired shift of the error vector at C caused by the added "
        "effect, median / p90 [m] (how far it moves each run's estimate, independent of the sign of the "
        "error it starts from). ≥ = a route estimator reached the route end D in some runs (its error is "
        "then capped).\n",
    ]
    for pid in args.presets:
        for traffic in TRAFFIC:
            out.append(f"## {load_preset(pid).name}: {traffic.replace('_', '-')}\n")
            out.append(markdown_table(table(records, pid, traffic)) + "\n")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "tables.md").write_text("\n".join(out), encoding="utf-8")
    with open(args.out / "runs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(
            {k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()} for r in records
        )
    print(f"wrote {args.out / 'tables.md'}; {len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
