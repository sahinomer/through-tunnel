"""Sensor-factor baseline study: how each sensor imperfection alone affects the existing estimators.

Every condition switches individual error sources on or off; everything else is identical. All
conditions use the preset drive. Run k uses sensor and GPS seed k in every condition. Each error source
has its own random stream, so switching one source never changes the realisation of another. GPS
availability (loss point, reacquisition) has its own stream too, so the outage is identical across the
conditions of a run.

Main conditions (GPS error-free, so only the IMU-side factor differs): ideal, IMU noise only, IMU bias
only, calibration error only (D34 default: yaw 2°, pitch 0.5°, roll 0.5°), and all three combined.
Supplementary conditions split noise and bias into accelerometer and gyroscope, and add GPS errors.

    uv run python -m throughtunnel.evaluation.factor_study --seeds 20 --out docs/factor_study

Writes ``runs.csv`` (one row per run, condition and estimator), ``curves.csv`` (median error vs time
since GPS loss), ``tables.md`` and, if matplotlib is installed (dev dependency), ``growth.png`` and
``exit_heatmap.png``.
"""

from __future__ import annotations

import argparse
import csv
import math
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from throughtunnel.evaluation.experiment import compare_estimators, markdown_table
from throughtunnel.positioning import ESTIMATORS
from throughtunnel.scenario import (
    list_presets,
    load_preset,
    run_scenario,
    with_calibration,
    with_sensor_config,
)
from throughtunnel.sensors.errors import ImuErrorConfig
from throughtunnel.sensors.gnss import GnssConfig
from throughtunnel.sensors.mounting import CalibrationErrorConfig


@dataclass(frozen=True)
class Condition:
    key: str
    label: str
    accel_noise: bool = False
    gyro_noise: bool = False
    accel_bias: bool = False
    gyro_bias: bool = False
    gps_errors: bool = False
    calibration: bool = False
    main: bool = False


CONDITIONS: tuple[Condition, ...] = (
    Condition("ideal", "Ideal sensors, correct calibration", main=True),
    Condition("noise", "IMU noise only", accel_noise=True, gyro_noise=True, main=True),
    Condition("bias", "IMU bias only", accel_bias=True, gyro_bias=True, main=True),
    Condition("calibration", "Calibration error only", calibration=True, main=True),
    Condition("combined", "Noise + bias + calibration", True, True, True, True, calibration=True, main=True),
    Condition("accel_noise", "Accelerometer noise only", accel_noise=True),
    Condition("gyro_noise", "Gyroscope noise only", gyro_noise=True),
    Condition("accel_bias", "Accelerometer bias only", accel_bias=True),
    Condition("gyro_bias", "Gyroscope bias only", gyro_bias=True),
    Condition("gps", "GPS errors only", gps_errors=True),
    Condition("default", "Noise + bias + GPS errors (results.md)", True, True, True, True, gps_errors=True),
    Condition(
        "all", "Noise + bias + GPS + calibration", True, True, True, True, gps_errors=True, calibration=True
    ),
)
GROWTH_TIMES_S = (15.0, 30.0, 60.0, 90.0, 120.0)
CURVE_GRID_S = np.arange(0.0, 161.0, 1.0)
EXPONENT_WINDOW_S = (30.0, 90.0)  # growth exponent p from e(t) ~ t^p between these times


def condition_configs(cfg, cond: Condition, seed: int):
    """IMU error config, GPS config and calibration error of one condition and run."""
    e = cfg.imu.errors
    errors = ImuErrorConfig(
        accel=e.accel.model_copy(update={"noise_enabled": cond.accel_noise, "bias_enabled": cond.accel_bias}),
        gyro=e.gyro.model_copy(update={"noise_enabled": cond.gyro_noise, "bias_enabled": cond.gyro_bias}),
        seed=seed,
    )
    imu = cfg.imu.model_copy(update={"errors": errors})
    gnss = cfg.gnss if cond.gps_errors else cfg.gnss.model_copy(update=GnssConfig.ideal().model_dump(
        include={"position_sigma_m", "white_sigma_m", "speed_sigma_mps"}
    ))  # fmt: skip
    gnss = gnss.model_copy(update={"seed": seed})
    return imu, gnss, CalibrationErrorConfig(enabled=cond.calibration)


