"""Error-source benchmark (D45): which sensor or calibration error causes how much position error.

One fixed scenario (the 5 km tunnel of the benchmark's length ladder, flat road) in free flow and in
stop-and-go. Each condition adds **one** error source to an error-free setup, so its effect is isolated;
the *floor* (everything error-free) shows what the algorithm itself leaves, and two combined conditions
show the realistic end (*realistic* = the benchmark's setting; *hard* = realistic + tilted dashboard
mount + typical calibration error). Run k uses the same drive and traffic in every condition (scenario
seed 1000 + k, traffic seed k) and error seed k, so conditions are paired.

Recorded per run and estimator:
* the error after 0.5, 1, 2, 3, 4 and 5 km into the tunnel (total and along-track). The estimators do
  not use the tunnel length while dead reckoning, so the error d km in equals the error at C of a
  d km tunnel (statistically; checked against the benchmark's length ladder);
* the state handed over at the tunnel entrance: speed and heading error at the last output before GPS
  loss, and for the GPS + IMU alignment its remaining pitch and yaw misalignment and gyro-bias error
  (estimate vs. truth, at GPS loss). This is the cause side: calibration and GPS problems show up here
  before they become position errors.

    uv run python -m throughtunnel.evaluation.error_sources --seeds 20 --out docs/benchmark/error_sources

Writes ``runs.csv``, ``meta.json``, ``tables.md`` and the configuration (``config.md``, ``config.json``).
``--compare`` against an earlier output and ``--from-csv`` work as in the benchmark. ``--dev``: the
development subset, the conditions an estimator change in the GPS handover can affect
(``DEV_CONDITIONS``) and the benchmark's ``DEV_ESTIMATORS``.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from throughtunnel.evaluation.benchmark import (
    DEV_ESTIMATORS,
    Case,
    _estimators,
    _label,
    _med_p90,
    _sel,
    config_markdown,
    git_commit,
    gross_error,
    read_runs,
    write_runs,
)
from throughtunnel.evaluation.benchmark import (
    run_config as benchmark_run_config,
)
from throughtunnel.evaluation.experiment import compare_estimators, markdown_table
from throughtunnel.geodesy import normal_gravity
from throughtunnel.observations import ImuStream, Observations
from throughtunnel.positioning import ESTIMATORS, REFERENCE_ESTIMATORS, portal
from throughtunnel.positioning.alignment import GpsImuAlignment
from throughtunnel.positioning.runner import align_imu
from throughtunnel.scenario import ScenarioConfig, run_scenario, truth_at
from throughtunnel.sensors.errors import MG, ImuErrorConfig
from throughtunnel.sensors.gnss import GnssConfig
from throughtunnel.sensors.mounting import MOUNT_PRESETS, CalibrationErrorConfig
from throughtunnel.sensors.standstill import StandstillOracleConfig

TUNNEL_KM = 5.0
CHECKPOINTS_KM = (0.5, 1.0, 2.0, 3.0, 4.0, 5.0)
TRAFFIC = ("free", "stop_and_go")
DEV_CONDITIONS = (
    "floor",
    "gps_speed",
    "gps_degr",
    "gps_degr_harsh",
    "realistic",
    "cal_pitch_0.1",
    "cal_yaw_2",
    "hard",
)
TEXT = ("case", "condition", "group", "traffic", "estimator")


# ---------------------------------------------------------------------- conditions
def _error_free(cfg: ScenarioConfig) -> ScenarioConfig:
    return cfg.model_copy(
        update={
            "imu": cfg.imu.model_copy(update={"errors": ImuErrorConfig.ideal()}),
            "gnss": GnssConfig.ideal().model_copy(
                update={
                    k: getattr(cfg.gnss, k)
                    for k in ("loss_window_m", "reacquisition_delay_s", "reacquisition_jitter_s")
                }
            ),
            "calibration": CalibrationErrorConfig(),
        }
    )


def _imu_errors(realistic: ImuErrorConfig, sensor: str, kind: str) -> ImuErrorConfig:
    """Error-free IMU with one error type of one sensor at its realistic size."""
    ideal = ImuErrorConfig.ideal()
    source = getattr(realistic, sensor)
    fields = {
        "noise": {"noise_enabled": True, "noise_density": source.noise_density},
        "bias": {"bias_enabled": True, "bias_magnitude": source.bias_magnitude},
        "drift": {
            "drift_enabled": True,
            "drift_sigma": source.drift_sigma,
            "drift_tau_s": source.drift_tau_s,
        },
    }[kind]
    return ideal.model_copy(update={sensor: getattr(ideal, sensor).model_copy(update=fields)})


@dataclass(frozen=True)
class Condition:
    key: str
    group: str
    label: str
    apply: Callable[[ScenarioConfig, ScenarioConfig], ScenarioConfig]  # (error-free, realistic) -> run config


def _imu(sensor: str, kind: str):
    def apply(free: ScenarioConfig, real: ScenarioConfig) -> ScenarioConfig:
        errors = _imu_errors(real.imu.errors, sensor, kind)
        return free.model_copy(update={"imu": free.imu.model_copy(update={"errors": errors})})

    return apply


def _calibration(**angles):
    def apply(free: ScenarioConfig, real: ScenarioConfig) -> ScenarioConfig:
        defaults = {"yaw_deg": 0.0, "pitch_deg": 0.0, "roll_deg": 0.0}
        return free.model_copy(
            update={"calibration": CalibrationErrorConfig(enabled=True, **defaults | angles)}
        )

    return apply


def _gnss(**update):
    def apply(free: ScenarioConfig, real: ScenarioConfig) -> ScenarioConfig:
        return free.model_copy(update={"gnss": free.gnss.model_copy(update=update)})

    return apply


def _gnss_from_realistic(*fields: str):
    def apply(free: ScenarioConfig, real: ScenarioConfig) -> ScenarioConfig:
        return free.model_copy(
            update={"gnss": free.gnss.model_copy(update={f: getattr(real.gnss, f) for f in fields})}
        )

    return apply


def _mount(free: ScenarioConfig, real: ScenarioConfig) -> ScenarioConfig:
    return free.model_copy(
        update={"imu": free.imu.model_copy(update={"mount": MOUNT_PRESETS["dash_portrait_tilted"]})}
    )


def _hard(free: ScenarioConfig, real: ScenarioConfig) -> ScenarioConfig:
    imu = real.imu.model_copy(update={"mount": MOUNT_PRESETS["dash_portrait_tilted"]})
    return real.model_copy(update={"imu": imu, "calibration": CalibrationErrorConfig(enabled=True)})


CONDITIONS: tuple[Condition, ...] = (
    Condition("floor", "floor", "Error-free (algorithm floor)", lambda free, real: free),
    Condition("acc_noise", "IMU", "Accelerometer noise", _imu("accel", "noise")),
    Condition("acc_bias", "IMU", "Accelerometer bias", _imu("accel", "bias")),
    Condition("acc_drift", "IMU", "Accelerometer bias drift", _imu("accel", "drift")),
    Condition("gyro_noise", "IMU", "Gyroscope noise", _imu("gyro", "noise")),
    Condition("gyro_bias", "IMU", "Gyroscope bias", _imu("gyro", "bias")),
    Condition("gyro_drift", "IMU", "Gyroscope bias drift", _imu("gyro", "drift")),
    Condition("mount_dash", "mounting", "Tilted dashboard mount", _mount),
    Condition("cal_pitch_0.1", "calibration", "Calibration error: pitch 0.1°", _calibration(pitch_deg=0.1)),
    Condition("cal_pitch_0.5", "calibration", "Calibration error: pitch 0.5°", _calibration(pitch_deg=0.5)),
    Condition("cal_yaw_2", "calibration", "Calibration error: yaw 2°", _calibration(yaw_deg=2.0)),
    Condition("cal_roll_0.5", "calibration", "Calibration error: roll 0.5°", _calibration(roll_deg=0.5)),
    Condition(
        "gps_position",
        "GPS",
        "GPS position error",
        _gnss_from_realistic("position_sigma_m", "position_tau_s", "white_sigma_m"),
    ),
    Condition("gps_speed", "GPS", "GPS speed noise", _gnss_from_realistic("speed_sigma_mps")),
    Condition(
        "gps_degr",
        "GPS",
        "GPS degradation before the portal (150 m, 8 m)",
        _gnss(
            portal_degradation=True,
            degradation_length_m=150.0,
            degradation_sigma_m=8.0,
            outlier_probability=0.05,
        ),
    ),
    Condition(
        "gps_degr_harsh",
        "GPS",
        "GPS degradation, harsh (500 m, 20 m, 10 % jumps)",
        _gnss(
            portal_degradation=True,
            degradation_length_m=500.0,
            degradation_sigma_m=20.0,
            outlier_probability=0.10,
        ),
    ),
    Condition("realistic", "combined", "All realistic (= benchmark setting)", lambda free, real: real),
    Condition("hard", "combined", "Hard: realistic + tilted mount + calibration error", _hard),
)
BY_KEY = {c.key: c for c in CONDITIONS}


def realistic_config(seed: int, traffic: str) -> ScenarioConfig:
    """Exactly the benchmark's realistic setting for its 5 km ladder scenario on the flat road."""
    return benchmark_run_config(Case(f"ladder_{TUNNEL_KM:g}km", "flat", traffic), seed)


