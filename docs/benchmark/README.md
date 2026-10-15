# Benchmark baselines

The benchmark (D43, `evaluation/benchmark.py`) is the fixed yardstick for every estimator: 48 scenarios
× 20 runs with the realism options on. Each later estimator change is compared against a saved
baseline on exactly the same runs:

    uv run python -m throughtunnel.evaluation.benchmark --quick --out out/dev --compare docs/benchmark/baseline

| Baseline | Commit | Estimators | Tables |
|---|---|---|---|
| `baseline/` | `36904cb` (2026-10-15) | the 5 phone-only estimators before any estimator work, + the reference | [tables](baseline/tables.md) |

## What the first baseline says

Error at the tunnel exit C, median (p90) over all 48 scenarios; † = reference (uses the car's speed):

| Estimator | map grade off | map grade on | announcement within ±3 s | failed runs |
|---|---|---|---|---|
| Route + vehicle speed † | 5 m (15) | 5 m (14) | 99 % | 0 % |
| Route + filtered IMU speed (best phone-only) | 782 m (889) | 39 m (544) | 20 % | 45 % |
| DR calibrated + GPS-blended | 1336 m (20668) | 58 m (543) | 21 % | 45 % |
| Route + last GPS speed (naive) | 435 m (881) | 435 m (881) | 24 % | 48 % |

The announcement and failure columns use the runs without map grade, so they include the sloped
cases that break the IMU estimators.

* **The reference sets the ceiling.** It holds 4–7 m median for every tunnel length, road profile and
  traffic case: car speed is worth about an order of magnitude.
* **Map grade is essential for the IMU estimators.** Without it, a sloped tunnel costs 0.8–25 km. With
  it, sloped roads match flat ones; the underwater V is even better (the grade-change feedback,
  [map_grade_study.md](../map_grade_study.md)).
* **The phone-only error grows with outage time.** On a flat road the best phone-only estimator goes
  from 5 m (0.5 km tunnel) to 231 m (5 km) in free flow, and to 482 m at 5 km in stop-and-go. 2–6 of
  20 runs fail from 2 km of stop-and-go upwards.
* **The naive constant-speed estimator** is competitive in free flow on short tunnels, but fails almost
  every stop-and-go run: it reaches the route end before C.
* **Announcements:** without car speed, few announcements are good (within ±3 s): 11–24 % over all
  runs without map grade. The sloped and long stop-and-go runs dominate this, since those estimates
  are hundreds of metres off. In stop-and-go, small position errors also become large timing errors
  at low speed (traffic study).

These are the numbers the estimator work has to improve: phone-only, with map grade, the 5 km and
stop-and-go cases.
