"""Handover diagnostic: does the GPS speed error of the *last* approach fix set the handover state?

Diagnostic only, no estimator change (step 0 of docs/estimator_plan.md). Hypothesis from the code: the
levelling of the GPS + IMU calibration (``mount_estimation``) averages "measured specific force −
predicted vehicle acceleration", with the forward part predicted as Δv_GPS/Δt per GPS interval. Summed
over the approach the Δv telescope, so the forward offset left in the calibrated forward channel is

    b ≈ (δv_last − δv_first) / T          (δv = GPS speed error, T = approach time the calibration used)

and the speed handed over by the 5 s GPS blend is an exponential average of the last few δv. Both come
from the same last fixes, with the same sign, so ½·b·t² and δv·t add up.

Per run (the error-source benchmark's conditions, traffic and seeds; the simulation is rerun, the
estimator results are joined from its ``runs.csv``):
* ``offset_meas_mg``: the forward offset at GPS loss (as in ``error_sources.alignment_at_loss``);
* ``offset_rows_mg``: the mean of (δv1 − δv0)/Δt over the calibration's GPS intervals (no telescoping
  assumed) and ``offset_end_mg``: (δv_last − δv_first)/T (telescoped);
* ``dv_last_mps`` / ``dv_blend_mps``: the last fix's speed error and the 5 s blend of all fixes' errors,
  with the offset integrated in between, i.e. the predicted handover speed error;
* ``offset_freeze_mg`` / ``dv_freeze_mps``: the same, with the calibration and the speed frozen at the
  last fix ``FREEZE_M`` before B and the speed carried to B with the frozen offset (a formula prediction
  for solutions 1a + 2a, not an implementation).

    uv run python -m throughtunnel.evaluation.handover_study --out docs/handover_study \
        --runs docs/benchmark/error_sources/runs.csv
"""

from __future__ import annotations

import argparse
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from throughtunnel.evaluation.benchmark import git_commit, read_runs, write_runs
from throughtunnel.evaluation.error_sources import BY_KEY, TEXT, TRAFFIC, run_config
from throughtunnel.evaluation.experiment import markdown_table
from throughtunnel.geodesy import normal_gravity
from throughtunnel.observations import ImuStream, Observations
from throughtunnel.positioning.alignment import GpsImuAlignment
from throughtunnel.positioning.route_constrained import BLEND_SPEED_TAU_S
from throughtunnel.positioning.runner import align_imu
from throughtunnel.scenario import run_scenario, truth_at
from throughtunnel.sensors.errors import MG

CONDITIONS = ("floor", "gps_speed", "gps_degr", "gps_degr_harsh", "realistic")
ESTIMATORS = ("route_imu", "dr_filtered")
FREEZE_M = 200.0  # freeze point before B for the 1a + 2a prediction (estimator_plan.md)


def _stage_at_loss(res) -> GpsImuAlignment:
    """The GPS + IMU alignment stage fed with everything before GPS loss (as in alignment_at_loss)."""
    obs = res.observations()
    t_loss = res.gnss_events.loss_t
    imu_mask, gnss_mask = obs.imu.t < t_loss, obs.gnss.t < t_loss
    upto = Observations(
        imu=ImuStream(t=obs.imu.t[imu_mask], accel=obs.imu.accel[imu_mask], gyro=obs.imu.gyro[imu_mask]),
        gnss=obs.gnss.select(gnss_mask),
        route=obs.route,
    )
    stage = GpsImuAlignment(obs.route, res.config.calibration.rotation_error())
    align_imu(stage, upto)
    return stage


def _blend(t_end, dt, dv1, b_cum, t_stop: float) -> float:
    """Speed error of the 5 s GPS blend (route_constrained) at ``t_stop``: between fixes the speed error
    grows with the calibration's current offset, at each fix it moves 1/5 of the way to the fix's error."""
    e = dv1[0]
    for k in range(1, len(dv1)):
        e += b_cum[k - 1] * dt[k]
        a = min(1.0, dt[k] / BLEND_SPEED_TAU_S)
        e += a * (dv1[k] - e)
    return float(e + b_cum[-1] * (t_stop - t_end[-1]))


