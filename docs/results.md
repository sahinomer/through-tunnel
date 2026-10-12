# Initial positioning results

First end-to-end results of the positioning pipeline. Generated on 2026-10-12 with

```bash
uv run python -m throughtunnel.evaluation.report --seeds 20 --vary-drive   # main tables
uv run python -m throughtunnel.evaluation.report --seeds 20                # same drive, sensor errors only
```

These are **initial** results under the simplifying assumptions of decision D05: flat road, no stops,
rigid aligned mount, constant bias + white noise, and the map derived from the same OSM geometry as the
driven path. Read §3 before drawing conclusions.

## 1. Setup

* **Scenarios** (presets, A–D). Seattle SR 99: 1.5 km urban approach, 2.97 km tunnel, 0.9 km recovery.
  Eisenhower I-70: 1.5 / 2.72 / 0.9 km, nearly straight. Synthetic route: 1.6 / 1.96 / 0.8 km, curvy.
  Navigation exit in the middle of B–C, announced 300 m before and at the exit.
* **Sensors** (defaults):
  * IMU 200 Hz; accelerometer 180 µg/√Hz, 10 mg bias; gyroscope 7 mdps/√Hz, 0.1 °/s bias
    (random directions).
  * GPS 1 Hz: Gauss-Markov 2.5 m / 30 s + 0.5 m white, speed noise 0.2 m/s.
  * GPS is lost up to 30 m before B and returns 3–5 s after C.
* **Runs.** 20 Monte-Carlo runs per preset. Main tables: a new drive (speed profile) *and* new
  sensor/GPS errors per run. Second set: the preset drive with only the sensor/GPS errors varied.
  Within a run all estimators see identical observations.
* **Estimators** (positioning_design.md §4; each step adds one technique):

| Estimator | What it uses |
|---|---|
| DR raw IMU | GPS-initialised 2-D dead reckoning. Phone axes *assumed* aligned with the vehicle; no calibration |
| DR GPS-calibrated IMU | + phone-to-vehicle alignment, levelling (absorbs horizontal accelerometer bias) and gyro bias, all estimated from approach-phase GPS |
| DR calibrated + GPS-blended | + causal complementary blending of GPS speed (5 s) and bearing (10 s) instead of adopting single fixes |
| Route + filtered IMU speed | + route constraint: 1-D position along the navigation route, speed from the filtered IMU |
| Route + last GPS speed (naive) | Reference: along the route at the last GPS speed |

Metrics are against the true **phone** position (evaluation only):
* *error at C*: when the vehicle actually leaves the tunnel;
* *max / RMS in tunnel*;
* *recovered after C*: time from C until the error stays < 10 m for 5 s;
* *announce*: estimated minus true time of reaching the announcement point (+ = late).

## 2. Results

### 2.1 New drive and new sensor errors per run (main result)

#### Eisenhower Tunnel, I-70 (westbound)

Tunnel B–C 2.72 km, crossed in 125 s (preset drive); 20 runs, a new drive per run, (sensor/GPS seeds 0–19), median (90th percentile) of absolute values; announcement columns also give the signed mean (+ = late). Computed in 40 s.

| estimator | runs | error at C [m] | max in tunnel [m] | RMS in tunnel [m] | recovered after C [s] | announce exit@300m [s] | announce exit@0m [s] |
|---|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 20 | 463.8 (p90 717.2) | 463.6 (p90 716.9) | 210.1 (p90 324.9) | 4.3 (p90 5.2) | 2.6 (p90 4.5), mean +0.1 | 4.1 (p90 8.4), mean +0.4 |
| DR GPS-calibrated IMU | 20 | 49.4 (p90 75.6) | 49.4 (p90 75.6) | 26.6 (p90 41.7) | 4.3 (p90 5.2) | 0.2 (p90 1.1), mean +0.3 | 0.4 (p90 1.3), mean +0.3 |
| DR calibrated + GPS-blended speed/heading | 20 | 33.5 (p90 45.8) | 33.5 (p90 45.8) | 16.2 (p90 22.6) | 4.3 (p90 5.2) | 0.3 (p90 0.6), mean +0.1 | 0.4 (p90 0.7), mean +0.2 |
| Route + filtered IMU speed | 20 | 28.9 (p90 44.3) | 28.9 (p90 44.3) | 13.8 (p90 21.0) | 4.3 (p90 5.3) | 0.3 (p90 0.5), mean +0.1 | 0.4 (p90 0.7), mean +0.2 |
| Route + last GPS speed (naive) | 20 | 78.8 (p90 188.6) | 87.0 (p90 202.5) | 50.2 (p90 105.0) | 4.5 (p90 6.1) | 1.6 (p90 3.1), mean +0.4 | 1.6 (p90 4.3), mean +0.8 |

