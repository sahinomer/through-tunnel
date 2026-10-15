# Benchmark: generated tables

Baseline: 5 phone-only estimators + reference, before estimator work · commit `36904cb` · 2026-10-15 13:22 UTC · 48 scenarios × 20 runs. Cells: error at C [m], median (p90). ✗n = n failed runs (route end reached before C, or announcement missed). † = reference estimator (uses the car's speed reading; not a phone-only solution). Realism options on (bias drift, GPS degradation before the portal).

## Overall

Flat roads are counted in both error columns (the map grade changes nothing there); the other columns use the runs without map grade.

| estimator | error at C, map grade off [m] | error at C, map grade on [m] | max in tunnel [m] | announcement within ±3 s | failed runs |
|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1762 (20958) | 526 (5433) | 1841 (20954) | 11 % | 53.5 % |
| DR GPS-calibrated IMU | 1338 (20563) | 96 (702) | 1338 (20559) | 18 % | 45.8 % |
| DR calibrated + GPS-blended speed/heading | 1336 (20668) | 58 (543) | 1336 (20667) | 21 % | 45.3 % |
| Route + filtered IMU speed | 782 (889) | 39 (544) | 1007 (2719) | 20 % | 45.3 % |
| Route + last GPS speed (naive) | 435 (881) | 435 (881) | 436 (1815) | 24 % | 47.8 % |
| Route + vehicle speed (reference) † | 5 (15) | 5 (14) | 6 (15) | 99 % | 0.0 % |

## Tunnel length, flat road, free flow

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 27 (57) | 78 (165) | 284 (565) | 628 (1214) ✗5 | 1720 (3021) ✗10 |
| DR GPS-calibrated IMU | 18 (32) | 37 (66) | 86 (157) | 142 (267) | 316 (512) |
| DR calibrated + GPS-blended speed/heading | 14 (19) | 18 (33) | 40 (87) | 88 (168) | 217 (393) |
| Route + filtered IMU speed | 5 (15) | 15 (32) | 38 (87) | 82 (173) | 231 (420) |
| Route + last GPS speed (naive) | 23 (50) | 35 (91) | 96 (168) | 144 (221) | 226 (462) |
| Route + vehicle speed (reference) † | 4 (11) | 4 (11) | 4 (12) | 5 (13) | 6 (17) |

## Tunnel length, flat road, stop-and-go

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 197 (1517) ✗7 | 376 (2820) ✗9 | 1131 (5658) ✗10 | 2207 (9891) ✗10 | 4481 (20810) ✗11 |
| DR GPS-calibrated IMU | 37 (350) | 81 (555) | 133 (1135) ✗3 | 223 (1898) ✗3 | 562 (3914) ✗5 |
| DR calibrated + GPS-blended speed/heading | 22 (221) | 39 (359) | 87 (823) ✗2 | 167 (1517) ✗3 | 470 (3314) ✗6 |
| Route + filtered IMU speed | 18 (220) | 34 (357) | 86 (770) ✗2 | 166 (782) ✗3 | 482 (804) ✗5 |
| Route + last GPS speed (naive) | 782 (782) ✗19 | 782 (782) ✗19 | 782 (782) ✗19 | 782 (782) ✗19 | 782 (782) ✗18 |
| Route + vehicle speed (reference) † | 4 (14) | 5 (14) | 5 (13) | 5 (13) | 7 (17) |

## Road profile, all geometries, free flow, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 340 (1174) ✗18 | 1886 (7281) ✗120 | 964 (1897) |
| DR GPS-calibrated IMU | 80 (235) | 1799 (8389) ✗120 | 1105 (1977) |
| DR calibrated + GPS-blended speed/heading | 42 (168) | 1851 (8459) ✗120 | 1157 (1987) |
| Route + filtered IMU speed | 33 (168) | 782 (889) ✗120 | 1155 (1972) |
| Route + last GPS speed (naive) | 79 (223) | 79 (223) | 79 (223) |
| Route + vehicle speed (reference) † | 5 (14) | 5 (15) | 5 (15) |

## Road profile, all geometries, free flow, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 340 (1174) ✗18 | 350 (1319) ✗19 | 179 (592) ✗2 |
| DR GPS-calibrated IMU | 80 (235) | 79 (239) | 42 (112) |
| DR calibrated + GPS-blended speed/heading | 42 (168) | 44 (171) | 26 (73) |
| Route + filtered IMU speed | 33 (168) | 33 (168) | 16 (46) |
| Route + last GPS speed (naive) | 79 (223) | 79 (223) | 79 (223) |
| Route + vehicle speed (reference) † | 5 (14) | 5 (14) | 5 (14) |

## Road profile, all geometries, stop-and-go, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1552 (9594) ✗79 | 24506 (61114) ✗160 | 4618 (12456) ✗137 |
| DR GPS-calibrated IMU | 235 (1273) ✗23 | 25411 (56201) ✗160 | 4603 (12289) ✗137 |
| DR calibrated + GPS-blended speed/heading | 159 (997) ✗19 | 25533 (56438) ✗160 | 4594 (12254) ✗136 |
| Route + filtered IMU speed | 127 (782) ✗18 | 782 (889) ✗160 | 782 (889) ✗137 |
| Route + last GPS speed (naive) | 782 (889) ✗153 | 782 (889) ✗153 | 782 (889) ✗153 |
| Route + vehicle speed (reference) † | 5 (14) | 6 (15) | 6 (15) |

## Road profile, all geometries, stop-and-go, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1552 (9594) ✗79 | 2321 (20707) ✗86 | 575 (2512) ✗36 |
| DR GPS-calibrated IMU | 235 (1273) ✗23 | 241 (3609) ✗37 | 128 (1070) ✗20 |
| DR calibrated + GPS-blended speed/heading | 159 (997) ✗19 | 172 (3005) ✗33 | 79 (690) ✗11 |
| Route + filtered IMU speed | 127 (782) ✗18 | 127 (792) ✗35 | 44 (680) ✗12 |
| Route + last GPS speed (naive) | 782 (889) ✗153 | 782 (889) ✗153 | 782 (889) ✗153 |
| Route + vehicle speed (reference) † | 5 (14) | 5 (14) | 5 (14) |

## Presets (real / demo geometry), flat road, free flow

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 442 (709) | 650 (1059) ✗3 | 257 (507) |
| DR GPS-calibrated IMU | 97 (153) | 96 (168) | 75 (142) |
| DR calibrated + GPS-blended speed/heading | 38 (94) | 74 (115) | 38 (76) |
| Route + filtered IMU speed | 34 (97) | 22 (91) | 35 (82) |
| Route + last GPS speed (naive) | 64 (205) | 94 (193) | 93 (167) |
| Route + vehicle speed (reference) † | 7 (17) | 8 (17) | 4 (12) |

## Presets (real / demo geometry), flat road, stop-and-go

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1984 (8701) ✗11 | 2249 (10099) ✗11 | 1030 (5140) ✗10 |
| DR GPS-calibrated IMU | 359 (995) ✗4 | 400 (1316) ✗5 | 129 (1011) ✗3 |
| DR calibrated + GPS-blended speed/heading | 305 (893) ✗3 | 351 (1257) ✗3 | 80 (740) ✗2 |
| Route + filtered IMU speed | 294 (838) ✗2 | 311 (889) ✗4 | 84 (754) ✗2 |
| Route + last GPS speed (naive) | 881 (881) ✗20 | 889 (889) ✗20 | 782 (782) ✗19 |
| Route + vehicle speed (reference) † | 7 (14) | 7 (15) | 5 (13) |
