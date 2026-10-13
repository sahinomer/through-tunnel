# Realism check: bias drift and GPS degradation before the portal

Median error at C [m] over 10 paired runs (seed k for sensors, GPS and traffic in every condition). In brackets: the size of the paired shift of the error vector at C caused by the added effect, median / p90 [m] (how far it moves each run's estimate, independent of the sign of the error it starts from). ≥ = a route estimator reached the route end D in some runs (its error is then capped).

## Eisenhower Tunnel, I-70 (westbound): free

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Realistic defaults (noise, bias, GPS errors) | 522 | 52 | 26 | 25 | 329 |
| + IMU bias drift | 523 (shift 28 / 37) | 46 (shift 14 / 30) | 38 (shift 15 / 30) | 28 (shift 14 / 30) | 329 (shift 0 / 0) |
| + GPS degradation before B | 513 (shift 53 / 128) | 86 (shift 68 / 126) | 40 (shift 37 / 69) | 32 (shift 27 / 69) | 340 (shift 22 / 63) |
| + both | 518 (shift 64 / 128) | 92 (shift 77 / 120) | 56 (shift 47 / 76) | 32 (shift 40 / 75) | 340 (shift 22 / 63) |

## Eisenhower Tunnel, I-70 (westbound): stop-and-go

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Realistic defaults (noise, bias, GPS errors) | 4840 | 168 | 118 | ≥115 | ≥881 |
| + IMU bias drift | 4578 (shift 262 / 451) | 179 (shift 103 / 600) | 173 (shift 87 / 603) | 166 (shift 84 / 576) | ≥881 (shift 0 / 0) |
| + GPS degradation before B | 4691 (shift 104 / 363) | 248 (shift 276 / 534) | 191 (shift 180 / 475) | ≥185 (shift 136 / 301) | ≥881 (shift 0 / 0) |
| + both | 4431 (shift 411 / 674) | 260 (shift 263 / 361) | 226 (shift 180 / 291) | ≥213 (shift 180 / 292) | ≥881 (shift 0 / 0) |

## Seattle SR 99 Tunnel (northbound): free

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Realistic defaults (noise, bias, GPS errors) | 746 | 74 | 68 | 28 | 22 |
| + IMU bias drift | 780 (shift 48 / 61) | 74 (shift 28 / 47) | 66 (shift 29 / 47) | 40 (shift 29 / 44) | 22 (shift 0 / 0) |
| + GPS degradation before B | 715 (shift 61 / 90) | 121 (shift 87 / 137) | 82 (shift 41 / 72) | 55 (shift 39 / 73) | 37 (shift 48 / 79) |
| + both | 736 (shift 75 / 125) | 132 (shift 77 / 141) | 72 (shift 43 / 102) | 49 (shift 44 / 105) | 37 (shift 48 / 79) |

## Seattle SR 99 Tunnel (northbound): stop-and-go

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Realistic defaults (noise, bias, GPS errors) | 5318 | 239 | 214 | 110 | ≥889 |
| + IMU bias drift | 5047 (shift 286 / 566) | 218 (shift 85 / 414) | 184 (shift 84 / 420) | ≥75 (shift 82 / 409) | ≥889 (shift 0 / 0) |
| + GPS degradation before B | 5215 (shift 141 / 352) | 311 (shift 235 / 1168) | 266 (shift 186 / 931) | ≥119 (shift 188 / 578) | ≥889 (shift 0 / 0) |
| + both | 4944 (shift 241 / 824) | 256 (shift 168 / 1078) | 246 (shift 90 / 762) | ≥189 (shift 89 / 555) | ≥889 (shift 0 / 0) |

## Synthetic demo route: free

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Realistic defaults (noise, bias, GPS errors) | 330 | 33 | 21 | 19 | 11 |
| + IMU bias drift | 333 (shift 18 / 24) | 33 (shift 8 / 18) | 21 (shift 9 / 20) | 17 (shift 9 / 21) | 11 (shift 0 / 0) |
| + GPS degradation before B | 349 (shift 35 / 55) | 52 (shift 43 / 78) | 21 (shift 24 / 47) | 17 (shift 24 / 51) | 26 (shift 29 / 53) |
| + both | 337 (shift 42 / 65) | 59 (shift 51 / 90) | 24 (shift 31 / 49) | 18 (shift 34 / 49) | 26 (shift 29 / 53) |

## Synthetic demo route: stop-and-go

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Realistic defaults (noise, bias, GPS errors) | 2923 | 63 | 41 | 39 | ≥782 |
| + IMU bias drift | 2736 (shift 169 / 263) | 67 (shift 45 / 334) | 46 (shift 42 / 335) | 41 (shift 41 / 354) | ≥782 (shift 0 / 0) |
| + GPS degradation before B | 2875 (shift 129 / 294) | 161 (shift 127 / 303) | 88 (shift 62 / 233) | 89 (shift 60 / 257) | ≥782 (shift 0 / 0) |
| + both | 2688 (shift 80 / 495) | 157 (shift 100 / 258) | 87 (shift 63 / 184) | 88 (shift 64 / 202) | ≥782 (shift 0 / 0) |
