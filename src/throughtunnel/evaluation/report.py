"""Reproducible comparison of all estimators on the bundled presets.

    uv run python -m throughtunnel.evaluation.report --seeds 20 > results.md

Every Monte-Carlo run draws new IMU and GPS error realisations (sensor seed = GPS seed = run index);
with ``--vary-drive`` each run also gets a new drive (driver seed 1000 + run index), otherwise the
preset's drive is kept. All estimators see identical observations in each run (D19).
"""

from __future__ import annotations

import argparse
import time

from throughtunnel.evaluation.experiment import markdown_table, monte_carlo, summary_rows
from throughtunnel.scenario import list_presets, load_preset, run_scenario


def report(
    preset_ids: list[str], seeds: range, names: list[str] | None = None, vary_drive: bool = False
) -> str:
    out = []
    for pid in preset_ids:
        cfg = load_preset(pid)
        base = run_scenario(cfg)
        rm, sec = base.route_map, base.sections
        t0 = time.perf_counter()
        runs = monte_carlo(cfg, seeds, names, vary_drive=vary_drive)
        out.append(f"### {cfg.name}\n")
        out.append(
            f"Tunnel B–C {(rm.tunnel_exit_m - rm.tunnel_entrance_m) / 1000:.2f} km, crossed in "
            f"{sec.exit_t - sec.entrance_t:.0f} s (preset drive); {len(seeds)} runs, "
            f"{'a new drive per run, ' if vary_drive else 'same drive, '}(sensor/GPS seeds "
            f"{seeds.start}–{seeds.stop - 1}), median (90th percentile) of absolute values; announcement "
            f"columns also give the signed mean (+ = late). Computed in {time.perf_counter() - t0:.0f} s.\n"
        )
        out.append(markdown_table(summary_rows(runs)) + "\n")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=20, help="number of Monte-Carlo runs per preset")
    parser.add_argument("--presets", nargs="*", default=list(list_presets()))
    parser.add_argument("--estimators", nargs="*", default=None)
    parser.add_argument("--vary-drive", action="store_true", help="new driver speed profile in every run")
    args = parser.parse_args()
    print(report(args.presets, range(args.seeds), args.estimators, args.vary_drive))


if __name__ == "__main__":
    main()