def study_preset(preset_id: str, seeds: list[int]) -> tuple[list[dict], dict]:
    """Per-run records and the error-vs-time samples (on CURVE_GRID_S) of one preset."""
    cfg = load_preset(preset_id)
    base = run_scenario(cfg)
    records: list[dict] = []
    curves: dict[tuple[str, str], list[np.ndarray]] = {}
    for seed in seeds:
        for cond in CONDITIONS:
            imu, gnss, cal = condition_configs(cfg, cond, seed)
            res = with_calibration(with_sensor_config(base, imu=imu, gnss=gnss), cal)
            loss = res.gnss_events.loss_t
            end = min(res.gnss_events.reacquire_t, res.sections.exit_t)
            for ev in compare_estimators(res).evaluations:
                s = ev.summary
                rec = {
                    "preset": preset_id,
                    "seed": seed,
                    "condition": cond.key,
                    "estimator": ev.name,
                    "exit_total_m": s["exit_total_m"],
                    "exit_along_m": s["exit_along_m"],
                    "exit_cross_m": s["exit_cross_m"],
                    "tunnel_max_m": s["tunnel_max_m"],
                    "tunnel_rms_m": s["tunnel_rms_m"],
                    "announcement_error_s": ev.announcement_time_error_s,
                    "outage_to_c_s": end - loss,
                }
                t = loss + CURVE_GRID_S
                curve = np.where(t <= end, np.interp(t, ev.t, ev.total), np.nan)
                for tau in GROWTH_TIMES_S:
                    rec[f"err_{tau:g}s_m"] = float(curve[int(tau)])
                records.append(rec)
                curves.setdefault((cond.key, ev.name), []).append(curve)
    medians = {k: _nanmedian_rows(np.array(v)) for k, v in curves.items()}
    return records, {"name": cfg.name, "medians": medians}


def _nanmedian_rows(a: np.ndarray) -> np.ndarray:
    """Median over runs at each time, only where every run is still in the outage (outage lengths differ
    by about a second between runs; a median over a changing subset would jump)."""
    valid = np.isfinite(a).all(axis=0)
    out = np.full(a.shape[1], np.nan)
    if valid.any():
        out[valid] = np.nanmedian(a[:, valid], axis=0)
    return out


# ---------------------------------------------------------------------- tables
def _sel(records, **kw):
    return [r for r in records if all(r[k] == v for k, v in kw.items())]


def _med_p90(vals) -> str:
    v = np.array(vals, dtype=float)
    v = v[np.isfinite(v)]
    return f"{np.median(v):.1f} ({np.percentile(v, 90):.1f})" if len(v) else "n/a"


def exit_table(records, preset) -> list[dict[str, str]]:
    rows = []
    for cond in CONDITIONS:
        row = {"condition": cond.label + ("" if cond.main else " ‡")}
        for name in ESTIMATORS:
            row[name] = _med_p90(
                [r["exit_total_m"] for r in _sel(records, preset=preset, condition=cond.key, estimator=name)]
            )
        rows.append(row)
    return rows


def component_table(records, preset) -> list[dict[str, str]]:
    """Median |along| / |cross| at C: which error component a factor produces."""
    rows = []
    for cond in CONDITIONS:
        row = {"condition": cond.label + ("" if cond.main else " ‡")}
        for name in ESTIMATORS:
            sel = _sel(records, preset=preset, condition=cond.key, estimator=name)
            a = np.median(np.abs([r["exit_along_m"] for r in sel]))
            c = np.median(np.abs([r["exit_cross_m"] for r in sel]))
            row[name] = f"{a:.0f} / {c:.0f}"
        rows.append(row)
    return rows


def exponent_table(curves_by_preset, preset) -> list[dict[str, str]]:
    """Growth exponent p of the median error, e(t) ~ t^p, between EXPONENT_WINDOW_S."""
    t1, t2 = EXPONENT_WINDOW_S
    med = curves_by_preset[preset]["medians"]
    rows = []
    for cond in CONDITIONS:
        row = {"condition": cond.label + ("" if cond.main else " ‡")}
        for name in ESTIMATORS:
            e1, e2 = med[(cond.key, name)][int(t1)], med[(cond.key, name)][int(t2)]
            ok = (
                np.isfinite(e1) and np.isfinite(e2) and e1 > 0.5 and e2 > 0.5
            )  # below 0.5 m: no growth to fit
            row[name] = f"{math.log(e2 / e1) / math.log(t2 / t1):.1f}" if ok else "–"
        rows.append(row)
    return rows


