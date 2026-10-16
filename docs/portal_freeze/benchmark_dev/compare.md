# Benchmark comparison

Baseline: commit `36904cb` (2026-10-15 13:22 UTC). This run: commit `1811edd+dirty`. 640 shared runs. Cells: median error at C [m], baseline → this run. ⚠ = worse by more than 10 % and 5 m.

| estimator | flat / free | flat / stop_and_go | climb3 / free | climb3 / stop_and_go | underwater / free | underwater / stop_and_go |
|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 76 → 32 | 239 → 239 | 317 → 167 | 524 → 523 | 104 → 106 | 726 → 766 |
| DR calibrated + GPS-blended speed/heading | 49 → 21 | 185 → 158 | 211 → 106 | 412 → 341 | 66 → 72 | 505 → 990 ⚠ |
| Route + filtered IMU speed | 19 → 13 | 152 → 93 | 223 → 109 | 427 → 297 | 44 → 42 | 490 → 767 ⚠ |
| Route + vehicle speed (reference) | 5 → 5 | 5 → 5 | 6 → 6 | 7 → 7 | 6 → 6 | 7 → 7 |

**Regressions:** DR calibrated + GPS-blended speed/heading, underwater / stop_and_go: 505 → 990 m; Route + filtered IMU speed, underwater / stop_and_go: 490 → 767 m

## Per scenario

Error at C [m], median (p90) ✗gross errors, baseline → this run.

| estimator | 0.5km/flat/free | 0.5km/flat/s&g | 5km/flat/free | 5km/flat/s&g | 5km/climb3/free (grade) | 5km/climb3/s&g (grade) | 5km/underwater/free (grade) | 5km/underwater/s&g (grade) |
|---|---|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 18 (32) → 18 (31) | 37 (350) ✗3 → 40 (231) ✗3 | 316 (512) ✗16 → 167 (306) ✗8 | 562 (3914) ✗19 → 561 (2100) ✗18 | 317 (517) ✗16 → 167 (303) ✗8 | 524 (12413) ✗19 → 523 (6142) ✗17 | 104 (205) ✗4 → 106 (215) ✗4 | 726 (10867) ✗19 → 766 (8726) ✗17 |
| DR calibrated + GPS-blended speed/heading | 14 (19) → 9 (20) | 22 (221) ✗3 → 23 (93) ✗1 | 217 (393) ✗11 → 117 (240) ✗4 | 470 (3314) ✗17 → 420 (2356) ✗17 | 211 (409) ✗10 → 106 (249) ✗4 | 412 (10405) ✗19 → 341 (7833) ✗15 | 66 (112) → 72 (103) | 505 (10803) ✗17 → 990 (8761) ✗15 |
| Route + filtered IMU speed | 5 (15) → 6 (12) | 18 (220) ✗3 → 18 (92) ✗1 | 231 (420) ✗11 → 103 (257) ✗4 | 482 (804) ✗16 → 385 (782) ✗16 | 223 (436) ✗12 → 109 (268) ✗4 | 427 (811) ✗17 → 297 (782) ✗13 | 44 (107) → 42 (93) | 490 (782) ✗14 → 767 (782) ✗13 |
| Route + vehicle speed (reference) | 4 (11) → 4 (11) | 4 (14) → 4 (14) | 6 (17) → 6 (17) | 7 (17) → 7 (17) | 6 (17) → 6 (17) | 7 (17) → 7 (17) | 6 (17) → 6 (17) | 7 (17) → 7 (17) |
