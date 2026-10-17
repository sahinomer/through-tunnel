# Benchmark: generated tables

D54: wider filter priors · commit `1b280f4+dirty` · 2026-10-17 14:07 UTC · 10 scenarios × 20 runs (**development subset**: map grade on, calibrated estimators only). † = reference estimator (uses the car's speed reading; not a phone-only solution). Realism options on (bias drift, GPS degradation before the portal).

## How to read the failure states

* **Gross error**: the estimate was more than 200 m from the true position at some time in the tunnel or at C, ahead *or* behind. The position is unusable for guidance.
* **Announcement off**: the exit announcement came more than 15 s early or late (or never). The driver gets the instruction at the wrong time. Never-fired does not happen in practice: a late estimate is pushed past the announcement point when GPS returns, so the announcement is late, not missing.
* **Capped at D** (a data-quality flag, not a third failure): the estimate reached the route end D before the vehicle reached C. A route estimate stops at D, so its error is a lower bound (cells of exactly 782 / 881 / 889 m are the C–D distances). Every capped run is also a gross error.
* In the scenario tables, cells are the error at C [m], median (p90); ✗n = n runs with a gross error, §n = n of them capped at D.

## Overall, without map grade

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 96 (702) | 100 (702) | 33 % | 25 % | 53 % | 8 % |
| DR calibrated + GPS-blended speed/heading | 62 (597) | 62 (596) | 25 % | 23 % | 57 % | 7 % |
| Route + filtered IMU speed | 45 (598) | 56 (598) | 24 % | 23 % | 57 % | 7 % |
| Route + IMU Kalman filter (distance, speed, offset) | 47 (406) | 51 (406) | 21 % | 22 % | 59 % | 5 % |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 62 (586) | 65 (588) | 28 % | 22 % | 51 % | 10 % |
| Route + vehicle speed (reference) † | 5 (15) | 6 (16) | 0 % | 0 % | 99 % | 0 % |
| Route + IMU + standstill oracle: speed reset ‡ | 35 (251) | 37 (251) | 13 % | 13 % | 57 % | 0 % |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 21 (132) | 25 (136) | 5 % | 6 % | 69 % | 0 % |

## Overall, with map grade

Flat roads (where the map grade changes nothing) are in both overall tables.

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 142 (939) | 154 (939) | 44 % | 31 % | 41 % | 11 % |
| DR calibrated + GPS-blended speed/heading | 96 (906) | 98 (906) | 34 % | 32 % | 48 % | 11 % |
| Route + filtered IMU speed | 79 (782) | 88 (821) | 32 % | 30 % | 46 % | 11 % |
| Route + IMU Kalman filter (distance, speed, offset) | 63 (717) | 78 (717) | 28 % | 30 % | 50 % | 10 % |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 91 (782) | 96 (982) | 32 % | 28 % | 45 % | 14 % |
| Route + vehicle speed (reference) † | 6 (17) | 6 (17) | 0 % | 0 % | 100 % | 0 % |
| Route + IMU + standstill oracle: speed reset ‡ | 55 (408) | 62 (408) | 20 % | 18 % | 50 % | 4 % |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 39 (202) | 46 (215) | 10 % | 13 % | 56 % | 2 % |

## Tunnel length, flat road, free flow

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 18 (31) | – | – | – | 167 (306) ✗8 |
| DR calibrated + GPS-blended speed/heading | 9 (20) | – | – | – | 117 (240) ✗4 |
| Route + filtered IMU speed | 6 (12) | – | – | – | 103 (257) ✗4 |
| Route + IMU Kalman filter (distance, speed, offset) | 6 (19) | – | – | – | 80 (324) ✗4 |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 6 (19) | – | – | – | 84 (253) ✗4 |
| Route + vehicle speed (reference) † | 4 (11) | – | – | – | 6 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 6 (12) | – | – | – | 103 (257) ✗4 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 6 (12) | – | – | – | 103 (257) ✗4 |

## Tunnel length, flat road, stop-and-go

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 40 (231) ✗3 | – | – | – | 561 (2099) ✗18 §5 |
| DR calibrated + GPS-blended speed/heading | 23 (93) ✗1 | – | – | – | 420 (2355) ✗17 §5 |
| Route + filtered IMU speed | 18 (92) ✗1 | – | – | – | 385 (782) ✗16 §5 |
| Route + IMU Kalman filter (distance, speed, offset) | 14 (51) ✗1 | – | – | – | 241 (782) ✗13 §4 |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 11 (82) ✗1 | – | – | – | 299 (782) ✗12 §7 |
| Route + vehicle speed (reference) † | 4 (14) | – | – | – | 7 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 6 (17) | – | – | – | 131 (607) ✗9 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 5 (14) | – | – | – | 103 (199) ✗2 |

## Road profile, all geometries, free flow, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 54 (224) ✗8 | – | – |
| DR calibrated + GPS-blended speed/heading | 38 (151) ✗4 | – | – |
| Route + filtered IMU speed | 24 (146) ✗4 | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | 31 (175) ✗4 | – | – |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 32 (219) ✗9 | – | – |
| Route + vehicle speed (reference) † | 5 (17) | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | 24 (146) ✗4 | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 24 (146) ✗4 | – | – |

## Road profile, all geometries, free flow, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 54 (224) ✗8 | 165 (285) ✗9 | 102 (217) ✗4 |
| DR calibrated + GPS-blended speed/heading | 38 (151) ✗4 | 110 (244) ✗5 | 71 (96) |
| Route + filtered IMU speed | 24 (146) ✗4 | 93 (247) ✗4 | 44 (95) |
| Route + IMU Kalman filter (distance, speed, offset) | 31 (175) ✗4 | 96 (293) ✗3 | 40 (86) |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 32 (219) ✗9 | 108 (238) ✗3 | 40 (96) |
| Route + vehicle speed (reference) † | 5 (17) | 6 (17) | 6 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 24 (146) ✗4 | 93 (247) ✗4 | 44 (95) |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 24 (146) ✗4 | 93 (247) ✗4 | 44 (95) |

## Road profile, all geometries, stop-and-go, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 249 (1018) ✗32 §9 | – | – |
| DR calibrated + GPS-blended speed/heading | 153 (1224) ✗26 §8 | – | – |
| Route + filtered IMU speed | 114 (782) ✗25 §8 | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | 80 (755) ✗21 §6 | – | – |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 107 (782) ✗24 §12 | – | – |
| Route + vehicle speed (reference) † | 6 (14) | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | 55 (329) ✗12 | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 18 (121) ✗2 | – | – |

## Road profile, all geometries, stop-and-go, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 249 (1018) ✗32 §9 | 601 (7198) ✗18 §6 | 658 (8740) ✗16 §7 |
| DR calibrated + GPS-blended speed/heading | 153 (1224) ✗26 §8 | 506 (8661) ✗18 §6 | 639 (7987) ✗15 §8 |
| Route + filtered IMU speed | 114 (782) ✗25 §8 | 501 (782) ✗17 §6 | 613 (782) ✗14 §8 |
| Route + IMU Kalman filter (distance, speed, offset) | 80 (755) ✗21 §6 | 319 (782) ✗13 §6 | 322 (782) ✗15 §7 |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 107 (782) ✗24 §12 | 373 (782) ✗14 §7 | 493 (782) ✗15 §8 |
| Route + vehicle speed (reference) † | 6 (14) | 7 (17) | 7 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 55 (329) ✗12 | 144 (782) ✗9 §3 | 132 (782) ✗10 §5 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 18 (121) ✗2 | 128 (199) ✗2 | 127 (782) ✗9 §5 |

## Presets (real / demo geometry), flat road, free flow

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR GPS-calibrated IMU | 80 (107) | – | – |
| DR calibrated + GPS-blended speed/heading | 41 (72) | – | – |
| Route + filtered IMU speed | 33 (70) | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | 43 (127) | – | – |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 86 (246) ✗5 | – | – |
| Route + vehicle speed (reference) † | 7 (17) | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | 33 (70) | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 33 (70) | – | – |

## Presets (real / demo geometry), flat road, stop-and-go

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR GPS-calibrated IMU | 254 (1018) ✗11 §4 | – | – |
| DR calibrated + GPS-blended speed/heading | 153 (1272) ✗8 §3 | – | – |
| Route + filtered IMU speed | 134 (881) ✗8 §3 | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | 133 (549) ✗7 §2 | – | – |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | 211 (881) ✗11 §5 | – | – |
| Route + vehicle speed (reference) † | 7 (14) | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | 102 (218) ✗3 | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 24 (36) | – | – |

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
| ladder_5km/flat/free | route_kf | plain | 50 % | 10 % | 45 % | 5 % | +2.1 | – |
| ladder_5km/flat/free | route_kf | aware | 0 % | 0 % | 10 % | 25 % | -13.1 | 0 % |
| ladder_5km/flat/free | route_kf_yaw | plain | 40 % | 5 % | 45 % | 5 % | +1.4 | – |
| ladder_5km/flat/free | route_kf_yaw | aware | 0 % | 0 % | 5 % | 30 % | -13.9 | 0 % |
| ladder_5km/flat/stop_and_go | route_kf | plain | 40 % | 20 % | 15 % | 45 % | +0.5 | – |
| ladder_5km/flat/stop_and_go | route_kf | aware | 10 % | 5 % | 0 % | 80 % | -33.7 | 0 % |
| ladder_5km/flat/stop_and_go | route_kf_yaw | plain | 45 % | 20 % | 5 % | 45 % | -6.2 | – |
| ladder_5km/flat/stop_and_go | route_kf_yaw | aware | 5 % | 5 % | 5 % | 85 % | -37.8 | 0 % |
| ladder_5km/climb3/free | route_kf | plain | 50 % | 5 % | 40 % | 5 % | +2.1 | – |
| ladder_5km/climb3/free | route_kf | aware | 0 % | 0 % | 10 % | 30 % | -13.3 | 0 % |
| ladder_5km/climb3/free | route_kf_yaw | plain | 40 % | 0 % | 40 % | 0 % | +1.2 | – |
| ladder_5km/climb3/free | route_kf_yaw | aware | 0 % | 0 % | 5 % | 35 % | -13.9 | 0 % |
| ladder_5km/climb3/stop_and_go | route_kf | plain | 40 % | 25 % | 15 % | 45 % | -0.1 | – |
| ladder_5km/climb3/stop_and_go | route_kf | aware | 10 % | 5 % | 0 % | 80 % | -32.7 | 0 % |
| ladder_5km/climb3/stop_and_go | route_kf_yaw | plain | 45 % | 20 % | 5 % | 45 % | -6.7 | – |
| ladder_5km/climb3/stop_and_go | route_kf_yaw | aware | 5 % | 5 % | 5 % | 85 % | -38.0 | 0 % |
| ladder_5km/underwater/free | route_kf | plain | 10 % | 0 % | 85 % | 0 % | -0.3 | – |
| ladder_5km/underwater/free | route_kf | aware | 0 % | 0 % | 0 % | 30 % | -14.3 | 0 % |
| ladder_5km/underwater/free | route_kf_yaw | plain | 10 % | 0 % | 85 % | 0 % | -0.4 | – |
| ladder_5km/underwater/free | route_kf_yaw | aware | 0 % | 0 % | 0 % | 50 % | -15.0 | 0 % |
| ladder_5km/underwater/stop_and_go | route_kf | plain | 50 % | 40 % | 0 % | 50 % | -4.9 | – |
| ladder_5km/underwater/stop_and_go | route_kf | aware | 15 % | 10 % | 5 % | 65 % | -45.0 | 5 % |
| ladder_5km/underwater/stop_and_go | route_kf_yaw | plain | 40 % | 30 % | 15 % | 45 % | +0.2 | – |
| ladder_5km/underwater/stop_and_go | route_kf_yaw | aware | 20 % | 15 % | 0 % | 65 % | -38.5 | 5 % |
| eisenhower_tunnel/flat/free | route_kf | plain | 15 % | 0 % | 75 % | 0 % | +0.9 | – |
| eisenhower_tunnel/flat/free | route_kf | aware | 5 % | 0 % | 50 % | 0 % | -2.9 | 0 % |
| eisenhower_tunnel/flat/free | route_kf_yaw | plain | 30 % | 0 % | 55 % | 0 % | +0.1 | – |
| eisenhower_tunnel/flat/free | route_kf_yaw | aware | 0 % | 0 % | 15 % | 5 % | -8.9 | 0 % |
| eisenhower_tunnel/flat/stop_and_go | route_kf | plain | 40 % | 20 % | 25 % | 30 % | -0.5 | – |
| eisenhower_tunnel/flat/stop_and_go | route_kf | aware | 0 % | 0 % | 5 % | 90 % | -74.2 | 0 % |
| eisenhower_tunnel/flat/stop_and_go | route_kf_yaw | plain | 50 % | 25 % | 5 % | 35 % | +3.6 | – |
| eisenhower_tunnel/flat/stop_and_go | route_kf_yaw | aware | 5 % | 0 % | 5 % | 80 % | -39.7 | 0 % |
