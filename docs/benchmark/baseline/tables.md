# Benchmark: generated tables

Baseline: 5 phone-only estimators + reference, before estimator work · commit `36904cb` · 2026-10-15 13:22 UTC · 48 scenarios × 20 runs. † = reference estimator (uses the car's speed reading; not a phone-only solution). Realism options on (bias drift, GPS degradation before the portal).

## How to read the failure states

* **Gross error**: the estimate was more than 200 m from the true position at some time in the tunnel or at C, ahead *or* behind. The position is unusable for guidance.
* **Announcement off**: the exit announcement came more than 15 s early or late (or never). The driver gets the instruction at the wrong time. Never-fired does not happen in practice: a late estimate is pushed past the announcement point when GPS returns, so the announcement is late, not missing.
* **Capped at D** (a data-quality flag, not a third failure): the estimate reached the route end D before the vehicle reached C. A route estimate stops at D, so its error is a lower bound (cells of exactly 782 / 881 / 889 m are the C–D distances). Every capped run is also a gross error.
* In the scenario tables, cells are the error at C [m], median (p90); ✗n = n runs with a gross error, §n = n of them capped at D.

## Overall, without map grade

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1762 (20958) | 1841 (20954) | 86 % | 77 % | 11 % | 54 % |
| DR GPS-calibrated IMU | 1338 (20563) | 1338 (20559) | 72 % | 65 % | 18 % | 46 % |
| DR calibrated + GPS-blended speed/heading | 1336 (20668) | 1336 (20667) | 69 % | 65 % | 21 % | 45 % |
| Route + filtered IMU speed | 782 (889) | 1007 (2719) | 69 % | 65 % | 20 % | 45 % |
| Route + last GPS speed (naive) | 435 (881) | 436 (1815) | 58 % | 52 % | 24 % | 48 % |
| Route + vehicle speed (reference) † | 5 (15) | 6 (15) | 0 % | 0 % | 99 % | 0 % |

## Overall, with map grade

Flat roads (where the map grade changes nothing) are in both overall tables.

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 526 (5433) | 529 (5432) | 72 % | 52 % | 22 % | 25 % |
| DR GPS-calibrated IMU | 96 (702) | 98 (702) | 30 % | 21 % | 50 % | 8 % |
| DR calibrated + GPS-blended speed/heading | 58 (543) | 62 (542) | 22 % | 19 % | 59 % | 7 % |
| Route + filtered IMU speed | 39 (544) | 44 (544) | 21 % | 20 % | 59 % | 7 % |
| Route + last GPS speed (naive) | 435 (881) | 436 (1815) | 58 % | 52 % | 24 % | 48 % |
| Route + vehicle speed (reference) † | 5 (14) | 6 (15) | 0 % | 0 % | 99 % | 0 % |

## Tunnel length, flat road, free flow

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 27 (57) | 78 (165) | 284 (565) ✗14 | 628 (1214) ✗18 §5 | 1720 (3021) ✗20 §10 |
| DR GPS-calibrated IMU | 18 (32) | 37 (66) | 86 (157) ✗1 | 142 (267) ✗4 | 316 (512) ✗16 |
| DR calibrated + GPS-blended speed/heading | 14 (19) | 18 (33) | 40 (87) | 88 (168) ✗1 | 217 (393) ✗11 |
| Route + filtered IMU speed | 5 (15) | 15 (32) | 38 (87) | 82 (173) ✗1 | 231 (420) ✗11 |
| Route + last GPS speed (naive) | 23 (50) | 35 (91) | 96 (168) ✗2 | 144 (221) ✗4 | 226 (462) ✗12 |
| Route + vehicle speed (reference) † | 4 (11) | 4 (11) | 4 (12) | 5 (13) | 6 (17) |

## Tunnel length, flat road, stop-and-go

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 197 (1517) ✗10 §7 | 376 (2820) ✗16 §9 | 1131 (5658) ✗20 §10 | 2207 (9891) ✗20 §10 | 4481 (20810) ✗20 §11 |
| DR GPS-calibrated IMU | 37 (350) ✗3 | 81 (555) ✗4 | 133 (1135) ✗9 §3 | 223 (1898) ✗12 §3 | 562 (3914) ✗19 §5 |
| DR calibrated + GPS-blended speed/heading | 22 (221) ✗3 | 39 (359) ✗4 | 87 (823) ✗6 §2 | 167 (1517) ✗9 §3 | 470 (3314) ✗17 §6 |
| Route + filtered IMU speed | 18 (220) ✗3 | 34 (357) ✗4 | 86 (770) ✗6 §2 | 166 (782) ✗9 §3 | 482 (804) ✗16 §5 |
| Route + last GPS speed (naive) | 782 (782) ✗20 §19 | 782 (782) ✗20 §19 | 782 (782) ✗20 §19 | 782 (782) ✗20 §19 | 782 (782) ✗20 §18 |
| Route + vehicle speed (reference) † | 4 (14) | 5 (14) | 5 (13) | 5 (13) | 7 (17) |

## Road profile, all geometries, free flow, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 340 (1174) ✗99 §18 | 1886 (7281) ✗139 §120 | 964 (1897) ✗131 |
| DR GPS-calibrated IMU | 80 (235) ✗22 | 1799 (8389) ✗140 §120 | 1105 (1977) ✗130 |
| DR calibrated + GPS-blended speed/heading | 42 (168) ✗12 | 1851 (8459) ✗140 §120 | 1157 (1987) ✗133 |
| Route + filtered IMU speed | 33 (168) ✗12 | 782 (889) ✗140 §120 | 1155 (1972) ✗133 |
| Route + last GPS speed (naive) | 79 (223) ✗25 | 79 (223) ✗25 | 79 (223) ✗25 |
| Route + vehicle speed (reference) † | 5 (14) | 5 (15) | 5 (15) |

## Road profile, all geometries, free flow, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 340 (1174) ✗99 §18 | 350 (1319) ✗100 §19 | 179 (592) ✗75 §2 |
| DR GPS-calibrated IMU | 80 (235) ✗22 | 79 (239) ✗22 | 42 (112) ✗4 |
| DR calibrated + GPS-blended speed/heading | 42 (168) ✗12 | 44 (171) ✗11 | 26 (73) |
| Route + filtered IMU speed | 33 (168) ✗12 | 33 (168) ✗13 | 16 (46) |
| Route + last GPS speed (naive) | 79 (223) ✗25 | 79 (223) ✗25 | 79 (223) ✗25 |
| Route + vehicle speed (reference) † | 5 (14) | 5 (14) | 5 (14) |

## Road profile, all geometries, stop-and-go, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1552 (9594) ✗145 §79 | 24506 (61114) ✗160 §160 | 4618 (12456) ✗152 §137 |
| DR GPS-calibrated IMU | 235 (1273) ✗89 §23 | 25411 (56201) ✗160 §160 | 4603 (12289) ✗149 §137 |
| DR calibrated + GPS-blended speed/heading | 159 (997) ✗73 §19 | 25533 (56438) ✗160 §160 | 4594 (12254) ✗149 §136 |
| Route + filtered IMU speed | 127 (782) ✗69 §18 | 782 (889) ✗160 §160 | 782 (889) ✗149 §137 |
| Route + last GPS speed (naive) | 782 (889) ✗160 §153 | 782 (889) ✗160 §153 | 782 (889) ✗160 §153 |
| Route + vehicle speed (reference) † | 5 (14) | 6 (15) | 6 (15) |

## Road profile, all geometries, stop-and-go, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1552 (9594) ✗145 §79 | 2321 (20707) ✗147 §86 | 575 (2512) ✗130 §36 |
| DR GPS-calibrated IMU | 235 (1273) ✗89 §23 | 241 (3609) ✗89 §37 | 128 (1070) ✗63 §20 |
| DR calibrated + GPS-blended speed/heading | 159 (997) ✗73 §19 | 172 (3005) ✗75 §33 | 79 (690) ✗45 §11 |
| Route + filtered IMU speed | 127 (782) ✗69 §18 | 127 (792) ✗68 §35 | 44 (680) ✗38 §12 |
| Route + last GPS speed (naive) | 782 (889) ✗160 §153 | 782 (889) ✗160 §153 | 782 (889) ✗160 §153 |
| Route + vehicle speed (reference) † | 5 (14) | 5 (14) | 5 (14) |

## Presets (real / demo geometry), flat road, free flow

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 442 (709) ✗15 | 650 (1059) ✗19 §3 | 257 (507) ✗13 |
| DR GPS-calibrated IMU | 97 (153) | 96 (168) ✗1 | 75 (142) |
| DR calibrated + GPS-blended speed/heading | 38 (94) | 74 (115) | 38 (76) |
| Route + filtered IMU speed | 34 (97) | 22 (91) | 35 (82) |
| Route + last GPS speed (naive) | 64 (205) ✗3 | 94 (193) ✗2 | 93 (167) ✗2 |
| Route + vehicle speed (reference) † | 7 (17) | 8 (17) | 4 (12) |

## Presets (real / demo geometry), flat road, stop-and-go

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1984 (8701) ✗20 §11 | 2249 (10099) ✗20 §11 | 1030 (5140) ✗19 §10 |
| DR GPS-calibrated IMU | 359 (995) ✗16 §4 | 400 (1316) ✗18 §5 | 129 (1011) ✗8 §3 |
| DR calibrated + GPS-blended speed/heading | 305 (893) ✗13 §3 | 351 (1257) ✗16 §3 | 80 (740) ✗5 §2 |
| Route + filtered IMU speed | 294 (838) ✗13 §2 | 311 (889) ✗12 §4 | 84 (754) ✗6 §2 |
| Route + last GPS speed (naive) | 881 (881) ✗20 §20 | 889 (889) ✗20 §20 | 782 (782) ✗20 §19 |
| Route + vehicle speed (reference) † | 7 (14) | 7 (15) | 5 (13) |
