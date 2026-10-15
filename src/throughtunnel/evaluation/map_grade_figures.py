"""Figures of the map-grade study (D39); palette and styling as in the other studies.

* ``exit_heatmap.png``: median error at C per profile and estimator, map grade off vs on (free flow).
* ``growth.png``: route + IMU median error vs time since GPS loss: flat road, underwater V 4 % with the
  map grade off and on, and the constant-speed reference, for free flow and stop-and-go traffic.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from throughtunnel.evaluation.factor_study import BLUES, DASHES, GRID, INK, INK_2, SERIES, SHORT, SURFACE
from throughtunnel.evaluation.slope_study import PROFILES
from throughtunnel.positioning import ESTIMATORS

BLOCK_TITLES = {"slope": "free flow", "traffic": "stop-and-go traffic (T3)"}


def _short_name(name: str) -> str:
    return name.split(",")[0].split("(")[0].strip()


def plot_figures(records, medians, names, out: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    from throughtunnel.evaluation.map_grade_study import CURVE_GRID_S, _sel

    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2,
        "ytick.color": INK_2, "text.color": INK, "axes.titlesize": 9, "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    })  # fmt: skip
    presets = list(names)
    paths = []

    # ------------------------------------------------------------------ exit heatmap, off vs on
    bounds = np.array([0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 1e9])
    cmap, norm = ListedColormap(BLUES), BoundaryNorm(bounds, len(BLUES))
    fig, axes = plt.subplots(len(presets), 2, figsize=(11, 3.9 * len(presets)), sharey=True)
    axes = np.atleast_2d(axes)
    for i, pid in enumerate(presets):
        real = _sel(records, preset=pid, block="slope", sensors="realistic")
        for j, grade in enumerate((False, True)):
            ax = axes[i, j]
            sel = _sel(real, map_grade=grade)
            grid = np.array([
                [np.median([r["exit_total_m"] for r in _sel(sel, profile=p.key, estimator=n)])
                 for n in ESTIMATORS]
                for p in PROFILES
            ])  # fmt: skip
            ax.imshow(grid, cmap=cmap, norm=norm, aspect="auto")
            for (r, c), v in np.ndenumerate(grid):
                ax.text(c, r, f"{v:.0f}", ha="center", va="center", fontsize=8,
                        color=INK if norm(v) < 7 else "#ffffff")  # fmt: skip
            ax.set_xticks(
                range(len(ESTIMATORS)), [SHORT[n].replace(" + ", "\n+ ") for n in ESTIMATORS], fontsize=8
            )
            ax.set_yticks(range(len(PROFILES)), [p.label for p in PROFILES])
            ax.set_title(f"{_short_name(names[pid])}: map grade {'on' if grade else 'off'}", color=INK)
            ax.tick_params(length=0)
            for s in ax.spines.values():
                s.set_visible(False)
    title = "Median horizontal error at the tunnel exit C [m], realistic sensors, free flow; darker = larger"
    fig.suptitle(title, color=INK, fontsize=11)
    fig.tight_layout()
    paths.append(out / "exit_heatmap.png")
    fig.savefig(paths[-1], dpi=130, bbox_inches="tight")
    plt.close(fig)

    # ------------------------------------------------------------------ growth curves, route + IMU
    series = (  # (label, profile, map grade, estimator); fixed colour order
        ("Flat road, no map grade", "flat", False, "route_imu"),
        ("Underwater V 4 %, map grade off", "v4", False, "route_imu"),
        ("Underwater V 4 %, map grade on", "v4", True, "route_imu"),
        ("Constant-speed reference (route + last GPS speed), V 4 %", "v4", False, "route_hold"),
    )
    blocks = ("slope", "traffic")
    fig, axes = plt.subplots(len(presets), 2, figsize=(11, 3.1 * len(presets)), sharey=True)
    axes = np.atleast_2d(axes)
    for i, pid in enumerate(presets):
        for j, block in enumerate(blocks):
            ax = axes[i, j]
            for k in reversed(range(len(series))):
                label, prof, grade, name = series[k]
                y = medians.get((pid, block, "realistic", prof, grade, name))
                if y is None:
                    continue
                ax.plot(CURVE_GRID_S, np.maximum(y, 0.1), color=SERIES[k], linestyle=DASHES[k],
                        linewidth=(1.8, 1.8, 2.4, 1.6)[k], label=label, zorder=10 - k)  # fmt: skip
            ax.set_yscale("log")
            ax.set_ylim(1, 5000)
            ax.grid(True, which="major", color=GRID, linewidth=0.6)
            ax.spines[["top", "right"]].set_visible(False)
            if i == 0:
                ax.set_title(f"Route + IMU speed, {BLOCK_TITLES[block]}", color=INK)
            if j == 0:
                ax.set_ylabel(f"{_short_name(names[pid])}\nerror [m]")
            if i == len(presets) - 1:
                ax.set_xlabel("time since GPS loss [s]")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles[::-1], labels[::-1], loc="upper center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, 1.0))  # fmt: skip
    title = "Median horizontal error during the GPS outage until C (realistic sensors; log scale)"
    fig.suptitle(title, y=1.05, color=INK, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    paths.append(out / "growth.png")
    fig.savefig(paths[-1], dpi=130, bbox_inches="tight")
    plt.close(fig)
    return paths