def announcement_table(records, preset) -> list[dict[str, str]]:
    rows = []
    for cond in CONDITIONS:
        if not cond.main:
            continue
        row = {"condition": cond.label}
        for name in ESTIMATORS:
            vals = [
                r["announcement_error_s"]
                for r in _sel(records, preset=preset, condition=cond.key, estimator=name)
            ]
            v = np.abs(np.array(vals, dtype=float))
            row[name] = f"{np.nanmedian(v):.1f}" if np.isfinite(v).any() else "missed"
        rows.append(row)
    return rows


def tables_markdown(records, curves_by_preset, seeds: list[int]) -> str:
    out = [
        "# Sensor-factor study: generated tables\n",
        f"{len(seeds)} runs per condition (sensor/GPS seeds {seeds[0]}–{seeds[-1]}), preset drive. "
        "‡ = supplementary condition. Values are medians over the runs unless stated.\n",
    ]
    for pid, info in curves_by_preset.items():
        sel = _sel(records, preset=pid, condition="ideal", estimator="dr_calibrated")
        outage = np.median([r["outage_to_c_s"] for r in sel])
        out.append(f"## {info['name']}\n")
        out.append(f"Dead-reckoning time from GPS loss to C: {outage:.0f} s.\n")
        out.append("**Horizontal error at C [m], median (p90):**\n")
        out.append(markdown_table(exit_table(records, pid)) + "\n")
        out.append("**Along-track / cross-track error at C [m], median of absolute values:**\n")
        out.append(markdown_table(component_table(records, pid)) + "\n")
        out.append(
            f"**Growth exponent p of the median error, e(t) ∝ t^p, between {EXPONENT_WINDOW_S[0]:g} s and "
            f"{EXPONENT_WINDOW_S[1]:g} s after GPS loss** (1 = constant speed or heading error, 1.5 = random "
            "walk of speed or heading, 2 = constant acceleration or turn-rate error; – = below 0.5 m):\n"
        )
        out.append(markdown_table(exponent_table(curves_by_preset, pid)) + "\n")
        out.append("**Median horizontal error vs. time since GPS loss [m]:**\n")
        rows = []
        for cond in CONDITIONS:
            for name in ESTIMATORS:
                sel = _sel(records, preset=pid, condition=cond.key, estimator=name)
                row = {"condition": cond.label + ("" if cond.main else " ‡"), "estimator": name}
                for tau in GROWTH_TIMES_S:
                    v = np.array([r[f"err_{tau:g}s_m"] for r in sel], dtype=float)
                    row[f"{tau:g} s"] = (
                        f"{np.nanmedian(v):.1f}" if np.isfinite(v).sum() >= len(v) / 2 else "–"
                    )
                rows.append(row)
        out.append(markdown_table(rows) + "\n")
        out.append("**Exit-announcement timing error [s], median of absolute values (main conditions):**\n")
        out.append(markdown_table(announcement_table(records, pid)) + "\n")
    return "\n".join(out)


# ---------------------------------------------------------------------- figures
# Reference palette (dataviz skill, light mode): categorical slots 1–5 in fixed order; blue sequential ramp.
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4")
DASHES = ("-", (0, (5, 2)), (0, (1, 1.5)), (0, (6, 2, 1, 2)), "-")
WIDTHS = (1.6, 1.8, 2.2, 2.6, 4.0)  # drawn back to front: wider lines underneath, so overlaps stay visible
BLUES = ("#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
         "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b")  # fmt: skip
SHORT = {
    "dr_raw": "DR raw IMU",
    "dr_calibrated": "DR calibrated",
    "dr_filtered": "DR calibrated + GPS-blended",
    "route_imu": "Route + IMU speed",
    "route_hold": "Route + last GPS speed",
}


