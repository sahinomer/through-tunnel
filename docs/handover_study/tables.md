# Handover diagnostic: tables

Commit `c242449`, 2026-10-16 08:52 UTC; 20 seeds per case; estimator results from `docs/benchmark/error_sources/runs.csv`. Corr = correlation, slope = least-squares slope through the origin (1 = the prediction has the right size), rms = rms of measured − predicted.

Rerun check: forward offset vs. the benchmark's `runs.csv`, max difference 0.0e+00 mg.

## 1. Forward offset at GPS loss: measured vs. predicted from the GPS speed errors

| case | approach T [s] | |offset| median [mg] | per interval: corr / slope / rms [mg] | telescoped (δv_last − δv_first)/T: corr / slope / rms | last fix only: corr | runs with gaps |
|---|---|---|---|---|---|---|
| floor/free | 82 | 0.00 | – / – / 0.000 | – / – / 0.000 | – | 0/20 |
| floor/stop_and_go | 84 | 0.00 | – / – / 0.004 | – / – / 0.004 | – | 0/20 |
| gps_speed/free | 82 | 0.23 | 1.00 / 1.01 / 0.008 | 1.00 / 1.01 / 0.008 | 0.52 | 0/20 |
| gps_speed/stop_and_go | 84 | 0.17 | 1.00 / 1.00 / 0.008 | 1.00 / 1.00 / 0.008 | 0.65 | 0/20 |
| gps_degr/free | 82 | 0.50 | 1.00 / 1.00 / 0.000 | 1.00 / 1.00 / 0.000 | 1.00 | 0/20 |
| gps_degr/stop_and_go | 84 | 0.40 | 1.00 / 1.00 / 0.004 | 1.00 / 1.00 / 0.004 | 1.00 | 0/20 |
| gps_degr_harsh/free | 82 | 0.55 | 1.00 / 1.00 / 0.001 | 1.00 / 1.00 / 0.001 | 1.00 | 0/20 |
| gps_degr_harsh/stop_and_go | 84 | 0.46 | 1.00 / 1.00 / 0.004 | 1.00 / 1.00 / 0.004 | 1.00 | 0/20 |
| realistic/free | 82 | 0.60 | 0.97 / 0.99 / 0.167 | 0.97 / 0.99 / 0.167 | 0.88 | 0/20 |
| realistic/stop_and_go | 84 | 0.64 | 0.98 / 1.03 / 0.161 | 0.98 / 1.03 / 0.161 | 0.89 | 0/20 |

## 2. Handover speed error: measured (estimator) vs. predicted

| case | |δv_last| median [m/s] | route_imu: |δv| median [m/s] | route_imu: blend prediction corr / slope / rms | dr_filtered: |δv| median [m/s] | dr_filtered: blend prediction corr / slope / rms |
|---|---|---|---|---|---|
| floor/free | 0.00 | 0.00 | – / – / 0.000 | 0.00 | – / – / 0.000 |
| floor/stop_and_go | 0.00 | 0.00 | – / – / 0.001 | 0.00 | – / – / 0.001 |
| gps_speed/free | 0.21 | 0.05 | 1.00 / 1.00 / 0.001 | 0.05 | 1.00 / 1.00 / 0.001 |
| gps_speed/stop_and_go | 0.18 | 0.05 | 1.00 / 1.00 / 0.001 | 0.05 | 1.00 / 1.00 / 0.001 |
| gps_degr/free | 0.40 | 0.12 | 1.00 / 1.00 / 0.000 | 0.12 | 1.00 / 1.00 / 0.000 |
| gps_degr/stop_and_go | 0.33 | 0.09 | 1.00 / 1.00 / 0.001 | 0.09 | 1.00 / 1.00 / 0.001 |
| gps_degr_harsh/free | 0.44 | 0.14 | 1.00 / 1.00 / 0.000 | 0.14 | 1.00 / 1.00 / 0.000 |
| gps_degr_harsh/stop_and_go | 0.38 | 0.13 | 1.00 / 1.00 / 0.001 | 0.13 | 1.00 / 1.00 / 0.001 |
| realistic/free | 0.39 | 0.11 | 1.00 / 0.99 / 0.007 | 0.11 | 1.00 / 0.99 / 0.007 |
| realistic/stop_and_go | 0.37 | 0.12 | 1.00 / 1.00 / 0.008 | 0.12 | 1.00 / 1.00 / 0.008 |

