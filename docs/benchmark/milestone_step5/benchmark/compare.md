# Benchmark comparison

Baseline: commit `00ab89b` (2026-10-16 15:18 UTC). This run: commit `0b4ee46`. 14400 shared runs. Cells: median error at C [m], baseline → this run. ⚠ = worse by more than 10 % and 5 m.

| estimator | flat / free | flat / stop_and_go | climb3 / free | climb3 / stop_and_go | underwater / free | underwater / stop_and_go |
|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 340 → 340 | 1552 → 1552 | 704 → 704 | 11367 → 11367 | 360 → 360 | 1530 → 1530 |
| DR GPS-calibrated IMU | 58 → 58 | 186 → 186 | 134 → 134 | 4244 → 4244 | 103 → 103 | 729 → 729 |
| DR calibrated + GPS-blended speed/heading | 33 → 33 | 129 → 129 | 113 → 113 | 4098 → 4098 | 72 → 72 | 526 → 526 |
| Route + filtered IMU speed | 23 → 23 | 96 → 96 | 109 → 109 | 782 → 782 | 54 → 54 | 488 → 488 |
| Route + IMU Kalman filter (distance, speed, offset) | 23 → 23 | 61 → 70 ⚠ | 122 → 116 | 782 → 782 | 57 → 54 | 437 → 364 |
| Route + last GPS speed (naive) | 79 → 79 | 782 → 782 | 79 → 79 | 782 → 782 | 79 → 79 | 782 → 782 |
| Route + vehicle speed (reference) | 5 → 5 | 5 → 5 | 5 → 5 | 6 → 6 | 5 → 5 | 6 → 6 |
| Route + IMU + standstill oracle: speed reset ‡ | 23 → 23 | 34 → 34 | 109 → 109 | 301 → 301 | 54 → 54 | 61 → 61 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 23 → 23 | 16 → 16 | 109 → 109 | 77 → 77 | 54 → 54 | 76 → 76 |

**Regressions:** Route + IMU Kalman filter (distance, speed, offset), flat / stop_and_go: 61 → 70 m
