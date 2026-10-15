"""Traffic study (R2, D37): how traffic in the tunnel affects the existing estimators.

Every scenario uses the preset's road and driver. Two sensor settings, as in the slope study:

* **ideal**: error-free IMU and GPS, traffic seed 0, one run per scenario. Isolates the traffic effect.
* **realistic**: the preset's IMU noise and bias and GPS errors. Run k uses seed k for the sensors, the
  GPS *and* the traffic events (positions, durations, speeds), for every scenario.

Two sweeps (realistic sensors) locate where the methods begin to fail:

* portal speed drop (T1) 0–30 km/h: the onset for the constant-speed baseline;
* number of stops (T3) 0–4: total standing time lengthens the outage, which is what IMU drift grows
  with.

    uv run python -m throughtunnel.evaluation.traffic_study --seeds 20 --out docs/traffic_study
"""

from __future__ import annotations

import argparse
import csv
import math
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from throughtunnel.evaluation.experiment import compare_estimators, markdown_table
from throughtunnel.evaluation.factor_study import BLUES, GRID, INK, INK_2, SERIES, SHORT, SURFACE, short_ticks
from throughtunnel.evaluation.slope_study import ideal_sensors, realistic_sensors
from throughtunnel.positioning import MAIN_ESTIMATORS
from throughtunnel.scenario import list_presets, load_preset, run_scenario, truth_at, with_sensor_config
from throughtunnel.vehicle.traffic import SCENARIO_LABELS, TrafficConfig

SCENARIOS = tuple(SCENARIO_LABELS)  # free, portal, speed_limit, stop_and_go, exit_queue, congested
PORTAL_DROPS_KMH = (0.0, 5.0, 10.0, 20.0, 30.0)
STOP_COUNTS = (0, 1, 2, 4)


def run_records(res, tag: dict) -> list[dict]:
    """One record per estimator for a simulated run (``tag`` identifies the run)."""
    sec, ev_g = res.sections, res.gnss_events
    c_t = sec.exit_t
    m = res.motion
    tunnel = (m.s >= sec.entrance_s) & (m.s <= sec.exit_s)
    standing = float(np.sum(m.v[tunnel] == 0.0) * (m.t[1] - m.t[0]))
    route_len = res.route_map.length_m
    out = []
    cmp = compare_estimators(res, list(MAIN_ESTIMATORS))
    for track, ev in zip(cmp.tracks, cmp.evaluations, strict=True):
        before_c = track.t < c_t
        k = int(np.flatnonzero(before_c)[-1])
        truth = truth_at(res, [track.t[k]])
        rd = track.route_distance[before_c]
        s = ev.summary
        out.append({
            **tag,
            "estimator": ev.name,
            "exit_total_m": s["exit_total_m"],
            "exit_along_m": s["exit_along_m"],
            "exit_cross_m": s["exit_cross_m"],
            "tunnel_max_m": s["tunnel_max_m"],
            "heading_error_deg": math.degrees(math.remainder(track.heading[k] - truth.yaw[0], 2 * math.pi)),
            "speed_error_mps": float(track.speed[k] - truth.speed[0]),
            "route_end_reached": bool(ev.name.startswith("route") and len(rd) and rd.max() >= route_len - 1),
            "announcement_error_s": ev.announcement_time_error_s,
            "tunnel_time_s": c_t - sec.entrance_t,
            "outage_s": ev_g.reacquire_t - ev_g.loss_t,
            "standing_s": standing,
            "mean_tunnel_speed_kmh": float(np.mean(m.v[tunnel]) * 3.6),
        })  # fmt: skip
    return out