#### Seattle SR 99 Tunnel (northbound)

Tunnel B–C 2.97 km, crossed in 150 s (preset drive); 20 runs, a new drive per run, (sensor/GPS seeds 0–19), median (90th percentile) of absolute values; announcement columns also give the signed mean (+ = late). Computed in 61 s.

| estimator | runs | error at C [m] | max in tunnel [m] | RMS in tunnel [m] | recovered after C [s] | announce exit@300m [s] | announce exit@0m [s] |
|---|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 20 | 661.8 (p90 997.3) | 661.5 (p90 996.7) | 300.1 (p90 448.5) | 4.2 (p90 5.4) | 4.9 (p90 9.2), mean +0.2 | 7.5 (p90 16.7), mean +0.9 |
| DR GPS-calibrated IMU | 20 | 80.1 (p90 132.9) | 80.1 (p90 132.8) | 41.6 (p90 67.8) | 4.2 (p90 5.4) | 0.8 (p90 1.4), mean +0.1 | 1.1 (p90 1.6), mean +0.2 |
| DR calibrated + GPS-blended speed/heading | 20 | 60.7 (p90 101.0) | 60.6 (p90 100.9) | 28.6 (p90 48.4) | 4.2 (p90 5.2) | 0.5 (p90 0.8), mean +0.1 | 0.5 (p90 1.2), mean +0.2 |
| Route + filtered IMU speed | 20 | 33.8 (p90 63.6) | 33.8 (p90 63.6) | 16.9 (p90 30.7) | 4.4 (p90 5.2) | 0.4 (p90 0.8), mean +0.1 | 0.6 (p90 1.0), mean +0.1 |
| Route + last GPS speed (naive) | 20 | 94.5 (p90 195.1) | 107.1 (p90 203.4) | 56.7 (p90 135.5) | 4.8 (p90 6.8) | 1.9 (p90 5.3), mean +0.5 | 2.6 (p90 6.5), mean +0.8 |

#### Synthetic demo route

Tunnel B–C 1.96 km, crossed in 103 s (preset drive); 20 runs, a new drive per run, (sensor/GPS seeds 0–19), median (90th percentile) of absolute values; announcement columns also give the signed mean (+ = late). Computed in 50 s.

| estimator | runs | error at C [m] | max in tunnel [m] | RMS in tunnel [m] | recovered after C [s] | announce exit@300m [s] | announce exit@0m [s] |
|---|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 20 | 286.2 (p90 463.1) | 286.1 (p90 462.9) | 131.0 (p90 208.8) | 4.3 (p90 5.1) | 1.9 (p90 3.2), mean -0.0 | 3.1 (p90 5.6), mean +0.1 |
| DR GPS-calibrated IMU | 20 | 29.7 (p90 59.6) | 29.7 (p90 59.6) | 16.7 (p90 34.3) | 4.3 (p90 4.9) | 0.4 (p90 0.9), mean +0.1 | 0.4 (p90 1.1), mean +0.2 |
| DR calibrated + GPS-blended speed/heading | 20 | 17.6 (p90 30.5) | 17.6 (p90 30.5) | 9.4 (p90 14.6) | 4.3 (p90 4.9) | 0.1 (p90 0.5), mean +0.1 | 0.2 (p90 0.5), mean +0.1 |
| Route + filtered IMU speed | 20 | 15.7 (p90 29.9) | 15.7 (p90 29.9) | 8.0 (p90 14.3) | 4.3 (p90 5.1) | 0.1 (p90 0.4), mean +0.1 | 0.3 (p90 0.6), mean +0.1 |
| Route + last GPS speed (naive) | 20 | 58.5 (p90 146.8) | 69.6 (p90 146.7) | 36.8 (p90 82.5) | 4.6 (p90 5.8) | 1.1 (p90 2.9), mean +0.1 | 1.8 (p90 3.8), mean +0.6 |


### 2.2 Same drive, new sensor/GPS errors per run

#### Eisenhower Tunnel, I-70 (westbound)