def run_config(condition: Condition, seed: int, traffic: str) -> ScenarioConfig:
    real = realistic_config(seed, traffic)
    free = _error_free(real)
    cfg = condition.apply(free, real)
    errors = cfg.imu.errors.model_copy(update={"seed": seed})
    return cfg.model_copy(
        update={
            "name": f"Error sources: {condition.label}, {traffic}",
            "imu": cfg.imu.model_copy(update={"errors": errors}),
            "gnss": cfg.gnss.model_copy(update={"seed": seed}),
        }
    )


# ---------------------------------------------------------------------- handover diagnostics
def alignment_at_loss(res) -> dict[str, float]:
    """GPS + IMU alignment at GPS loss vs. the true mount: pitch and yaw misalignment of the forward
    axis [deg] and the gyro-bias error about up [deg/s] (calibration error included)."""
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
    a = stage.alignment
    keys = ("align_pitch_deg", "align_yaw_deg", "align_gyro_bias_dps", "forward_offset_mg")
    nan = dict.fromkeys(keys, math.nan)
    if a is None:
        return nan
    r_bs = res.config.imu.mount.rotation_body_from_phone()
    fwd, left, up = (r_bs.T @ np.eye(3)[:, k] for k in range(3))  # true vehicle axes in phone coordinates
    pitch = math.degrees(math.asin(float(np.clip(a.forward @ up, -1, 1))))  # + = assumed forward points up
    yaw = math.degrees(math.atan2(float(a.forward @ left), float(a.forward @ fwd)))
    i = int(np.searchsorted(res.imu.t, t_loss)) - 1
    gyro, accel = res.imu_errors.gyro, res.imu_errors.accel
    gyro_bias = gyro.bias + (gyro.drift[i] if gyro.drift is not None else 0.0)
    accel_bias = accel.bias + (accel.drift[i] if accel.drift is not None else 0.0)
    # What the calibrated forward channel reads with the car level and still: gravity leak + bias. The
    # levelling tilts its axes to cancel the bias, so this, not the pitch alone, is what gets integrated.
    g = float(normal_gravity(np.interp(t_loss, res.truth.t, res.truth.lat)))
    offset = float(a.forward @ (g * up + accel_bias))
    return {
        "align_pitch_deg": pitch,
        "align_yaw_deg": yaw,
        "align_gyro_bias_dps": math.degrees(a.gyro_bias_up - float(up @ gyro_bias)),
        "forward_offset_mg": offset / MG,
    }


