# Map grade: effect of the road grade from the map on the estimators

Study of 2026-10-15 (D39). The slope study showed that a grade *change* after the approach
calibration costs the IMU estimators 0.4–1.0 km at C per 1 % ([slope_study.md](slope_study.md)). Here
the navigation map provides the road grade (an option, assumed exact), and the estimators remove the
gravity it adds to the forward accelerometer axis.

**Status:** method and ideal-sensor validation done; the realistic-sensor runs (20 paired seeds,
free flow and stop-and-go) are pending and will be added with their tables and figures.

## Method

* **Map data.** With `map_data.road_grade` on, `RouteMap.road_grade` holds the grade every 10 m along
  the map route: the true grade at the closest point of the driven path. The map carries the grade
  itself, not heights. Differentiating heights over *map* distance shows false grade dips (≈0.26 %)
  wherever the driven path cuts a polyline corner, because map and driven distance diverge by 1–3 m
  there. In validation, those dips biased the calibration grade and cost 23 m on a steady climb that
  should cost nothing.
* **Correction.** Every IMU estimator subtracts g·sin(φ(d̂) − φ_cal) from the forward specific force.
  * φ(d̂) is the map grade angle at the estimator's own along-route distance.
  * φ_cal is the mean map grade over the GPS intervals the alignment calibrated on. The levelling
    has already absorbed that grade, so only the change since calibration is removed.
  * `dr_raw` does no levelling, so its φ_cal = 0.
  * `route_hold` uses no IMU and is unchanged.
* **Pairing.** Each simulated run is evaluated with the grade off and on. The switch is information
  for the estimators only, so the drive, sensor data and GPS are identical.

## Ideal sensors (error-free IMU and GPS): error at C [m], map grade off → on

| preset | profile | dr_raw | dr_calibrated | dr_filtered | route_imu |
|---|---|---|---|---|---|
| Eisenhower | steady climb 2 % | 1555 → 1.0 | 0 → 0.0 | 0 → 0.3 | 1 → 1.3 |
| Eisenhower | climb in tunnel +2 % | 1489 → 0.5 | 1457 → 1.9 | 1476 → 1.5 | 881 → 1.8 |
| Eisenhower | descent in tunnel −2 % | 1481 → 1.1 | 1453 → 1.3 | 1471 → 0.8 | 1471 → 1.6 |
| Eisenhower | underwater V 4 % | 1364 → 0.8 | 1301 → 7.6 | 1339 → 7.4 | 1339 → 7.6 |
| Seattle SR 99 | steady climb 2 % | 2188 → 0.5 | 0 → 0.4 | 0 → 0.4 | 1 → 0.5 |
| Seattle SR 99 | climb in tunnel +2 % | 2100 → 0.9 | 2058 → 0.8 | 2088 → 0.9 | 889 → 0.6 |
| Seattle SR 99 | descent in tunnel −2 % | 1878 → 0.2 | 1861 → 0.5 | 1880 → 0.6 | 1878 → 0.5 |
| Seattle SR 99 | underwater V 4 % | 1713 → 0.7 | 1675 → 1.1 | 1696 → 1.2 | 1678 → 0.6 |

With exact map grade, the gravity leakage disappears, to within 0.2–7.6 m at C. The remainder comes
from three sources:
* the grade looked up at the estimated rather than the true position, at grade changes;
* the second-order terms in `positioning/map_grade.py` (along-road vs horizontal acceleration,
  0.08 % at 4 %);
* the 10 m grade sampling.

On a flat road the map grade is zero, and every estimate is bit-identical to running without it
(tested).

## Reproduce

    uv run python -m throughtunnel.evaluation.map_grade_study --seeds 20 --out docs/map_grade_study

`--from-csv` regenerates the tables and figures from a saved run.