def study_preset(preset_id: str, seeds: list[int]) -> list[dict]:
    cfg = load_preset(preset_id)
    records: list[dict] = []

    def simulate(traffic: TrafficConfig, sensors: str, seed: int, **tag):
        base = run_scenario(cfg.model_copy(update={"traffic": traffic}))
        imu, gnss = ideal_sensors(cfg) if sensors == "ideal" else realistic_sensors(cfg, seed)
        res = with_sensor_config(base, imu=imu, gnss=gnss)
        records.extend(run_records(res, {"preset": preset_id, "sensors": sensors, "seed": seed, **tag}))

    for sc in SCENARIOS:
        print(f"{preset_id}: {sc}", flush=True)
        simulate(TrafficConfig(scenario=sc, seed=0), "ideal", 0, study="main", scenario=sc, value=math.nan)
        for k in seeds:
            simulate(
                TrafficConfig(scenario=sc, seed=k), "realistic", k, study="main", scenario=sc, value=math.nan
            )
    sweep_seeds = seeds[: max(1, len(seeds) // 2)]
    print(f"{preset_id}: sweeps", flush=True)
    for drop in PORTAL_DROPS_KMH:
        for k in sweep_seeds:
            t = TrafficConfig(scenario="portal", seed=k, portal_drop_kmh=drop, jitter=0.0)
            simulate(t, "realistic", k, study="portal_drop", scenario="portal", value=drop)
    for count in STOP_COUNTS:
        for k in sweep_seeds:
            t = TrafficConfig(scenario="stop_and_go", seed=k, stop_count=count)
            simulate(t, "realistic", k, study="stop_count", scenario="stop_and_go", value=float(count))
    return records


# ---------------------------------------------------------------------- tables
def _sel(records, **kw):
    return [r for r in records if all(r[k] == v for k, v in kw.items())]


def _med(vals, fmt="{:.0f}") -> str:
    v = np.array(vals, dtype=float)
    v = v[np.isfinite(v)]
    return fmt.format(np.median(v)) if len(v) else "n/a"


def _med_p90(vals) -> str:
    v = np.array(vals, dtype=float)
    v = v[np.isfinite(v)]
    return f"{np.median(v):.0f} ({np.percentile(v, 90):.0f})" if len(v) else "n/a"


def _flag(sel) -> str:
    n = sum(r["route_end_reached"] for r in sel)
    return f" §{n}" if n else ""


def _mostly_capped(sel) -> bool:
    return bool(sel) and 2 * sum(r["route_end_reached"] for r in sel) >= len(sel)


def _capped(text: str, sel) -> str:
    """Mark values that are lower bounds: if most runs hit the route end, the error is at least this."""
    return ("≥" + text if _mostly_capped(sel) else text) + _flag(sel)


def scenario_facts(records, preset) -> list[dict[str, str]]:
    rows = []
    for sc in SCENARIOS:
        sel = _sel(
            records, preset=preset, study="main", sensors="realistic", scenario=sc, estimator="dr_calibrated"
        )
        rows.append({
            "scenario": SCENARIO_LABELS[sc],
            "time in tunnel [s]": _med([r["tunnel_time_s"] for r in sel]),
            "GPS outage [s]": _med([r["outage_s"] for r in sel]),
            "standing [s]": _med([r["standing_s"] for r in sel]),
            "mean speed in tunnel [km/h]": _med([r["mean_tunnel_speed_kmh"] for r in sel]),
        })  # fmt: skip
    return rows


def error_table(records, preset, sensors) -> list[dict[str, str]]:
    rows = []
    for sc in SCENARIOS:
        row = {"scenario": SCENARIO_LABELS[sc]}
        for name in MAIN_ESTIMATORS:
            sel = _sel(records, preset=preset, study="main", sensors=sensors, scenario=sc, estimator=name)
            vals = [r["exit_total_m"] for r in sel]
            row[name] = _capped(_med_p90(vals) if sensors == "realistic" else _med(vals), sel)
        rows.append(row)
    return rows


def max_table(records, preset) -> list[dict[str, str]]:
    rows = []
    for sc in SCENARIOS:
        row = {"scenario": SCENARIO_LABELS[sc]}
        for name in MAIN_ESTIMATORS:
            sel = _sel(records, preset=preset, study="main", sensors="realistic", scenario=sc, estimator=name)
            row[name] = _med([r["tunnel_max_m"] for r in sel])
        rows.append(row)
    return rows


def heading_announcement_table(records, preset) -> list[dict[str, str]]:
    rows = []
    for sc in SCENARIOS:
        row = {"scenario": SCENARIO_LABELS[sc]}
        dc = _sel(
            records, preset=preset, study="main", sensors="realistic", scenario=sc, estimator="dr_calibrated"
        )
        row["dr_calibrated |heading err.|"] = _med([abs(r["heading_error_deg"]) for r in dc], "{:.2f}°")
        for name in MAIN_ESTIMATORS:
            sel = _sel(records, preset=preset, study="main", sensors="realistic", scenario=sc, estimator=name)
            v = np.array([r["announcement_error_s"] for r in sel], dtype=float)
            row[f"{name} announce"] = (
                f"{np.nanmedian(np.abs(v)):.0f} ({np.nanmean(v):+.0f})" if np.isfinite(v).any() else "missed"
            )
        rows.append(row)
    return rows


def sweep_table(records, preset, study, label, fmt) -> list[dict[str, str]]:
    rows = []
    values = sorted({r["value"] for r in _sel(records, preset=preset, study=study)})
    for val in values:
        sel_v = _sel(records, preset=preset, study=study, value=val)
        dc = [r for r in sel_v if r["estimator"] == "dr_calibrated"]
        row = {label: fmt.format(val), "time in tunnel [s]": _med([r["tunnel_time_s"] for r in dc])}
        for name in MAIN_ESTIMATORS:
            sel = [r for r in sel_v if r["estimator"] == name]
            row[name] = _capped(_med([r["exit_total_m"] for r in sel]), sel)
        rows.append(row)
    return rows


def tables_markdown(records, names, seeds) -> str:
    out = [
        "# Traffic study: generated tables\n",
        "Preset roads and drivers. Ideal = error-free sensors and GPS, traffic seed 0. Realistic = preset "
        f"sensor and GPS errors, {len(seeds)} runs (seed k for sensors, GPS and traffic events). Sweeps: "
        f"realistic, {max(1, len(seeds) // 2)} runs per value, medians. § = a route estimator reached the "
        "route end D before C in that many runs (its error is then capped by the route length).\n",
    ]
    for pid, name in names.items():
        out.append(f"## {name}\n")
        out.append("**Scenario facts (medians):**\n")
        out.append(markdown_table(scenario_facts(records, pid)) + "\n")
        out.append("**Ideal sensors: error at C [m]:**\n")
        out.append(markdown_table(error_table(records, pid, "ideal")) + "\n")
        out.append("**Realistic sensors: error at C [m], median (p90):**\n")
        out.append(markdown_table(error_table(records, pid, "realistic")) + "\n")
        out.append("**Realistic sensors: maximum error in the tunnel [m], median:**\n")
        out.append(markdown_table(max_table(records, pid)) + "\n")
        out.append("**Realistic sensors: heading error and exit-announcement timing [s], median |error| "
                   "(signed mean; + = late):**\n")  # fmt: skip
        out.append(markdown_table(heading_announcement_table(records, pid)) + "\n")
        out.append("**Sweep: portal speed drop (T1, no jitter), error at C [m], median:**\n")
        out.append(markdown_table(sweep_table(records, pid, "portal_drop", "drop", "{:.0f} km/h")) + "\n")
        out.append("**Sweep: number of stops (T3), error at C [m], median:**\n")
        out.append(markdown_table(sweep_table(records, pid, "stop_count", "stops", "{:.0f}")) + "\n")
    return "\n".join(out)


# ---------------------------------------------------------------------- figures
def plot_figures(records, names, out: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2,
        "ytick.color": INK_2, "text.color": INK, "axes.titlesize": 9, "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    })  # fmt: skip
    presets = list(names)
    paths = []

    # Figure 1: error at C, scenarios x estimators, realistic sensors.
    bounds = np.array([0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 1e9])
    cmap, norm = ListedColormap(BLUES), BoundaryNorm(bounds, len(BLUES))
    fig, axes = plt.subplots(1, len(presets), figsize=(5.4 * len(presets), 4.2), sharey=True)
    for ax, pid in zip(np.atleast_1d(axes), presets, strict=True):
        real = _sel(records, preset=pid, study="main", sensors="realistic")
        grid = np.array([
            [np.median([r["exit_total_m"] for r in _sel(real, scenario=sc, estimator=n)])
             for n in MAIN_ESTIMATORS]
            for sc in SCENARIOS
        ])  # fmt: skip
        capped = np.array([
            [_mostly_capped(_sel(real, scenario=sc, estimator=n)) for n in MAIN_ESTIMATORS]
            for sc in SCENARIOS
        ])  # fmt: skip
        ax.imshow(grid, cmap=cmap, norm=norm, aspect="auto")
        for (r, c), v in np.ndenumerate(grid):
            ax.text(
                c,
                r,
                ("≥" if capped[r, c] else "") + f"{v:.0f}",
                ha="center",
                va="center",
                fontsize=8,
                color=INK if norm(v) < 7 else "#ffffff",
            )
        ax.set_xticks(range(len(MAIN_ESTIMATORS)), short_ticks(MAIN_ESTIMATORS), fontsize=8)
        ax.set_yticks(range(len(SCENARIOS)), [SCENARIO_LABELS[s] for s in SCENARIOS])
        ax.set_title(names[pid], color=INK)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
    title = (
        "Median horizontal error at the tunnel exit C [m], realistic sensors; darker = larger (log bins); "
        "≥ = capped: the estimate reached the route end D"
    )
    fig.suptitle(title, color=INK, fontsize=11)
    fig.tight_layout()
    paths.append(out / "exit_heatmap.png")
    fig.savefig(paths[-1], dpi=130, bbox_inches="tight")
    plt.close(fig)

    # Figure 2: the two sweeps; lines = estimators (fixed colour order), rows = sweeps, columns = presets.
    shown = ["dr_calibrated", "dr_filtered", "route_imu", "route_hold"]
    fig, axes = plt.subplots(2, len(presets), figsize=(5.2 * len(presets), 7.0), sharey="row", squeeze=False)
    for j, pid in enumerate(presets):
        for i, (study, xlabel) in enumerate((("portal_drop", "portal speed drop [km/h]"),
                                             ("stop_count", "number of stops in the tunnel"))):  # fmt: skip
            ax = axes[i, j]
            vals = sorted({r["value"] for r in _sel(records, preset=pid, study=study)})
            for k, name in enumerate(shown):
                sel = _sel(records, preset=pid, study=study, estimator=name)
                at = [[r for r in sel if r["value"] == v] for v in vals]
                y = np.maximum([np.median([r["exit_total_m"] for r in g]) for g in at], 1.0)
                cap = np.array([_mostly_capped(g) for g in at])
                ax.plot(vals, y, color=SERIES[k], linewidth=2, label=SHORT[name])
                ax.plot(np.array(vals)[~cap], y[~cap], "o", color=SERIES[k], markersize=5)
                ax.plot(np.array(vals)[cap], y[cap], "o", markerfacecolor=SURFACE, markeredgecolor=SERIES[k],
                        markersize=6, markeredgewidth=1.5)  # fmt: skip
            if study == "stop_count":
                ax.set_xticks(vals)
            ax.set_yscale("log")
            ax.grid(True, color=GRID, linewidth=0.6)
            ax.spines[["top", "right"]].set_visible(False)
            ax.set_xlabel(xlabel)
            if j == 0:
                ax.set_ylabel("median error at C [m]")
            if i == 0:
                ax.set_title(names[pid], color=INK)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles, labels, loc="upper center", ncol=len(shown), frameon=False, bbox_to_anchor=(0.5, 1.02)
    )
    title = "Where the methods begin to fail (realistic sensors; hollow marker = capped at the route end D)"
    fig.suptitle(title, y=1.06, color=INK, fontsize=11)
    fig.tight_layout()
    paths.append(out / "sweeps.png")
    fig.savefig(paths[-1], dpi=130, bbox_inches="tight")
    plt.close(fig)
    return paths


# ---------------------------------------------------------------------- main
def write_outputs(records, names, seeds, out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "runs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(
            {k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()} for r in records
        )
    (out / "tables.md").write_text(tables_markdown(records, names, seeds), encoding="utf-8")
    paths = [out / "runs.csv", out / "tables.md"]
    try:
        paths += plot_figures(records, names, out)
    except ImportError:
        print("matplotlib not installed (dev dependency): figures skipped")
    return paths


def read_records(path: Path) -> list[dict]:
    """Records from a saved ``runs.csv`` (to regenerate tables and figures without re-running)."""
    out = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rec: dict = {}
            for k, v in row.items():
                if k in ("preset", "sensors", "study", "scenario", "estimator"):
                    rec[k] = v
                elif k == "seed":
                    rec[k] = int(v)
                elif k == "route_end_reached":
                    rec[k] = v == "True"
                else:
                    rec[k] = float(v)
            out.append(rec)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=20, help="realistic runs per scenario and preset")
    parser.add_argument("--presets", nargs="*", default=list(list_presets()))
    parser.add_argument("--workers", type=int, default=2, help="parallel processes (memory: ~0.5 GB each)")
    parser.add_argument("--out", type=Path, default=Path("docs/traffic_study"))
    parser.add_argument(
        "--from-csv", type=Path, default=None, help="regenerate outputs from a saved runs.csv"
    )
    args = parser.parse_args()
    seeds = list(range(args.seeds))
    t0 = time.perf_counter()
    if args.from_csv is not None:
        records = read_records(args.from_csv)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(study_preset, args.presets, [seeds] * len(args.presets)))
        records = [r for recs in results for r in recs]
    names = {pid: load_preset(pid).name for pid in args.presets}
    for p in write_outputs(records, names, seeds, args.out):
        print("wrote", p)
    print(f"{len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
