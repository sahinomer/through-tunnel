"""Controlled calibration-error experiment (D34): identical runs with and without the error.

For each preset and sensor seed the scenario is simulated once (preset drive, sensor and GPS seed =
run index). The estimators then run on these identical observations once without calibration error
and once per error case, so every comparison is paired: only the orientation the estimators assume
differs. Everything else (drive, sensor noise and bias, GPS errors and outage) is unchanged.

    uv run python -m throughtunnel.evaluation.calibration_study --seeds 10
"""

from __future__ import annotations

import argparse
import math
import time

import numpy as np

from throughtunnel.evaluation.experiment import compare_estimators, markdown_table
from throughtunnel.evaluation.metrics import TrackEvaluation
from throughtunnel.positioning import MAIN_ESTIMATORS
from throughtunnel.scenario import (
    list_presets,
    load_preset,
    run_scenario,
    with_calibration,
    with_sensor_config,
)
from throughtunnel.sensors.mounting import CalibrationErrorConfig


def _error(yaw: float = 0.0, pitch: float = 0.0, roll: float = 0.0) -> CalibrationErrorConfig:
    return CalibrationErrorConfig(enabled=True, yaw_deg=yaw, pitch_deg=pitch, roll_deg=roll)


CASES: dict[str, CalibrationErrorConfig] = {
    "none": CalibrationErrorConfig(),
    "yaw +1°": _error(yaw=1.0),
    "yaw +2°": _error(yaw=2.0),
    "yaw −2°": _error(yaw=-2.0),
    "yaw +5°": _error(yaw=5.0),
    "pitch +0.05°": _error(pitch=0.05),
    "pitch +0.1°": _error(pitch=0.1),
    "pitch +0.25°": _error(pitch=0.25),
    "pitch +0.5°": _error(pitch=0.5),
    "roll +2°": _error(roll=2.0),
    "roll +5°": _error(roll=5.0),
    "typical (2°, 0.5°, 0.5°)": CalibrationErrorConfig(enabled=True),
}
GROWTH_CASES = ("none", "yaw +2°", "pitch +0.1°", "pitch +0.5°", "typical (2°, 0.5°, 0.5°)")
GROWTH_ESTIMATORS = ("dr_calibrated", "route_imu")
GROWTH_TIMES_S = (15.0, 30.0, 60.0, 90.0, 120.0)
G = 9.80

Runs = dict[str, dict[str, list[TrackEvaluation]]]  # case -> estimator -> one evaluation per run


def run_study(preset_id: str, seeds: range, cases: dict[str, CalibrationErrorConfig] = CASES):
    cfg = load_preset(preset_id)
    base = run_scenario(cfg)
    runs: Runs = {c: {} for c in cases}
    results = []
    for seed in seeds:
        imu = cfg.imu.model_copy(update={"errors": cfg.imu.errors.model_copy(update={"seed": seed})})
        res = with_sensor_config(base, imu=imu, gnss=cfg.gnss.model_copy(update={"seed": seed}))
        results.append(res)
        for case, cal in cases.items():
            for ev in compare_estimators(with_calibration(res, cal), list(MAIN_ESTIMATORS)).evaluations:
                runs[case].setdefault(ev.name, []).append(ev)
    return base, results, runs


def _cell(vals: np.ndarray) -> str:
    vals = vals[np.isfinite(vals)]
    return f"{np.median(vals):.0f} ({np.percentile(vals, 90):.0f})" if len(vals) else "n/a"


def exit_error_rows(runs: Runs) -> list[dict[str, str]]:
    """Median (p90) horizontal error at the tunnel exit C per case and estimator."""
    rows = []
    for case, by_est in runs.items():
        row = {"calibration error": case}
        for name, evals in by_est.items():
            row[MAIN_ESTIMATORS[name].name] = _cell(np.array([e.summary["exit_total_m"] for e in evals]))
        rows.append(row)
    return rows