def diagnose(key: str, traffic: str, seed: int) -> dict:
    res = run_scenario(run_config(BY_KEY[key], seed, traffic))
    t_loss = res.gnss_events.loss_t
    stage = _stage_at_loss(res)
    a = stage.alignment
    r_bs = res.config.imu.mount.rotation_body_from_phone()
    up_true = r_bs.T @ np.eye(3)[:, 2]
    i = int(np.searchsorted(res.imu.t, t_loss)) - 1
    accel = res.imu_errors.accel
    accel_bias = accel.bias + (accel.drift[i] if accel.drift is not None else 0.0)
    g = float(normal_gravity(np.interp(t_loss, res.truth.t, res.truth.lat)))
    offset_meas = float(a.forward @ (g * up_true + accel_bias))

    rows = stage._solver._rows  # diagnostic access: the GPS intervals the calibration used
    dt = np.array([r[2] for r in rows])
    t_end = np.array([r[7] for r in rows])
    v0 = np.array([r[3] for r in rows])
    v1 = np.array([r[4] for r in rows])
    dv0 = v0 - truth_at(res, t_end - dt).speed
    dv1 = v1 - truth_at(res, t_end).speed
    per_row = (dv1 - dv0) / dt
    b_cum = np.cumsum(per_row) / np.arange(1, len(rows) + 1)  # offset of the calibration after each fix

    # Freeze: last fix at least FREEZE_M before B; speed carried to the loss with the frozen offset.
    t_freeze = float(np.interp(res.sections.entrance_s - FREEZE_M, res.motion.s, res.motion.t))
    kf = int(np.searchsorted(t_end, t_freeze, side="right"))  # rows up to and including the freeze fix
    offset_freeze = float(b_cum[kf - 1])
    dv_freeze = _blend(t_end[:kf], dt[:kf], dv1[:kf], b_cum[:kf], t_end[kf - 1])
    dv_freeze += offset_freeze * (t_loss - t_end[kf - 1])

    return {
        "case": f"{key}/{traffic}",
        "condition": key,
        "traffic": traffic,
        "seed": seed,
        "intervals": len(rows),
        "approach_s": float(dt.sum()),
        "gaps": int(np.sum(~np.isclose(t_end[1:] - dt[1:], t_end[:-1]))),  # breaks in the fix sequence
        "offset_meas_mg": offset_meas / MG,
        "offset_rows_mg": float(per_row.mean()) / MG,
        "offset_end_mg": float((dv1[-1] - dv0[0]) / dt.sum()) / MG,
        "dv_first_mps": float(dv0[0]),
        "dv_last_mps": float(dv1[-1]),
        "dv_blend_mps": _blend(t_end, dt, dv1, b_cum, t_loss),
        "freeze_before_loss_s": float(t_loss - t_end[kf - 1]),
        "offset_freeze_mg": offset_freeze / MG,
        "dv_freeze_mps": dv_freeze,
    }


def _job(args: tuple[str, str, list[int]]) -> list[dict]:
    key, traffic, seeds = args
    out = [diagnose(key, traffic, s) for s in seeds]
    print(f"{key}/{traffic}: {len(seeds)} runs", flush=True)
    return out


# ---------------------------------------------------------------------- analysis
def _fit(x, y) -> tuple[float, float, float]:
    """Correlation, least-squares slope through the origin, rms of y − x."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    rms = float(np.sqrt(np.mean((y - x) ** 2)))
    if np.sqrt(np.mean(x**2)) < 1e-6:  # nothing predicted (error-free GPS): correlation and slope are noise
        return math.nan, math.nan, rms
    return float(np.corrcoef(x, y)[0, 1]), float(x @ y / (x @ x)), rms


def joined(diag: list[dict], runs: list[dict]) -> list[dict]:
    """Diagnostic records + the estimators' handover speed and along-track error 5 km in."""
    index = {(r["condition"], r["traffic"], r["seed"], r["estimator"]): r for r in runs}
    out = []
    for d in diag:
        rec = dict(d)
        for name in ESTIMATORS:
            r = index[(d["condition"], d["traffic"], d["seed"], name)]
            rec[f"{name}_dv_mps"] = r["handover_speed_mps"]
            rec[f"{name}_along_5km_m"] = r["along_5km_m"]
            rec[f"{name}_offset_check_mg"] = r["forward_offset_mg"]
            rec["t_5km_s"] = r["t_5km_s"]
        out.append(rec)
    return out


def _f(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}" if math.isfinite(x) else "–"