def handover_state(track, res) -> tuple[float, float]:
    """Speed [m/s] and heading [deg] error at the estimator's last output before GPS loss."""
    before = np.flatnonzero(track.t < res.gnss_events.loss_t)
    if not len(before):
        return math.nan, math.nan
    k = int(before[-1])
    tr = truth_at(res, [track.t[k]])
    heading = math.degrees(math.remainder(track.heading[k] - tr.yaw[0], 2 * math.pi))
    return float(track.speed[k] - tr.speed[0]), heading


# ---------------------------------------------------------------------- running
def parse_oracle(text: str) -> StandstillOracleConfig:
    """ "delay_s=1,miss_probability=0.1,false_standstill_kmh=3" (any subset; empty = perfect)."""
    fields = dict(item.split("=") for item in text.split(",") if item.strip())
    return StandstillOracleConfig(**{k.strip(): float(v) for k, v in fields.items()})


def run_condition(
    key: str,
    traffic: str,
    seeds: list[int],
    names: list[str] | None = None,
    freeze_m: str = "default",
    oracle: str = "",
) -> list[dict]:
    """All runs of one condition (passed by key: worker processes cannot receive its functions);
    ``names``: only these estimators (default: all); ``freeze_m``: the portal freeze distance in metres,
    "off", or "default" (D46; set per worker process); ``oracle``: errors of the standstill oracle
    (``parse_oracle``; D50)."""
    if freeze_m != "default":
        portal.FREEZE_BEFORE_ENTRANCE_M = None if freeze_m == "off" else float(freeze_m)
    condition = BY_KEY[key]
    oracle_cfg = parse_oracle(oracle)
    records = []
    for seed in seeds:
        res = run_scenario(
            run_config(condition, seed, traffic).model_copy(update={"standstill_oracle": oracle_cfg})
        )
        sec, motion = res.sections, res.motion
        align = alignment_at_loss(res)
        times = {
            km: float(np.interp(sec.entrance_s + 1000.0 * km, motion.s, motion.t)) for km in CHECKPOINTS_KM
        }
        cmp = compare_estimators(res, names)
        for track, ev in zip(cmp.tracks, cmp.evaluations, strict=True):
            dv, dpsi = handover_state(track, res)
            rec = {
                "case": f"{condition.key}/{traffic}",
                "condition": condition.key,
                "group": condition.group,
                "traffic": traffic,
                "seed": seed,
                "estimator": ev.name,
                "outage_s": res.gnss_events.reacquire_t - res.gnss_events.loss_t,
                "exit_total_m": ev.summary["exit_total_m"],
                "tunnel_max_m": ev.summary["tunnel_max_m"],
                "handover_speed_mps": dv,
                "handover_heading_deg": dpsi,
                **align,
            }
            for km, t in times.items():
                rec[f"err_{km:g}km_m"] = float(np.interp(t, ev.t, ev.total))
                rec[f"along_{km:g}km_m"] = float(np.interp(t, ev.t, ev.along))
                rec[f"t_{km:g}km_s"] = t - res.gnss_events.loss_t
            records.append(rec)
    print(f"{condition.key}/{traffic}: {len(seeds)} runs", flush=True)
    return records