def paired_shift_rows(runs: Runs) -> list[dict[str, str]]:
    """Per-run change of the along-track error at C caused by the calibration error (the same run without
    it subtracted): median [min, max] over the runs. + = estimate further ahead (or less behind)."""
    rows = []
    none = runs["none"]
    for case, by_est in runs.items():
        if case == "none":
            continue
        row = {"calibration error": case}
        for name, evals in by_est.items():
            pairs = zip(evals, none[name], strict=True)
            d = np.array([e.summary["exit_along_m"] - b.summary["exit_along_m"] for e, b in pairs])
            row[name] = f"{np.median(d):+.0f} [{d.min():+.0f}, {d.max():+.0f}]"
        rows.append(row)
    return rows


def growth_rows(results, runs: Runs) -> list[dict[str, str]]:
    """Median horizontal error vs. time since GPS loss (within the outage), for selected cases."""
    rows = []
    for tau in GROWTH_TIMES_S:
        row = {"time since GPS loss": f"{tau:g} s"}
        for name in GROWTH_ESTIMATORS:
            for case in GROWTH_CASES:
                vals = []
                for res, ev in zip(results, runs[case][name], strict=True):
                    t = res.gnss_events.loss_t + tau
                    ok = t < min(res.gnss_events.reacquire_t, ev.t[-1])
                    vals.append(float(np.interp(t, ev.t, ev.total)) if ok else math.nan)
                row[f"{name}: {case}"] = _cell(np.array(vals))
        row["½·g·sin(0.1°)·τ²"] = f"{0.5 * G * math.sin(math.radians(0.1)) * tau**2:.0f}"
        row["½·g·sin(0.5°)·τ²"] = f"{0.5 * G * math.sin(math.radians(0.5)) * tau**2:.0f}"
        rows.append(row)
    return rows


def geometry_note(base) -> str:
    """Tunnel facts that explain the yaw sensitivity: net heading change and integrated |a_lat|."""
    sec, tr = base.sections, base.truth
    m = (tr.t >= sec.entrance_t) & (tr.t <= sec.exit_t)
    net_heading = math.degrees(math.remainder(float(tr.yaw[m][-1] - tr.yaw[m][0]), 2 * math.pi))
    a_lat_int = float(np.trapezoid(tr.accel_lat[m], tr.t[m]))
    a_lat_abs = float(np.trapezoid(np.abs(tr.accel_lat[m]), tr.t[m]))
    return (
        f"Tunnel B–C crossed in {sec.exit_t - sec.entrance_t:.0f} s (preset drive); net heading change "
        f"{net_heading:+.0f}°; ∫a_lat dt = {a_lat_int:+.1f} m/s (∫|a_lat| dt = {a_lat_abs:.1f} m/s)."
    )


def report(preset_ids: list[str], seeds: range) -> str:
    out = []
    for pid in preset_ids:
        t0 = time.perf_counter()
        base, results, runs = run_study(pid, seeds)
        out.append(f"### {base.config.name}\n")
        out.append(
            f"{geometry_note(base)} {len(seeds)} runs (sensor/GPS seeds {seeds.start}–{seeds.stop - 1}), "
            f"same drive; every case uses the identical observations. Computed in "
            f"{time.perf_counter() - t0:.0f} s.\n"
        )
        out.append("Horizontal error at C [m], median (p90):\n")
        out.append(markdown_table(exit_error_rows(runs)) + "\n")
        out.append(
            "Along-track shift at C caused by the calibration error (paired) [m], median [min, max]:\n"
        )
        out.append(markdown_table(paired_shift_rows(runs)) + "\n")
        out.append("Horizontal error vs. time since GPS loss [m], median (p90):\n")
        out.append(markdown_table(growth_rows(results, runs)) + "\n")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=10, help="number of runs per preset")
    parser.add_argument("--presets", nargs="*", default=list(list_presets()))
    args = parser.parse_args()
    print(report(args.presets, range(args.seeds)))


if __name__ == "__main__":
    main()
