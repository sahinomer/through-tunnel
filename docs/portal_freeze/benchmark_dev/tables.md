# Benchmark: generated tables

step 1: portal freeze 200 m · commit `1811edd+dirty` · 2026-10-16 10:05 UTC · 8 scenarios × 20 runs (**development subset**: map grade on, calibrated estimators only). † = reference estimator (uses the car's speed reading; not a phone-only solution). Realism options on (bias drift, GPS degradation before the portal).

## How to read the failure states

* **Gross error**: the estimate was more than 200 m from the true position at some time in the tunnel or at C, ahead *or* behind. The position is unusable for guidance.
* **Announcement off**: the exit announcement came more than 15 s early or late (or never). The driver gets the instruction at the wrong time. Never-fired does not happen in practice: a late estimate is pushed past the announcement point when GPS returns, so the announcement is late, not missing.
* **Capped at D** (a data-quality flag, not a third failure): the estimate reached the route end D before the vehicle reached C. A route estimate stops at D, so its error is a lower bound (cells of exactly 782 / 881 / 889 m are the C–D distances). Every capped run is also a gross error.
* In the scenario tables, cells are the error at C [m], median (p90); ✗n = n runs with a gross error, §n = n of them capped at D.

## Overall, without map grade

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 77 (614) | 83 (614) | 36 % | 24 % | 55 % | 6 % |
| DR calibrated + GPS-blended speed/heading | 60 (447) | 60 (447) | 28 % | 21 % | 57 % | 6 % |
| Route + filtered IMU speed | 40 (462) | 45 (462) | 26 % | 21 % | 57 % | 6 % |
| Route + vehicle speed (reference) † | 5 (14) | 5 (15) | 0 % | 0 % | 100 % | 0 % |

## Overall, with map grade

Flat roads (where the map grade changes nothing) are in both overall tables.

| estimator | error at C [m] | max in tunnel [m] | gross error (> 200 m) | announcement off (> ±15 s) | announcement good (±3 s) | capped at D |
|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 174 (1355) | 174 (1355) | 47 % | 30 % | 41 % | 11 % |
| DR calibrated + GPS-blended speed/heading | 107 (1233) | 110 (1233) | 35 % | 28 % | 44 % | 12 % |
| Route + filtered IMU speed | 91 (782) | 105 (936) | 32 % | 28 % | 44 % | 12 % |
| Route + vehicle speed (reference) † | 5 (17) | 6 (17) | 0 % | 0 % | 100 % | 0 % |

## Tunnel length, flat road, free flow

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 18 (31) | – | – | – | 167 (306) ✗8 |
| DR calibrated + GPS-blended speed/heading | 9 (20) | – | – | – | 117 (240) ✗4 |
| Route + filtered IMU speed | 6 (12) | – | – | – | 103 (257) ✗4 |
| Route + vehicle speed (reference) † | 4 (11) | – | – | – | 6 (17) |

## Tunnel length, flat road, stop-and-go

| estimator | 0.5 km | 1 km | 2 km | 3 km | 5 km |
|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 40 (231) ✗3 | – | – | – | 561 (2100) ✗18 §5 |
| DR calibrated + GPS-blended speed/heading | 23 (93) ✗1 | – | – | – | 420 (2356) ✗17 §5 |
| Route + filtered IMU speed | 18 (92) ✗1 | – | – | – | 385 (782) ✗16 §5 |
| Route + vehicle speed (reference) † | 4 (14) | – | – | – | 7 (17) |

## Road profile, all geometries, free flow, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 32 (261) ✗8 | – | – |
| DR calibrated + GPS-blended speed/heading | 21 (180) ✗4 | – | – |
| Route + filtered IMU speed | 13 (172) ✗4 | – | – |
| Route + vehicle speed (reference) † | 5 (14) | – | – |

## Road profile, all geometries, free flow, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 32 (261) ✗8 | 167 (303) ✗8 | 106 (215) ✗4 |
| DR calibrated + GPS-blended speed/heading | 21 (180) ✗4 | 106 (249) ✗4 | 72 (103) |
| Route + filtered IMU speed | 13 (172) ✗4 | 109 (268) ✗4 | 42 (93) |
| Route + vehicle speed (reference) † | 5 (14) | 6 (17) | 6 (17) |

## Road profile, all geometries, stop-and-go, map grade off

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 239 (1034) ✗21 §5 | – | – |
| DR calibrated + GPS-blended speed/heading | 158 (814) ✗18 §5 | – | – |
| Route + filtered IMU speed | 93 (782) ✗17 §5 | – | – |
| Route + vehicle speed (reference) † | 5 (14) | – | – |

## Road profile, all geometries, stop-and-go, map grade on

| estimator | flat | climb3 | underwater |
|---|---|---|---|
| DR GPS-calibrated IMU | 239 (1034) ✗21 §5 | 523 (6142) ✗17 §5 | 766 (8726) ✗17 §8 |
| DR calibrated + GPS-blended speed/heading | 158 (814) ✗18 §5 | 341 (7833) ✗15 §5 | 990 (8761) ✗15 §10 |
| Route + filtered IMU speed | 93 (782) ✗17 §5 | 297 (782) ✗13 §5 | 767 (782) ✗13 §10 |
| Route + vehicle speed (reference) † | 5 (14) | 7 (17) | 7 (17) |

## Presets (real / demo geometry), flat road, free flow

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR GPS-calibrated IMU | – | – | – |
| DR calibrated + GPS-blended speed/heading | – | – | – |
| Route + filtered IMU speed | – | – | – |
| Route + vehicle speed (reference) † | – | – | – |

## Presets (real / demo geometry), flat road, stop-and-go

| estimator | Eisenhower Tunnel | Seattle SR 99 Tunnel | Synthetic demo route |
|---|---|---|---|
| DR GPS-calibrated IMU | – | – | – |
| DR calibrated + GPS-blended speed/heading | – | – | – |
| Route + filtered IMU speed | – | – | – |
| Route + vehicle speed (reference) † | – | – | – |
