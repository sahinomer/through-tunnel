"""Yaw diagnostic (step 4.1 of docs/estimator_plan.md): does the yaw residual corrupt the filter?

Diagnostic only, no estimator change. Hypothesis: a yaw residual ψ of the calibrated axes leaks lateral
specific force into the forward channel (≈ ψ · f_lat). On the approach (curves of 150–400 m radius,
1–2.5 m/s² at 70 km/h) ``route_kf`` learns the forward offset b from GPS speed and absorbs the leak into
b; in the long stop-and-go outage a wrong b costs more than the leak itself, which ``route_imu`` (no b)
only sees inside the tunnel.

Counterfactual ("yaw oracle", not an estimator): the leak is removed from the forward channel of the
alignment stage's output, sample by sample, using the truth:

    leak_i = (F_i · L) · (L · f_i)      F_i: forward axis the stage uses at sample i (calibration error
                                        included), L: true vehicle left axis, f_i: error-free specific
                                        force (phone axes, ``imu_ideal``)

Everything else (noise, bias, pitch residual, re-solve shifts) is untouched, so the difference to the
unmodified estimator is what the yaw leak costs. Variants per run:
* ``route_imu`` / ``route_imu+yaw``: unmodified / leak removed everywhere;
* ``route_kf``: unmodified (reproduces the milestone's numbers);
* ``route_kf+yaw_approach``: leak removed before GPS loss only (b learned without it);
* ``route_kf+yaw_tunnel``: leak removed from GPS loss on only;
* ``route_kf+yaw``: leak removed everywhere (the ceiling of a perfect yaw state, solution 6b).

Per run also: the yaw residual at GPS loss, the true forward offset at loss and the filter's b after
the last fix before loss.

    uv run python -m throughtunnel.evaluation.yaw_study --out docs/yaw_study
"""

from __future__ import annotations

import argparse
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from throughtunnel.evaluation import error_sources as es
from throughtunnel.evaluation.benchmark import (
    Case,
    _med_p90,
    git_commit,
    gross_error,
    read_runs,
    write_runs,
)
from throughtunnel.evaluation.benchmark import run_config as benchmark_run_config
from throughtunnel.evaluation.experiment import markdown_table
from throughtunnel.evaluation.metrics import evaluate_track
from throughtunnel.geodesy import normal_gravity
from throughtunnel.observations import GnssFix
from throughtunnel.positioning.alignment import GpsImuAlignment, VehicleImu
from throughtunnel.positioning.route_constrained import RouteImuDeadReckoning
from throughtunnel.positioning.route_kalman import RouteKalman
from throughtunnel.positioning.runner import align_imu, replay
from throughtunnel.scenario import run_scenario
from throughtunnel.sensors.errors import MG

ES_CONDITIONS = ("floor", "cal_pitch_0.1", "cal_yaw_2", "hard", "gps_speed", "realistic")
BENCH_GEOMETRIES = ("ladder_2km", "ladder_3km", "ladder_5km")
TRAFFIC = ("free", "stop_and_go")
VARIANTS = (
    "route_imu",
    "route_imu+yaw",
    "route_kf",
    "route_kf+yaw_approach",
    "route_kf+yaw_tunnel",
    "route_kf+yaw",
)
TEXT = ("case", "source", "scenario", "traffic", "variant")


class _RecordingStage(GpsImuAlignment):
    """The GPS + IMU stage, recording the forward axis it uses at every sample (diagnostics)."""

    def __init__(self, route, calibration_error=None) -> None:
        super().__init__(route, calibration_error)
        self.forward: list[tuple[float, float, float]] = []

    def on_imu(self, t, accel, gyro):
        out = super().on_imu(t, accel, gyro)
        self.forward.append(self._rows[0] if self._rows is not None else (math.nan,) * 3)
        return out


class _RecordingKalman(RouteKalman):
    """``route_kf`` recording its offset b after every GPS fix (diagnostics)."""

    def __init__(self, route) -> None:
        super().__init__(route)
        self.b_at_fix: list[tuple[float, float]] = []

    def on_gnss(self, fix: GnssFix) -> None:
        super().on_gnss(fix)
        self.b_at_fix.append((fix.t, self._b))


def _corrected(stream, leak, mask) -> list[VehicleImu | None]:
    """The stream with the leak removed from the forward channel where ``mask``."""
    out = []
    for s, lk, m in zip(stream, leak, mask, strict=True):
        if s is None or not m:
            out.append(s)
        else:
            out.append(replace(s, accel=(s.accel[0] - lk, s.accel[1], s.accel[2])))
    return out


def diagnose(res, source: str, scenario: str, traffic: str, seed: int) -> list[dict]:
    obs = res.observations()
    stage = _RecordingStage(obs.route, res.config.calibration.rotation_error())
    stream = align_imu(stage, obs)
    t_loss = res.gnss_events.loss_t
    r_bs = res.config.imu.mount.rotation_body_from_phone()
    _, left, up = (r_bs.T @ np.eye(3)[:, k] for k in range(3))  # true vehicle axes in phone coordinates
    fwd = np.asarray(stage.forward)  # (N, 3)
    c_left = np.nan_to_num(fwd @ left)  # leak coefficient F·L ≈ sin(yaw residual)
    leak = c_left * (res.imu_ideal.accel @ left)
    before = res.imu.t < t_loss
    i = int(np.flatnonzero(before)[-1])
    accel = res.imu_errors.accel
    bias = accel.bias + (accel.drift[i] if accel.drift is not None else 0.0)
    g = float(normal_gravity(np.interp(t_loss, res.truth.t, res.truth.lat)))
    offset_true = float(fwd[i] @ (g * up + bias))
    # approach curves: rms lateral specific force over the last 60 s of GPS (what b is learned from)
    win = before & (res.imu.t > t_loss - 60.0)
    f_lat_rms = float(np.sqrt(np.mean((res.imu_ideal.accel[win] @ left) ** 2)))

    streams = {
        "": stream,
        "+yaw": _corrected(stream, leak, np.ones(len(stream), bool)),
        "+yaw_approach": _corrected(stream, leak, before),
        "+yaw_tunnel": _corrected(stream, leak, ~before),
    }
    sec = res.sections
    tunnel_m = sec.exit_s - sec.entrance_s
    base = {
        "case": f"{scenario}/{traffic}",
        "source": source,
        "scenario": scenario,
        "traffic": traffic,
        "seed": seed,
        "tunnel_m": tunnel_m,
        "outage_s": res.gnss_events.reacquire_t - t_loss,
        "yaw_loss_deg": math.degrees(math.asin(float(np.clip(c_left[i], -1, 1)))),
        "offset_true_mg": offset_true / MG,
        "f_lat_rms_mps2": f_lat_rms,
    }
    records = []
    for variant in VARIANTS:
        name, _, suffix = variant.partition("+")
        est = _RecordingKalman(obs.route) if name == "route_kf" else RouteImuDeadReckoning(obs.route)
        track = replay(est, obs, streams["+" + suffix if suffix else ""])
        ev = evaluate_track(track, res)
        b_loss = math.nan
        if name == "route_kf":
            b_loss = [b for t, b in est.b_at_fix if t < t_loss][-1] / MG
        records.append(
            {
                **base,
                "variant": variant,
                "exit_total_m": ev.summary["exit_total_m"],
                "exit_along_m": ev.summary["exit_along_m"],
                "tunnel_max_m": ev.summary["tunnel_max_m"],
                "b_loss_mg": b_loss,
            }
        )
    return records


def _job(args: tuple[str, str, str, list[int]]) -> list[dict]:
    source, scenario, traffic, seeds = args
    out = []
    for seed in seeds:
        if source == "error_sources":
            cfg = es.run_config(es.BY_KEY[scenario], seed, traffic)
        else:
            cfg = benchmark_run_config(Case(scenario, "flat", traffic), seed)
        out += diagnose(run_scenario(cfg), source, scenario, traffic, seed)
    print(f"{source}: {scenario}/{traffic}: {len(seeds)} runs", flush=True)
    return out


# ---------------------------------------------------------------------- analysis
def _cell(rs) -> str:
    return f"{_med_p90([r['exit_total_m'] for r in rs])} ✗{sum(gross_error(r) for r in rs)}"


def _check(records, reference: dict[str, Path]) -> list[str]:
    """Unmodified variants vs. the milestone's runs.csv (same runs): max |difference| of the error at C."""
    out = []
    for source, path in reference.items():
        ref = {}
        text = es.TEXT if source == "error_sources" else ("case", "geometry", "road", "traffic", "estimator")
        for r in read_runs(path, text=text):
            if source == "benchmark" and r["road"] != "flat":
                continue
            key = r["condition"] if source == "error_sources" else r["geometry"]
            ref[(key, r["traffic"], r["seed"], r["estimator"])] = r["exit_total_m"]
        diffs = [
            abs(r["exit_total_m"] - ref[(r["scenario"], r["traffic"], r["seed"], r["variant"])])
            for r in records
            if r["source"] == source
            and r["variant"] in ("route_imu", "route_kf")
            and (r["scenario"], r["traffic"], r["seed"], r["variant"]) in ref
        ]
        out.append(
            f"{source}: {len(diffs)} runs, max difference {max(diffs):.1e} m" if diffs else f"{source}: –"
        )
    return out


