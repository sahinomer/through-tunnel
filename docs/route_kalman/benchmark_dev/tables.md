# Benchmark: generated tables

step 4: route_kf v1 · commit `8e07c8b+dirty` · 2026-10-16 13:49 UTC · 8 scenarios × 20 runs (**development subset**: map grade on, calibrated estimators only). † = reference estimator (uses the car's speed reading; not a phone-only solution). Realism options on (bias drift, GPS degradation before the portal).

## How to read the failure states

* **Gross error**: the estimate was more than 200 m from the true position at some time in the tunnel or at C, ahead *or* behind. The position is unusable for guidance.
* **Announcement off**: the exit announcement came more than 15 s early or late (or never). The driver gets the instruction at the wrong time. Never-fired does not happen in practice: a late estimate is pushed past the announcement point when GPS returns, so the announcement is late, not missing.
* **Capped at D** (a data-quality flag, not a third failure): the estimate reached the route end D before the vehicle reached C. A route estimate stops at D, so its error is a lower bound (cells of exactly 782 / 881 / 889 m are the C–D distances). Every capped run is also a gross error.
* In the scenario tables, cells are the error at C [m], median (p90); ✗n = n runs with a gross error, §n = n of them capped at D.

## Overall, without map grade

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 77 (614) | 82 (614) | 36 % | 24 % | 55 % | 6 % |
| DR calibrated + GPS-blended speed/heading | 60 (447) | 60 (447) | 28 % | 21 % | 57 % | 6 % |
| Route + filtered IMU speed | 40 (462) | 45 (462) | 26 % | 21 % | 57 % | 6 % |
| Route + IMU Kalman filter (distance, speed, offset) | 29 (387) | 35 (387) | 18 % | 19 % | 62 % | 6 % |
| Route + vehicle speed (reference) † | 5 (14) | 5 (15) | 0 % | 0 % | 100 % | 0 % |
| Route + IMU + standstill oracle: speed reset ‡ | 19 (305) | 22 (305) | 16 % | 11 % | 60 % | 0 % |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 13 (169) | 19 (168) | 8 % | 9 % | 65 % | 0 % |

## Overall, with map grade

Flat roads (where the map grade changes nothing) are in both overall tables.

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 182 (1290) | 182 (1290) | 48 % | 32 % | 39 % | 11 % |
| DR calibrated + GPS-blended speed/heading | 116 (957) | 117 (956) | 38 % | 32 % | 46 % | 12 % |
| Route + filtered IMU speed | 91 (782) | 99 (870) | 35 % | 30 % | 44 % | 12 % |
| Route + IMU Kalman filter (distance, speed, offset) | 66 (782) | 77 (895) | 28 % | 28 % | 49 % | 11 % |
| Route + vehicle speed (reference) † | 5 (17) | 6 (17) | 0 % | 0 % | 100 % | 0 % |
| Route + IMU + standstill oracle: speed reset ‡ | 55 (463) | 66 (462) | 22 % | 18 % | 49 % | 5 % |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 47 (241) | 55 (241) | 13 % | 16 % | 50 % | 3 % |

## Tunnel length, flat road, free flow

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 18 (31) | – | – | – | 167 (306) ✗8 |
| DR calibrated + GPS-blended speed/heading | 9 (20) | – | – | – | 117 (240) ✗4 |
| Route + filtered IMU speed | 6 (12) | – | – | – | 103 (257) ✗4 |
| Route + IMU Kalman filter (distance, speed, offset) | 6 (19) | – | – | – | 85 (283) ✗4 |
| Route + vehicle speed (reference) † | 4 (11) | – | – | – | 6 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 6 (12) | – | – | – | 103 (257) ✗4 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 6 (12) | – | – | – | 103 (257) ✗4 |

## Tunnel length, flat road, stop-and-go

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 40 (231) ✗3 | – | – | – | 561 (2099) ✗18 §5 |
| DR calibrated + GPS-blended speed/heading | 23 (93) ✗1 | – | – | – | 420 (2355) ✗17 §5 |
| Route + filtered IMU speed | 18 (92) ✗1 | – | – | – | 385 (782) ✗16 §5 |
| Route + IMU Kalman filter (distance, speed, offset) | 11 (59) ✗1 | – | – | – | 188 (782) ✗9 §5 |
| Route + vehicle speed (reference) † | 4 (14) | – | – | – | 7 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 6 (17) | – | – | – | 131 (607) ✗9 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 5 (14) | – | – | – | 103 (199) ✗2 |

## Road profile, all geometries, free flow, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 32 (261) ✗8 | – | – |
| DR calibrated + GPS-blended speed/heading | 21 (180) ✗4 | – | – |
| Route + filtered IMU speed | 13 (172) ✗4 | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | 19 (183) ✗4 | – | – |
| Route + vehicle speed (reference) † | 5 (14) | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | 13 (172) ✗4 | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 13 (172) ✗4 | – | – |

## Road profile, all geometries, free flow, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 32 (261) ✗8 | 165 (285) ✗9 | 102 (217) ✗4 |
| DR calibrated + GPS-blended speed/heading | 21 (180) ✗4 | 110 (244) ✗5 | 71 (96) |
| Route + filtered IMU speed | 13 (172) ✗4 | 93 (247) ✗4 | 44 (95) |
| Route + IMU Kalman filter (distance, speed, offset) | 19 (183) ✗4 | 103 (268) ✗4 | 40 (86) |
| Route + vehicle speed (reference) † | 5 (14) | 6 (17) | 6 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 13 (172) ✗4 | 93 (247) ✗4 | 44 (95) |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 13 (172) ✗4 | 93 (247) ✗4 | 44 (95) |

## Road profile, all geometries, stop-and-go, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 238 (1033) ✗21 §5 | – | – |
| DR calibrated + GPS-blended speed/heading | 158 (813) ✗18 §5 | – | – |
| Route + filtered IMU speed | 93 (782) ✗17 §5 | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | 41 (782) ✗10 §5 | – | – |
| Route + vehicle speed (reference) † | 5 (14) | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | 20 (467) ✗9 | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 13 (139) ✗2 | – | – |

## Road profile, all geometries, stop-and-go, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 238 (1033) ✗21 §5 | 601 (7198) ✗18 §6 | 658 (8740) ✗16 §7 |
| DR calibrated + GPS-blended speed/heading | 158 (813) ✗18 §5 | 506 (8661) ✗18 §6 | 639 (7987) ✗15 §8 |
| Route + filtered IMU speed | 93 (782) ✗17 §5 | 501 (782) ✗17 §6 | 613 (782) ✗14 §8 |
| Route + IMU Kalman filter (distance, speed, offset) | 41 (782) ✗10 §5 | 228 (782) ✗12 §6 | 312 (782) ✗15 §7 |
| Route + vehicle speed (reference) † | 5 (14) | 7 (17) | 7 (17) |
| Route + IMU + standstill oracle: speed reset ‡ | 20 (467) ✗9 | 144 (782) ✗9 §3 | 132 (782) ✗10 §5 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 13 (139) ✗2 | 128 (199) ✗2 | 127 (782) ✗9 §5 |

## Presets (real / demo geometry), flat road, free flow

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR GPS-calibrated IMU | – | – | – |
| DR calibrated + GPS-blended speed/heading | – | – | – |
| Route + filtered IMU speed | – | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | – | – | – |
| Route + vehicle speed (reference) † | – | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | – | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | – | – | – |

## Presets (real / demo geometry), flat road, stop-and-go

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR GPS-calibrated IMU | – | – | – |
| DR calibrated + GPS-blended speed/heading | – | – | – |
| Route + filtered IMU speed | – | – | – |
| Route + IMU Kalman filter (distance, speed, offset) | – | – | – |
| Route + vehicle speed (reference) † | – | – | – |
| Route + IMU + standstill oracle: speed reset ‡ | – | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | – | – | – |
