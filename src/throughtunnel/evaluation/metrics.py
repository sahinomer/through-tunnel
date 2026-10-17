"""Evaluation of estimate tracks against the hidden ground truth (D23, PD2, PD3).

This is the only place where estimates and truth meet. The reference is the true **phone** position
(the GPS antenna, reference point + lever arm), evaluated exactly at each estimate timestamp.

Error vector e = estimate - truth (horizontal ENU):
* along-track = e · t̂ (+ = estimate ahead of the vehicle);
* cross-track = e · n̂ (+ = estimate to the left);
* total = |e|.

t̂ and n̂ are the true heading and its left normal at the same time. Defining errors on the truth side
avoids mixing the map's and the true path's arc lengths.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from throughtunnel.positioning.runner import EstimateTrack
from throughtunnel.scenario import SimulationResult, truth_at

RECOVERY_THRESHOLD_M = 10.0
RECOVERY_HOLD_S = 5.0


@dataclass(frozen=True)
class TrackEvaluation:
    name: str
    label: str
    t: NDArray[np.float64]
    along: NDArray[np.float64]
    cross: NDArray[np.float64]
    total: NDArray[np.float64]
    true_s: NDArray[np.float64]  # true distance along the driven path
    phase: NDArray[np.str_]  # "approach" | "tunnel" | "recovery" | "open" (no tunnel)
    summary: dict[str, float] = field(default_factory=dict)
    announcement_time_error_s: float = math.nan  # + = late; NaN = no tunnel or never announced
    announcement_distance_error_m: float = math.nan  # + = late (vehicle already past the point)
    # The estimator's own 1σ along-route uncertainty at each time (NaN where it reports none; step 6.1)
    position_std_m: NDArray[np.float64] = field(default_factory=lambda: np.empty(0))
    # Uncertainty-aware announcement (step 6.2): time error (+ = late; NaN = never fired) and its kind
    aware_announcement_time_error_s: float = math.nan
    aware_announcement_precise: bool | None = None


def evaluate_track(
    track: EstimateTrack,
    result: SimulationResult,
    recovery_threshold_m: float = RECOVERY_THRESHOLD_M,
    recovery_hold_s: float = RECOVERY_HOLD_S,
) -> TrackEvaluation:
    t = track.t
    truth = truth_at(result, t)
    phone = truth.point_enu(result.config.imu.mount.lever_arm_m)
    de, dn = track.east - phone[:, 0], track.north - phone[:, 1]
    c, s = np.cos(truth.yaw), np.sin(truth.yaw)
    along, cross = de * c + dn * s, -de * s + dn * c
    total = np.hypot(de, dn)

    sec, ev = result.sections, result.gnss_events
    if sec is None:
        phase = np.full(len(t), "open")
    else:
        phase = np.where(
            truth.s < sec.entrance_s, "approach", np.where(truth.s <= sec.exit_s, "tunnel", "recovery")
        )

    def at(time: float, arr: NDArray[np.float64]) -> float:
        return float(np.interp(time, t, arr)) if len(t) and t[0] <= time <= t[-1] else math.nan

    def stat(arr: NDArray[np.float64], mask: NDArray[np.bool_], fn) -> float:
        return float(fn(arr[mask])) if mask.any() else math.nan

    summary: dict[str, float] = {}
    gps = phase == "approach"
    summary["approach_rms_m"] = stat(total, gps, lambda x: np.sqrt(np.mean(x**2)))
    if sec is not None:
        tunnel = phase == "tunnel"
        outage = (t >= ev.loss_t) & (t < ev.reacquire_t)
        summary["tunnel_rms_m"] = stat(total, tunnel, lambda x: np.sqrt(np.mean(x**2)))
        summary["tunnel_max_m"] = stat(total, tunnel, np.max)
        summary["outage_max_m"] = stat(total, outage, np.max)
        summary["exit_total_m"] = at(sec.exit_t, total)
        summary["exit_along_m"] = at(sec.exit_t, along)
        summary["exit_cross_m"] = at(sec.exit_t, cross)
        summary["outage_s"] = ev.reacquire_t - ev.loss_t
        summary["recovery_time_s"] = (
            _recovery_time(t, total, ev.reacquire_t, recovery_threshold_m, recovery_hold_s) - sec.exit_t
        )
    summary["final_m"] = float(total[-1]) if len(total) else math.nan
    # The estimator's own uncertainty (NaN if none reported): at C, and when it announced (what it knew then)
    std = track.position_std_m
    if sec is not None:
        summary["exit_std_m"] = at(sec.exit_t, std)
        summary["announce_std_m"] = (
            at(track.announcement_t, std) if math.isfinite(track.announcement_t) else math.nan
        )

    # Announcement (D32): the estimator's announcement vs. the vehicle truly reaching the same point.
    time_err = dist_err = aware_err = math.nan
    if sec is not None and math.isfinite(track.aware_announcement_t):
        aware_err = track.aware_announcement_t - sec.announcement_t
    if sec is not None and math.isfinite(track.announcement_t):
        time_err = track.announcement_t - sec.announcement_t
        dist_err = (
            float(np.interp(track.announcement_t, result.motion.t, result.motion.s)) - sec.announcement_s
        )
    return TrackEvaluation(
        name=track.name,
        label=track.label,
        t=t,
        along=along,
        cross=cross,
        total=total,
        true_s=truth.s,
        phase=phase,
        summary=summary,
        announcement_time_error_s=time_err,
        announcement_distance_error_m=dist_err,
        position_std_m=std,
        aware_announcement_time_error_s=aware_err,
        aware_announcement_precise=track.aware_announcement_precise,
    )


def _recovery_time(t, total, start: float, threshold: float, hold: float) -> float:
    """First time >= start from which the error stays below ``threshold`` for ``hold`` seconds."""
    if not math.isfinite(start):
        return math.nan
    ok = total < threshold
    idx = np.flatnonzero(t >= start)
    for i in idx:
        window = (t >= t[i]) & (t <= t[i] + hold)
        if t[-1] < t[i] + hold:
            return math.nan
        if ok[window].all():
            return float(t[i])
    return math.nan
