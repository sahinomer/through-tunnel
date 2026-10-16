# Error-source benchmark comparison

Baseline commit `e69543f`, this run `1811edd+dirty`. Median error 5 km into the tunnel [m], baseline → this run.

| estimator | floor / free | gps_speed / free | gps_degr / free | gps_degr_harsh / free | realistic / free | floor / stop_and_go | gps_speed / stop_and_go | gps_degr / stop_and_go | gps_degr_harsh / stop_and_go | realistic / stop_and_go |
|---|---|---|---|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 0 → 2 | 117 → 101 | 264 → 121 | 286 → 140 | 316 → 156 | 13 → 6 | 301 → 363 | 435 → 157 | 472 → 182 | 562 → 779 |
| DR calibrated + GPS-blended speed/heading | 0 → 2 | 95 → 94 | 170 → 7 | 175 → 20 | 217 → 151 | 12 → 6 | 210 → 379 | 325 → 11 | 337 → 26 | 470 → 493 |
| Route + filtered IMU speed | 0 → 0 | 98 → 81 | 184 → 4 | 188 → 11 | 231 → 139 | 13 → 1 | 196 → 386 | 354 → 5 | 373 → 11 | 482 → 509 |
| Route + vehicle speed (reference) | 0 → 0 | 4 → 4 | 5 → 5 | 11 → 11 | 6 → 6 | 0 → 0 | 4 → 4 | 4 → 4 | 10 → 10 | 7 → 7 |