# ---------------------------------------------------------------------- tables
def _cond_label(key: str) -> str:
    return BY_KEY[key].label if key in BY_KEY else key


def _conditions(records) -> list[str]:
    present = {r["condition"] for r in records}
    return [c.key for c in CONDITIONS if c.key in present]


def at_5km_table(records, traffic: str) -> list[dict[str, str]]:
    """Error 5 km into the tunnel: rows conditions, columns estimators; ✗n = gross errors (> 200 m)."""
    rows = []
    for cond in _conditions(records):
        row = {"condition": _cond_label(cond)}
        for name in _estimators(records):
            sel = _sel(records, condition=cond, traffic=traffic, estimator=name)
            gross = sum(gross_error(r) for r in sel)
            row[_label(name) + (" †" if name in REFERENCE_ESTIMATORS else "")] = _med_p90(
                [r["err_5km_m"] for r in sel]
            ) + (f" ✗{gross}" if gross else "")
        rows.append(row)
    return rows


def growth_table(records, traffic: str, estimator: str) -> list[dict[str, str]]:
    """Median error d km into the tunnel (= error at C of a d km tunnel) for one estimator."""
    rows = []
    for cond in _conditions(records):
        sel = _sel(records, condition=cond, traffic=traffic, estimator=estimator)
        row = {"condition": _cond_label(cond)}
        for km in CHECKPOINTS_KM:
            row[f"{km:g} km"] = f"{np.median([r[f'err_{km:g}km_m'] for r in sel]):.0f}"
        row["time to 5 km"] = f"{np.median([r['t_5km_s'] for r in sel]):.0f} s"
        rows.append(row)
    return rows


