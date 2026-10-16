# Benchmark: generated tables

Milestone after step 4: freeze, calibration fixes, oracle, Kalman filter · commit `00ab89b` · 2026-10-16 15:18 UTC · 48 scenarios × 20 runs. † = reference estimator (uses the car's speed reading; not a phone-only solution). Realism options on (bias drift, GPS degradation before the portal).

## How to read the failure states

* **Gross error**: the estimate was more than 200 m from the true position at some time in the tunnel or at C, ahead *or* behind. The position is unusable for guidance.
* **Announcement off**: the exit announcement came more than 15 s early or late (or never). The driver gets the instruction at the wrong time. Never-fired does not happen in practice: a late estimate is pushed past the announcement point when GPS returns, so the announcement is late, not missing.
* **Capped at D** (a data-quality flag, not a third failure): the estimate reached the route end D before the vehicle reached C. A route estimate stops at D, so its error is a lower bound (cells of exactly 782 / 881 / 889 m are the C–D distances). Every capped run is also a gross error.
* In the scenario tables, cells are the error at C [m], median (p90); ✗n = n runs with a gross error, §n = n of them capped at D.

## Overall, without map grade

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1762 (20958) | 1841 (20954) | 86 % | 77 % | 11 % | 54 % |
| DR GPS-calibrated IMU | 1317 (20232) | 1317 (20229) | 70 % | 64 % | 22 % | 45 % |
| DR calibrated + GPS-blended speed/heading | 1348 (20479) | 1348 (20476) | 67 % | 64 % | 23 % | 45 % |
| Route + filtered IMU speed | 782 (943) | 1018 (2763) | 67 % | 64 % | 23 % | 45 % |
| Route + IMU Kalman filter (distance, speed, offset) | 782 (959) | 1018 (2749) | 66 % | 63 % | 23 % | 44 % |
| Route + last GPS speed (naive) | 435 (881) | 436 (1815) | 58 % | 52 % | 24 % | 48 % |
| Route + vehicle speed (reference) † | 5 (15) | 6 (15) | 0 % | 0 % | 99 % | 0 % |
| Route + IMU + standstill oracle: speed reset ‡ | 397 (943) | 767 (2315) | 63 % | 54 % | 26 % | 32 % |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 269 (943) | 316 (1746) | 56 % | 54 % | 31 % | 23 % |

## Overall, with map grade

Flat roads (where the map grade changes nothing) are in both overall tables.

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 530 (5560) | 532 (5559) | 72 % | 52 % | 22 % | 25 % |
| DR GPS-calibrated IMU | 80 (584) | 83 (584) | 26 % | 18 % | 58 % | 7 % |
| DR calibrated + GPS-blended speed/heading | 51 (443) | 53 (443) | 17 % | 16 % | 64 % | 6 % |
| Route + filtered IMU speed | 31 (413) | 36 (413) | 16 % | 16 % | 65 % | 6 % |
| Route + IMU Kalman filter (distance, speed, offset) | 30 (325) | 34 (325) | 15 % | 14 % | 65 % | 5 % |
| Route + last GPS speed (naive) | 435 (881) | 436 (1815) | 58 % | 52 % | 24 % | 48 % |
| Route + vehicle speed (reference) † | 5 (14) | 6 (15) | 0 % | 0 % | 99 % | 0 % |
| Route + IMU + standstill oracle: speed reset ‡ | 22 (142) | 26 (145) | 7 % | 8 % | 71 % | 1 % |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 17 (87) | 21 (94) | 3 % | 4 % | 78 % | 1 % |

## Tunnel length, flat road, free flow

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 27 (57) | 78 (165) | 284 (565) ✗14 | 628 (1214) ✗18 §5 | 1720 (3021) ✗20 §10 |
| DR GPS-calibrated IMU | 18 (31) | 27 (53) | 58 (92) | 86 (139) ✗1 | 167 (306) ✗8 |
| DR calibrated + GPS-blended speed/heading | 9 (20) | 13 (24) | 31 (48) | 55 (82) | 117 (240) ✗4 |
| Route + filtered IMU speed | 6 (12) | 11 (20) | 25 (46) | 46 (77) | 103 (257) ✗4 |
| Route + IMU Kalman filter (distance, speed, offset) | 6 (19) | 9 (28) | 20 (72) | 28 (134) | 85 (283) ✗4 |
| Route + last GPS speed (naive) | 23 (50) | 35 (91) | 96 (168) ✗2 | 144 (221) ✗4 | 226 (462) ✗12 |
| Route + vehicle speed (reference) † | 4 (11) | 4 (11) | 4 (12) | 5 (13) | 6 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 6 (12) | 11 (20) | 25 (46) | 46 (77) | 103 (257) ✗4 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 6 (12) | 11 (20) | 25 (46) | 46 (77) | 103 (257) ✗4 |

## Tunnel length, flat road, stop-and-go

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 197 (1517) ✗10 §7 | 376 (2820) ✗16 §9 | 1131 (5658) ✗20 §10 | 2207 (9891) ✗20 §10 | 4481 (20810) ✗20 §11 |
| DR GPS-calibrated IMU | 40 (231) ✗3 | 68 (353) ✗3 | 155 (631) ✗7 §1 | 256 (1024) ✗13 §3 | 561 (2099) ✗18 §5 |
| DR calibrated + GPS-blended speed/heading | 23 (93) ✗1 | 31 (163) ✗2 | 92 (459) ✗4 §1 | 171 (943) ✗8 §3 | 420 (2355) ✗17 §5 |
| Route + filtered IMU speed | 18 (92) ✗1 | 26 (161) ✗2 | 87 (451) ✗4 §1 | 167 (782) ✗8 §3 | 385 (782) ✗16 §5 |
| Route + IMU Kalman filter (distance, speed, offset) | 11 (59) ✗1 | 21 (121) ✗2 | 51 (240) ✗3 | 98 (450) ✗6 §2 | 188 (782) ✗9 §5 |
| Route + last GPS speed (naive) | 782 (782) ✗20 §19 | 782 (782) ✗20 §19 | 782 (782) ✗20 §19 | 782 (782) ✗20 §19 | 782 (782) ✗20 §18 |
| Route + vehicle speed (reference) † | 4 (14) | 5 (14) | 5 (13) | 5 (13) | 7 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 6 (17) | 12 (29) | 31 (96) | 51 (203) ✗2 | 131 (607) ✗9 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 5 (14) | 6 (17) | 16 (27) | 19 (54) | 103 (199) ✗2 |

## Road profile, all geometries, free flow, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 340 (1174) ✗99 §18 | 1886 (7281) ✗139 §120 | 964 (1897) ✗131 |
| DR GPS-calibrated IMU | 58 (149) ✗10 | 1861 (8630) ✗140 §120 | 1185 (2071) ✗132 |
| DR calibrated + GPS-blended speed/heading | 33 (105) ✗4 | 1928 (8680) ✗140 §120 | 1265 (2105) ✗140 |
| Route + filtered IMU speed | 23 (89) ✗4 | 782 (889) ✗140 §120 | 1264 (2103) ✗140 |
| Route + IMU Kalman filter (distance, speed, offset) | 23 (120) ✗6 | 782 (889) ✗140 §120 | 1286 (2115) ✗140 |
| Route + last GPS speed (naive) | 79 (223) ✗25 | 79 (223) ✗25 | 79 (223) ✗25 |
| Route + vehicle speed (reference) † | 5 (14) | 5 (15) | 5 (15) |
| Route + IMU + standstill oracle: speed reset ‡ | 23 (89) ✗4 | 782 (889) ✗140 §120 | 1264 (2103) ✗140 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 23 (89) ✗4 | 782 (889) ✗140 §120 | 1264 (2103) ✗140 |

## Road profile, all geometries, free flow, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 340 (1174) ✗99 §18 | 350 (1318) ✗100 §19 | 180 (593) ✗73 §2 |
| DR GPS-calibrated IMU | 58 (149) ✗10 | 58 (147) ✗11 | 36 (116) ✗4 |
| DR calibrated + GPS-blended speed/heading | 33 (105) ✗4 | 31 (105) ✗5 | 22 (73) |
| Route + filtered IMU speed | 23 (89) ✗4 | 21 (90) ✗4 | 10 (42) |
| Route + IMU Kalman filter (distance, speed, offset) | 23 (120) ✗6 | 22 (126) ✗6 | 12 (44) |
| Route + last GPS speed (naive) | 79 (223) ✗25 | 79 (223) ✗25 | 79 (223) ✗25 |
| Route + vehicle speed (reference) † | 5 (14) | 5 (14) | 5 (14) |
| Route + IMU + standstill oracle: speed reset ‡ | 23 (89) ✗4 | 21 (90) ✗4 | 10 (42) |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 23 (89) ✗4 | 21 (90) ✗4 | 10 (42) |

## Road profile, all geometries, stop-and-go, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1552 (9594) ✗145 §79 | 24506 (61114) ✗160 §160 | 4618 (12456) ✗152 §137 |
| DR GPS-calibrated IMU | 186 (906) ✗79 §16 | 26032 (57783) ✗160 §160 | 4323 (11661) ✗147 §136 |
| DR calibrated + GPS-blended speed/heading | 129 (765) ✗54 §16 | 26462 (58666) ✗160 §160 | 4297 (11659) ✗145 §136 |
| Route + filtered IMU speed | 96 (782) ✗52 §15 | 782 (889) ✗160 §160 | 782 (889) ✗145 §136 |
| Route + IMU Kalman filter (distance, speed, offset) | 61 (595) ✗43 §11 | 782 (889) ✗160 §160 | 782 (889) ✗146 §136 |
| Route + last GPS speed (naive) | 782 (889) ✗160 §153 | 782 (889) ✗160 §153 | 782 (889) ✗160 §153 |
| Route + vehicle speed (reference) † | 5 (14) | 6 (15) | 6 (15) |
| Route + IMU + standstill oracle: speed reset ‡ | 34 (197) ✗17 | 782 (889) ✗160 §132 | 468 (881) ✗140 §51 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 16 (66) ✗2 | 387 (782) ✗126 §40 | 629 (881) ✗124 §60 |

## Road profile, all geometries, stop-and-go, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1552 (9594) ✗145 §79 | 2386 (21152) ✗147 §86 | 569 (2651) ✗130 §36 |
| DR GPS-calibrated IMU | 186 (906) ✗79 §16 | 223 (2321) ✗84 §31 | 131 (939) ✗59 §17 |
| DR calibrated + GPS-blended speed/heading | 129 (765) ✗54 §16 | 142 (2194) ✗63 §27 | 88 (780) ✗39 §15 |
| Route + filtered IMU speed | 96 (782) ✗52 §15 | 116 (782) ✗60 §28 | 40 (762) ✗32 §15 |
| Route + IMU Kalman filter (distance, speed, offset) | 61 (595) ✗43 §11 | 92 (782) ✗57 §25 | 37 (466) ✗34 §13 |
| Route + last GPS speed (naive) | 782 (889) ✗160 §153 | 782 (889) ✗160 §153 | 782 (889) ✗160 §153 |
| Route + vehicle speed (reference) † | 5 (14) | 5 (14) | 5 (14) |
| Route + IMU + standstill oracle: speed reset ‡ | 34 (197) ✗17 | 36 (259) ✗24 §3 | 19 (180) ✗16 §5 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 16 (66) ✗2 | 17 (78) ✗2 | 18 (135) ✗13 §5 |

## Presets (real / demo geometry), flat road, free flow

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 442 (709) ✗15 | 650 (1059) ✗19 §3 | 257 (507) ✗13 |
| DR GPS-calibrated IMU | 80 (107) | 83 (150) ✗1 | 54 (90) |
| DR calibrated + GPS-blended speed/heading | 41 (72) | 81 (119) | 25 (44) |
| Route + filtered IMU speed | 33 (70) | 46 (90) | 21 (47) |
| Route + IMU Kalman filter (distance, speed, offset) | 75 (196) ✗2 | 38 (63) | 17 (58) |
| Route + last GPS speed (naive) | 64 (205) ✗3 | 94 (193) ✗2 | 93 (167) ✗2 |
| Route + vehicle speed (reference) † | 7 (17) | 8 (17) | 4 (12) |
| Route + IMU + standstill oracle: speed reset ‡ | 33 (70) | 46 (90) | 21 (47) |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 33 (70) | 46 (90) | 21 (47) |

## Presets (real / demo geometry), flat road, stop-and-go

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1984 (8701) ✗20 §11 | 2249 (10099) ✗20 §11 | 1030 (5140) ✗19 §10 |
| DR GPS-calibrated IMU | 254 (1018) ✗11 §4 | 281 (886) ✗18 §2 | 142 (574) ✗6 §1 |
| DR calibrated + GPS-blended speed/heading | 153 (1272) ✗8 §3 | 202 (973) ✗10 §3 | 77 (408) ✗4 §1 |
| Route + filtered IMU speed | 134 (881) ✗8 §3 | 132 (864) ✗9 §2 | 84 (436) ✗4 §1 |
| Route + IMU Kalman filter (distance, speed, offset) | 276 (796) ✗11 §2 | 133 (567) ✗8 §2 | 45 (240) ✗3 |
| Route + last GPS speed (naive) | 881 (881) ✗20 §20 | 889 (889) ✗20 §20 | 782 (782) ✗20 §19 |
| Route + vehicle speed (reference) † | 7 (14) | 7 (15) | 5 (13) |
| Route + IMU + standstill oracle: speed reset ‡ | 102 (218) ✗3 | 68 (224) ✗3 | 28 (91) |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 24 (36) | 26 (54) | 16 (24) |