Tunnel B–C 2.72 km, crossed in 125 s (preset drive); 20 runs, same drive, (sensor/GPS seeds 0–19), median (90th percentile) of absolute values; announcement columns also give the signed mean (+ = late). Computed in 38 s.

| estimator | runs | error at C [m] | max in tunnel [m] | RMS in tunnel [m] | recovered after C [s] | announce exit@300m [s] | announce exit@0m [s] |
|---|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 20 | 459.8 (p90 772.7) | 459.7 (p90 772.6) | 210.4 (p90 344.8) | 4.5 (p90 5.0) | 3.4 (p90 5.2), mean -0.0 | 5.3 (p90 9.0), mean +0.1 |
| DR GPS-calibrated IMU | 20 | 54.8 (p90 75.9) | 54.8 (p90 75.8) | 28.8 (p90 39.6) | 4.5 (p90 5.0) | 0.6 (p90 1.0), mean +0.1 | 0.8 (p90 1.3), mean +0.2 |
| DR calibrated + GPS-blended speed/heading | 20 | 38.3 (p90 59.9) | 38.3 (p90 59.9) | 18.9 (p90 30.9) | 4.5 (p90 5.0) | 0.5 (p90 0.7), mean +0.1 | 0.6 (p90 0.9), mean +0.2 |
| Route + filtered IMU speed | 20 | 34.0 (p90 54.6) | 34.0 (p90 54.6) | 18.0 (p90 26.4) | 4.1 (p90 5.0) | 0.5 (p90 0.7), mean +0.1 | 0.7 (p90 0.9), mean +0.2 |
| Route + last GPS speed (naive) | 20 | 330.2 (p90 362.5) | 330.1 (p90 362.4) | 192.1 (p90 211.2) | 11.0 (p90 12.0) | 4.5 (p90 5.0), mean -4.5 | 6.5 (p90 7.1), mean -6.5 |

#### Seattle SR 99 Tunnel (northbound)

Tunnel B–C 2.97 km, crossed in 150 s (preset drive); 20 runs, same drive, (sensor/GPS seeds 0–19), median (90th percentile) of absolute values; announcement columns also give the signed mean (+ = late). Computed in 55 s.

| estimator | runs | error at C [m] | max in tunnel [m] | RMS in tunnel [m] | recovered after C [s] | announce exit@300m [s] | announce exit@0m [s] |
|---|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 20 | 639.8 (p90 1069.9) | 639.5 (p90 1069.4) | 290.5 (p90 481.4) | 4.1 (p90 5.1) | 5.3 (p90 9.6), mean +0.0 | 7.6 (p90 15.2), mean +0.5 |
| DR GPS-calibrated IMU | 20 | 64.5 (p90 115.6) | 64.5 (p90 115.6) | 32.7 (p90 58.1) | 4.1 (p90 5.1) | 0.7 (p90 1.5), mean +0.0 | 0.7 (p90 1.9), mean +0.1 |
| DR calibrated + GPS-blended speed/heading | 20 | 61.1 (p90 93.3) | 61.1 (p90 93.3) | 29.7 (p90 45.2) | 4.1 (p90 5.1) | 0.4 (p90 0.9), mean +0.1 | 0.4 (p90 1.2), mean +0.1 |
| Route + filtered IMU speed | 20 | 31.6 (p90 72.1) | 31.6 (p90 72.1) | 15.3 (p90 35.3) | 4.2 (p90 5.1) | 0.4 (p90 0.8), mean +0.0 | 0.6 (p90 1.1), mean +0.0 |
| Route + last GPS speed (naive) | 20 | 19.5 (p90 56.4) | 34.4 (p90 64.7) | 15.2 (p90 34.0) | 4.2 (p90 5.1) | 0.6 (p90 1.1), mean +0.2 | 0.9 (p90 1.6), mean +0.5 |

#### Synthetic demo route

Tunnel B–C 1.96 km, crossed in 103 s (preset drive); 20 runs, same drive, (sensor/GPS seeds 0–19), median (90th percentile) of absolute values; announcement columns also give the signed mean (+ = late). Computed in 45 s.