def handover_table(records, traffic: str) -> list[dict[str, str]]:
    """The cause side: what each condition does to the state handed over at the tunnel entrance."""
    rows = []
    for cond in _conditions(records):
        sel = _sel(records, condition=cond, traffic=traffic)
        one = [r for r in sel if r["estimator"] == "dr_filtered"]  # alignment values are per run
        route = [r for r in sel if r["estimator"] == "route_imu"]

        def med(key: str, rs=one, scale: float = 1.0, digits: int = 3) -> str:
            return f"{scale * np.median(np.abs([r[key] for r in rs])):.{digits}f}"

        rows.append(
            {
                "condition": _cond_label(cond),
                "forward offset [mg]": med("forward_offset_mg", digits=2),
                "pitch misalignment [°]": med("align_pitch_deg"),
                "yaw misalignment [°]": med("align_yaw_deg"),
                "gyro-bias error [mdps]": med("align_gyro_bias_dps", scale=1000.0, digits=2),
                "speed error, DR filtered [m/s]": med("handover_speed_mps"),
                "heading error, DR filtered [°]": med("handover_heading_deg"),
                "speed error, route + IMU [m/s]": med("handover_speed_mps", route),
            }
        )
    return rows


def tables_markdown(records, meta: dict) -> str:
    n_seeds = len({r["seed"] for r in records})
    out = [
        "# Error-source benchmark: generated tables\n",
        f"{meta.get('label', '')} · commit `{meta.get('commit', '?')}` · {meta.get('date', '')} · "
        f"{len(_conditions(records))} conditions × {len(TRAFFIC)} traffic cases × {n_seeds} runs. "
        "One scenario: "
        f"the benchmark's {TUNNEL_KM:g} km tunnel, flat road. Each condition adds one error source to an "
        "error-free setup (paired: same drive and traffic per run). Cells: median (p90) error [m]. "
        "✗n = n runs with a gross error (> 200 m in the tunnel or at C). † = reference estimator.\n",
    ]
    for traffic in TRAFFIC:
        t_label = "free flow" if traffic == "free" else "stop-and-go"
        out.append(f"## {t_label.capitalize()}: error 5 km into the tunnel\n")
        out.append(markdown_table(at_5km_table(records, traffic)) + "\n")
        for name in ("route_imu", "dr_filtered"):
            out.append(f"### {t_label.capitalize()}: error growth, {_label(name)} (median [m])\n")
            out.append("The error d km into the tunnel equals the error at C of a d km tunnel.\n")
            out.append(markdown_table(growth_table(records, traffic, name)) + "\n")
        out.append(f"### {t_label.capitalize()}: state handed over at the tunnel entrance (median |value|)\n")
        out.append(
            "Forward offset = what the calibrated forward accelerometer channel reads with the car level and "
            "still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The "
            "levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while "
            "the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount "
            "(injected calibration error included). Speed and heading errors = the estimate at the last "
            "output before GPS loss vs. the truth.\n"
        )
        out.append(markdown_table(handover_table(records, traffic)) + "\n")
    return "\n".join(out)


def compare_markdown(records, baseline, meta: dict, base_meta: dict) -> str:
    key = lambda r: (r["case"], r["seed"], r["estimator"])  # noqa: E731
    base = {key(r): r for r in baseline}
    rows = []
    for name in _estimators(records):
        row = {"estimator": _label(name)}
        for traffic in TRAFFIC:
            for cond in _conditions(records):
                pairs = [
                    (r, base[key(r)])
                    for r in records
                    if r["estimator"] == name
                    and r["condition"] == cond
                    and r["traffic"] == traffic
                    and key(r) in base
                ]
                if pairs:
                    old = np.median([b["err_5km_m"] for _, b in pairs])
                    new = np.median([r["err_5km_m"] for r, _ in pairs])
                    row[f"{cond} / {traffic}"] = f"{old:.0f} → {new:.0f}"
                else:  # an estimator the baseline does not have
                    row[f"{cond} / {traffic}"] = "–"
        rows.append(row)
    return "\n".join(
        [
            "# Error-source benchmark comparison\n",
            f"Baseline commit `{base_meta.get('commit', '?')}`, this run `{meta.get('commit', '?')}`. "
            "Median error "
            "5 km into the tunnel [m], baseline → this run.\n",
            markdown_table(rows) + "\n",
        ]
    )


