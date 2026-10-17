"""Calibration start diagnostic (after step 6.2): why do the Kalman filters go wrong on Eisenhower?

Diagnostic only, no estimator change. Hypothesis from a traced run: the filters start learning the forward
offset b (and ``route_kf_yaw`` the yaw ψ) as soon as the GPS + IMU calibration is first solved, with priors
that describe a *converged* calibration (b: 1 mg, ψ: 3°). On a short or weakly excited approach the first
solutions are much worse; the re-solves then move the axes (reported as ``offset_shift`` / ``yaw_shift``,
which b and ψ follow by design), so the filter carries the initial error, and too little approach remains
to learn it away.

Per run (flat roads, realistic sensors as the benchmark): when the calibration is first solved, how wrong
its forward offset and yaw are then, b and ψ at GPS loss, and the error at C of both filters with their
priors as they are and widened (b 10 mg, ψ 10°: a counterfactual, not a tuning).

    uv run python -m throughtunnel.evaluation.calibration_start_study --out docs/calibration_start_study
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

from throughtunnel.evaluation import yaw_study as ys
from throughtunnel.evaluation.benchmark import Case, _med_p90, git_commit, read_runs, write_runs
from throughtunnel.evaluation.benchmark import run_config as benchmark_run_config
from throughtunnel.evaluation.experiment import markdown_table
from throughtunnel.evaluation.metrics import evaluate_track
from throughtunnel.geodesy import STANDARD_GRAVITY, normal_gravity
from throughtunnel.positioning import route_kalman as rk
from throughtunnel.positioning.runner import align_imu, replay
from throughtunnel.scenario import run_scenario
from throughtunnel.sensors.errors import MG

GEOMETRIES = ("eisenhower_tunnel", "seattle_sr99_tunnel", "synthetic_demo_track", "ladder_5km")
TRAFFIC = ("free", "stop_and_go")
# "now": the priors before D54 (1 mg, 3°); "wide": 10 mg / 10°, the values D54 then adopted
PRIORS = {
    "now": (1e-3 * STANDARD_GRAVITY, math.radians(3.0)),
    "wide": (10e-3 * STANDARD_GRAVITY, math.radians(10.0)),
}
TEXT = ("case", "geometry", "traffic")


def _logged(cls: type[rk.RouteKalman], b0: float, y0: float) -> type[rk.RouteKalman]:
    """The filter class with the priors b0 / y0, recording (t, b, ψ) after every GPS fix."""

    class Logged(cls):  # type: ignore[valid-type, misc]
        offset_sigma0 = b0
        yaw_sigma0 = y0

        def __init__(self, route) -> None:
            super().__init__(route)
            self.log: list[tuple[float, float, float]] = []

        def on_gnss(self, fix) -> None:
            super().on_gnss(fix)
            self.log.append((fix.t, self._b, self._psi))

    return Logged


def _filters(obs, stream, res, t_loss: float) -> dict[str, float]:
    out = {}
    for prior, (b0, y0) in PRIORS.items():
        for cls in (rk.RouteKalman, rk.RouteKalmanYaw):
            kf = _logged(cls, b0, y0)(obs.route)
            ev = evaluate_track(replay(kf, obs, stream), res)
            _, b, psi = [x for x in kf.log if x[0] < t_loss][-1]
            out[f"{cls.name}_{prior}_exit_m"] = ev.summary["exit_total_m"]
            out[f"{cls.name}_{prior}_tunnel_max_m"] = ev.summary["tunnel_max_m"]
            out[f"{cls.name}_{prior}_b_mg"] = b / MG
            out[f"{cls.name}_{prior}_psi_deg"] = math.degrees(psi)
    return out


def diagnose(geometry: str, traffic: str, seed: int) -> dict:
    res = run_scenario(benchmark_run_config(Case(geometry, "flat", traffic), seed))
    obs = res.observations()
    stage = ys._RecordingStage(obs.route, res.config.calibration.rotation_error())
    stream = align_imu(stage, obs)
    r_bs = res.config.imu.mount.rotation_body_from_phone()
    left, up = r_bs.T @ np.eye(3)[:, 1], r_bs.T @ np.eye(3)[:, 2]
    fwd = np.asarray(stage.forward)
    t, t_loss = res.imu.t, res.gnss_events.loss_t
    acc = res.imu_errors.accel
    g = float(normal_gravity(res.truth.lat[0]))

    def offset(i: int) -> float:  # what the calibrated forward channel reads level and still [mg]
        bias = acc.bias + (acc.drift[i] if acc.drift is not None else 0.0)
        return float(fwd[i] @ (g * up + bias)) / MG

    i0 = int(np.flatnonzero(~np.isnan(fwd[:, 0]))[0])
    il = int(np.flatnonzero(t < t_loss)[-1])
    return {
        "case": f"{geometry}/{traffic}", "geometry": geometry, "traffic": traffic, "seed": seed,
        "gps_before_loss_s": t_loss - float(obs.gnss.t[0]), "ready_before_loss_s": t_loss - float(t[i0]),
        "offset_first_mg": offset(i0), "yaw_first_deg": math.degrees(float(fwd[i0] @ left)),
        "offset_loss_mg": offset(il), "yaw_loss_deg": math.degrees(float(fwd[il] @ left)),
        **_filters(obs, stream, res, t_loss),
    }  # fmt: skip


def _job(args: tuple[str, str, list[int]]) -> list[dict]:
    geometry, traffic, seeds = args
    out = [diagnose(geometry, traffic, s) for s in seeds]
    print(f"{geometry}/{traffic}: {len(seeds)} runs", flush=True)
    return out


def tables_markdown(records: list[dict], meta: dict) -> str:
    out = [
        "# Calibration start diagnostic: tables\n",
        f"Commit `{meta['commit']}`, {meta['date']}; {len(meta['seeds'])} seeds per case, flat roads. "
        "Medians unless stated. *wide* = the filters' offset and yaw priors widened to 10 mg / 10° "
        "(counterfactual).\n",
        "## 1. The calibration's start\n",
    ]
    cases = list(dict.fromkeys(r["case"] for r in records))
    rows = []
    for case in cases:
        sel = [r for r in records if r["case"] == case]
        m = {k: float(np.median([r[k] for r in sel])) for k in ("gps_before_loss_s", "ready_before_loss_s")}
        a = {
            k: np.array([abs(r[k]) for r in sel])
            for k in ("offset_first_mg", "yaw_first_deg", "yaw_loss_deg")
        }
        rows.append({
            "case": case, "GPS before loss [s]": f"{m['gps_before_loss_s']:.0f}",
            "calibration ready before loss [s]": f"{m['ready_before_loss_s']:.0f}",
            "first solution: |offset| [mg] median (max)": f"{np.median(a['offset_first_mg']):.1f} "
            f"({a['offset_first_mg'].max():.1f})",
            "first solution: |yaw| [°] median (max)": f"{np.median(a['yaw_first_deg']):.1f} "
            f"({a['yaw_first_deg'].max():.1f})",
            "at loss: |yaw| [°]": f"{np.median(a['yaw_loss_deg']):.2f}",
        })  # fmt: skip
    out.append(markdown_table(rows) + "\n")
    out.append("## 2. The filters: offset error at GPS loss and error at C, priors as they are → wide\n")
    rows = []
    for case in cases:
        sel = [r for r in records if r["case"] == case]
        row = {"case": case}
        for name in ("route_kf", "route_kf_yaw"):
            for prior in PRIORS:
                b_err = np.array([abs(r[f"{name}_{prior}_b_mg"] - r["offset_loss_mg"]) for r in sel])
                gross = sum(
                    max(r[f"{name}_{prior}_exit_m"], r[f"{name}_{prior}_tunnel_max_m"]) > 200 for r in sel
                )
                row[f"{name} {prior}: |b err| [mg]"] = f"{np.median(b_err):.2f} ({b_err.max():.1f})"
                row[f"{name} {prior}: error at C [m]"] = _med_p90(
                    [r[f"{name}_{prior}_exit_m"] for r in sel]
                ) + (f" ✗{gross}" if gross else "")
        rows.append(row)
    out.append(markdown_table(rows) + "\n")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--from-csv", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if args.from_csv:
        records = read_runs(args.out / "runs.csv", text=TEXT)
        meta = json.loads((args.out / "meta.json").read_text(encoding="utf-8"))
    else:
        seeds = list(range(args.seeds))
        jobs = [(g, tr, seeds) for g in GEOMETRIES for tr in TRAFFIC]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            records = [r for recs in pool.map(_job, jobs) for r in recs]
        meta = {
            "commit": git_commit(),
            "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "seeds": seeds,
            "geometries": list(GEOMETRIES),
            "wide_prior": {"offset_mg": 10.0, "yaw_deg": 10.0},
            "runtime_s": round(time.perf_counter() - t0),
        }
        write_runs(records, args.out / "runs.csv")
        (args.out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    (args.out / "tables.md").write_text(tables_markdown(records, meta), encoding="utf-8")
    print(f"wrote {args.out / 'tables.md'}; {len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
