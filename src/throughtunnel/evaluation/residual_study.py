"""Residual diagnostic (step 2 of docs/estimator_plan.md): what is left with ideal sensors and map grade?

Diagnostic only, no estimator change. The map-grade study left an unexplained residual with error-free
sensors in long outages (Eisenhower, stop-and-go, +2 %: 42 m at C), and the error-source benchmark a
12–13 m stop-and-go floor. Hypothesis: a steady offset in the grade-compensated forward channel.

With ideal sensors, standing on a grade φ, the calibrated forward axis (tilted by p above the true
vehicle forward axis) reads g·sin(φ + p); the estimator subtracts G·sin(φ − φ_cal), with G the
standard gravity and φ_cal the mean map grade the calibration reports to have absorbed. The leftover

    r = g·sin(φ + p) − G·sin(φ − φ_cal)
      = (g − G)·sin(φ − φ_cal)                 T1: gravity constant (simulator: normal gravity)
      + g·[sin(φ + p) − sin(φ − φ_cal)]        T2: levelling ≠ reported grade (≈ g·(p + φ_cal))

T2 is split into T2a, the half-sample lag of the per-interval IMU means (−(h/2)·(a_last − a_first)/T,
large when the calibration ends while braking), and T2b, a yaw error of the alignment leaking the
approach's mean lateral specific force into the levelling (−yaw·mean f_left).

is integrated twice over the outage (from the last fix to C, true φ along the true path) and compared
with the along-track error of ``dr_calibrated`` (no speed blending) at C. What the two terms do not
explain is the rest (position feedback at grade changes, the v ≥ 0 clamp at stops).

Variants per case: portal freeze (D46) off / on × the estimators' gravity standard / local. "Local" =
the simulator's normal gravity at the tunnel, set as the estimators' constant for this diagnostic; an
implementation would take it from the calibration's measured |f|.

    uv run python -m throughtunnel.evaluation.residual_study --out docs/residual_study
"""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from throughtunnel.evaluation.benchmark import git_commit, read_runs, write_runs
from throughtunnel.evaluation.experiment import compare_estimators, markdown_table
from throughtunnel.evaluation.map_grade_study import BY_KEY
from throughtunnel.evaluation.slope_study import ideal_sensors, profile_config
from throughtunnel.observations import ImuStream, Observations
from throughtunnel.positioning import map_grade, portal
from throughtunnel.positioning.alignment import GpsImuAlignment
from throughtunnel.positioning.runner import align_imu
from throughtunnel.scenario import (
    MapDataConfig,
    load_preset,
    run_scenario,
    with_map_data,
    with_sensor_config,
)
from throughtunnel.sensors.errors import MG
from throughtunnel.sensors.imu import normal_gravity
from throughtunnel.vehicle.traffic import TrafficConfig

# (preset, profile): the ideal-sensor residuals of the map-grade study, plus the flat road of each
CASES = (
    ("eisenhower_tunnel", "up2"),
    ("eisenhower_tunnel", "flat"),
    ("synthetic_demo_track", "down2"),
    ("synthetic_demo_track", "flat"),
    ("seattle_sr99_tunnel", "v4"),
    ("seattle_sr99_tunnel", "flat"),
)
TRAFFIC = ("free", "stop_and_go")
ESTIMATORS = ("dr_calibrated", "route_imu")
TEXT = ("case", "preset", "profile", "traffic", "gravity")


def simulate(preset: str, profile: str, traffic: str):
    """The map-grade study's ideal-sensor run (traffic seed 0), map grade on."""
    cfg = load_preset(preset)
    t = TrafficConfig(scenario="stop_and_go", seed=0) if traffic == "stop_and_go" else TrafficConfig()
    base = run_scenario(
        cfg.model_copy(update={"road_profile": profile_config(cfg, BY_KEY[profile]), "traffic": t})
    )
    imu, gnss = ideal_sensors(cfg)
    return with_map_data(with_sensor_config(base, imu=imu, gnss=gnss), MapDataConfig(road_grade=True))


