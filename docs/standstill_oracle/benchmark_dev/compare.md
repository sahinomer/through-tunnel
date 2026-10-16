# Benchmark comparison

Baseline: commit `36904cb` (2026-10-15 13:22 UTC). This run: commit `d0dc11a+dirty`. 640 shared runs. Cells: median error at C [m], baseline → this run. ⚠ = worse by more than 10 % and 5 m.

| estimator | flat / free | flat / stop_and_go | climb3 / free | climb3 / stop_and_go | underwater / free | underwater / stop_and_go |
|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 76 → 32 | 239 → 238 | 317 → 165 | 524 → 601 ⚠ | 104 → 102 | 726 → 658 |
| DR calibrated + GPS-blended speed/heading | 49 → 21 | 185 → 158 | 211 → 110 | 412 → 506 ⚠ | 66 → 71 | 505 → 639 ⚠ |
| Route + filtered IMU speed | 19 → 13 | 152 → 93 | 223 → 93 | 427 → 501 ⚠ | 44 → 44 | 490 → 613 ⚠ |
| Route + vehicle speed (reference) | 5 → 5 | 5 → 5 | 6 → 6 | 7 → 7 | 6 → 6 | 7 → 7 |

**Regressions:** DR GPS-calibrated IMU, climb3 / stop_and_go: 524 → 601 m; DR calibrated + GPS-blended speed/heading, climb3 / stop_and_go: 412 → 506 m; DR calibrated + GPS-blended speed/heading, underwater / stop_and_go: 505 → 639 m; Route + filtered IMU speed, climb3 / stop_and_go: 427 → 501 m; Route + filtered IMU speed, underwater / stop_and_go: 490 → 613 m

## Per scenario

Error at C [m], median (p90) ✗gross errors, baseline → this run.

| estimator | 0.5km/flat/free | 0.5km/flat/s&g | 5km/flat/free | 5km/flat/s&g | 5km/climb3/free (grade) | 5km/climb3/s&g (grade) | 5km/underwater/free (grade) | 5km/underwater/s&g (grade) |
|---|---|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 18 (32) → 18 (31) | 37 (350) ✗3 → 40 (231) ✗3 | 316 (512) ✗16 → 167 (306) ✗8 | 562 (3914) ✗19 → 561 (2099) ✗18 | 317 (517) ✗16 → 165 (285) ✗9 | 524 (12413) ✗19 → 601 (7198) ✗18 | 104 (205) ✗4 → 102 (217) ✗4 | 726 (10867) ✗19 → 658 (8740) ✗16 |
| DR calibrated + GPS-blended speed/heading | 14 (19) → 9 (20) | 22 (221) ✗3 → 23 (93) ✗1 | 217 (393) ✗11 → 117 (240) ✗4 | 470 (3314) ✗17 → 420 (2355) ✗17 | 211 (409) ✗10 → 110 (244) ✗5 | 412 (10405) ✗19 → 506 (8661) ✗18 | 66 (112) → 71 (96) | 505 (10803) ✗17 → 639 (7987) ✗15 |
| Route + filtered IMU speed | 5 (15) → 6 (12) | 18 (220) ✗3 → 18 (92) ✗1 | 231 (420) ✗11 → 103 (257) ✗4 | 482 (804) ✗16 → 385 (782) ✗16 | 223 (436) ✗12 → 93 (247) ✗4 | 427 (811) ✗17 → 501 (782) ✗17 | 44 (107) → 44 (95) | 490 (782) ✗14 → 613 (782) ✗14 |
| Route + vehicle speed (reference) | 4 (11) → 4 (11) | 4 (14) → 4 (14) | 6 (17) → 6 (17) | 7 (17) → 7 (17) | 6 (17) → 6 (17) | 7 (17) → 7 (17) | 6 (17) → 6 (17) | 7 (17) → 7 (17) |
