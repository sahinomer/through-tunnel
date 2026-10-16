# Benchmark baselines

The benchmark (D43, `evaluation/benchmark.py`) is the fixed yardstick for every estimator: 48 scenarios
× 20 runs with the realism options on. Each later estimator change is compared against a saved
baseline on exactly the same runs:

    uv run python -m throughtunnel.evaluation.benchmark --quick --out out/dev --compare docs/benchmark/baseline

**During development (D47)** each change runs the development subsets, ~6 min each instead of 32–42:

    uv run python -m throughtunnel.evaluation.benchmark --dev --out out/dev/<step> --compare docs/benchmark/baseline
    uv run python -m throughtunnel.evaluation.error_sources --dev --out out/dev/<step>_es --compare docs/benchmark/error_sources

* `--dev` (benchmark): the 0.5 and 5 km flat tunnels, the 5 km climb and underwater tunnels, both traffic
  cases; map grade on only; the calibrated estimators and the reference; 20 seeds.
* `--dev` (error sources): floor, GPS speed noise, degradation (normal, harsh), realistic.
* On unchanged code both reproduce the baselines exactly.
* The full set is rerun at milestones.

| Baseline | Commit | Estimators | Tables |
|---|---|---|---|
| `baseline/` | `36904cb` (2026-10-15) | the 5 phone-only estimators before any estimator work, + the reference | [tables](baseline/tables.md) · [configuration](baseline/config.md) |
| `error_sources/` (D45) | `e69543f` (2026-10-15) | the same estimators; one error source at a time on the 5 km flat tunnel | [tables](error_sources/tables.md) · [configuration](error_sources/config.md) |

Each baseline directory holds, next to its results, the configuration it ran with: `config.md` (readable,
including where the setup is optimistic) and `config.json` (the complete effective configuration of every
scenario). They are as important as the results: a number means nothing without its settings.

**Note on the profiles:** the labels "+3 % climb" and "−4 % / +4 % underwater" are the design grades.
The actual steepest grades are 3.1–3.4 % and 3.1–4.5 % (`config.md`). The 0.5 km underwater tunnel dips
only 5 m, because its descent is too short for the 400 m grade transitions to reach 4 %.

## Failure states (D44)

Per run and estimator:
* **Gross error** (failure): the estimate was more than **200 m** from the true position at some time
  in the tunnel or at C, **ahead or behind**. The position is unusable for guidance.
* **Announcement off** (failure): the exit announcement was more than **15 s** early or late, or never
  fired. The driver gets the instruction at the wrong time. In practice it is never missing: a late
  estimate is pushed past the announcement point when GPS returns, so it is late.
* **Capped at D** (data-quality flag, not a failure): the estimate reached the route end D before the
  vehicle reached C. A route estimate stops at D, so its error is a lower bound (exactly 782 / 881 /
  889 m = the C–D distance). Every capped run is also a gross error.

The first version counted only "capped at D" (plus a missed announcement, which never happens) as a
failure. That is one-sided: an estimate 1 km behind never counted. For the best phone-only estimator
with map grade, 7 % of runs failed by that definition and 21 % have a gross error.

## What the first baseline says