def tables_markdown(records: list[dict], meta: dict) -> str:
    out = [
        "# Handover diagnostic: tables\n",
        f"Commit `{meta['commit']}`, {meta['date']}; {len(meta['seeds'])} seeds per case; estimator results "
        f"from `{meta['runs']}`. Corr = correlation, slope = least-squares slope through the origin "
        "(1 = the prediction has the right size), rms = rms of measured − predicted.\n",
    ]
    check = max(abs(r["offset_meas_mg"] - r["route_imu_offset_check_mg"]) for r in records)
    out.append(
        f"Rerun check: forward offset vs. the benchmark's `runs.csv`, max difference {check:.1e} mg.\n"
    )

    out.append("## 1. Forward offset at GPS loss: measured vs. predicted from the GPS speed errors\n")
    rows = []
    for case in dict.fromkeys(r["case"] for r in records):
        sel = [r for r in records if r["case"] == case]
        meas = [r["offset_meas_mg"] for r in sel]
        c1, s1, e1 = _fit([r["offset_rows_mg"] for r in sel], meas)
        c2, s2, e2 = _fit([r["offset_end_mg"] for r in sel], meas)
        c3, _, _ = _fit([r["dv_last_mps"] / r["approach_s"] / MG for r in sel], meas)
        rows.append(
            {
                "case": case,
                "approach T [s]": f"{np.median([r['approach_s'] for r in sel]):.0f}",
                "|offset| median [mg]": _f(float(np.median(np.abs(meas)))),
                "per interval: corr / slope / rms [mg]": f"{_f(c1)} / {_f(s1)} / {_f(e1, 3)}",
                "telescoped (δv_last − δv_first)/T: corr / slope / rms": f"{_f(c2)} / {_f(s2)} / {_f(e2, 3)}",
                "last fix only: corr": _f(c3),
                "runs with gaps": f"{sum(r['gaps'] > 0 for r in sel)}/{len(sel)}",
            }
        )
    out.append(markdown_table(rows) + "\n")

    out.append("## 2. Handover speed error: measured (estimator) vs. predicted\n")
    rows = []
    for case in dict.fromkeys(r["case"] for r in records):
        sel = [r for r in records if r["case"] == case]
        row = {
            "case": case,
            "|δv_last| median [m/s]": _f(float(np.median([abs(r["dv_last_mps"]) for r in sel]))),
        }
        for name in ESTIMATORS:
            meas = [r[f"{name}_dv_mps"] for r in sel]
            c, s, e = _fit([r["dv_blend_mps"] for r in sel], meas)
            row[f"{name}: |δv| median [m/s]"] = _f(float(np.median(np.abs(meas))))
            row[f"{name}: blend prediction corr / slope / rms"] = f"{_f(c)} / {_f(s)} / {_f(e, 3)}"
        rows.append(row)
    out.append(markdown_table(rows) + "\n")

    out.append("## 3. Same sign? Offset term and speed term of the along-track error 5 km in (route + IMU)\n")
    out.append(
        "Offset term ½·b·t², speed term δv·t (t = time to 5 km), both from the measured handover state. "
        "Same sign = the two terms add up.\n"
    )
    rows = []
    for case in dict.fromkeys(r["case"] for r in records):
        sel = [r for r in records if r["case"] == case]
        t = np.array([r["t_5km_s"] for r in sel])
        b = np.array([r["offset_meas_mg"] for r in sel]) * MG
        dv = np.array([r["route_imu_dv_mps"] for r in sel])
        along = np.array([r["route_imu_along_5km_m"] for r in sel])
        off_term, v_term = 0.5 * b * t**2, dv * t
        c, s, _ = _fit(off_term + v_term, along)
        cs, _, _ = _fit(dv, b)
        rows.append(
            {
                "case": case,
                "t to 5 km [s]": f"{np.median(t):.0f}",
                "|offset term| median [m]": f"{np.median(np.abs(off_term)):.0f}",
                "|speed term| median [m]": f"{np.median(np.abs(v_term)):.0f}",
                "same sign": f"{int(np.sum(np.sign(off_term) == np.sign(v_term)))}/{len(sel)}",
                "corr(δv, b)": _f(cs),
                "|along 5 km| median [m]": f"{np.median(np.abs(along)):.0f}",
                "sum vs. along: corr / slope": f"{_f(c)} / {_f(s)}",
            }
        )
    out.append(markdown_table(rows) + "\n")

    out.append("### Stop-and-go by the sign of the offset (route + IMU)\n")
    out.append(
        "Measured / predicted along-track error 5 km in, median per run. The v ≥ 0 clamp resets a negative "
        "speed error at every stop, so negative offsets do not grow as ½·b·t²; positive ones creep on.\n"
    )
    rows = []
    for case in dict.fromkeys(r["case"] for r in records if r["traffic"] == "stop_and_go"):
        row = {"case": case}
        for sign, label in ((1, "positive offset"), (-1, "negative offset")):
            sel = [r for r in records if r["case"] == case and np.sign(r["offset_meas_mg"]) == sign]
            if not sel:
                row[label] = "–"
                continue
            t = np.array([r["t_5km_s"] for r in sel])
            pred = (
                0.5 * np.array([r["offset_meas_mg"] for r in sel]) * MG * t**2
                + np.array([r["route_imu_dv_mps"] for r in sel]) * t
            )
            meas = np.array([r["route_imu_along_5km_m"] for r in sel])
            row[label] = f"{len(sel)} runs: {np.median(meas / pred):.2f}"
        rows.append(row)
    out.append(markdown_table(rows) + "\n")

    out.append(f"## 4. Prediction for 1a + 2a: calibration and speed frozen {FREEZE_M:g} m before B\n")
    out.append(
        "Formula prediction, not an implementation, free flow only (in stop-and-go the formula does not "
        f"hold, above): the offset and speed of the last fix at least {FREEZE_M:g} m before B, the speed "
        "carried to B with the frozen offset; along-track error 5 km in ≈ ½·b·t² + δv·t. The part of the "
        "offset the GPS speed errors do not explain (IMU errors absorbed by the levelling, table 1) is "
        "carried over unchanged. Compared with the same formula on the measured state (route + IMU).\n"
    )

    def mp(x) -> str:
        x = np.abs(x)
        return f"{np.median(x):.0f} ({np.percentile(x, 90):.0f})"

    rows = []
    for case in dict.fromkeys(r["case"] for r in records if r["traffic"] == "free"):
        sel = [r for r in records if r["case"] == case]
        t = np.array([r["t_5km_s"] for r in sel])
        b_now = np.array([r["offset_meas_mg"] for r in sel]) * MG
        b_imu = b_now - np.array([r["offset_rows_mg"] for r in sel]) * MG
        b_frz = np.array([r["offset_freeze_mg"] for r in sel]) * MG + b_imu
        dv_now = np.array([r["route_imu_dv_mps"] for r in sel])
        dv_frz = np.array([r["dv_freeze_mps"] for r in sel])
        e_now, e_frz = 0.5 * b_now * t**2 + dv_now * t, 0.5 * b_frz * t**2 + dv_frz * t
        rows.append(
            {
                "case": case,
                "freeze before loss [s]": f"{np.median([r['freeze_before_loss_s'] for r in sel]):.0f}",
                "|offset| now → frozen [mg]": f"{np.median(np.abs(b_now)) / MG:.2f} → "
                f"{np.median(np.abs(b_frz)) / MG:.2f}",
                "|δv| now → frozen [m/s]": f"{np.median(np.abs(dv_now)):.3f} → "
                f"{np.median(np.abs(dv_frz)):.3f}",
                "|predicted error 5 km| now → frozen, median (p90) [m]": f"{mp(e_now)} → {mp(e_frz)}",
            }
        )
    out.append(markdown_table(rows) + "\n")
    return "\n".join(out)