def plot_figures(curves_by_preset, records, out: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2,
        "ytick.color": INK_2, "text.color": INK, "axes.titlesize": 9, "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    })  # fmt: skip
    main = [c for c in CONDITIONS if c.main]
    presets = list(curves_by_preset)
    paths = []

    # Figure 1: median error vs time since GPS loss; rows = presets, columns = estimators.
    fig, axes = plt.subplots(
        len(presets), len(ESTIMATORS), figsize=(16, 3.1 * len(presets)), sharex=True, sharey=True
    )
    axes = np.atleast_2d(axes)
    for i, pid in enumerate(presets):
        med = curves_by_preset[pid]["medians"]
        for j, name in enumerate(ESTIMATORS):
            ax = axes[i, j]
            for k in reversed(range(len(main))):
                y = np.maximum(med[(main[k].key, name)], 0.1)
                ax.plot(CURVE_GRID_S, y, color=SERIES[k], linestyle=DASHES[k], linewidth=WIDTHS[k],
                        label=main[k].label, zorder=10 - k)  # fmt: skip
            ax.set_yscale("log")
            ax.set_ylim(0.1, 3000)
            ax.grid(True, which="major", color=GRID, linewidth=0.6)
            ax.spines[["top", "right"]].set_visible(False)
            if i == 0:
                ax.set_title(SHORT[name], color=INK)
            if j == 0:
                ax.set_ylabel(
                    f"{curves_by_preset[pid]['name'].split(',')[0].split('(')[0].strip()}\nerror [m]"
                )
            if i == len(presets) - 1:
                ax.set_xlabel("time since GPS loss [s]")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    handles, labels = handles[::-1], labels[::-1]  # legend in condition order
    fig.legend(handles, labels, loc="upper center", ncol=len(main), frameon=False, bbox_to_anchor=(0.5, 1.0))
    title = "Median horizontal error during the GPS outage, by sensor condition (log scale; floor 0.1 m)"
    fig.suptitle(title, y=1.035, color=INK, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    paths.append(out / "growth.png")
    fig.savefig(paths[-1], dpi=130, bbox_inches="tight")
    plt.close(fig)

    # Figure 2: median error at C, conditions x estimators, one panel per preset (log-binned blue ramp).
    bounds = np.array([0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 1e9])
    cmap, norm = ListedColormap(BLUES), BoundaryNorm(bounds, len(BLUES))
    fig, axes = plt.subplots(1, len(presets), figsize=(5.4 * len(presets), 6.2), sharey=True)
    for ax, pid in zip(np.atleast_1d(axes), presets, strict=True):
        grid = np.array([
            [np.median([r["exit_total_m"] for r in _sel(records, preset=pid, condition=c.key, estimator=n)])
             for n in ESTIMATORS] for c in CONDITIONS
        ])  # fmt: skip
        ax.imshow(grid, cmap=cmap, norm=norm, aspect="auto")
        for (r, c), v in np.ndenumerate(grid):
            light_cell = norm(v) < 7
            ax.text(c, r, f"{v:.0f}" if v >= 10 else f"{v:.1f}", ha="center", va="center", fontsize=8,
                    color=INK if light_cell else "#ffffff")  # fmt: skip
        ax.axhline(sum(c.main for c in CONDITIONS) - 0.5, color=INK_2, linewidth=1.2)
        ax.set_xticks(
            range(len(ESTIMATORS)), [SHORT[n].replace(" + ", "\n+ ") for n in ESTIMATORS], fontsize=8
        )
        ax.set_yticks(range(len(CONDITIONS)), [c.label + ("" if c.main else " ‡") for c in CONDITIONS])
        ax.set_title(curves_by_preset[pid]["name"], color=INK)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.suptitle("Median horizontal error at the tunnel exit C [m]; darker = larger (log bins); "
                 "‡ supplementary, below the line",
                 color=INK, fontsize=11)  # fmt: skip
    fig.tight_layout()
    paths.append(out / "exit_heatmap.png")
    fig.savefig(paths[-1], dpi=130, bbox_inches="tight")
    plt.close(fig)
    return paths


# ---------------------------------------------------------------------- main
def write_outputs(records, curves_by_preset, seeds: list[int], out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "runs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(
            {k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()} for r in records
        )
    with open(out / "curves.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["preset", "condition", "estimator", *[f"{t:g}" for t in CURVE_GRID_S]])
        for pid, info in curves_by_preset.items():
            for (cond, name), y in info["medians"].items():
                writer.writerow([pid, cond, name, *[f"{v:.3f}" if np.isfinite(v) else "" for v in y]])
    (out / "tables.md").write_text(tables_markdown(records, curves_by_preset, seeds), encoding="utf-8")
    paths = [out / "runs.csv", out / "curves.csv", out / "tables.md"]
    try:
        paths += plot_figures(curves_by_preset, records, out)
    except ImportError:
        print("matplotlib not installed (dev dependency): figures skipped")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=20, help="runs per condition and preset")
    parser.add_argument("--presets", nargs="*", default=list(list_presets()))
    parser.add_argument("--out", type=Path, default=Path("docs/factor_study"))
    args = parser.parse_args()
    seeds = list(range(args.seeds))
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=len(args.presets)) as pool:
        results = list(pool.map(study_preset, args.presets, [seeds] * len(args.presets)))
    records = [r for recs, _ in results for r in recs]
    curves_by_preset = {pid: info for pid, (_, info) in zip(args.presets, results, strict=True)}
    for p in write_outputs(records, curves_by_preset, seeds, args.out):
        print("wrote", p)
    print(f"{len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