| estimator | runs | error at C [m] | max in tunnel [m] | RMS in tunnel [m] | recovered after C [s] | announce exit@300m [s] | announce exit@0m [s] |
|---|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 20 | 281.7 (p90 462.9) | 281.5 (p90 462.7) | 129.5 (p90 208.1) | 4.2 (p90 5.2) | 2.3 (p90 3.7), mean -0.0 | 3.4 (p90 5.5), mean -0.1 |
| DR GPS-calibrated IMU | 20 | 29.3 (p90 55.9) | 29.3 (p90 55.9) | 15.7 (p90 32.4) | 4.2 (p90 5.2) | 0.3 (p90 1.0), mean +0.2 | 0.5 (p90 1.4), mean +0.1 |
| DR calibrated + GPS-blended speed/heading | 20 | 17.5 (p90 37.0) | 17.5 (p90 37.0) | 9.2 (p90 18.8) | 4.2 (p90 5.2) | 0.2 (p90 0.5), mean +0.1 | 0.2 (p90 0.6), mean +0.1 |
| Route + filtered IMU speed | 20 | 16.8 (p90 39.8) | 16.8 (p90 39.8) | 7.4 (p90 19.8) | 4.2 (p90 5.2) | 0.2 (p90 0.5), mean +0.1 | 0.2 (p90 0.7), mean +0.1 |
| Route + last GPS speed (naive) | 20 | 17.7 (p90 44.9) | 46.8 (p90 56.1) | 25.5 (p90 31.5) | 4.2 (p90 5.2) | 2.2 (p90 2.5), mean -2.1 | 2.0 (p90 2.5), mean -1.9 |


## 3. Interpretation

1. **Raw inertial dead reckoning is unusable on a phone** (290–660 m median at the exit after
   1.7–2.5 min). This matches the analytic error budget: a constant forward specific-force error grows
   as ½·b·t². The tests reproduce the exact vector prediction within 1 %.
2. **GPS-aided calibration during the approach is the biggest single gain** (≈ 8–10× smaller error).
   On a level road, gravity levelling absorbs the horizontal accelerometer bias. The gyro bias is
   estimated by regression against the GPS bearing (< 0.02 °/s residual). The phone's mounting is
   estimated, not assumed: a tilted dashboard mount is recovered to < 1°.
3. **Blending GPS speed/heading before the tunnel** removes the "single noisy fix" hand-over error
   (another 25–40 %).
4. **The route constraint** removes cross-track error and heading drift. The best estimator stays at
   **16–34 m median (p90 30–64 m) after 2–3 km of tunnel**, and announces the exit **0.1–0.6 s late in
   the median (p90 ≤ 1.0 s)**. The remaining error is along-track: integrated speed error.
5. **The naive "last GPS speed" reference is drive-dependent.** On a fixed drive it can look excellent
   (Seattle: 20 m) or terrible (Eisenhower: 330 m), depending on how the speed changes in the tunnel.
   Across varied drives its median is 59–95 m, p90 147–195 m, and its announcements are 1.1–2.6 s off
   (median).
   Evaluating on one drive would have given a misleading ranking.
6. **Recovery after the exit** is immediate for every estimator: they reset to the first fix, so
   "recovered after C" just equals the simulated reacquisition delay (≈ 4–5 s). Smarter recovery
   (gating, first-fix quality) is only meaningful once GPS degradation is modelled (R4, A10).

## 3.1 Caveats that limit these numbers

* **Flat road. This is the most important caveat.** The calibrated estimators rely on levelling during
  the approach to cancel the accelerometer bias. That cancellation holds only while the road keeps the
  grade it had during the approach. Example: the approach is level and the tunnel descends at 3 %.
  The forward specific force then gains g·sin(1.7°) ≈ 0.29 m/s², three times the entire default
  accelerometer bias (10 mg ≈ 0.1 m/s²), which is ~1.2 km of error after 90 s if uncorrected. Real tunnels often have grades (underwater tunnels: 4–6 %),
  so these results are optimistic until road grade is simulated (roadmap R1).
* **Map = truth geometry.** Route-constrained estimators use the original OSM polyline, which is within
  ~1–5 m of the driven path. Real map/road mismatches (lane offsets, length scale errors) would add
  along-track error (R3).
* **No stops in the tunnel** (R2). A stop would break the naive reference completely, and inertial
  speed integration needs zero-velocity handling.
* **White GPS speed/bearing noise.** Real Doppler errors are time-correlated, which makes blending less
  effective. GPS position errors are already time-correlated (Gauss-Markov).
* **First-order IMU errors** (constant bias + white noise; R5). 20 seeds per case: percentiles are
  indicative, not precise.
