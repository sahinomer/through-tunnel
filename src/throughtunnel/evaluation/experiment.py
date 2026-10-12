"""Running and comparing estimators on identical observations (D19), incl. Monte Carlo over seeds."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from throughtunnel.evaluation.metrics import TrackEvaluation, evaluate_track
from throughtunnel.positioning import ESTIMATORS, EstimateTrack, run_estimator
from throughtunnel.scenario import ScenarioConfig, SimulationResult, run_scenario, with_sensor_config


@dataclass(frozen=True)
class Comparison:
    tracks: list[EstimateTrack]
    evaluations: list[TrackEvaluation]


def compare_estimators(result: SimulationResult, names: Sequence[str] | None = None) -> Comparison:
    """Run the named estimators (default: all registered) on the result's observations."""
    obs = result.observations()
    tracks = [run_estimator(ESTIMATORS[n](obs.route), obs) for n in (names or list(ESTIMATORS))]
    return Comparison(tracks=tracks, evaluations=[evaluate_track(tr, result) for tr in tracks])


def monte_carlo(
    config: ScenarioConfig, seeds: Iterable[int], names: Sequence[str] | None = None
) -> dict[str, list[TrackEvaluation]]:
    """Same drive (scenario seed fixed), different IMU and GPS error realisations per seed."""
    base = run_scenario(config)
    out: dict[str, list[TrackEvaluation]] = {}
    for seed in seeds:
        imu = config.imu.model_copy(update={"errors": config.imu.errors.model_copy(update={"seed": seed})})
        gnss = config.gnss.model_copy(update={"seed": seed})
        res = with_sensor_config(base, imu=imu, gnss=gnss)
        for ev in compare_estimators(res, names).evaluations:
            out.setdefault(ev.name, []).append(ev)
    return out


SUMMARY_COLUMNS = {
    "exit_total_m": "error at C [m]",
    "tunnel_max_m": "max in tunnel [m]",
    "tunnel_rms_m": "RMS in tunnel [m]",
    "recovery_time_s": "recovered after C [s]",
}


def summary_rows(runs: dict[str, list[TrackEvaluation]]) -> list[dict[str, str]]:
    """Median and 90th percentile per estimator (robust to the occasional outlier run)."""
    rows = []
    for evals in runs.values():
        row = {"estimator": evals[0].label, "runs": str(len(evals))}
        for key, title in SUMMARY_COLUMNS.items():
            vals = np.array([e.summary.get(key, math.nan) for e in evals])
            row[title] = _median_p90(np.abs(vals) if key != "recovery_time_s" else vals)
        for target in evals[0].announcement_time_error_s:
            vals = np.array([e.announcement_time_error_s[target] for e in evals])
            row[f"announce {target} [s]"] = _median_p90(np.abs(vals), signed_mean=float(np.nanmean(vals)))
        rows.append(row)
    return rows


def markdown_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    cols = list(rows[0])
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(r[c] for c in cols) + " |" for r in rows]
    return "\n".join(lines)


def _median_p90(vals: np.ndarray, signed_mean: float | None = None) -> str:
    vals = vals[np.isfinite(vals)]
    if not len(vals):
        return "n/a"
    text = f"{np.median(vals):.1f} (p90 {np.percentile(vals, 90):.1f})"
    if signed_mean is not None:
        text += f", mean {signed_mean:+.1f}"
    return text
