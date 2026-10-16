# Error-source benchmark comparison

Baseline commit `e69543f`, this run `1811edd+dirty`. Median error 5 km into the tunnel [m], baseline → this run.

| estimator | floor / free | gps_speed / free | gps_degr / free | gps_degr_harsh / free | realistic / free | floor / stop_and_go | gps_speed / stop_and_go | gps_degr / stop_and_go | gps_degr_harsh / stop_and_go | realistic / stop_and_go |
|---|---|---|---|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 0 → 0 | 117 → 83 | 264 → 112 | 286 → 144 | 316 → 184 | 13 → 4 | 301 → 316 | 435 → 215 | 472 → 391 | 562 → 543 |
| DR calibrated + GPS-blended speed/heading | 0 → 0 | 95 → 93 | 170 → 43 | 175 → 118 | 217 → 150 | 12 → 2 | 210 → 309 | 325 → 86 | 337 → 196 | 470 → 432 |
| Route + filtered IMU speed | 0 → 0 | 98 → 95 | 184 → 46 | 188 → 112 | 231 → 147 | 13 → 2 | 196 → 307 | 354 → 94 | 373 → 215 | 482 → 447 |
| Route + vehicle speed (reference) | 0 → 0 | 4 → 4 | 5 → 5 | 11 → 11 | 6 → 6 | 0 → 0 | 4 → 4 | 4 → 4 | 10 → 10 | 7 → 7 |