All 48 scenarios, median (p90); † = reference (uses the car's speed):

| Estimator | map grade | error at C | gross error | announcement off | announcement good (±3 s) |
|---|---|---|---|---|---|
| Route + vehicle speed † | either | 5 m (14–15) | 0 % | 0 % | 99 % |
| Route + filtered IMU speed (best phone-only) | on | 39 m (544) | 21 % | 20 % | 59 % |
| | off | 782 m (889) | 69 % | 65 % | 20 % |
| DR calibrated + GPS-blended | on | 58 m (543) | 22 % | 19 % | 59 % |
| Route + last GPS speed (naive) | either | 435 m (881) | 58 % | 52 % | 24 % |

* **The reference sets the ceiling.** It holds 4–7 m median for every tunnel length, road profile and
  traffic case: car speed is worth about an order of magnitude.
* **Map grade is essential for the IMU estimators.** Without it, a sloped tunnel costs 0.8–25 km. With
  it, sloped roads match flat ones; the underwater V is even better (the grade-change feedback,
  [map_grade_study.md](../map_grade_study.md)).
* **The phone-only error grows with outage time.** On a flat road the best phone-only estimator goes
  from 5 m (0.5 km tunnel) to 231 m (5 km) in free flow, and to 482 m at 5 km in stop-and-go. Gross
  errors: 0 of 20 runs up to 2 km and 11 of 20 at 5 km in free flow; 3 of 20 at 0.5 km and 16 of 20
  at 5 km in stop-and-go.
* **The naive constant-speed estimator** is competitive in free flow on short tunnels, but has a gross
  error in every stop-and-go run, nearly all capped at D (it keeps driving while the car stands).
* **Announcements:** with map grade, the best phone-only estimators announce within ±3 s in 59 % of
  runs and are more than 15 s off in 19–20 %; 85–89 % of those runs also have a gross error. In
  stop-and-go, small position errors also become large timing errors at low speed (traffic study).

These are the numbers the estimator work has to improve: phone-only, with map grade, the 5 km and
stop-and-go cases.

## What the error-source benchmark says

The 5 km flat tunnel, error 5 km in for the best phone-only estimators (route + IMU / DR filtered),
median [m]. Each condition adds one error source to an error-free setup:

| Error source | free flow | stop-and-go | through (handover at GPS loss) |
|---|---|---|---|
| none (floor) | 0 | 12–13 | – |
| calibration pitch 0.1° / 0.5° | 540–590 / 2 600 | 880–950 / 3 300 | forward offset 1.7 / 8.7 mg |
| GPS degradation before the portal (normal / harsh) | 170–184 / 175–188 | 325–354 / 337–373 | forward offset 0.5 mg, speed 0.12–0.14 m/s |
| GPS speed noise | 95–98 | 196–210 | forward offset 0.2 mg, speed 0.05 m/s |
| accelerometer bias drift | 78–85 | 328–354 | changes inside the tunnel |
| calibration yaw 2° | 57–58 | 79–82 | lateral acceleration on curves |
| accelerometer noise | 7 | 26–28 | – |
| gyro noise / bias / drift, accelerometer bias, tilted mount, calibration roll, GPS position error | 0–15 | 12–67 | constant errors are calibrated away |
| all realistic (benchmark setting) | 217–231 | 470–482 | forward offset 0.6 mg, speed 0.11 m/s |
| hard (+ tilted mount + calibration error) | 2 610–2 640 | 3 280–3 300 | dominated by the 0.5° pitch |
| reference (car speed), realistic | 6 | 7 | – |

* **The handover state decides the error.** For the calibration and GPS conditions in free flow, the
  along-track error 5 km in is ½ · forward offset · t² + speed error · t from the state at GPS loss
  (correlation 0.99–1.00 per run). Only bias drift, which changes inside the tunnel, is not predicted
  this way (0.48). The tunnel phase adds almost nothing: the error is set before the tunnel.
  *Correction (2026-10-16, [handover_study.md](../handover_study.md)):* this was checked in free flow
  only. In stop-and-go the v ≥ 0 clamp resets negative speed errors at stops, and the formula
  overshoots 3–5×. The same diagnostic shows where the handover state comes from: the forward offset is
  (δv_last − δv_first)/T, set by the GPS speed errors of the first and last approach fix.
* **Unreliable GPS before the entrance hurts the GPS-calibrated estimators (confirmed).** Degraded
  fixes in the last 150 m before B corrupt the levelling (0.5 mg forward offset ≈ 0.03° pitch) and
  the handed-over speed (0.12 m/s). Alone, this costs 170–190 m after 5 km. The harsh version (500 m,
  20 m) is barely worse: the damage comes from the last fixes, not from how long the degradation lasts.
* **Calibration pitch is the single largest risk.** 0.1° = 1.7 mg costs ~550 m after 5 km; the
  estimators cannot observe it after the calibration.
* **What the calibration already handles.** Constant errors (accelerometer and gyro bias, a tilted
  mount, roll) are calibrated away almost completely.
* **Stop-and-go doubles the time-driven errors** (drift, offsets): 738 s instead of 258 s to 5 km. The
  floor itself is 12–13 m there (error-free sensors), so the algorithm alone loses some accuracy at
  stops.
