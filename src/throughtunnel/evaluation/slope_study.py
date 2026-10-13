"""Road-slope study (D36): how a road elevation profile affects the existing estimators.

Every profile uses the preset's own drive (the profile changes only the vertical motion; the horizontal
drive is identical). Two sensor settings:

* **ideal**: error-free IMU and GPS, one run per profile. It isolates the slope effect, which is then
  deterministic and is checked against the gravity-leakage prediction
  speed error ≈ g ∫ (sin φ(t) - sin φ_cal) dt, with φ = atan(grade) and φ_cal the mean approach grade
  that the levelling calibrated in.
* **realistic**: the preset's IMU noise and bias and GPS errors, one run per seed. Run k uses sensor and
  GPS seed k for every profile, so the slope's effect is a paired difference.

    uv run python -m throughtunnel.evaluation.slope_study --seeds 20 --out docs/slope_study

Writes ``runs.csv``, ``curves.csv``, ``tables.md`` and (with matplotlib, a dev dependency)
``growth.png`` and ``exit_heatmap.png``.
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
from throughtunnel.evaluation.factor_study import (
    BLUES,
    DASHES,
    GRID,
    INK,
    INK_2,
    SERIES,
    SHORT,
    SURFACE,
    WIDTHS,
    _nanmedian_rows,
)
from throughtunnel.positioning import ESTIMATORS
from throughtunnel.road_profile import RoadProfileConfig, point_distances, template_heights
from throughtunnel.scenario import (
    build_route_map,
    list_presets,
    load_preset,
    run_scenario,
    truth_at,
    with_sensor_config,
)
from throughtunnel.sensors.errors import ImuErrorConfig

G = 9.80


@dataclass(frozen=True)
class Profile:
    key: str
    label: str
    template: str
    scale: float  # template heights are multiplied by this (grade scales with it)


PROFILES: tuple[Profile, ...] = (
    Profile("flat", "Flat", "flat", 1.0),
    Profile("steady", "Steady climb 2 % (whole route)", "climb", 1.0),
    Profile("up1", "Climb in the tunnel +1 %", "tunnel_climb", 1.0 / 3.0),
    Profile("up2", "Climb in the tunnel +2 %", "tunnel_climb", 2.0 / 3.0),
    Profile("up4", "Climb in the tunnel +4 %", "tunnel_climb", 4.0 / 3.0),
    Profile("down2", "Descent in the tunnel −2 %", "tunnel_climb", -2.0 / 3.0),
    Profile("v2", "Underwater V 2 %", "underwater", 0.5),
    Profile("v4", "Underwater V 4 %", "underwater", 1.0),
)
FIGURE_PROFILES = ("flat", "steady", "up2", "down2", "v4")  # five series (validated palette)
GROWTH_TIMES_S = (15.0, 30.0, 60.0, 90.0, 120.0)
CURVE_GRID_S = np.arange(0.0, 161.0, 1.0)


def profile_config(cfg, profile: Profile) -> RoadProfileConfig:
    rm = build_route_map(cfg)
    b, c = rm.tunnel_entrance_m, rm.tunnel_exit_m
    d = point_distances(rm.length_m, b, c)
    z = template_heights(profile.template, d, b, c, 0.06) * profile.scale
    if not np.any(z):
        return RoadProfileConfig()
    return RoadProfileConfig(points=tuple(zip(d.tolist(), z.tolist(), strict=True)))


def ideal_sensors(cfg):
    imu = cfg.imu.model_copy(update={"errors": ImuErrorConfig.ideal()})
    gnss = cfg.gnss.model_copy(
        update={"position_sigma_m": 0.0, "white_sigma_m": 0.0, "speed_sigma_mps": 0.0, "seed": 0}
    )
    return imu, gnss


def realistic_sensors(cfg, seed: int):
    imu = cfg.imu.model_copy(update={"errors": cfg.imu.errors.model_copy(update={"seed": seed})})
    return imu, cfg.gnss.model_copy(update={"seed": seed})


def predicted_speed_error(res) -> float:
    """Gravity leakage integrated from the last fix to C: g ∫ (sin φ - sin φ_cal) dt.

    φ_cal is the mean grade angle over the approach until GPS loss (what the levelling absorbed)."""
    tr = res.truth
    t_f = float(res.gnss.t[res.gnss.t < res.gnss_events.loss_t][-1])
    phi = np.arctan(tr.grade)
    approach = tr.t <= t_f
    phi_cal = float(np.mean(phi[approach]))
    m = (tr.t >= t_f) & (tr.t <= res.sections.exit_t)
    return float(G * np.trapezoid(np.sin(phi[m]) - math.sin(phi_cal), tr.t[m]))


def run_records(res, profile: Profile, sensors: str, seed: int, preset: str):
    """Records and error curves (vs time since GPS loss) of all estimators on one simulated run."""
    loss, c_t = res.gnss_events.loss_t, res.sections.exit_t
    end = min(res.gnss_events.reacquire_t, c_t)
    route_len = res.route_map.length_m
    cmp = compare_estimators(res)
    records, curves = [], {}
    for track, ev in zip(cmp.tracks, cmp.evaluations, strict=True):
        before_c = track.t < c_t
        k = int(np.flatnonzero(before_c)[-1])
        truth = truth_at(res, [track.t[k]])
        rd = track.route_distance[before_c]
        s = ev.summary
        rec = {
            "preset": preset,
            "sensors": sensors,
            "seed": seed,
            "profile": profile.key,
            "estimator": ev.name,
            "exit_total_m": s["exit_total_m"],
            "exit_along_m": s["exit_along_m"],
            "exit_cross_m": s["exit_cross_m"],
            "heading_error_deg": math.degrees(math.remainder(track.heading[k] - truth.yaw[0], 2 * math.pi)),
            "speed_error_mps": float(track.speed[k] - truth.speed[0]),
            "predicted_speed_error_mps": predicted_speed_error(res)
            if ev.name == "dr_calibrated"
            else math.nan,
            "route_end_reached": bool(
                ev.name.startswith("route") and len(rd) and rd.max() >= route_len - 1.0
            ),
            "announcement_error_s": ev.announcement_time_error_s,
            "outage_to_c_s": end - loss,
        }
        t = loss + CURVE_GRID_S
        curve = np.where(t <= end, np.interp(t, ev.t, ev.total), np.nan)
        for tau in GROWTH_TIMES_S:
            rec[f"err_{tau:g}s_m"] = float(curve[int(tau)])
        records.append(rec)
        curves[ev.name] = curve
    return records, curves


def study_preset(preset_id: str, seeds: list[int]):
    cfg = load_preset(preset_id)
    records: list[dict] = []
    curves: dict[tuple[str, str, str], list[np.ndarray]] = {}
    for profile in PROFILES:
        base = run_scenario(cfg.model_copy(update={"road_profile": profile_config(cfg, profile)}))
        runs = [("ideal", 0, ideal_sensors(cfg))] + [
            ("realistic", k, realistic_sensors(cfg, k)) for k in seeds
        ]
        for sensors, seed, (imu, gnss) in runs:
            res = with_sensor_config(base, imu=imu, gnss=gnss)
            recs, cur = run_records(res, profile, sensors, seed, preset_id)
            records += recs
            for name, c in cur.items():
                curves.setdefault((sensors, profile.key, name), []).append(c)
    medians = {k: _nanmedian_rows(np.array(v)) for k, v in curves.items()}
    return records, {"name": cfg.name, "medians": medians}


# ---------------------------------------------------------------------- tables
def _sel(records, **kw):
    return [r for r in records if all(r[k] == v for k, v in kw.items())]


def _med_p90(vals) -> str:
    v = np.array(vals, dtype=float)
    v = v[np.isfinite(v)]
    return f"{np.median(v):.0f} ({np.percentile(v, 90):.0f})" if len(v) else "n/a"


def _flag(sel) -> str:
    n = sum(r["route_end_reached"] for r in sel)
    return f" §{n}" if n else ""


def ideal_table(records, preset) -> list[dict[str, str]]:
    rows = []
    for p in PROFILES:
        sel = {r["estimator"]: r for r in _sel(records, preset=preset, sensors="ideal", profile=p.key)}
        dc = sel["dr_calibrated"]
        row = {"profile": p.label}
        for name in ESTIMATORS:
            r = sel[name]
            row[name] = f"{r['exit_total_m']:.0f}" + (" §" if r["route_end_reached"] else "")
        row["dr_calibrated along / cross"] = f"{dc['exit_along_m']:+.0f} / {dc['exit_cross_m']:+.0f}"
        row["dr_calibrated heading err."] = f"{dc['heading_error_deg']:+.3f}°"
        row["speed err. measured / predicted"] = (
            f"{dc['speed_error_mps']:+.2f} / {dc['predicted_speed_error_mps']:+.2f} m/s"
        )
        rows.append(row)
    return rows


def realistic_table(records, preset) -> list[dict[str, str]]:
    rows = []
    for p in PROFILES:
        row = {"profile": p.label}
        for name in ESTIMATORS:
            sel = _sel(records, preset=preset, sensors="realistic", profile=p.key, estimator=name)
            row[name] = _med_p90([r["exit_total_m"] for r in sel]) + _flag(sel)
        rows.append(row)
    return rows


def shift_table(records, preset) -> list[dict[str, str]]:
    """Paired change of the along-track error at C caused by the profile (same seed, flat subtracted)."""
    rows = []
    flat = {
        (r["seed"], r["estimator"]): r
        for r in _sel(records, preset=preset, sensors="realistic", profile="flat")
    }
    for p in PROFILES[1:]:
        row = {"profile": p.label}
        for name in ESTIMATORS:
            sel = _sel(records, preset=preset, sensors="realistic", profile=p.key, estimator=name)
            d = np.array([r["exit_along_m"] - flat[(r["seed"], name)]["exit_along_m"] for r in sel])
            row[name] = f"{np.median(d):+.0f} [{d.min():+.0f}, {d.max():+.0f}]"
        rows.append(row)
    return rows


def heading_table(records, preset) -> list[dict[str, str]]:
    rows = []
    for p in PROFILES:
        row = {"profile": p.label}
        for name in ("dr_raw", "dr_calibrated", "dr_filtered"):
            sel = _sel(records, preset=preset, sensors="realistic", profile=p.key, estimator=name)
            v = np.abs([r["heading_error_deg"] for r in sel])
            row[name] = f"{np.median(v):.2f}° ({np.percentile(v, 90):.2f}°)"
        rows.append(row)
    return rows


def announcement_table(records, preset) -> list[dict[str, str]]:
    rows = []
    for p in PROFILES:
        row = {"profile": p.label}
        for name in ESTIMATORS:
            sel = _sel(records, preset=preset, sensors="realistic", profile=p.key, estimator=name)
            v = np.array([r["announcement_error_s"] for r in sel], dtype=float)
            row[name] = (
                f"{np.nanmedian(np.abs(v)):.1f} ({np.nanmean(v):+.1f})" if np.isfinite(v).any() else "missed"
            )
        rows.append(row)
    return rows


def tables_markdown(records, info, seeds) -> str:
    out = [
        "# Road-slope study: generated tables\n",
        "Preset drives; ideal = error-free sensors and GPS (one run); realistic = preset sensor and GPS "
        f"errors, {len(seeds)} runs (seeds {seeds[0]}–{seeds[-1]}), paired across profiles. § = the route "
        "estimator reached the route end D before C in that many runs (its error is then capped by the "
        "route length).\n",
    ]
    for pid, inf in info.items():
        sel = _sel(records, preset=pid, sensors="ideal", profile="flat", estimator="dr_calibrated")
        out.append(f"## {inf['name']}\n")
        out.append(f"Dead-reckoning time from GPS loss to C: {sel[0]['outage_to_c_s']:.0f} s.\n")
        heading = "**Ideal sensors: error at C [m]; dr_calibrated details; speed error measured vs predicted"
        out.append(heading + " from gravity leakage:**\n")
        out.append(markdown_table(ideal_table(records, pid)) + "\n")
        out.append("**Realistic sensors: error at C [m], median (p90):**\n")
        out.append(markdown_table(realistic_table(records, pid)) + "\n")
        out.append("**Realistic sensors: along-track shift at C caused by the profile (paired) [m], median "
                   "[min, max]:**\n")  # fmt: skip
        out.append(markdown_table(shift_table(records, pid)) + "\n")
        out.append("**Realistic sensors: |heading error| at C, median (p90):**\n")
        out.append(markdown_table(heading_table(records, pid)) + "\n")
        out.append(
            "**Realistic sensors: exit-announcement timing error [s], median |error| (signed mean):**\n"
        )
        out.append(markdown_table(announcement_table(records, pid)) + "\n")
        rows = []
        for p in PROFILES:
            for name in ESTIMATORS:
                sel = _sel(records, preset=pid, sensors="realistic", profile=p.key, estimator=name)
                row = {"profile": p.label, "estimator": name}
                for tau in GROWTH_TIMES_S:
                    v = np.array([r[f"err_{tau:g}s_m"] for r in sel], dtype=float)
                    row[f"{tau:g} s"] = f"{np.nanmedian(v):.0f}" if np.isfinite(v).all() else "–"
                rows.append(row)
        out.append("**Realistic sensors: median error vs time since GPS loss [m]:**\n")
        out.append(markdown_table(rows) + "\n")
    return "\n".join(out)


# ---------------------------------------------------------------------- figures
def plot_figures(info, records, out: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2,
        "ytick.color": INK_2, "text.color": INK, "axes.titlesize": 9, "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    })  # fmt: skip
    by_key = {p.key: p for p in PROFILES}
    shown = [by_key[k] for k in FIGURE_PROFILES]
    presets = list(info)
    paths = []

    fig, axes = plt.subplots(
        len(presets), len(ESTIMATORS), figsize=(16, 3.1 * len(presets)), sharex=True, sharey=True
    )
    axes = np.atleast_2d(axes)
    for i, pid in enumerate(presets):
        med = info[pid]["medians"]
        for j, name in enumerate(ESTIMATORS):
            ax = axes[i, j]
            for k in reversed(range(len(shown))):
                y = np.maximum(med[("realistic", shown[k].key, name)], 0.1)
                ax.plot(CURVE_GRID_S, y, color=SERIES[k], linestyle=DASHES[k], linewidth=WIDTHS[k],
                        label=shown[k].label, zorder=10 - k)  # fmt: skip
            ax.set_yscale("log")
            ax.set_ylim(1, 5000)
            ax.grid(True, which="major", color=GRID, linewidth=0.6)
            ax.spines[["top", "right"]].set_visible(False)
            if i == 0:
                ax.set_title(SHORT[name], color=INK)
            if j == 0:
                ax.set_ylabel(f"{info[pid]['name'].split(',')[0].split('(')[0].strip()}\nerror [m]")
            if i == len(presets) - 1:
                ax.set_xlabel("time since GPS loss [s]")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles[::-1],
        labels[::-1],
        loc="upper center",
        ncol=len(shown),
        frameon=False,
        bbox_to_anchor=(0.5, 1.0),
    )
    title = "Median horizontal error during the GPS outage by road profile (realistic sensors; log scale)"
    fig.suptitle(title, y=1.035, color=INK, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    paths.append(out / "growth.png")
    fig.savefig(paths[-1], dpi=130, bbox_inches="tight")
    plt.close(fig)

    bounds = np.array([0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 1e9])
    cmap, norm = ListedColormap(BLUES), BoundaryNorm(bounds, len(BLUES))
    fig, axes = plt.subplots(1, len(presets), figsize=(5.4 * len(presets), 4.8), sharey=True)
    for ax, pid in zip(np.atleast_1d(axes), presets, strict=True):
        real = _sel(records, preset=pid, sensors="realistic")
        grid = np.array([
            [np.median([r["exit_total_m"] for r in _sel(real, profile=p.key, estimator=n)])
             for n in ESTIMATORS]
            for p in PROFILES
        ])  # fmt: skip
        ax.imshow(grid, cmap=cmap, norm=norm, aspect="auto")
        for (r, c), v in np.ndenumerate(grid):
            ax.text(
                c,
                r,
                f"{v:.0f}",
                ha="center",
                va="center",
                fontsize=8,
                color=INK if norm(v) < 7 else "#ffffff",
            )
        ax.set_xticks(
            range(len(ESTIMATORS)), [SHORT[n].replace(" + ", "\n+ ") for n in ESTIMATORS], fontsize=8
        )
        ax.set_yticks(range(len(PROFILES)), [p.label for p in PROFILES])
        ax.set_title(info[pid]["name"], color=INK)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
    title = "Median horizontal error at the tunnel exit C [m], realistic sensors; darker = larger (log bins)"
    fig.suptitle(title, color=INK, fontsize=11)
    fig.tight_layout()
    paths.append(out / "exit_heatmap.png")
    fig.savefig(paths[-1], dpi=130, bbox_inches="tight")
    plt.close(fig)
    return paths


# ---------------------------------------------------------------------- main
def write_outputs(records, info, seeds, out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "runs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(
            {k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()} for r in records
        )
    with open(out / "curves.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["preset", "sensors", "profile", "estimator", *[f"{t:g}" for t in CURVE_GRID_S]])
        for pid, inf in info.items():
            for (sensors, prof, name), y in inf["medians"].items():
                writer.writerow(
                    [pid, sensors, prof, name, *[f"{v:.3f}" if np.isfinite(v) else "" for v in y]]
                )
    (out / "tables.md").write_text(tables_markdown(records, info, seeds), encoding="utf-8")
    paths = [out / "runs.csv", out / "curves.csv", out / "tables.md"]
    try:
        paths += plot_figures(info, records, out)
    except ImportError:
        print("matplotlib not installed (dev dependency): figures skipped")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=20, help="realistic runs per profile and preset")
    parser.add_argument("--presets", nargs="*", default=list(list_presets()))
    parser.add_argument("--out", type=Path, default=Path("docs/slope_study"))
    args = parser.parse_args()
    seeds = list(range(args.seeds))
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=len(args.presets)) as pool:
        results = list(pool.map(study_preset, args.presets, [seeds] * len(args.presets)))
    records = [r for recs, _ in results for r in recs]
    info = {pid: inf for pid, (_, inf) in zip(args.presets, results, strict=True)}
    for p in write_outputs(records, info, seeds, args.out):
        print("wrote", p)
    print(f"{len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
