# Benchmark: generated tables

Milestone after step 5: yaw state, announcement policy, wider priors, map curve fixes · commit `0b4ee46` · 2026-10-17 17:02 UTC · 48 scenarios × 20 runs. † = reference estimator (uses the car's speed reading; not a phone-only solution). Realism options on (bias drift, GPS degradation before the portal).

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
| Route + IMU Kalman filter (distance, speed, offset) | 782 (953) | 1017 (2751) | 66 % | 63 % | 24 % | 44 % |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 782 (947) | 1018 (2763) | 67 % | 63 % | 22 % | 45 % |
| Route + IMU Kalman filter + map curves | 349 (1923) | 611 (2140) | 62 % | 51 % | 35 % | 22 % |
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
| Route + IMU Kalman filter (distance, speed, offset) | 29 (312) | 33 (312) | 14 % | 15 % | 67 % | 5 % |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 33 (387) | 38 (387) | 17 % | 15 % | 63 % | 6 % |
| Route + IMU Kalman filter + map curves | 8 (51) | 18 (76) | 3 % | 3 % | 89 % | 0 % |
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
| Route + IMU Kalman filter (distance, speed, offset) | 6 (19) | 10 (32) | 22 (77) | 32 (141) | 80 (324) ✗4 |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 6 (19) | 9 (25) | 18 (56) | 28 (107) | 84 (253) ✗4 |
| Route + IMU Kalman filter + map curves | 2 (7) | 2 (8) | 2 (7) | 7 (12) | 12 (23) |
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
| Route + IMU Kalman filter (distance, speed, offset) | 14 (51) ✗1 | 24 (96) ✗1 | 65 (233) ✗3 §1 | 122 (547) ✗6 §1 | 241 (782) ✗13 §4 |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 11 (82) ✗1 | 15 (155) ✗1 | 58 (312) ✗4 §1 | 118 (554) ✗8 §1 | 299 (782) ✗12 §7 |
| Route + IMU Kalman filter + map curves | 2 (6) | 3 (10) | 9 (23) | 17 (41) | 30 (94) ✗1 |
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
| Route + IMU Kalman filter (distance, speed, offset) | 23 (119) ✗4 | 782 (889) ✗140 §120 | 1253 (2117) ✗140 |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 23 (156) ✗9 | 782 (889) ✗140 §120 | 1175 (2105) ✗140 |
| Route + IMU Kalman filter + map curves | 5 (22) | 371 (889) ✗140 §50 | 1298 (3102) ✗131 |
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
| Route + IMU Kalman filter (distance, speed, offset) | 23 (119) ✗4 | 21 (116) ✗3 | 12 (42) |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 23 (156) ✗9 | 20 (151) ✗7 | 12 (45) |
| Route + IMU Kalman filter + map curves | 5 (22) | 5 (22) | 5 (20) |
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
| Route + IMU Kalman filter (distance, speed, offset) | 70 (524) ✗42 §10 | 782 (889) ✗160 §160 | 782 (889) ✗146 §136 |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 83 (782) ✗48 §17 | 782 (889) ✗160 §160 | 782 (889) ✗146 §136 |
| Route + IMU Kalman filter + map curves | 12 (54) ✗9 | 782 (889) ✗160 §105 | 881 (3049) ✗151 §54 |
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
| Route + IMU Kalman filter (distance, speed, offset) | 70 (524) ✗42 §10 | 89 (782) ✗55 §22 | 34 (379) ✗29 §12 |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 83 (782) ✗48 §17 | 105 (782) ✗59 §24 | 37 (782) ✗36 §16 |
| Route + IMU Kalman filter + map curves | 12 (54) ✗9 | 14 (76) ✗10 §1 | 16 (112) ✗7 §1 |
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
| Route + IMU Kalman filter (distance, speed, offset) | 43 (127) | 37 (63) | 17 (69) |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 86 (246) ✗5 | 44 (102) | 15 (53) |
| Route + IMU Kalman filter + map curves | 22 (85) | 10 (29) | 4 (8) |
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
| Route + IMU Kalman filter (distance, speed, offset) | 133 (549) ✗7 §2 | 132 (560) ✗8 §2 | 58 (227) ✗3 |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 211 (881) ✗11 §5 | 127 (705) ✗8 §2 | 57 (304) ✗3 §1 |
| Route + IMU Kalman filter + map curves | 20 (211) ✗8 | 21 (31) | 7 (47) |
| Route + last GPS speed (naive) | 881 (881) ✗20 §20 | 889 (889) ✗20 §20 | 782 (782) ✗20 §19 |
| Route + vehicle speed (reference) † | 7 (14) | 7 (15) | 5 (13) |
| Route + IMU + standstill oracle: speed reset ‡ | 102 (218) ✗3 | 68 (224) ✗3 | 28 (91) |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 24 (36) | 26 (54) | 16 (24) |

## Uncertainty-aware announcement (step 6.2)

Plain = the shared announcement at the estimated announcement point. Aware = fires when the estimate plus min(2σ, 300 m) reaches it; precise if σ ≤ 30 m then, else hedged. Time error + = late; a never-fired announcement counts as late. Map grade on for sloped roads.

| scenario | estimator | announcement | late > 3 s | late > 15 s | good ±3 s | early > 15 s | median [s] | precise |
|---|---|---|---|---|---|---|---|---|
| ladder_0.5km/flat/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_0.5km/flat/free | route_kf | aware | 0 % | 0 % | 100 % | 0 % | -1.0 | 100 % |
| ladder_0.5km/flat/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.1 | – |
| ladder_0.5km/flat/free | route_kf_yaw | aware | 0 % | 0 % | 100 % | 0 % | -1.1 | 100 % |
| ladder_0.5km/flat/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | +0.1 | – |
| ladder_0.5km/flat/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -1.0 | 100 % |
| ladder_0.5km/flat/stop_and_go | route_kf | plain | 0 % | 0 % | 95 % | 0 % | -0.1 | – |
| ladder_0.5km/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 10 % | 5 % | -5.0 | 100 % |
| ladder_0.5km/flat/stop_and_go | route_kf_yaw | plain | 0 % | 0 % | 95 % | 0 % | -0.3 | – |
| ladder_0.5km/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 10 % | 0 % | -5.5 | 100 % |
| ladder_0.5km/flat/stop_and_go | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.5 | – |
| ladder_0.5km/flat/stop_and_go | route_kf_map | aware | 0 % | 0 % | 10 % | 5 % | -4.7 | 100 % |
| ladder_0.5km/climb3/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_0.5km/climb3/free | route_kf | aware | 0 % | 0 % | 100 % | 0 % | -1.1 | 100 % |
| ladder_0.5km/climb3/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.1 | – |
| ladder_0.5km/climb3/free | route_kf_yaw | aware | 0 % | 0 % | 100 % | 0 % | -1.1 | 100 % |
| ladder_0.5km/climb3/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | +0.0 | – |
| ladder_0.5km/climb3/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -1.0 | 100 % |
| ladder_0.5km/climb3/stop_and_go | route_kf | plain | 0 % | 0 % | 100 % | 0 % | -0.3 | – |
| ladder_0.5km/climb3/stop_and_go | route_kf | aware | 0 % | 0 % | 10 % | 5 % | -4.8 | 100 % |
| ladder_0.5km/climb3/stop_and_go | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | -0.5 | – |
| ladder_0.5km/climb3/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 5 % | 0 % | -5.4 | 100 % |
| ladder_0.5km/climb3/stop_and_go | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.6 | – |
| ladder_0.5km/climb3/stop_and_go | route_kf_map | aware | 0 % | 0 % | 15 % | 5 % | -4.3 | 100 % |
| ladder_0.5km/underwater/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_0.5km/underwater/free | route_kf | aware | 0 % | 0 % | 100 % | 0 % | -1.0 | 100 % |
| ladder_0.5km/underwater/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.1 | – |
| ladder_0.5km/underwater/free | route_kf_yaw | aware | 0 % | 0 % | 100 % | 0 % | -1.1 | 100 % |
| ladder_0.5km/underwater/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | +0.1 | – |
| ladder_0.5km/underwater/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -1.0 | 100 % |
| ladder_0.5km/underwater/stop_and_go | route_kf | plain | 0 % | 0 % | 100 % | 0 % | -0.2 | – |
| ladder_0.5km/underwater/stop_and_go | route_kf | aware | 0 % | 0 % | 10 % | 0 % | -5.3 | 100 % |
| ladder_0.5km/underwater/stop_and_go | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | -0.4 | – |
| ladder_0.5km/underwater/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 5 % | 0 % | -5.5 | 100 % |
| ladder_0.5km/underwater/stop_and_go | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.6 | – |
| ladder_0.5km/underwater/stop_and_go | route_kf_map | aware | 0 % | 0 % | 10 % | 0 % | -4.9 | 100 % |
| ladder_1km/flat/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_1km/flat/free | route_kf | aware | 0 % | 0 % | 100 % | 0 % | -1.1 | 100 % |
| ladder_1km/flat/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_1km/flat/free | route_kf_yaw | aware | 0 % | 0 % | 100 % | 0 % | -1.2 | 100 % |
| ladder_1km/flat/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | +0.0 | – |
| ladder_1km/flat/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.6 | 100 % |
| ladder_1km/flat/stop_and_go | route_kf | plain | 5 % | 5 % | 65 % | 5 % | -0.3 | – |
| ladder_1km/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 40 % | -14.2 | 0 % |
| ladder_1km/flat/stop_and_go | route_kf_yaw | plain | 10 % | 5 % | 65 % | 5 % | -0.0 | – |
| ladder_1km/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 60 % | -15.7 | 0 % |
| ladder_1km/flat/stop_and_go | route_kf_map | plain | 0 % | 0 % | 95 % | 0 % | -0.1 | – |
| ladder_1km/flat/stop_and_go | route_kf_map | aware | 0 % | 0 % | 0 % | 15 % | -6.5 | 60 % |
| ladder_1km/climb3/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_1km/climb3/free | route_kf | aware | 0 % | 0 % | 100 % | 0 % | -1.2 | 100 % |
| ladder_1km/climb3/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.1 | – |
| ladder_1km/climb3/free | route_kf_yaw | aware | 0 % | 0 % | 100 % | 0 % | -1.2 | 100 % |
| ladder_1km/climb3/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.0 | – |
| ladder_1km/climb3/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.7 | 100 % |
| ladder_1km/climb3/stop_and_go | route_kf | plain | 5 % | 0 % | 75 % | 5 % | -0.3 | – |
| ladder_1km/climb3/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 40 % | -14.1 | 0 % |
| ladder_1km/climb3/stop_and_go | route_kf_yaw | plain | 5 % | 0 % | 75 % | 5 % | -0.2 | – |
| ladder_1km/climb3/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 55 % | -15.8 | 0 % |
| ladder_1km/climb3/stop_and_go | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.2 | – |
| ladder_1km/climb3/stop_and_go | route_kf_map | aware | 0 % | 0 % | 0 % | 15 % | -6.6 | 60 % |
| ladder_1km/underwater/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_1km/underwater/free | route_kf | aware | 0 % | 0 % | 100 % | 0 % | -1.1 | 100 % |
| ladder_1km/underwater/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.1 | – |
| ladder_1km/underwater/free | route_kf_yaw | aware | 0 % | 0 % | 100 % | 0 % | -1.2 | 100 % |
| ladder_1km/underwater/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | +0.0 | – |
| ladder_1km/underwater/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.6 | 100 % |
| ladder_1km/underwater/stop_and_go | route_kf | plain | 0 % | 0 % | 95 % | 0 % | -0.4 | – |
| ladder_1km/underwater/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 45 % | -14.4 | 0 % |
| ladder_1km/underwater/stop_and_go | route_kf_yaw | plain | 0 % | 0 % | 95 % | 0 % | -0.6 | – |
| ladder_1km/underwater/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 55 % | -15.4 | 0 % |
| ladder_1km/underwater/stop_and_go | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | +0.1 | – |
| ladder_1km/underwater/stop_and_go | route_kf_map | aware | 0 % | 0 % | 0 % | 5 % | -5.8 | 65 % |
| ladder_2km/flat/free | route_kf | plain | 10 % | 0 % | 85 % | 0 % | +0.4 | – |
| ladder_2km/flat/free | route_kf | aware | 0 % | 0 % | 85 % | 0 % | -2.1 | 100 % |
| ladder_2km/flat/free | route_kf_yaw | plain | 5 % | 0 % | 90 % | 0 % | +0.3 | – |
| ladder_2km/flat/free | route_kf_yaw | aware | 0 % | 0 % | 65 % | 0 % | -2.3 | 100 % |
| ladder_2km/flat/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.1 | – |
| ladder_2km/flat/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.8 | 100 % |
| ladder_2km/flat/stop_and_go | route_kf | plain | 25 % | 0 % | 35 % | 25 % | -0.8 | – |
| ladder_2km/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -87.5 | 0 % |
| ladder_2km/flat/stop_and_go | route_kf_yaw | plain | 20 % | 0 % | 35 % | 25 % | -0.4 | – |
| ladder_2km/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -87.7 | 0 % |
| ladder_2km/flat/stop_and_go | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.3 | – |
| ladder_2km/flat/stop_and_go | route_kf_map | aware | 0 % | 0 % | 10 % | 10 % | -4.8 | 95 % |
| ladder_2km/climb3/free | route_kf | plain | 5 % | 0 % | 95 % | 0 % | +0.3 | – |
| ladder_2km/climb3/free | route_kf | aware | 0 % | 0 % | 85 % | 0 % | -2.0 | 100 % |
| ladder_2km/climb3/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_2km/climb3/free | route_kf_yaw | aware | 0 % | 0 % | 70 % | 0 % | -2.4 | 100 % |
| ladder_2km/climb3/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.1 | – |
| ladder_2km/climb3/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.8 | 100 % |
| ladder_2km/climb3/stop_and_go | route_kf | plain | 25 % | 0 % | 35 % | 25 % | -1.3 | – |
| ladder_2km/climb3/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -87.3 | 0 % |
| ladder_2km/climb3/stop_and_go | route_kf_yaw | plain | 20 % | 0 % | 35 % | 20 % | -1.1 | – |
| ladder_2km/climb3/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -88.7 | 0 % |
| ladder_2km/climb3/stop_and_go | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.5 | – |
| ladder_2km/climb3/stop_and_go | route_kf_map | aware | 0 % | 0 % | 10 % | 10 % | -4.9 | 95 % |
| ladder_2km/underwater/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_2km/underwater/free | route_kf | aware | 0 % | 0 % | 85 % | 0 % | -2.1 | 100 % |
| ladder_2km/underwater/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_2km/underwater/free | route_kf_yaw | aware | 0 % | 0 % | 70 % | 0 % | -2.4 | 100 % |
| ladder_2km/underwater/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.0 | – |
| ladder_2km/underwater/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.8 | 100 % |
| ladder_2km/underwater/stop_and_go | route_kf | plain | 5 % | 0 % | 70 % | 0 % | -0.6 | – |
| ladder_2km/underwater/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -88.2 | 0 % |
| ladder_2km/underwater/stop_and_go | route_kf_yaw | plain | 0 % | 0 % | 75 % | 0 % | -0.9 | – |
| ladder_2km/underwater/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -88.5 | 0 % |
| ladder_2km/underwater/stop_and_go | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.7 | – |
| ladder_2km/underwater/stop_and_go | route_kf_map | aware | 0 % | 0 % | 10 % | 10 % | -4.8 | 95 % |
| ladder_3km/flat/free | route_kf | plain | 20 % | 0 % | 75 % | 0 % | +0.9 | – |
| ladder_3km/flat/free | route_kf | aware | 0 % | 0 % | 35 % | 0 % | -3.8 | 0 % |
| ladder_3km/flat/free | route_kf_yaw | plain | 25 % | 0 % | 65 % | 0 % | +0.8 | – |
| ladder_3km/flat/free | route_kf_yaw | aware | 0 % | 0 % | 30 % | 0 % | -4.3 | 0 % |
| ladder_3km/flat/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.2 | – |
| ladder_3km/flat/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.9 | 100 % |
| ladder_3km/flat/stop_and_go | route_kf | plain | 30 % | 15 % | 25 % | 25 % | -2.1 | – |
| ladder_3km/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -70.4 | 0 % |
| ladder_3km/flat/stop_and_go | route_kf_yaw | plain | 25 % | 5 % | 25 % | 35 % | -6.0 | – |
| ladder_3km/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -82.0 | 0 % |
| ladder_3km/flat/stop_and_go | route_kf_map | plain | 0 % | 0 % | 85 % | 0 % | -0.8 | – |
| ladder_3km/flat/stop_and_go | route_kf_map | aware | 0 % | 0 % | 10 % | 10 % | -7.0 | 55 % |
| ladder_3km/climb3/free | route_kf | plain | 20 % | 0 % | 75 % | 0 % | +0.6 | – |
| ladder_3km/climb3/free | route_kf | aware | 0 % | 0 % | 30 % | 0 % | -4.1 | 0 % |
| ladder_3km/climb3/free | route_kf_yaw | plain | 25 % | 0 % | 65 % | 0 % | +0.2 | – |
| ladder_3km/climb3/free | route_kf_yaw | aware | 0 % | 0 % | 30 % | 0 % | -4.8 | 0 % |
| ladder_3km/climb3/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.1 | – |
| ladder_3km/climb3/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.9 | 100 % |
| ladder_3km/climb3/stop_and_go | route_kf | plain | 30 % | 15 % | 25 % | 25 % | -1.7 | – |
| ladder_3km/climb3/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -70.3 | 0 % |
| ladder_3km/climb3/stop_and_go | route_kf_yaw | plain | 30 % | 5 % | 15 % | 35 % | -4.8 | – |
| ladder_3km/climb3/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -79.4 | 0 % |
| ladder_3km/climb3/stop_and_go | route_kf_map | plain | 0 % | 0 % | 85 % | 0 % | -0.9 | – |
| ladder_3km/climb3/stop_and_go | route_kf_map | aware | 0 % | 0 % | 10 % | 5 % | -7.0 | 55 % |
| ladder_3km/underwater/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.3 | – |
| ladder_3km/underwater/free | route_kf | aware | 0 % | 0 % | 0 % | 0 % | -4.8 | 0 % |
| ladder_3km/underwater/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_3km/underwater/free | route_kf_yaw | aware | 0 % | 0 % | 0 % | 0 % | -4.9 | 0 % |
| ladder_3km/underwater/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.2 | – |
| ladder_3km/underwater/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.9 | 100 % |
| ladder_3km/underwater/stop_and_go | route_kf | plain | 10 % | 5 % | 35 % | 25 % | -4.2 | – |
| ladder_3km/underwater/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 95 % | -69.4 | 0 % |
| ladder_3km/underwater/stop_and_go | route_kf_yaw | plain | 10 % | 5 % | 50 % | 20 % | -1.3 | – |
| ladder_3km/underwater/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 95 % | -66.9 | 0 % |
| ladder_3km/underwater/stop_and_go | route_kf_map | plain | 0 % | 0 % | 85 % | 0 % | -0.6 | – |
| ladder_3km/underwater/stop_and_go | route_kf_map | aware | 0 % | 0 % | 15 % | 5 % | -7.1 | 55 % |
| ladder_5km/flat/free | route_kf | plain | 50 % | 10 % | 45 % | 5 % | +2.1 | – |
| ladder_5km/flat/free | route_kf | aware | 0 % | 0 % | 10 % | 25 % | -13.1 | 0 % |
| ladder_5km/flat/free | route_kf_yaw | plain | 40 % | 5 % | 45 % | 5 % | +1.4 | – |
| ladder_5km/flat/free | route_kf_yaw | aware | 0 % | 0 % | 5 % | 30 % | -13.9 | 0 % |
| ladder_5km/flat/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.1 | – |
| ladder_5km/flat/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -1.6 | 100 % |
| ladder_5km/flat/stop_and_go | route_kf | plain | 40 % | 20 % | 15 % | 45 % | +0.5 | – |
| ladder_5km/flat/stop_and_go | route_kf | aware | 10 % | 5 % | 0 % | 80 % | -33.7 | 0 % |
| ladder_5km/flat/stop_and_go | route_kf_yaw | plain | 45 % | 20 % | 5 % | 45 % | -6.2 | – |
| ladder_5km/flat/stop_and_go | route_kf_yaw | aware | 5 % | 5 % | 5 % | 85 % | -37.8 | 0 % |
| ladder_5km/flat/stop_and_go | route_kf_map | plain | 10 % | 0 % | 70 % | 0 % | +0.5 | – |
| ladder_5km/flat/stop_and_go | route_kf_map | aware | 0 % | 0 % | 0 % | 30 % | -10.3 | 20 % |
| ladder_5km/climb3/free | route_kf | plain | 50 % | 5 % | 40 % | 5 % | +2.1 | – |
| ladder_5km/climb3/free | route_kf | aware | 0 % | 0 % | 10 % | 30 % | -13.3 | 0 % |
| ladder_5km/climb3/free | route_kf_yaw | plain | 40 % | 0 % | 40 % | 0 % | +1.2 | – |
| ladder_5km/climb3/free | route_kf_yaw | aware | 0 % | 0 % | 5 % | 35 % | -13.9 | 0 % |
| ladder_5km/climb3/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.1 | – |
| ladder_5km/climb3/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -1.6 | 100 % |
| ladder_5km/climb3/stop_and_go | route_kf | plain | 40 % | 25 % | 15 % | 45 % | -0.1 | – |
| ladder_5km/climb3/stop_and_go | route_kf | aware | 10 % | 5 % | 0 % | 80 % | -32.7 | 0 % |
| ladder_5km/climb3/stop_and_go | route_kf_yaw | plain | 45 % | 20 % | 5 % | 45 % | -6.7 | – |
| ladder_5km/climb3/stop_and_go | route_kf_yaw | aware | 5 % | 5 % | 5 % | 85 % | -38.0 | 0 % |
| ladder_5km/climb3/stop_and_go | route_kf_map | plain | 10 % | 0 % | 70 % | 0 % | +0.1 | – |
| ladder_5km/climb3/stop_and_go | route_kf_map | aware | 0 % | 0 % | 0 % | 30 % | -10.2 | 20 % |
| ladder_5km/underwater/free | route_kf | plain | 10 % | 0 % | 85 % | 0 % | -0.3 | – |
| ladder_5km/underwater/free | route_kf | aware | 0 % | 0 % | 0 % | 30 % | -14.3 | 0 % |
| ladder_5km/underwater/free | route_kf_yaw | plain | 10 % | 0 % | 85 % | 0 % | -0.4 | – |
| ladder_5km/underwater/free | route_kf_yaw | aware | 0 % | 0 % | 0 % | 50 % | -15.0 | 0 % |
| ladder_5km/underwater/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.3 | – |
| ladder_5km/underwater/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -1.7 | 100 % |
| ladder_5km/underwater/stop_and_go | route_kf | plain | 50 % | 40 % | 0 % | 50 % | -4.9 | – |
| ladder_5km/underwater/stop_and_go | route_kf | aware | 15 % | 10 % | 5 % | 65 % | -45.0 | 5 % |
| ladder_5km/underwater/stop_and_go | route_kf_yaw | plain | 40 % | 30 % | 15 % | 45 % | +0.2 | – |
| ladder_5km/underwater/stop_and_go | route_kf_yaw | aware | 20 % | 15 % | 0 % | 65 % | -38.5 | 5 % |
| ladder_5km/underwater/stop_and_go | route_kf_map | plain | 15 % | 0 % | 40 % | 10 % | -1.7 | – |
| ladder_5km/underwater/stop_and_go | route_kf_map | aware | 0 % | 0 % | 0 % | 40 % | -12.0 | 20 % |
| eisenhower_tunnel/flat/free | route_kf | plain | 15 % | 0 % | 75 % | 0 % | +0.9 | – |
| eisenhower_tunnel/flat/free | route_kf | aware | 5 % | 0 % | 50 % | 0 % | -2.9 | 0 % |
| eisenhower_tunnel/flat/free | route_kf_yaw | plain | 30 % | 0 % | 55 % | 0 % | +0.1 | – |
| eisenhower_tunnel/flat/free | route_kf_yaw | aware | 0 % | 0 % | 15 % | 5 % | -8.9 | 0 % |
| eisenhower_tunnel/flat/free | route_kf_map | plain | 15 % | 0 % | 75 % | 0 % | +1.0 | – |
| eisenhower_tunnel/flat/free | route_kf_map | aware | 5 % | 0 % | 50 % | 0 % | -2.5 | 0 % |
| eisenhower_tunnel/flat/stop_and_go | route_kf | plain | 40 % | 20 % | 25 % | 30 % | -0.5 | – |
| eisenhower_tunnel/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 5 % | 90 % | -74.2 | 0 % |
| eisenhower_tunnel/flat/stop_and_go | route_kf_yaw | plain | 50 % | 25 % | 5 % | 35 % | +3.6 | – |
| eisenhower_tunnel/flat/stop_and_go | route_kf_yaw | aware | 5 % | 0 % | 5 % | 80 % | -39.7 | 0 % |
| eisenhower_tunnel/flat/stop_and_go | route_kf_map | plain | 40 % | 20 % | 25 % | 25 % | +0.1 | – |
| eisenhower_tunnel/flat/stop_and_go | route_kf_map | aware | 0 % | 0 % | 5 % | 90 % | -73.2 | 0 % |
| eisenhower_tunnel/climb3/free | route_kf | plain | 10 % | 0 % | 80 % | 0 % | +0.9 | – |
| eisenhower_tunnel/climb3/free | route_kf | aware | 5 % | 0 % | 50 % | 0 % | -2.7 | 0 % |
| eisenhower_tunnel/climb3/free | route_kf_yaw | plain | 30 % | 0 % | 55 % | 0 % | +0.3 | – |
| eisenhower_tunnel/climb3/free | route_kf_yaw | aware | 0 % | 0 % | 10 % | 5 % | -8.7 | 0 % |
| eisenhower_tunnel/climb3/free | route_kf_map | plain | 15 % | 0 % | 75 % | 0 % | +0.9 | – |
| eisenhower_tunnel/climb3/free | route_kf_map | aware | 5 % | 0 % | 55 % | 0 % | -2.6 | 0 % |
| eisenhower_tunnel/climb3/stop_and_go | route_kf | plain | 40 % | 20 % | 20 % | 30 % | -1.1 | – |
| eisenhower_tunnel/climb3/stop_and_go | route_kf | aware | 0 % | 0 % | 5 % | 90 % | -73.2 | 0 % |
| eisenhower_tunnel/climb3/stop_and_go | route_kf_yaw | plain | 50 % | 25 % | 5 % | 35 % | +1.7 | – |
| eisenhower_tunnel/climb3/stop_and_go | route_kf_yaw | aware | 5 % | 0 % | 5 % | 80 % | -39.8 | 0 % |
| eisenhower_tunnel/climb3/stop_and_go | route_kf_map | plain | 40 % | 25 % | 20 % | 25 % | -0.1 | – |
| eisenhower_tunnel/climb3/stop_and_go | route_kf_map | aware | 0 % | 0 % | 0 % | 90 % | -72.3 | 0 % |
| eisenhower_tunnel/underwater/free | route_kf | plain | 5 % | 0 % | 95 % | 0 % | +0.6 | – |
| eisenhower_tunnel/underwater/free | route_kf | aware | 0 % | 0 % | 40 % | 0 % | -3.2 | 0 % |
| eisenhower_tunnel/underwater/free | route_kf_yaw | plain | 20 % | 0 % | 70 % | 0 % | +0.4 | – |
| eisenhower_tunnel/underwater/free | route_kf_yaw | aware | 0 % | 0 % | 0 % | 0 % | -8.6 | 0 % |
| eisenhower_tunnel/underwater/free | route_kf_map | plain | 5 % | 0 % | 95 % | 0 % | +0.5 | – |
| eisenhower_tunnel/underwater/free | route_kf_map | aware | 0 % | 0 % | 45 % | 0 % | -3.2 | 0 % |
| eisenhower_tunnel/underwater/stop_and_go | route_kf | plain | 30 % | 5 % | 35 % | 5 % | +0.2 | – |
| eisenhower_tunnel/underwater/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -58.6 | 0 % |
| eisenhower_tunnel/underwater/stop_and_go | route_kf_yaw | plain | 20 % | 5 % | 35 % | 30 % | -1.8 | – |
| eisenhower_tunnel/underwater/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -84.9 | 0 % |
| eisenhower_tunnel/underwater/stop_and_go | route_kf_map | plain | 30 % | 5 % | 35 % | 5 % | -0.3 | – |
| eisenhower_tunnel/underwater/stop_and_go | route_kf_map | aware | 0 % | 0 % | 0 % | 100 % | -46.7 | 0 % |
| seattle_sr99_tunnel/flat/free | route_kf | plain | 5 % | 0 % | 90 % | 0 % | +0.7 | – |
| seattle_sr99_tunnel/flat/free | route_kf | aware | 0 % | 0 % | 45 % | 0 % | -3.4 | 0 % |
| seattle_sr99_tunnel/flat/free | route_kf_yaw | plain | 25 % | 0 % | 65 % | 0 % | +0.9 | – |
| seattle_sr99_tunnel/flat/free | route_kf_yaw | aware | 0 % | 0 % | 30 % | 0 % | -4.0 | 0 % |
| seattle_sr99_tunnel/flat/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.2 | – |
| seattle_sr99_tunnel/flat/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -1.2 | 100 % |
| seattle_sr99_tunnel/flat/stop_and_go | route_kf | plain | 40 % | 5 % | 10 % | 45 % | -5.9 | – |
| seattle_sr99_tunnel/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -71.4 | 0 % |
| seattle_sr99_tunnel/flat/stop_and_go | route_kf_yaw | plain | 45 % | 5 % | 5 % | 40 % | -6.7 | – |
| seattle_sr99_tunnel/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -71.5 | 0 % |
| seattle_sr99_tunnel/flat/stop_and_go | route_kf_map | plain | 0 % | 0 % | 90 % | 0 % | -1.6 | – |
| seattle_sr99_tunnel/flat/stop_and_go | route_kf_map | aware | 0 % | 0 % | 10 % | 0 % | -6.3 | 95 % |
| seattle_sr99_tunnel/climb3/free | route_kf | plain | 0 % | 0 % | 95 % | 0 % | +0.8 | – |
| seattle_sr99_tunnel/climb3/free | route_kf | aware | 0 % | 0 % | 35 % | 0 % | -3.4 | 0 % |
| seattle_sr99_tunnel/climb3/free | route_kf_yaw | plain | 20 % | 0 % | 65 % | 0 % | +1.0 | – |
| seattle_sr99_tunnel/climb3/free | route_kf_yaw | aware | 0 % | 0 % | 30 % | 0 % | -4.2 | 0 % |
| seattle_sr99_tunnel/climb3/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.2 | – |
| seattle_sr99_tunnel/climb3/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -1.2 | 100 % |
| seattle_sr99_tunnel/climb3/stop_and_go | route_kf | plain | 35 % | 0 % | 15 % | 40 % | -6.2 | – |
| seattle_sr99_tunnel/climb3/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -70.1 | 0 % |
| seattle_sr99_tunnel/climb3/stop_and_go | route_kf_yaw | plain | 40 % | 5 % | 5 % | 40 % | -6.2 | – |
| seattle_sr99_tunnel/climb3/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -70.1 | 0 % |
| seattle_sr99_tunnel/climb3/stop_and_go | route_kf_map | plain | 0 % | 0 % | 90 % | 0 % | -1.6 | – |
| seattle_sr99_tunnel/climb3/stop_and_go | route_kf_map | aware | 0 % | 0 % | 10 % | 0 % | -6.2 | 95 % |
| seattle_sr99_tunnel/underwater/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.4 | – |
| seattle_sr99_tunnel/underwater/free | route_kf | aware | 0 % | 0 % | 5 % | 0 % | -4.1 | 0 % |
| seattle_sr99_tunnel/underwater/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.4 | – |
| seattle_sr99_tunnel/underwater/free | route_kf_yaw | aware | 0 % | 0 % | 5 % | 0 % | -4.5 | 0 % |
| seattle_sr99_tunnel/underwater/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.2 | – |
| seattle_sr99_tunnel/underwater/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -1.3 | 100 % |
| seattle_sr99_tunnel/underwater/stop_and_go | route_kf | plain | 20 % | 10 % | 45 % | 15 % | -0.5 | – |
| seattle_sr99_tunnel/underwater/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -52.5 | 0 % |
| seattle_sr99_tunnel/underwater/stop_and_go | route_kf_yaw | plain | 30 % | 5 % | 40 % | 25 % | -0.7 | – |
| seattle_sr99_tunnel/underwater/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -52.6 | 0 % |
| seattle_sr99_tunnel/underwater/stop_and_go | route_kf_map | plain | 10 % | 5 % | 85 % | 0 % | -1.4 | – |
| seattle_sr99_tunnel/underwater/stop_and_go | route_kf_map | aware | 10 % | 0 % | 5 % | 5 % | -4.8 | 95 % |
| synthetic_demo_track/flat/free | route_kf | plain | 5 % | 0 % | 95 % | 0 % | +0.5 | – |
| synthetic_demo_track/flat/free | route_kf | aware | 0 % | 0 % | 85 % | 0 % | -2.0 | 100 % |
| synthetic_demo_track/flat/free | route_kf_yaw | plain | 5 % | 0 % | 90 % | 0 % | +0.3 | – |
| synthetic_demo_track/flat/free | route_kf_yaw | aware | 0 % | 0 % | 85 % | 0 % | -2.0 | 100 % |
| synthetic_demo_track/flat/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.1 | – |
| synthetic_demo_track/flat/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.4 | 100 % |
| synthetic_demo_track/flat/stop_and_go | route_kf | plain | 25 % | 0 % | 35 % | 25 % | -0.9 | – |
| synthetic_demo_track/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -86.9 | 0 % |
| synthetic_demo_track/flat/stop_and_go | route_kf_yaw | plain | 20 % | 0 % | 35 % | 25 % | -0.4 | – |
| synthetic_demo_track/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -87.4 | 0 % |
| synthetic_demo_track/flat/stop_and_go | route_kf_map | plain | 0 % | 0 % | 85 % | 5 % | -0.6 | – |
| synthetic_demo_track/flat/stop_and_go | route_kf_map | aware | 0 % | 0 % | 45 % | 10 % | -3.3 | 100 % |
| synthetic_demo_track/climb3/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.3 | – |
| synthetic_demo_track/climb3/free | route_kf | aware | 0 % | 0 % | 85 % | 0 % | -2.0 | 100 % |
| synthetic_demo_track/climb3/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.3 | – |
| synthetic_demo_track/climb3/free | route_kf_yaw | aware | 0 % | 0 % | 75 % | 0 % | -2.2 | 100 % |
| synthetic_demo_track/climb3/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.1 | – |
| synthetic_demo_track/climb3/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.4 | 100 % |
| synthetic_demo_track/climb3/stop_and_go | route_kf | plain | 25 % | 0 % | 30 % | 30 % | -1.0 | – |
| synthetic_demo_track/climb3/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -86.6 | 0 % |
| synthetic_demo_track/climb3/stop_and_go | route_kf_yaw | plain | 20 % | 0 % | 35 % | 20 % | -0.6 | – |
| synthetic_demo_track/climb3/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -87.7 | 0 % |
| synthetic_demo_track/climb3/stop_and_go | route_kf_map | plain | 0 % | 0 % | 85 % | 5 % | -0.5 | – |
| synthetic_demo_track/climb3/stop_and_go | route_kf_map | aware | 0 % | 0 % | 50 % | 10 % | -3.1 | 100 % |
| synthetic_demo_track/underwater/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| synthetic_demo_track/underwater/free | route_kf | aware | 0 % | 0 % | 90 % | 0 % | -2.1 | 100 % |
| synthetic_demo_track/underwater/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| synthetic_demo_track/underwater/free | route_kf_yaw | aware | 0 % | 0 % | 90 % | 0 % | -2.2 | 100 % |
| synthetic_demo_track/underwater/free | route_kf_map | plain | 0 % | 0 % | 100 % | 0 % | -0.1 | – |
| synthetic_demo_track/underwater/free | route_kf_map | aware | 0 % | 0 % | 100 % | 0 % | -0.4 | 100 % |
| synthetic_demo_track/underwater/stop_and_go | route_kf | plain | 0 % | 0 % | 80 % | 0 % | -0.8 | – |
| synthetic_demo_track/underwater/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -88.3 | 0 % |
| synthetic_demo_track/underwater/stop_and_go | route_kf_yaw | plain | 0 % | 0 % | 75 % | 0 % | -0.7 | – |
| synthetic_demo_track/underwater/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -88.3 | 0 % |
| synthetic_demo_track/underwater/stop_and_go | route_kf_map | plain | 0 % | 0 % | 75 % | 5 % | -1.1 | – |
| synthetic_demo_track/underwater/stop_and_go | route_kf_map | aware | 0 % | 0 % | 40 % | 10 % | -3.5 | 100 % |
