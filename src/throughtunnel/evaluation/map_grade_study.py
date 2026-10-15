"""Map-grade study (D39): how the road grade from the map changes the estimators' performance.

Every simulated run is evaluated twice, with the map grade off and on. Nothing else differs: the
switch is information for the estimators only, so the drive, sensor data and GPS are identical
(paired comparison). Two blocks:

* **slope**: the eight road profiles of the slope study (free flow), same sensors and seeds, so the
  "off" results reproduce docs/slope_study;
* **traffic**: stop-and-go (T3) on four of the profiles. Traffic lengthens the outage, and the gravity
  leakage of a grade change grows with the square of the outage time, so this is the case flagged as
  worst for the IMU in the traffic study.

Sensors as in the slope study: *ideal* (error-free IMU and GPS, one run) isolates what the grade
correction leaves; *realistic* (preset IMU and GPS errors) uses seed k for the sensors, GPS and traffic
of run k.

    uv run python -m throughtunnel.evaluation.map_grade_study --seeds 20 --out docs/map_grade_study

Writes ``runs.csv``, ``curves.csv``, ``tables.md`` and (with matplotlib, a dev dependency)
``exit_heatmap.png`` and ``growth.png``. ``--from-csv`` regenerates the tables and figures.
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
from throughtunnel.evaluation.factor_study import _nanmedian_rows
from throughtunnel.evaluation.slope_study import (
    PROFILES,
    Profile,
    ideal_sensors,
    profile_config,
    realistic_sensors,
)
from throughtunnel.positioning import ESTIMATORS
from throughtunnel.scenario import (
    MapDataConfig,
    list_presets,
    load_preset,
    run_scenario,
    truth_at,
    with_map_data,
    with_sensor_config,
)
from throughtunnel.vehicle.traffic import TrafficConfig

BY_KEY = {p.key: p for p in PROFILES}
TRAFFIC_PROFILES = ("flat", "up2", "down2", "v4")
GROWTH_TIMES_S = (30.0, 60.0, 120.0, 240.0)
CURVE_GRID_S = np.arange(0.0, 601.0, 2.0)
IMU_ESTIMATORS = ("dr_raw", "dr_calibrated", "dr_filtered", "route_imu")


def run_records(res, tags: dict) -> tuple[list[dict], dict]:
    """Records and error curves (vs time since GPS loss) of all estimators, map grade off and on."""
    loss, c_t = res.gnss_events.loss_t, res.sections.exit_t
    end = min(res.gnss_events.reacquire_t, c_t)
    route_len = res.route_map.length_m
    records, curves = [], {}
    for grade in (False, True):
        cmp = compare_estimators(with_map_data(res, MapDataConfig(road_grade=grade)))
        for track, ev in zip(cmp.tracks, cmp.evaluations, strict=True):
            before_c = track.t < c_t
            k = int(np.flatnonzero(before_c)[-1])
            rd = track.route_distance[before_c]
            s = ev.summary
            rec = {
                **tags,
                "map_grade": grade,
                "estimator": ev.name,
                "exit_total_m": s["exit_total_m"],
                "exit_along_m": s["exit_along_m"],
                "tunnel_max_m": s["tunnel_max_m"],
                "speed_error_mps": float(track.speed[k] - truth_at(res, [track.t[k]]).speed[0]),
                "route_end_reached": bool(
                    ev.name.startswith("route") and len(rd) and rd.max() >= route_len - 1
                ),
                "announcement_error_s": ev.announcement_time_error_s,
                "outage_to_c_s": end - loss,
            }  # fmt: skip
            t = loss + CURVE_GRID_S
            curve = np.where(t <= end, np.interp(t, ev.t, ev.total), np.nan)
            for tau in GROWTH_TIMES_S:
                rec[f"err_{tau:g}s_m"] = float(np.interp(tau, CURVE_GRID_S, curve))
            records.append(rec)
            curves[(grade, ev.name)] = curve
    return records, curves


def study_preset(preset_id: str, seeds: list[int]):
    cfg = load_preset(preset_id)
    records: list[dict] = []
    curves: dict[tuple, list[np.ndarray]] = {}
    blocks = [("slope", p, TrafficConfig()) for p in PROFILES]
    blocks += [("traffic", BY_KEY[k], None) for k in TRAFFIC_PROFILES]
    for block, profile, traffic in blocks:
        print(f"{preset_id}: {block} {profile.key}", flush=True)
        road = profile_config(cfg, profile)
        runs = [("ideal", 0)] + [("realistic", k) for k in seeds]
        base = None
        for sensors, seed in runs:
            if traffic is None:  # stop-and-go: run k also draws its own traffic events
                t = TrafficConfig(scenario="stop_and_go", seed=seed)
                base = run_scenario(cfg.model_copy(update={"road_profile": road, "traffic": t}))
            elif base is None:
                base = run_scenario(cfg.model_copy(update={"road_profile": road, "traffic": traffic}))
            imu, gnss = ideal_sensors(cfg) if sensors == "ideal" else realistic_sensors(cfg, seed)
            res = with_sensor_config(base, imu=imu, gnss=gnss)
            tags = {"preset": preset_id, "block": block, "profile": profile.key}
            tags |= {"sensors": sensors, "seed": seed}
            recs, cur = run_records(res, tags)
            records += recs
            for (grade, name), c in cur.items():
                curves.setdefault((block, sensors, profile.key, grade, name), []).append(c)
    medians = {k: _nanmedian_rows(np.array(v)) for k, v in curves.items()}
    return records, medians


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


def _profiles(block: str) -> list[Profile]:
    return list(PROFILES) if block == "slope" else [BY_KEY[k] for k in TRAFFIC_PROFILES]


def ideal_table(records, preset, block) -> list[dict[str, str]]:
    """Error at C [m], map grade off -> on (ideal sensors, one run)."""
    rows = []
    for p in _profiles(block):
        sel = _sel(records, preset=preset, block=block, profile=p.key, sensors="ideal")
        by = {(r["map_grade"], r["estimator"]): r for r in sel}
        row = {"profile": p.label}
        for name in ESTIMATORS:
            off, on = by[(False, name)], by[(True, name)]
            row[name] = f"{off['exit_total_m']:.0f}{' §' if off['route_end_reached'] else ''} → " + (
                f"{on['exit_total_m']:.1f}{' §' if on['route_end_reached'] else ''}"
            )
        rows.append(row)
    return rows


def realistic_table(records, preset, block, key="exit_total_m") -> list[dict[str, str]]:
    """Median (p90) of ``key``, map grade off | on."""
    rows = []
    for p in _profiles(block):
        row = {"profile": p.label}
        for name in ESTIMATORS:
            cells = []
            for grade in (False, True):
                sel = _sel(
                    records, preset=preset, block=block, profile=p.key, sensors="realistic",
                    estimator=name, map_grade=grade,
                )  # fmt: skip
                cells.append(_med_p90([abs(r[key]) for r in sel]) + _flag(sel))
            row[name] = " / ".join(cells)
        rows.append(row)
    return rows


def paired_table(records, preset, block) -> list[dict[str, str]]:
    """Per run: |error at C| with grade minus without (same run), median [min, max]."""
    rows = []
    for p in _profiles(block):
        row = {"profile": p.label}
        for name in ESTIMATORS:
            sel = _sel(
                records, preset=preset, block=block, profile=p.key, sensors="realistic", estimator=name
            )
            off = {r["seed"]: r["exit_total_m"] for r in sel if not r["map_grade"]}
            d = np.array([r["exit_total_m"] - off[r["seed"]] for r in sel if r["map_grade"]])
            row[name] = f"{np.median(d):+.0f} [{d.min():+.0f}, {d.max():+.0f}]"
        rows.append(row)
    return rows


def vs_flat_table(records, preset, block) -> list[dict[str, str]]:
    """With map grade: does a sloped road get back to the flat-road result? Median |error at C| [m]."""
    rows = []
    flat = {
        (r["seed"], r["estimator"]): r["exit_total_m"]
        for r in _sel(
            records, preset=preset, block=block, profile="flat", sensors="realistic", map_grade=False
        )
    }
    for p in _profiles(block)[1:]:
        row = {"profile": p.label}
        for name in IMU_ESTIMATORS:
            sel = _sel(
                records, preset=preset, block=block, profile=p.key, sensors="realistic",
                estimator=name, map_grade=True,
            )  # fmt: skip
            d = np.array([r["exit_total_m"] - flat[(r["seed"], name)] for r in sel])
            row[name] = f"{np.median(d):+.0f} [{np.percentile(d, 10):+.0f}, {np.percentile(d, 90):+.0f}]"
        rows.append(row)
    return rows


def announcement_table(records, preset, block) -> list[dict[str, str]]:
    rows = []
    for p in _profiles(block):
        row = {"profile": p.label}
        for name in ESTIMATORS:
            cells = []
            for grade in (False, True):
                sel = _sel(
                    records, preset=preset, block=block, profile=p.key, sensors="realistic",
                    estimator=name, map_grade=grade,
                )  # fmt: skip
                v = np.array([r["announcement_error_s"] for r in sel], dtype=float)
                missed = int(np.isnan(v).sum())
                cell = f"{np.nanmedian(np.abs(v)):.1f}" if np.isfinite(v).any() else "–"
                cells.append(cell + (f" ({missed} missed)" if missed else ""))
            row[name] = " / ".join(cells)
        rows.append(row)
    return rows


def tables_markdown(records, names, seeds) -> str:
    out = [
        "# Map-grade study: generated tables\n",
        "Each run is evaluated with the map grade off and on (paired: identical drive, sensor data and GPS). "
        "Ideal = error-free sensors and GPS (one run); realistic = preset sensor and GPS errors, "
        f"{len(seeds)} runs (seeds {seeds[0]}–{seeds[-1]}). Cells with two values are **off / on**. "
        "§ = the route estimator reached the route end D before C in that many runs (its error is "
        "then capped by the route length).\n",
    ]
    for pid, name in names.items():
        out.append(f"## {name}\n")
        for block, title in (("slope", "Free flow"), ("traffic", "Stop-and-go traffic (T3)")):
            sel = _sel(records, preset=pid, block=block, sensors="realistic", estimator="dr_calibrated")
            if not sel:
                continue
            outage = np.median([r["outage_to_c_s"] for r in sel])
            out.append(f"### {title}\n")
            out.append(f"Median dead-reckoning time from GPS loss to C: {outage:.0f} s.\n")
            out.append("**Ideal sensors: error at C [m], map grade off → on:**\n")
            out.append(markdown_table(ideal_table(records, pid, block)) + "\n")
            out.append("**Realistic sensors: error at C [m], median (p90), off / on:**\n")
            out.append(markdown_table(realistic_table(records, pid, block)) + "\n")
            out.append("**Realistic sensors: maximum error in the tunnel [m], median (p90), off / on:**\n")
            out.append(markdown_table(realistic_table(records, pid, block, "tunnel_max_m")) + "\n")
            out.append("**Realistic sensors: paired change of the error at C from switching the grade "
                       "on [m], median [min, max]:**\n")  # fmt: skip
            out.append(markdown_table(paired_table(records, pid, block)) + "\n")
            out.append("**Realistic sensors, map grade on: error at C minus the same run on the flat road "
                       "without grade [m], median [p10, p90]:**\n")  # fmt: skip
            out.append(markdown_table(vs_flat_table(records, pid, block)) + "\n")
            out.append("**Realistic sensors: exit-announcement timing, median |error| [s], off / on:**\n")
            out.append(markdown_table(announcement_table(records, pid, block)) + "\n")
    return "\n".join(out)


# ---------------------------------------------------------------------- figures
def plot_figures(records, medians, names, out: Path) -> list[Path]:
    """Defined in ``map_grade_figures`` (kept apart so the study logic stays readable)."""
    from throughtunnel.evaluation.map_grade_figures import plot_figures as plot

    return plot(records, medians, names, out)


# ---------------------------------------------------------------------- I/O
def write_outputs(records, medians, names, seeds, out: Path, write_data: bool = True) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    if write_data:
        with open(out / "runs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(
                {k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()} for r in records
            )
        with open(out / "curves.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            head = ["preset", "block", "sensors", "profile", "map_grade", "estimator"]
            writer.writerow([*head, *[f"{t:g}" for t in CURVE_GRID_S]])
            for key, y in medians.items():
                writer.writerow([*key, *[f"{v:.3f}" if np.isfinite(v) else "" for v in y]])
        paths += [out / "runs.csv", out / "curves.csv"]
    (out / "tables.md").write_text(tables_markdown(records, names, seeds), encoding="utf-8")
    paths.append(out / "tables.md")
    try:
        paths += plot_figures(records, medians, names, out)
    except ImportError:
        print("matplotlib not installed (dev dependency): figures skipped")
    return paths


def read_records(path: Path) -> list[dict]:
    text_keys = ("preset", "block", "profile", "sensors", "estimator")
    out = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rec: dict = {}
            for k, v in row.items():
                if k in text_keys:
                    rec[k] = v
                elif k == "seed":
                    rec[k] = int(v)
                elif k in ("map_grade", "route_end_reached"):
                    rec[k] = v == "True"
                else:
                    rec[k] = float(v)
            out.append(rec)
    return out


def read_curves(path: Path) -> dict[tuple, np.ndarray]:
    out = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            pid, block, sensors, prof, grade, name, *vals = row
            y = np.array([float(v) if v else math.nan for v in vals])
            out[(pid, block, sensors, prof, grade == "True", name)] = y
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=20, help="realistic runs per scenario and preset")
    parser.add_argument("--presets", nargs="*", default=list(list_presets()))
    parser.add_argument("--workers", type=int, default=2, help="parallel processes (memory: ~0.5 GB each)")
    parser.add_argument("--out", type=Path, default=Path("docs/map_grade_study"))
    parser.add_argument("--from-csv", action="store_true", help="regenerate tables and figures from --out")
    args = parser.parse_args()
    seeds = list(range(args.seeds))
    t0 = time.perf_counter()
    if args.from_csv:
        records = read_records(args.out / "runs.csv")
        medians = read_curves(args.out / "curves.csv")
        presets = list(dict.fromkeys(r["preset"] for r in records))
        seeds = sorted({r["seed"] for r in records if r["sensors"] == "realistic"})
    else:
        presets = args.presets
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(study_preset, presets, [seeds] * len(presets)))
        records = [r for recs, _ in results for r in recs]
        medians = {
            (pid, *k): v for pid, (_, med) in zip(presets, results, strict=True) for k, v in med.items()
        }
    names = {pid: load_preset(pid).name for pid in presets}
    for p in write_outputs(records, medians, names, seeds, args.out, write_data=not args.from_csv):
        print("wrote", p)
    print(f"{len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
