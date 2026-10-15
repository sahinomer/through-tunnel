# Benchmark baselines

The benchmark (D43, `evaluation/benchmark.py`) is the fixed yardstick for every estimator: 48 scenarios
× 20 runs with the realism options on. Each later estimator change is compared against a saved
baseline on exactly the same runs:

    uv run python -m throughtunnel.evaluation.benchmark --quick --out out/dev --compare docs/benchmark/baseline

| Baseline | Commit | Estimators | Tables |
|---|---|---|---|
| `baseline/` | `36904cb` (2026-10-15) | the 5 phone-only estimators before any estimator work, + the reference | [tables](baseline/tables.md) · [configuration](baseline/config.md) |

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
