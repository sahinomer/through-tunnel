# Benchmark: generated tables

D54: wider filter priors, flat roads · commit `1b280f4+dirty` · 2026-10-17 14:29 UTC · 16 scenarios × 20 runs. † = reference estimator (uses the car's speed reading; not a phone-only solution). Realism options on (bias drift, GPS degradation before the portal).

## How to read the failure states

* **Gross error**: the estimate was more than 200 m from the true position at some time in the tunnel or at C, ahead *or* behind. The position is unusable for guidance.
* **Announcement off**: the exit announcement came more than 15 s early or late (or never). The driver gets the instruction at the wrong time. Never-fired does not happen in practice: a late estimate is pushed past the announcement point when GPS returns, so the announcement is late, not missing.
* **Capped at D** (a data-quality flag, not a third failure): the estimate reached the route end D before the vehicle reached C. A route estimate stops at D, so its error is a lower bound (cells of exactly 782 / 881 / 889 m are the C–D distances). Every capped run is also a gross error.
* In the scenario tables, cells are the error at C [m], median (p90); ✗n = n runs with a gross error, §n = n of them capped at D.

## Overall, without map grade

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 678 (6329) | 678 (6328) | 76 % | 63 % | 18 % | 30 % |
| DR GPS-calibrated IMU | 85 (525) | 89 (525) | 28 % | 22 % | 52 % | 5 % |
| DR calibrated + GPS-blended speed/heading | 58 (418) | 59 (418) | 18 % | 19 % | 57 % | 5 % |
| Route + filtered IMU speed | 44 (392) | 46 (392) | 18 % | 20 % | 57 % | 5 % |
| Route + IMU Kalman filter (distance, speed, offset) | 36 (322) | 40 (322) | 14 % | 18 % | 61 % | 3 % |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 43 (340) | 44 (340) | 18 % | 18 % | 55 % | 5 % |
| Route + last GPS speed (naive) | 435 (881) | 436 (1815) | 58 % | 52 % | 24 % | 48 % |
| Route + vehicle speed (reference) † | 5 (14) | 6 (15) | 0 % | 0 % | 99 % | 0 % |
| Route + IMU + standstill oracle: speed reset ‡ | 27 (149) | 30 (149) | 7 % | 11 % | 64 % | 0 % |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 19 (86) | 22 (87) | 2 % | 3 % | 76 % | 0 % |

## Overall, with map grade

Flat roads (where the map grade changes nothing) are in both overall tables.

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 678 (6329) | 678 (6328) | 76 % | 63 % | 18 % | 30 % |
| DR GPS-calibrated IMU | 85 (525) | 89 (525) | 28 % | 22 % | 52 % | 5 % |
| DR calibrated + GPS-blended speed/heading | 58 (418) | 59 (418) | 18 % | 19 % | 57 % | 5 % |
| Route + filtered IMU speed | 44 (392) | 46 (392) | 18 % | 20 % | 57 % | 5 % |
| Route + IMU Kalman filter (distance, speed, offset) | 36 (322) | 40 (322) | 14 % | 18 % | 61 % | 3 % |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 43 (340) | 44 (340) | 18 % | 18 % | 55 % | 5 % |
| Route + last GPS speed (naive) | 435 (881) | 436 (1815) | 58 % | 52 % | 24 % | 48 % |
| Route + vehicle speed (reference) † | 5 (14) | 6 (15) | 0 % | 0 % | 99 % | 0 % |
| Route + IMU + standstill oracle: speed reset ‡ | 27 (149) | 30 (149) | 7 % | 11 % | 64 % | 0 % |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 19 (86) | 22 (87) | 2 % | 3 % | 76 % | 0 % |

## Tunnel length, flat road, free flow

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 27 (57) | 78 (165) | 284 (565) ✗14 | 628 (1214) ✗18 §5 | 1720 (3021) ✗20 §10 |
| DR GPS-calibrated IMU | 18 (31) | 27 (53) | 58 (92) | 86 (139) ✗1 | 167 (306) ✗8 |
| DR calibrated + GPS-blended speed/heading | 9 (20) | 13 (24) | 31 (48) | 55 (82) | 117 (240) ✗4 |
| Route + filtered IMU speed | 6 (12) | 11 (20) | 25 (46) | 46 (77) | 103 (257) ✗4 |
| Route + IMU Kalman filter (distance, speed, offset) | 6 (19) | 10 (32) | 22 (77) | 32 (141) | 80 (324) ✗4 |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 6 (19) | 9 (25) | 18 (56) | 28 (107) | 84 (253) ✗4 |
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
| Route + last GPS speed (naive) | 782 (782) ✗20 §19 | 782 (782) ✗20 §19 | 782 (782) ✗20 §19 | 782 (782) ✗20 §19 | 782 (782) ✗20 §18 |
| Route + vehicle speed (reference) † | 4 (14) | 5 (14) | 5 (13) | 5 (13) | 7 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 6 (17) | 12 (29) | 31 (96) | 51 (203) ✗2 | 131 (607) ✗9 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 5 (14) | 6 (17) | 16 (27) | 19 (54) | 103 (199) ✗2 |

## Road profile, all geometries, free flow, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 340 (1174) ✗99 §18 | – | – |
| DR GPS-calibrated IMU | 58 (149) ✗10 | – | – |
| DR calibrated + GPS-blended speed/heading | 33 (105) ✗4 | – | – |
| Route + filtered IMU speed | 23 (89) ✗4 | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | 23 (119) ✗4 | – | – |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 23 (156) ✗9 | – | – |
| Route + last GPS speed (naive) | 79 (223) ✗25 | – | – |
| Route + vehicle speed (reference) † | 5 (14) | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | 23 (89) ✗4 | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 23 (89) ✗4 | – | – |

## Road profile, all geometries, free flow, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 340 (1174) ✗99 §18 | – | – |
| DR GPS-calibrated IMU | 58 (149) ✗10 | – | – |
| DR calibrated + GPS-blended speed/heading | 33 (105) ✗4 | – | – |
| Route + filtered IMU speed | 23 (89) ✗4 | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | 23 (119) ✗4 | – | – |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 23 (156) ✗9 | – | – |
| Route + last GPS speed (naive) | 79 (223) ✗25 | – | – |
| Route + vehicle speed (reference) † | 5 (14) | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | 23 (89) ✗4 | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 23 (89) ✗4 | – | – |

## Road profile, all geometries, stop-and-go, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1552 (9594) ✗145 §79 | – | – |
| DR GPS-calibrated IMU | 186 (906) ✗79 §16 | – | – |
| DR calibrated + GPS-blended speed/heading | 129 (765) ✗54 §16 | – | – |
| Route + filtered IMU speed | 96 (782) ✗52 §15 | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | 70 (524) ✗42 §10 | – | – |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 83 (782) ✗48 §17 | – | – |
| Route + last GPS speed (naive) | 782 (889) ✗160 §153 | – | – |
| Route + vehicle speed (reference) † | 5 (14) | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | 34 (197) ✗17 | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 16 (66) ✗2 | – | – |

## Road profile, all geometries, stop-and-go, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 1552 (9594) ✗145 §79 | – | – |
| DR GPS-calibrated IMU | 186 (906) ✗79 §16 | – | – |
| DR calibrated + GPS-blended speed/heading | 129 (765) ✗54 §16 | – | – |
| Route + filtered IMU speed | 96 (782) ✗52 §15 | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | 70 (524) ✗42 §10 | – | – |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 83 (782) ✗48 §17 | – | – |
| Route + last GPS speed (naive) | 782 (889) ✗160 §153 | – | – |
| Route + vehicle speed (reference) † | 5 (14) | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | 34 (197) ✗17 | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 16 (66) ✗2 | – | – |

## Presets (real / demo geometry), flat road, free flow

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR raw IMU (assumed aligned mount) | 442 (709) ✗15 | 650 (1059) ✗19 §3 | 257 (507) ✗13 |
| DR GPS-calibrated IMU | 80 (107) | 83 (150) ✗1 | 54 (90) |
| DR calibrated + GPS-blended speed/heading | 41 (72) | 81 (119) | 25 (44) |
| Route + filtered IMU speed | 33 (70) | 46 (90) | 21 (47) |
| Route + IMU Kalman filter (distance, speed, offset) | 43 (127) | 37 (63) | 17 (69) |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 86 (246) ✗5 | 44 (102) | 15 (53) |
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
| ladder_0.5km/flat/stop_and_go | route_kf | plain | 0 % | 0 % | 95 % | 0 % | -0.1 | – |
| ladder_0.5km/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 10 % | 5 % | -5.0 | 100 % |
| ladder_0.5km/flat/stop_and_go | route_kf_yaw | plain | 0 % | 0 % | 95 % | 0 % | -0.3 | – |
| ladder_0.5km/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 10 % | 0 % | -5.5 | 100 % |
| ladder_1km/flat/free | route_kf | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_1km/flat/free | route_kf | aware | 0 % | 0 % | 100 % | 0 % | -1.1 | 100 % |
| ladder_1km/flat/free | route_kf_yaw | plain | 0 % | 0 % | 100 % | 0 % | +0.2 | – |
| ladder_1km/flat/free | route_kf_yaw | aware | 0 % | 0 % | 100 % | 0 % | -1.2 | 100 % |
| ladder_1km/flat/stop_and_go | route_kf | plain | 5 % | 5 % | 65 % | 5 % | -0.3 | – |
| ladder_1km/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 40 % | -14.2 | 0 % |
| ladder_1km/flat/stop_and_go | route_kf_yaw | plain | 10 % | 5 % | 65 % | 5 % | -0.0 | – |
| ladder_1km/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 60 % | -15.7 | 0 % |
| ladder_2km/flat/free | route_kf | plain | 10 % | 0 % | 85 % | 0 % | +0.4 | – |
| ladder_2km/flat/free | route_kf | aware | 0 % | 0 % | 85 % | 0 % | -2.1 | 100 % |
| ladder_2km/flat/free | route_kf_yaw | plain | 5 % | 0 % | 90 % | 0 % | +0.3 | – |
| ladder_2km/flat/free | route_kf_yaw | aware | 0 % | 0 % | 65 % | 0 % | -2.3 | 100 % |
| ladder_2km/flat/stop_and_go | route_kf | plain | 25 % | 0 % | 35 % | 25 % | -0.8 | – |
| ladder_2km/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -87.5 | 0 % |
| ladder_2km/flat/stop_and_go | route_kf_yaw | plain | 20 % | 0 % | 35 % | 25 % | -0.4 | – |
| ladder_2km/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -87.7 | 0 % |
| ladder_3km/flat/free | route_kf | plain | 20 % | 0 % | 75 % | 0 % | +0.9 | – |
| ladder_3km/flat/free | route_kf | aware | 0 % | 0 % | 35 % | 0 % | -3.8 | 0 % |
| ladder_3km/flat/free | route_kf_yaw | plain | 25 % | 0 % | 65 % | 0 % | +0.8 | – |
| ladder_3km/flat/free | route_kf_yaw | aware | 0 % | 0 % | 30 % | 0 % | -4.3 | 0 % |
| ladder_3km/flat/stop_and_go | route_kf | plain | 30 % | 15 % | 25 % | 25 % | -2.1 | – |
| ladder_3km/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -70.4 | 0 % |
| ladder_3km/flat/stop_and_go | route_kf_yaw | plain | 25 % | 5 % | 25 % | 35 % | -6.0 | – |
| ladder_3km/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -82.0 | 0 % |
| ladder_5km/flat/free | route_kf | plain | 50 % | 10 % | 45 % | 5 % | +2.1 | – |
| ladder_5km/flat/free | route_kf | aware | 0 % | 0 % | 10 % | 25 % | -13.1 | 0 % |
| ladder_5km/flat/free | route_kf_yaw | plain | 40 % | 5 % | 45 % | 5 % | +1.4 | – |
| ladder_5km/flat/free | route_kf_yaw | aware | 0 % | 0 % | 5 % | 30 % | -13.9 | 0 % |
| ladder_5km/flat/stop_and_go | route_kf | plain | 40 % | 20 % | 15 % | 45 % | +0.5 | – |
| ladder_5km/flat/stop_and_go | route_kf | aware | 10 % | 5 % | 0 % | 80 % | -33.7 | 0 % |
| ladder_5km/flat/stop_and_go | route_kf_yaw | plain | 45 % | 20 % | 5 % | 45 % | -6.2 | – |
| ladder_5km/flat/stop_and_go | route_kf_yaw | aware | 5 % | 5 % | 5 % | 85 % | -37.8 | 0 % |
| eisenhower_tunnel/flat/free | route_kf | plain | 15 % | 0 % | 75 % | 0 % | +0.9 | – |
| eisenhower_tunnel/flat/free | route_kf | aware | 5 % | 0 % | 50 % | 0 % | -2.9 | 0 % |
| eisenhower_tunnel/flat/free | route_kf_yaw | plain | 30 % | 0 % | 55 % | 0 % | +0.1 | – |
| eisenhower_tunnel/flat/free | route_kf_yaw | aware | 0 % | 0 % | 15 % | 5 % | -8.9 | 0 % |
| eisenhower_tunnel/flat/stop_and_go | route_kf | plain | 40 % | 20 % | 25 % | 30 % | -0.5 | – |
| eisenhower_tunnel/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 5 % | 90 % | -74.2 | 0 % |
| eisenhower_tunnel/flat/stop_and_go | route_kf_yaw | plain | 50 % | 25 % | 5 % | 35 % | +3.6 | – |
| eisenhower_tunnel/flat/stop_and_go | route_kf_yaw | aware | 5 % | 0 % | 5 % | 80 % | -39.7 | 0 % |
| seattle_sr99_tunnel/flat/free | route_kf | plain | 5 % | 0 % | 90 % | 0 % | +0.7 | – |
| seattle_sr99_tunnel/flat/free | route_kf | aware | 0 % | 0 % | 45 % | 0 % | -3.4 | 0 % |
| seattle_sr99_tunnel/flat/free | route_kf_yaw | plain | 25 % | 0 % | 65 % | 0 % | +0.9 | – |
| seattle_sr99_tunnel/flat/free | route_kf_yaw | aware | 0 % | 0 % | 30 % | 0 % | -4.0 | 0 % |
| seattle_sr99_tunnel/flat/stop_and_go | route_kf | plain | 40 % | 5 % | 10 % | 45 % | -5.9 | – |
| seattle_sr99_tunnel/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -71.4 | 0 % |
| seattle_sr99_tunnel/flat/stop_and_go | route_kf_yaw | plain | 45 % | 5 % | 5 % | 40 % | -6.7 | – |
| seattle_sr99_tunnel/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -71.5 | 0 % |
| synthetic_demo_track/flat/free | route_kf | plain | 5 % | 0 % | 95 % | 0 % | +0.5 | – |
| synthetic_demo_track/flat/free | route_kf | aware | 0 % | 0 % | 85 % | 0 % | -2.0 | 100 % |
| synthetic_demo_track/flat/free | route_kf_yaw | plain | 5 % | 0 % | 90 % | 0 % | +0.3 | – |
| synthetic_demo_track/flat/free | route_kf_yaw | aware | 0 % | 0 % | 85 % | 0 % | -2.0 | 100 % |
| synthetic_demo_track/flat/stop_and_go | route_kf | plain | 25 % | 0 % | 35 % | 25 % | -0.9 | – |
| synthetic_demo_track/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 0 % | 100 % | -86.9 | 0 % |
| synthetic_demo_track/flat/stop_and_go | route_kf_yaw | plain | 20 % | 0 % | 35 % | 25 % | -0.4 | – |
| synthetic_demo_track/flat/stop_and_go | route_kf_yaw | aware | 0 % | 0 % | 0 % | 100 % | -87.4 | 0 % |