# ---------------------------------------------------------------------- I/O
def _group(keys: list[str]) -> str:
    conditions = sorted({k.split("/")[0] for k in keys}, key=lambda c: [x.key for x in CONDITIONS].index(c))
    traffic = sorted({k.split("/")[1] for k in keys})
    return ", ".join(conditions) + ("" if len(traffic) == len(TRAFFIC) else f" ({', '.join(traffic)})")


def write_config(out_dir: Path, seeds: list[int], meta: dict) -> None:
    cases = {}
    for cond in CONDITIONS:
        for traffic in TRAFFIC:
            cfg = run_config(cond, seeds[0], traffic)
            d = cfg.model_dump(mode="json")
            d["route"] = {"source": cfg.route.source, "vertices": len(cfg.route.coordinates)}
            cases[f"{cond.key}/{traffic}"] = d
    snapshot = {
        "seed_rule": "run k: scenario seed 1000 + k; IMU, GPS and traffic seed k (same drive in every "
        "condition)",
        "seeds": seeds,
        "shown_for_seed": seeds[0],
        "cases": cases,
    }
    notes = (
        "Each condition isolates one error source; interactions between sources show only in *realistic* and "
        "*hard*.",
        "The map is exact and the road flat, so map errors and grade play no part here (see the benchmark).",
    )
    (out_dir / "config.json").write_text(json.dumps(snapshot, indent=1), encoding="utf-8")
    text = config_markdown(snapshot, meta, group=_group, notes=notes, title="Error-source benchmark")
    (out_dir / "config.md").write_text(text, encoding="utf-8")


def _read(path: Path) -> list[dict]:
    return read_runs(path, text=TEXT)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--conditions", default="", help="only conditions whose key contains this text")
    parser.add_argument(
        "--dev", action="store_true", help="development subset: DEV_CONDITIONS, DEV_ESTIMATORS"
    )
    parser.add_argument(
        "--freeze-m", default="default", help="portal freeze distance before B [m], 'off', or 'default' (D46)"
    )
    parser.add_argument(
        "--oracle", default="", help="standstill oracle errors, e.g. 'delay_s=1,miss_probability=0.1' (D50)"
    )
    parser.add_argument("--estimators", default="", help="comma-separated estimator names (default: all)")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", default="")
    parser.add_argument("--compare", type=Path, default=None)
    parser.add_argument("--from-csv", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if args.from_csv:
        records = _read(args.out / "runs.csv")
        meta = json.loads((args.out / "meta.json").read_text(encoding="utf-8"))
    else:
        seeds = list(range(args.seeds))
        chosen = [
            c for c in CONDITIONS if args.conditions in c.key and (not args.dev or c.key in DEV_CONDITIONS)
        ]
        jobs = [(c, t) for c in chosen for t in TRAFFIC]
        names = list(DEV_ESTIMATORS) if args.dev else None
        if args.estimators:
            names = [n.strip() for n in args.estimators.split(",")]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results = list(
                pool.map(
                    run_condition,
                    [c.key for c, _ in jobs],
                    [t for _, t in jobs],
                    [seeds] * len(jobs),
                    [names] * len(jobs),
                    [args.freeze_m] * len(jobs),
                    [args.oracle] * len(jobs),
                )
            )
        records = [r for recs in results for r in recs]
        meta = {
            "commit": git_commit(),
            "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "label": args.label,
            "seeds": seeds,
            "freeze_m": args.freeze_m,
            "oracle": parse_oracle(args.oracle).model_dump(),
            "conditions": list(dict.fromkeys(c.key for c, _ in jobs)),
            "estimators": names or list(ESTIMATORS),
            "dev": args.dev,
            "runtime_s": round(time.perf_counter() - t0),
        }
        write_runs(records, args.out / "runs.csv")
        (args.out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
        write_config(args.out, seeds, meta)
    (args.out / "tables.md").write_text(tables_markdown(records, meta), encoding="utf-8")
    print("wrote", args.out / "tables.md")
    if args.compare is not None:
        baseline = _read(args.compare / "runs.csv")
        base_meta = json.loads((args.compare / "meta.json").read_text(encoding="utf-8"))
        (args.out / "compare.md").write_text(
            compare_markdown(records, baseline, meta, base_meta), encoding="utf-8"
        )
    print(f"{len(records)} records in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
