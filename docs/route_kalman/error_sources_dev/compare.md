# Error-source benchmark comparison

Baseline commit `e69543f`, this run `8e07c8b+dirty`. Median error 5 km into the tunnel [m], baseline → this run.

| estimator | floor / free | gps_speed / free | gps_degr / free | gps_degr_harsh / free | realistic / free | floor / stop_and_go | gps_speed / stop_and_go | gps_degr / stop_and_go | gps_degr_harsh / stop_and_go | realistic / stop_and_go |
|---|---|---|---|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 0 → 0 | 117 → 112 | 264 → 121 | 286 → 170 | 316 → 167 | 13 → 2 | 301 → 391 | 435 → 159 | 472 → 316 | 562 → 561 |
| DR calibrated + GPS-blended speed/heading | 0 → 0 | 95 → 116 | 170 → 6 | 175 → 129 | 217 → 117 | 12 → 0 | 210 → 386 | 325 → 7 | 337 → 266 | 470 → 420 |
| Route + filtered IMU speed | 0 → 0 | 98 → 102 | 184 → 4 | 188 → 133 | 231 → 103 | 13 → 0 | 196 → 393 | 354 → 3 | 373 → 289 | 482 → 385 |
| Route + IMU Kalman filter (distance, speed, offset) | – | – | – | – | – | – | – | – | – | – |
| Route + vehicle speed (reference) | 0 → 0 | 4 → 4 | 5 → 5 | 11 → 11 | 6 → 6 | 0 → 0 | 4 → 4 | 4 → 4 | 10 → 10 | 7 → 7 |
| Route + IMU + standstill oracle: speed reset ‡ | – | – | – | – | – | – | – | – | – | – |
| Route + IMU + standstill oracle: speed reset + offset ‡ | – | – | – | – | – | – | – | – | – | – |