def stage_at_loss(res) -> GpsImuAlignment:
    obs = res.observations()
    t_loss = res.gnss_events.loss_t
    imu_mask, gnss_mask = obs.imu.t < t_loss, obs.gnss.t < t_loss
    upto = Observations(
        imu=ImuStream(t=obs.imu.t[imu_mask], accel=obs.imu.accel[imu_mask], gyro=obs.imu.gyro[imu_mask]),
        gnss=obs.gnss.select(gnss_mask),
        route=obs.route,
    )
    stage = GpsImuAlignment(obs.route)
    align_imu(stage, upto)
    return stage


def _double_integral(t, r) -> float:
    """∫∫ r from t[0]: the position error a constant-free speed error r would leave at t[-1]."""
    dv = np.concatenate([[0.0], np.cumsum(0.5 * (r[1:] + r[:-1]) * np.diff(t))])
    return float(np.sum(0.5 * (dv[1:] + dv[:-1]) * np.diff(t)))


def diagnose(res, freeze: bool, local_gravity: bool) -> dict:
    t_loss, c_t = res.gnss_events.loss_t, res.sections.exit_t
    g_local = float(normal_gravity(np.interp(t_loss, res.truth.t, res.truth.lat)))
    portal.FREEZE_BEFORE_ENTRANCE_M = 200.0 if freeze else None
    map_grade.GRAVITY = g_local if local_gravity else 9.80665
    try:
        stage = stage_at_loss(res)
        a = stage.alignment
        r_bs = res.config.imu.mount.rotation_body_from_phone()
        fwd_true, left_true, up_true = (r_bs.T @ np.eye(3)[:, k] for k in range(3))
        p = math.asin(float(np.clip(a.forward @ up_true, -1.0, 1.0)))  # + = forward axis tilted up
        yaw = math.atan2(float(a.forward @ left_true), float(a.forward @ fwd_true))  # + = towards left
        phi_cal = a.calibration_grade_angle
        # T2 split: (a) IMU samples of each GPS interval include the fix time, not the start: the interval
        # means lag by half a sample and the sum leaves −(h/2)·(a_last − a_first)/T; (b) a yaw error
        # leaks the approach's mean lateral specific force into the levelling: −yaw·mean(f_left).
        rows = stage._solver._rows
        dt = np.array([r[2] for r in rows])
        t_end = np.array([r[7] for r in rows])
        f_left = float(np.mean([r[0] @ left_true for r in rows]))
        acc = np.interp([t_end[0] - dt[0], t_end[-1]], res.truth.t, res.truth.accel_long)
        h = 1.0 / res.config.imu.rate_hz
        t2a = -0.5 * h * (acc[1] - acc[0]) / dt.sum()
        t2b = -yaw * f_left
        t_fix = float(res.gnss.t[res.gnss.t < t_loss][-1])
        m = (res.truth.t >= t_fix) & (res.truth.t <= c_t)
        t, phi = res.truth.t[m], np.arctan(res.truth.grade[m])
        g_sim = normal_gravity(res.truth.lat[m])
        big_g = map_grade.GRAVITY
        t1 = (g_sim - big_g) * np.sin(phi - phi_cal)
        t2 = g_sim * (np.sin(phi + p) - np.sin(phi - phi_cal))
        cmp = compare_estimators(res, list(ESTIMATORS))
        along = {ev.name: ev.summary["exit_along_m"] for ev in cmp.evaluations}
    finally:
        portal.FREEZE_BEFORE_ENTRANCE_M = 200.0
        map_grade.GRAVITY = 9.80665
    return {
        "outage_s": c_t - t_fix,
        "p_plus_phi_cal_mg": g_local * (p + phi_cal) / MG,
        "t2a_mg": t2a / MG,
        "t2b_mg": t2b / MG,
        "yaw_deg": math.degrees(yaw),
        "f_left_mean_mps2": f_left,
        "phi_cal_pct": 100.0 * math.tan(phi_cal),
        "t1_mean_mg": float(np.mean(t1)) / MG,
        "t2_mean_mg": float(np.mean(t2)) / MG,
        "pred_t1_m": _double_integral(t, t1),
        "pred_t2_m": _double_integral(t, t2),
        **{f"{n}_along_m": v for n, v in along.items()},
    }


