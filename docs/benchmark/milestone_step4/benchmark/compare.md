# Benchmark comparison

Baseline: commit `36904cb` (2026-10-15 13:22 UTC). This run: commit `00ab89b`. 9600 shared runs. Cells: median error at C [m], baseline → this run. ⚠ = worse by more than 10 % and 5 m.

| estimator | flat / free | flat / stop_and_go | climb3 / free | climb3 / stop_and_go | underwater / free | underwater / stop_and_go |
|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 340 → 340 | 1552 → 1552 | 713 → 704 | 11367 → 11367 | 360 → 360 | 1490 → 1530 |
| DR GPS-calibrated IMU | 80 → 58 | 235 → 186 | 213 → 134 | 4705 → 4244 | 103 → 103 | 821 → 729 |
| DR calibrated + GPS-blended speed/heading | 42 → 33 | 159 → 129 | 150 → 113 | 4371 → 4098 | 67 → 72 | 635 → 526 |
| Route + filtered IMU speed | 33 → 23 | 127 → 96 | 156 → 109 | 782 → 782 | 50 → 54 | 590 → 488 |
| Route + last GPS speed (naive) | 79 → 79 | 782 → 782 | 79 → 79 | 782 → 782 | 79 → 79 | 782 → 782 |
| Route + vehicle speed (reference) | 5 → 5 | 5 → 5 | 5 → 5 | 6 → 6 | 5 → 5 | 6 → 6 |

**Regressions:** none