def figure(records: list[dict], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    cases = list(dict.fromkeys(r["case"] for r in records))
    for case in cases:
        sel = [r for r in records if r["case"] == case]
        axes[0].scatter(
            [r["offset_end_mg"] for r in sel], [r["offset_meas_mg"] for r in sel], s=12, label=case
        )
        axes[1].scatter(
            [r["dv_blend_mps"] for r in sel], [r["route_imu_dv_mps"] for r in sel], s=12, label=case
        )
    for ax in axes:
        lo, hi = ax.get_xlim()
        ax.plot([lo, hi], [lo, hi], color="0.5", lw=0.8)
        ax.grid(alpha=0.3)
    axes[0].set(
        xlabel="predicted (δv_last − δv_first)/T [mg]",
        ylabel="measured forward offset [mg]",
        title="Forward offset at GPS loss",
    )
    axes[1].set(
        xlabel="predicted: 5 s blend of the GPS speed errors [m/s]",
        ylabel="measured, route + IMU [m/s]",
        title="Handover speed error",
    )
    axes[1].legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runs", type=Path, default=Path("docs/benchmark/error_sources/runs.csv"))
    parser.add_argument("--from-csv", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if args.from_csv:
        diag = read_runs(args.out / "diagnostic.csv", text=TEXT)
        meta = json.loads((args.out / "meta.json").read_text(encoding="utf-8"))
    else:
        seeds = list(range(args.seeds))
        jobs = [(c, t, seeds) for c in CONDITIONS for t in TRAFFIC]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            diag = [r for recs in pool.map(_job, jobs) for r in recs]
        meta = {
            "commit": git_commit(),
            "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "seeds": seeds,
            "conditions": list(CONDITIONS),
            "runs": args.runs.as_posix(),
            "freeze_m": FREEZE_M,
            "runtime_s": round(time.perf_counter() - t0),
        }
        write_runs(diag, args.out / "diagnostic.csv")
        (args.out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    records = joined(diag, read_runs(args.runs, text=TEXT))
    (args.out / "tables.md").write_text(tables_markdown(records, meta), encoding="utf-8")
    figure(records, args.out / "handover.png")
    print(f"wrote {args.out / 'tables.md'}; {len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