def run_all() -> list[dict]:
    records = []
    for preset, profile in CASES:
        for traffic in TRAFFIC:
            res = simulate(preset, profile, traffic)
            for freeze in (False, True):
                for local in (False, True):
                    rec = {
                        "case": f"{preset}/{profile}/{traffic}",
                        "preset": preset,
                        "profile": profile,
                        "traffic": traffic,
                        "freeze": int(freeze),
                        "gravity": "local" if local else "standard",
                        **diagnose(res, freeze, local),
                    }
                    records.append(rec)
            print(f"{preset}/{profile}/{traffic}", flush=True)
    return records


# ---------------------------------------------------------------------- tables
def tables_markdown(records: list[dict], meta: dict) -> str:
    out = [
        "# Residual diagnostic: tables\n",
        f"Commit `{meta['commit']}`, {meta['date']}. Ideal sensors, map grade on, traffic seed 0 (as the "
        "map-grade study). Along-track error at C [m] (+ = ahead). Prediction = ∫∫(T1 + T2) from the last "
        "fix to C. T1 = gravity constant, T2 = levelling vs. reported grade (module docstring).\n",
    ]
    for traffic in TRAFFIC:
        out.append(f"## {'Free flow' if traffic == 'free' else 'Stop-and-go'}\n")
        rows = []
        for r in records:
            if r["traffic"] != traffic:
                continue
            rows.append(
                {
                    "preset / profile": f"{r['preset'].split('_')[0]} / {r['profile']}",
                    "freeze": "on" if r["freeze"] else "off",
                    "gravity": r["gravity"],
                    "outage [s]": f"{r['outage_s']:.0f}",
                    "φ_cal [%]": f"{r['phi_cal_pct']:.3f}",
                    "g(p + φ_cal) [mg]": f"{r['p_plus_phi_cal_mg']:+.4f}",
                    "= T2a + T2b (+ rest) [mg]": f"{r['t2a_mg']:+.4f} {r['t2b_mg']:+.4f} "
                    f"({r['p_plus_phi_cal_mg'] - r['t2a_mg'] - r['t2b_mg']:+.4f})",
                    "yaw error [°]": f"{r['yaw_deg']:+.3f}",
                    "T1 / T2 mean [mg]": f"{r['t1_mean_mg']:+.4f} / {r['t2_mean_mg']:+.4f}",
                    "predicted T1 / T2 [m]": f"{r['pred_t1_m']:+.1f} / {r['pred_t2_m']:+.1f}",
                    "predicted total [m]": f"{r['pred_t1_m'] + r['pred_t2_m']:+.1f}",
                    "dr_calibrated [m]": f"{r['dr_calibrated_along_m']:+.1f}",
                    "route_imu [m]": f"{r['route_imu_along_m']:+.1f}",
                }
            )
        out.append(markdown_table(rows) + "\n")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--from-csv", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if args.from_csv:
        records = read_runs(args.out / "runs.csv", text=TEXT)
        meta = json.loads((args.out / "meta.json").read_text(encoding="utf-8"))
    else:
        records = run_all()
        meta = {
            "commit": git_commit(),
            "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "cases": [f"{p}/{q}" for p, q in CASES],
            "runtime_s": round(time.perf_counter() - t0),
        }
        write_runs(records, args.out / "runs.csv")
        (args.out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    (args.out / "tables.md").write_text(tables_markdown(records, meta), encoding="utf-8")
    print(f"wrote {args.out / 'tables.md'}; {len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
