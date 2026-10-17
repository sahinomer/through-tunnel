# Benchmark comparison

Baseline: commit `00ab89b` (2026-10-16 15:18 UTC). This run: commit `11e51ee+dirty`. 1400 shared runs. Cells: median error at C [m], baseline → this run. ⚠ = worse by more than 10 % and 5 m.

| estimator | flat / free | flat / stop_and_go | climb3 / free | climb3 / stop_and_go | underwater / free | underwater / stop_and_go |
|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 54 → 54 | 249 → 249 | 165 → 165 | 601 → 601 | 102 → 102 | 658 → 658 |
| DR calibrated + GPS-blended speed/heading | 38 → 38 | 153 → 153 | 110 → 110 | 506 → 506 | 71 → 71 | 639 → 639 |
| Route + filtered IMU speed | 24 → 24 | 114 → 114 | 93 → 93 | 501 → 501 | 44 → 44 | 613 → 613 |
| Route + IMU Kalman filter (distance, speed, offset) | 46 → 31 | 104 → 80 | 103 → 96 | 228 → 319 ⚠ | 40 → 40 | 312 → 322 |
| Route + vehicle speed (reference) | 5 → 5 | 6 → 6 | 6 → 6 | 7 → 7 | 6 → 6 | 7 → 7 |
| Route + IMU + standstill oracle: speed reset ‡ | 24 → 24 | 55 → 55 | 93 → 93 | 144 → 144 | 44 → 44 | 132 → 132 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 24 → 24 | 18 → 18 | 93 → 93 | 128 → 128 | 44 → 44 | 127 → 127 |

**Regressions:** Route + IMU Kalman filter (distance, speed, offset), climb3 / stop_and_go: 228 → 319 m

## Per scenario

Error at C [m], median (p90) ✗gross errors, baseline → this run.

| estimator | 0.5km/flat/free | 0.5km/flat/s&g | 5km/flat/free | 5km/flat/s&g | 5km/climb3/free (grade) | 5km/climb3/s&g (grade) | 5km/underwater/free (grade) | 5km/underwater/s&g (grade) | eisenhower_tunnel/flat/free | eisenhower_tunnel/flat/s&g |
|---|---|---|---|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 18 (31) → 18 (31) | 40 (231) ✗3 → 40 (231) ✗3 | 167 (306) ✗8 → 167 (306) ✗8 | 561 (2099) ✗18 → 561 (2099) ✗18 | 165 (285) ✗9 → 165 (285) ✗9 | 601 (7198) ✗18 → 601 (7198) ✗18 | 102 (217) ✗4 → 102 (217) ✗4 | 658 (8740) ✗16 → 658 (8740) ✗16 | 80 (107) → 80 (107) | 254 (1018) ✗11 → 254 (1018) ✗11 |
| DR calibrated + GPS-blended speed/heading | 9 (20) → 9 (20) | 23 (93) ✗1 → 23 (93) ✗1 | 117 (240) ✗4 → 117 (240) ✗4 | 420 (2355) ✗17 → 420 (2355) ✗17 | 110 (244) ✗5 → 110 (244) ✗5 | 506 (8661) ✗18 → 506 (8661) ✗18 | 71 (96) → 71 (96) | 639 (7987) ✗15 → 639 (7987) ✗15 | 41 (72) → 41 (72) | 153 (1272) ✗8 → 153 (1272) ✗8 |
| Route + filtered IMU speed | 6 (12) → 6 (12) | 18 (92) ✗1 → 18 (92) ✗1 | 103 (257) ✗4 → 103 (257) ✗4 | 385 (782) ✗16 → 385 (782) ✗16 | 93 (247) ✗4 → 93 (247) ✗4 | 501 (782) ✗17 → 501 (782) ✗17 | 44 (95) → 44 (95) | 613 (782) ✗14 → 613 (782) ✗14 | 33 (70) → 33 (70) | 134 (881) ✗8 → 134 (881) ✗8 |
| Route + IMU Kalman filter (distance, speed, offset) | 6 (19) → 6 (19) | 11 (59) ✗1 → 14 (51) ✗1 | 85 (283) ✗4 → 80 (324) ✗4 | 188 (782) ✗9 → 241 (782) ✗13 | 103 (268) ✗4 → 96 (293) ✗3 | 228 (782) ✗12 → 319 (782) ✗13 | 40 (86) → 40 (86) | 312 (782) ✗15 → 322 (782) ✗15 | 75 (196) ✗2 → 43 (127) | 276 (796) ✗11 → 133 (549) ✗7 |
| Route + vehicle speed (reference) | 4 (11) → 4 (11) | 4 (14) → 4 (14) | 6 (17) → 6 (17) | 7 (17) → 7 (17) | 6 (17) → 6 (17) | 7 (17) → 7 (17) | 6 (17) → 6 (17) | 7 (17) → 7 (17) | 7 (17) → 7 (17) | 7 (14) → 7 (14) |
| Route + IMU + standstill oracle: speed reset ‡ | 6 (12) → 6 (12) | 6 (17) → 6 (17) | 103 (257) ✗4 → 103 (257) ✗4 | 131 (607) ✗9 → 131 (607) ✗9 | 93 (247) ✗4 → 93 (247) ✗4 | 144 (782) ✗9 → 144 (782) ✗9 | 44 (95) → 44 (95) | 132 (782) ✗10 → 132 (782) ✗10 | 33 (70) → 33 (70) | 102 (218) ✗3 → 102 (218) ✗3 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 6 (12) → 6 (12) | 5 (14) → 5 (14) | 103 (257) ✗4 → 103 (257) ✗4 | 103 (199) ✗2 → 103 (199) ✗2 | 93 (247) ✗4 → 93 (247) ✗4 | 128 (199) ✗2 → 128 (199) ✗2 | 44 (95) → 44 (95) | 127 (782) ✗9 → 127 (782) ✗9 | 33 (70) → 33 (70) | 24 (36) → 24 (36) |
