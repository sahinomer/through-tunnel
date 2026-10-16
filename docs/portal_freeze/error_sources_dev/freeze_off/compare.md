# Error-source benchmark comparison

Baseline commit `e69543f`, this run `1811edd+dirty`. Median error 5 km into the tunnel [m], baseline → this run.

| estimator | floor / free | gps_speed / free | gps_degr / free | gps_degr_harsh / free | realistic / free | floor / stop_and_go | gps_speed / stop_and_go | gps_degr / stop_and_go | gps_degr_harsh / stop_and_go | realistic / stop_and_go |
|---|---|---|---|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 0 → 0 | 117 → 117 | 264 → 264 | 286 → 286 | 316 → 316 | 13 → 13 | 301 → 301 | 435 → 435 | 472 → 472 | 562 → 562 |
| DR calibrated + GPS-blended speed/heading | 0 → 0 | 95 → 95 | 170 → 170 | 175 → 175 | 217 → 217 | 12 → 12 | 210 → 210 | 325 → 325 | 337 → 337 | 470 → 470 |
| Route + filtered IMU speed | 0 → 0 | 98 → 98 | 184 → 184 | 188 → 188 | 231 → 231 | 13 → 13 | 196 → 196 | 354 → 354 | 373 → 373 | 482 → 482 |
| Route + vehicle speed (reference) | 0 → 0 | 4 → 4 | 5 → 5 | 11 → 11 | 6 → 6 | 0 → 0 | 4 → 4 | 4 → 4 | 10 → 10 | 7 → 7 |
