"""Figures of the write-up (docs/report.md), drawn from saved benchmark runs; no simulation is run.

* ``report_tunnel_length.png``: median error at the tunnel exit vs. tunnel length (flat synthetic
  tunnels), free flow and stop-and-go, for the final estimators carried into the report's results,
  all from the final milestone run.

    uv run python -m throughtunnel.evaluation.report_figures --out docs/img
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

from throughtunnel.app.positioning_view import ESTIMATOR_STYLES
from throughtunnel.evaluation.factor_study import GRID, INK, INK_2, SURFACE

FINAL = Path("docs/benchmark/milestone_step5/benchmark/runs.csv")
LENGTHS_KM = (0.5, 1, 2, 3, 5)
TRAFFIC = {"free": "Free flow", "stop_and_go": "Stop-and-go"}
GROSS_ERROR_M = 200.0
MPL_DASH = {"solid": "-", "dash": (0, (5, 2.5)), "dot": (0, (1, 2))}

# (label, estimator, line style, traffic cases); drawn in this order.
SERIES = (
    ("Route + IMU", "route_imu", "solid", ("free", "stop_and_go")),
    ("Kalman filter", "route_kf", "solid", ("free", "stop_and_go")),
    ("Kalman filter + map curves", "route_kf_map", "solid", ("free", "stop_and_go")),
    ("Route + IMU + standstill (oracle)", "route_imu_zupt", "dot", ("stop_and_go",)),
    ("Route + car speed (reference)", "route_vspeed", "solid", ("free", "stop_and_go")),
)


def ladder_medians(path: Path) -> dict[tuple[str, str], list[float]]:
    """(estimator, traffic) -> median exit error per tunnel length, flat ladder tunnels."""
    errors: dict[tuple[str, str, float], list[float]] = defaultdict(list)
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            if not row["geometry"].startswith("ladder_") or row["road"] != "flat":
                continue
            km = float(row["geometry"].removeprefix("ladder_").removesuffix("km"))
            errors[(row["estimator"], row["traffic"], km)].append(float(row["exit_total_m"]))
    return {
        (est, traffic): [float(np.median(errors[(est, traffic, km)])) for km in LENGTHS_KM]
        for est, traffic, _ in errors
    }


def spread_labels(values: list[float], min_gap_decades: float = 0.14) -> list[float]:
    """End-label heights on a log axis, pushed apart so that no two overlap."""
    order = np.argsort(values)
    logs = np.log10(np.asarray(values, dtype=float)[order])
    for i in range(1, len(logs)):  # bottom to top: move a label up until it clears the one below
        logs[i] = max(logs[i], logs[i - 1] + min_gap_decades)
    out = np.empty_like(logs)
    out[order] = 10**logs
    return out.tolist()


def plot_tunnel_length(out: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    medians = ladder_medians(FINAL)
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2), sharey=True, facecolor=SURFACE)
    handles = {}
    for ax, (traffic, title) in zip(axes, TRAFFIC.items(), strict=True):
        ax.set_facecolor(SURFACE)
        ax.axhline(GROSS_ERROR_M, color=INK_2, lw=0.8, ls=(0, (4, 3)), zorder=1)
        ax.text(0.47, GROSS_ERROR_M * 1.08, "gross error (200 m)", color=INK_2, fontsize=8)
        ends = []
        for label, est, dash, cases in SERIES:
            if traffic not in cases:
                continue
            y = medians[(est, traffic)]
            (line,) = ax.plot(
                LENGTHS_KM, y, color=ESTIMATOR_STYLES[est][0], ls=MPL_DASH[dash], lw=2,
                marker="o", ms=5, mec=SURFACE, mew=1.5, solid_capstyle="round", zorder=3,
            )  # fmt: skip
            handles[label] = line
            ends.append(y[-1])
        for value, y_label in zip(ends, spread_labels(ends), strict=True):
            ax.text(LENGTHS_KM[-1] + 0.12, y_label, f"{value:.0f} m", va="center", fontsize=8.5, color=INK)
        ax.set_title(title, loc="left", fontsize=11, color=INK)
        ax.set_yscale("log")
        ax.set_ylim(1, 1000)
        ax.set_xlim(0.3, 5.6)
        ax.set_xticks(LENGTHS_KM, [f"{km:g}" for km in LENGTHS_KM])
        ax.set_yticks([1, 10, 100, 1000], ["1 m", "10 m", "100 m", "1 km"])
        ax.set_xlabel("tunnel length [km]", color=INK_2, fontsize=9)
        ax.grid(True, which="major", color=GRID, lw=0.8)
        ax.tick_params(which="both", colors=INK_2, labelsize=9, length=0)
        for side in ("top", "right", "left", "bottom"):
            ax.spines[side].set_visible(False)
    axes[0].set_ylabel("error at the tunnel exit (median of 20 runs)", color=INK_2, fontsize=9)
    fig.legend(
        handles.values(), handles.keys(), loc="lower center", ncol=3, frameon=False, fontsize=9,
        labelcolor=INK, handlelength=2.6,
    )  # fmt: skip
    fig.tight_layout(rect=(0, 0.14, 1, 1))
    out.mkdir(parents=True, exist_ok=True)
    path = out / "report_tunnel_length.png"
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path("docs/img"))
    print(plot_tunnel_length(parser.parse_args().out))


if __name__ == "__main__":
    main()
