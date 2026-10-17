# Benchmark comparison

Baseline: commit `00ab89b` (2026-10-16 15:18 UTC). This run: commit `11e51ee+dirty`. 2880 shared runs. Cells: median error at C [m], baseline → this run. ⚠ = worse by more than 10 % and 5 m.

| estimator | flat / free | flat / stop_and_go | climb3 / free | climb3 / stop_and_go | underwater / free | underwater / stop_and_go |
|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 340 → 340 | 1552 → 1552 | – | – | – | – |
| DR GPS-calibrated IMU | 58 → 58 | 186 → 186 | – | – | – | – |
| DR calibrated + GPS-blended speed/heading | 33 → 33 | 129 → 129 | – | – | – | – |
| Route + filtered IMU speed | 23 → 23 | 96 → 96 | – | – | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | 23 → 23 | 61 → 70 ⚠ | – | – | – | – |
| Route + last GPS speed (naive) | 79 → 79 | 782 → 782 | – | – | – | – |
| Route + vehicle speed (reference) | 5 → 5 | 5 → 5 | – | – | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | 23 → 23 | 34 → 34 | – | – | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 23 → 23 | 16 → 16 | – | – | – | – |

**Regressions:** Route + IMU Kalman filter (distance, speed, offset), flat / stop_and_go: 61 → 70 m