def tables_markdown(records: list[dict], meta: dict) -> str:
    cases = list(dict.fromkeys(r["case"] for r in records))
    out = [
        "# Yaw diagnostic: tables\n",
        f"Commit `{meta['commit']}`, {meta['date']}; {len(meta['seeds'])} seeds per case. Error at C, median "
        "(p90) [m], ✗ = gross errors (> 200 m in the tunnel or at C). +yaw = the yaw leak removed from the "
        "forward channel using the truth (counterfactual, not an estimator).\n",
        "Rerun check against the milestone (unmodified variants): " + "; ".join(meta.get("check", [])) + "\n",
        "## 1. Error at C\n",
    ]
    rows = []
    for case in cases:
        row = {"case": case, "source": records[[r["case"] for r in records].index(case)]["source"]}
        for v in VARIANTS:
            row[v] = _cell([r for r in records if r["case"] == case and r["variant"] == v])
        rows.append(row)
    out.append(markdown_table(rows) + "\n")

    out.append("## 2. Yaw residual and forward offset at GPS loss (route_kf)\n")
    out.append(
        "|yaw| = yaw residual of the stage's forward axis at loss (calibration error included). b error = "
        "filter offset after the last fix before loss − true offset at loss. f_lat rms = lateral specific "
        "force over the last 60 s before loss.\n"
    )
    rows = []
    for case in cases:
        kf = {r["seed"]: r for r in records if r["case"] == case and r["variant"] == "route_kf"}
        ya = {r["seed"]: r for r in records if r["case"] == case and r["variant"] == "route_kf+yaw_approach"}
        seeds = sorted(kf)
        yaw = np.abs([kf[s]["yaw_loss_deg"] for s in seeds])
        e0 = np.array([kf[s]["b_loss_mg"] - kf[s]["offset_true_mg"] for s in seeds])
        e1 = np.array([ya[s]["b_loss_mg"] - ya[s]["offset_true_mg"] for s in seeds])
        rows.append(
            {
                "case": case,
                "|yaw| median (p90) [deg]": f"{np.median(yaw):.2f} ({np.percentile(yaw, 90):.2f})",
                "f_lat rms median [m/s²]": f"{np.median([kf[s]['f_lat_rms_mps2'] for s in seeds]):.2f}",
                "|b error| median (p90) [mg]": f"{np.median(np.abs(e0)):.2f} "
                f"({np.percentile(np.abs(e0), 90):.2f})",
                "same, leak removed on the approach": f"{np.median(np.abs(e1)):.2f} "
                f"({np.percentile(np.abs(e1), 90):.2f})",
            }
        )
    out.append(markdown_table(rows) + "\n")

    out.append("## 3. Free-flow tails: the three worst route_kf runs per free-flow case\n")
    rows = []
    for case in cases:
        if not case.endswith("/free"):
            continue
        by = {v: {r["seed"]: r for r in records if r["case"] == case and r["variant"] == v} for v in VARIANTS}
        worst = sorted(by["route_kf"], key=lambda s: -by["route_kf"][s]["exit_total_m"])[:3]
        for s in worst:
            k = by["route_kf"][s]
            rows.append(
                {
                    "case": case,
                    "seed": str(s),
                    "|yaw| [deg]": f"{abs(k['yaw_loss_deg']):.2f}",
                    "b error [mg]": f"{k['b_loss_mg'] - k['offset_true_mg']:+.2f}",
                    "route_imu": f"{by['route_imu'][s]['exit_total_m']:.0f}",
                    "route_kf": f"{k['exit_total_m']:.0f}",
                    "route_kf+yaw_approach": f"{by['route_kf+yaw_approach'][s]['exit_total_m']:.0f}",
                    "route_kf+yaw": f"{by['route_kf+yaw'][s]['exit_total_m']:.0f}",
                }
            )
    out.append(markdown_table(rows) + "\n")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--from-csv", action="store_true")
    parser.add_argument("--reference", type=Path, default=Path("docs/benchmark/milestone_step4"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if args.from_csv:
        records = read_runs(args.out / "runs.csv", text=TEXT)
        meta = json.loads((args.out / "meta.json").read_text(encoding="utf-8"))
    else:
        seeds = list(range(args.seeds))
        jobs = [("error_sources", c, t, seeds) for c in ES_CONDITIONS for t in TRAFFIC]
        jobs += [("benchmark", g, t, seeds) for g in BENCH_GEOMETRIES for t in TRAFFIC]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            records = [r for recs in pool.map(_job, jobs) for r in recs]
        meta = {
            "commit": git_commit(),
            "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "seeds": seeds,
            "error_sources": list(ES_CONDITIONS),
            "benchmark": [f"{g}/flat" for g in BENCH_GEOMETRIES],
            "runtime_s": round(time.perf_counter() - t0),
        }
        meta["check"] = _check(records, {
            "error_sources": args.reference / "error_sources" / "runs.csv",
            "benchmark": args.reference / "benchmark" / "runs.csv",
        })  # fmt: skip
        write_runs(records, args.out / "runs.csv")
        (args.out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    (args.out / "tables.md").write_text(tables_markdown(records, meta), encoding="utf-8")
    print(f"wrote {args.out / 'tables.md'}; {len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
