# Benchmark comparison

Baseline: commit `00ab89b` (2026-10-16 15:18 UTC). This run: commit `d6f657d+dirty`. 1120 shared runs. Cells: median error at C [m], baseline → this run. ⚠ = worse by more than 10 % and 5 m.

| estimator | flat / free | flat / stop_and_go | climb3 / free | climb3 / stop_and_go | underwater / free | underwater / stop_and_go |
|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 32 → 32 | 238 → 238 | 165 → 165 | 601 → 601 | 102 → 102 | 658 → 658 |
| DR calibrated + GPS-blended speed/heading | 21 → 21 | 158 → 158 | 110 → 110 | 506 → 506 | 71 → 71 | 639 → 639 |
| Route + filtered IMU speed | 13 → 13 | 93 → 93 | 93 → 93 | 501 → 501 | 44 → 44 | 613 → 613 |
| Route + IMU Kalman filter (distance, speed, offset, yaw) | 19 → 20 | 41 → 68 ⚠ | 103 → 104 | 228 → 467 ⚠ | 40 → 38 | 312 → 531 ⚠ |
| Route + vehicle speed (reference) | 5 → 5 | 5 → 5 | 6 → 6 | 7 → 7 | 6 → 6 | 7 → 7 |
| Route + IMU + standstill oracle: speed reset ‡ | 13 → 13 | 20 → 20 | 93 → 93 | 144 → 144 | 44 → 44 | 132 → 132 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 13 → 13 | 13 → 13 | 93 → 93 | 128 → 128 | 44 → 44 | 127 → 127 |

**Regressions:** Route + IMU Kalman filter (distance, speed, offset, yaw), flat / stop_and_go: 41 → 68 m; Route + IMU Kalman filter (distance, speed, offset, yaw), climb3 / stop_and_go: 228 → 467 m; Route + IMU Kalman filter (distance, speed, offset, yaw), underwater / stop_and_go: 312 → 531 m

## Per scenario

Error at C [m], median (p90) ✗gross errors, baseline → this run.

| estimator | 0.5km/flat/free | 0.5km/flat/s&g | 5km/flat/free | 5km/flat/s&g | 5km/climb3/free (grade) | 5km/climb3/s&g (grade) | 5km/underwater/free (grade) | 5km/underwater/s&g (grade) |
|---|---|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 18 (31) → 18 (31) | 40 (231) ✗3 → 40 (231) ✗3 | 167 (306) ✗8 → 167 (306) ✗8 | 561 (2099) ✗18 → 561 (2099) ✗18 | 165 (285) ✗9 → 165 (285) ✗9 | 601 (7198) ✗18 → 601 (7198) ✗18 | 102 (217) ✗4 → 102 (217) ✗4 | 658 (8740) ✗16 → 658 (8740) ✗16 |
| DR calibrated + GPS-blended speed/heading | 9 (20) → 9 (20) | 23 (93) ✗1 → 23 (93) ✗1 | 117 (240) ✗4 → 117 (240) ✗4 | 420 (2355) ✗17 → 420 (2355) ✗17 | 110 (244) ✗5 → 110 (244) ✗5 | 506 (8661) ✗18 → 506 (8661) ✗18 | 71 (96) → 71 (96) | 639 (7987) ✗15 → 639 (7987) ✗15 |
| Route + filtered IMU speed | 6 (12) → 6 (12) | 18 (92) ✗1 → 18 (92) ✗1 | 103 (257) ✗4 → 103 (257) ✗4 | 385 (782) ✗16 → 385 (782) ✗16 | 93 (247) ✗4 → 93 (247) ✗4 | 501 (782) ✗17 → 501 (782) ✗17 | 44 (95) → 44 (95) | 613 (782) ✗14 → 613 (782) ✗14 |
| Route + IMU Kalman filter (distance, speed, offset, yaw) | 6 (19) → 6 (17) | 11 (59) ✗1 → 12 (95) ✗1 | 85 (283) ✗4 → 89 (244) ✗3 | 188 (782) ✗9 → 402 (782) ✗12 | 103 (268) ✗4 → 104 (237) ✗3 | 228 (782) ✗12 → 467 (782) ✗13 | 40 (86) → 38 (93) | 312 (782) ✗15 → 531 (782) ✗13 |
| Route + vehicle speed (reference) | 4 (11) → 4 (11) | 4 (14) → 4 (14) | 6 (17) → 6 (17) | 7 (17) → 7 (17) | 6 (17) → 6 (17) | 7 (17) → 7 (17) | 6 (17) → 6 (17) | 7 (17) → 7 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 6 (12) → 6 (12) | 6 (17) → 6 (17) | 103 (257) ✗4 → 103 (257) ✗4 | 131 (607) ✗9 → 131 (607) ✗9 | 93 (247) ✗4 → 93 (247) ✗4 | 144 (782) ✗9 → 144 (782) ✗9 | 44 (95) → 44 (95) | 132 (782) ✗10 → 132 (782) ✗10 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 6 (12) → 6 (12) | 5 (14) → 5 (14) | 103 (257) ✗4 → 103 (257) ✗4 | 103 (199) ✗2 → 103 (199) ✗2 | 93 (247) ✗4 → 93 (247) ✗4 | 128 (199) ✗2 → 128 (199) ✗2 | 44 (95) → 44 (95) | 127 (782) ✗9 → 127 (782) ✗9 |