## 3. Same sign? Offset term and speed term of the along-track error 5 km in (route + IMU)

Offset term ½·b·t², speed term δv·t (t = time to 5 km), both from the measured handover state. Same sign = the two terms add up.

| case | t to 5 km [s] | |offset term| median [m] | |speed term| median [m] | same sign | corr(δv, b) | |along 5 km| median [m] | sum vs. along: corr / slope |
|---|---|---|---|---|---|---|---|
| floor/free | 258 | 0 | 0 | 7/20 | -0.31 | 0 | 0.83 / 1.86 |
| floor/stop_and_go | 738 | 11 | 0 | 2/20 | -0.70 | 13 | 0.99 / 1.22 |
| gps_speed/free | 258 | 79 | 12 | 16/20 | 0.53 | 98 | 0.99 / 1.02 |
| gps_speed/stop_and_go | 738 | 444 | 37 | 12/20 | 0.57 | 196 | 0.89 / 0.31 |
| gps_degr/free | 258 | 168 | 30 | 18/20 | 0.83 | 184 | 1.00 / 1.00 |
| gps_degr/stop_and_go | 738 | 877 | 63 | 14/20 | 0.60 | 354 | 0.94 / 0.22 |
| gps_degr_harsh/free | 258 | 183 | 38 | 17/20 | 0.73 | 188 | 1.00 / 1.00 |
| gps_degr_harsh/stop_and_go | 738 | 1040 | 101 | 13/20 | 0.44 | 373 | 0.94 / 0.21 |
| realistic/free | 258 | 194 | 28 | 15/20 | 0.76 | 231 | 0.93 / 1.03 |
| realistic/stop_and_go | 738 | 1563 | 92 | 18/20 | 0.70 | 482 | 0.80 / 0.18 |

### Stop-and-go by the sign of the offset (route + IMU)

Measured / predicted along-track error 5 km in, median per run. The v ≥ 0 clamp resets a negative speed error at every stop, so negative offsets do not grow as ½·b·t²; positive ones creep on.

| case | positive offset | negative offset |
|---|---|---|
| floor/stop_and_go | 20 runs: 1.23 | – |
| gps_speed/stop_and_go | 10 runs: 0.94 | 10 runs: 0.19 |
| gps_degr/stop_and_go | 6 runs: 0.68 | 14 runs: 0.20 |
| gps_degr_harsh/stop_and_go | 6 runs: 0.66 | 14 runs: 0.19 |
| realistic/stop_and_go | 8 runs: 0.51 | 12 runs: 0.12 |

## 4. Prediction for 1a + 2a: calibration and speed frozen 200 m before B

Formula prediction, not an implementation, free flow only (in stop-and-go the formula does not hold, above): the offset and speed of the last fix at least 200 m before B, the speed carried to B with the frozen offset; along-track error 5 km in ≈ ½·b·t² + δv·t. The part of the offset the GPS speed errors do not explain (IMU errors absorbed by the levelling, table 1) is carried over unchanged. Compared with the same formula on the measured state (route + IMU).

| case | freeze before loss [s] | |offset| now → frozen [mg] | |δv| now → frozen [m/s] | |predicted error 5 km| now → frozen, median (p90) [m] |
|---|---|---|---|---|
| floor/free | 10 | 0.00 → 0.00 | 0.000 → 0.000 | 0 (0) → 0 (0) |
| gps_speed/free | 10 | 0.23 → 0.24 | 0.048 → 0.052 | 87 (172) → 82 (272) |
| gps_degr/free | 10 | 0.50 → 0.00 | 0.117 → 0.000 | 190 (347) → 0 (0) |
| gps_degr_harsh/free | 10 | 0.55 → 0.30 | 0.144 → 0.104 | 200 (422) → 129 (256) |
| realistic/free | 10 | 0.60 → 0.25 | 0.112 → 0.052 | 218 (340) → 109 (236) |
