# Traffic study: generated tables

Preset roads and drivers. Ideal = error-free sensors and GPS, traffic seed 0. Realistic = preset sensor and GPS errors, 20 runs (seed k for sensors, GPS and traffic events). Sweeps: realistic, 10 runs per value, medians. § = a route estimator reached the route end D before C in that many runs (its error is then capped by the route length).

## Eisenhower Tunnel, I-70 (westbound)

**Scenario facts (medians):**

| scenario | time in tunnel [s] | GPS outage [s] | standing [s] | mean speed in tunnel [km/h] |
|---|---|---|---|---|
| Free flow | 125 | 129 | 0 | 79 |
| Portal slowdown (T1) | 131 | 136 | 0 | 75 |
| Tunnel speed limit (T2) | 163 | 168 | 0 | 60 |
| Stop-and-go (T3) | 454 | 460 | 103 | 22 |
| Exit queue (T5) | 251 | 256 | 40 | 39 |
| Congested slow flow (T6) | 351 | 356 | 0 | 28 |

**Ideal sensors: error at C [m]:**

| scenario | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Free flow | 0 | 0 | 0 | 1 | 336 |
| Portal slowdown (T1) | 0 | 0 | 0 | 1 | 339 |
| Tunnel speed limit (T2) | 0 | 1 | 1 | 1 | 18 |
| Stop-and-go (T3) | 2 | 7 | 7 | 7 | ≥881 §1 |
| Exit queue (T5) | 0 | 0 | 0 | 1 | ≥881 §1 |
| Congested slow flow (T6) | 1 | 5 | 5 | 5 | ≥881 §1 |

**Realistic sensors: error at C [m], median (p90):**

| scenario | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Free flow | 460 (773) | 55 (76) | 38 (60) | 34 (55) | 330 (362) |
| Portal slowdown (T1) | 490 (817) | 60 (117) | 38 (77) | 37 (66) | 338 (401) |
| Tunnel speed limit (T2) | 772 (1252) | 69 (162) | 51 (106) | 50 (97) | 117 (206) |
| Stop-and-go (T3) | 1682 (8438) | 142 (596) | 118 (532) | 115 (530) §1 | ≥881 (881) §20 |
| Exit queue (T5) | 838 (2915) | 103 (189) | 85 (144) | 84 (143) | ≥881 (881) §20 |
| Congested slow flow (T6) | 2152 (4887) | 240 (532) | 194 (495) | 194 (494) | ≥881 (881) §12 |

**Realistic sensors: maximum error in the tunnel [m], median:**

| scenario | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Free flow | 460 | 55 | 38 | 34 | 330 |
| Portal slowdown (T1) | 490 | 60 | 38 | 37 | 338 |
| Tunnel speed limit (T2) | 771 | 69 | 50 | 50 | 117 |
| Stop-and-go (T3) | 1682 | 142 | 118 | 115 | 1622 |
| Exit queue (T5) | 838 | 103 | 85 | 84 | 1150 |
| Congested slow flow (T6) | 2151 | 240 | 194 | 194 | 1015 |

**Realistic sensors: heading error and exit-announcement timing [s], median |error| (signed mean; + = late):**

| scenario | dr_calibrated |heading err.| | dr_raw announce | dr_calibrated announce | dr_filtered announce | route_imu announce | route_hold announce |
|---|---|---|---|---|---|---|
| Free flow | 0.42° | 15 (-1) | 2 (+0) | 1 (+0) | 1 (+0) | 12 (-12) |
| Portal slowdown (T1) | 0.47° | 15 (-1) | 2 (+1) | 1 (+1) | 1 (+1) | 15 (+14) |
| Tunnel speed limit (T2) | 0.52° | 22 (-5) | 3 (+1) | 3 (+1) | 3 (+1) | 6 (-5) |
| Stop-and-go (T3) | 1.26° | 111 (-97) | 15 (-23) | 12 (-21) | 12 (-21) | 205 (-200) |
| Exit queue (T5) | 0.66° | 49 (+32) | 12 (+9) | 10 (+8) | 10 (+8) | 42 (-40) |
| Congested slow flow (T6) | 0.88° | 48 (-46) | 18 (-3) | 17 (-1) | 17 (-1) | 87 (-88) |

**Sweep: portal speed drop (T1, no jitter), error at C [m], median:**

| drop | time in tunnel [s] | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|---|
| 0 km/h | 126 | 519 | 66 | 44 | 35 | 108 |
| 5 km/h | 127 | 532 | 68 | 46 | 36 | 30 |
| 10 km/h | 129 | 548 | 58 | 41 | 40 | 197 |
| 20 km/h | 133 | 559 | 60 | 40 | 30 | 442 |
| 30 km/h | 139 | 638 | 90 | 70 | 68 | 697 |

**Sweep: number of stops (T3), error at C [m], median:**

| stops | time in tunnel [s] | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|---|
| 0 | 323 | 2982 | 168 | 122 | 117 | 634 §4 |
| 1 | 377 | 3409 | 173 | 153 | 145 | ≥881 §6 |
| 2 | 410 | 3883 | 179 | 143 | 133 | ≥881 §10 |
| 4 | 501 | 5557 | 185 | 135 | 131 §1 | ≥881 §10 |

## Seattle SR 99 Tunnel (northbound)

**Scenario facts (medians):**

| scenario | time in tunnel [s] | GPS outage [s] | standing [s] | mean speed in tunnel [km/h] |
|---|---|---|---|---|
| Free flow | 150 | 155 | 0 | 71 |
| Portal slowdown (T1) | 156 | 161 | 0 | 69 |
| Tunnel speed limit (T2) | 178 | 183 | 0 | 60 |
| Stop-and-go (T3) | 484 | 490 | 103 | 22 |
| Exit queue (T5) | 273 | 278 | 40 | 39 |
| Congested slow flow (T6) | 374 | 380 | 0 | 29 |

**Ideal sensors: error at C [m]:**

| scenario | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Free flow | 0 | 0 | 0 | 1 | 1 |
| Portal slowdown (T1) | 0 | 1 | 1 | 0 | 374 |
| Tunnel speed limit (T2) | 0 | 1 | 1 | 1 | 131 |
| Stop-and-go (T3) | 2 | 5 | 4 | 4 | ≥889 §1 |
| Exit queue (T5) | 0 | 0 | 0 | 1 | ≥889 §1 |
| Congested slow flow (T6) | 1 | 3 | 3 | 3 | ≥889 §1 |

**Realistic sensors: error at C [m], median (p90):**

| scenario | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Free flow | 640 (1070) | 65 (116) | 61 (93) | 32 (72) | 20 (56) |
| Portal slowdown (T1) | 683 (1169) | 68 (136) | 63 (106) | 33 (85) | 396 (530) |
| Tunnel speed limit (T2) | 903 (1480) | 79 (147) | 76 (119) | 43 (95) | 244 (351) |
| Stop-and-go (T3) | 2036 (9751) | 228 (450) | 199 (433) | 86 (366) | ≥889 (889) §20 |
| Exit queue (T5) | 1051 (3355) | 103 (187) | 100 (173) | 86 (161) | ≥889 (889) §20 |
| Congested slow flow (T6) | 2351 (5614) | 224 (438) | 208 (377) | 151 (360) | ≥889 (889) §14 |

**Realistic sensors: maximum error in the tunnel [m], median:**

| scenario | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Free flow | 640 | 65 | 61 | 32 | 34 |
| Portal slowdown (T1) | 683 | 67 | 63 | 33 | 396 |
| Tunnel speed limit (T2) | 903 | 79 | 76 | 43 | 244 |
| Stop-and-go (T3) | 2036 | 228 | 199 | 86 | 1865 |
| Exit queue (T5) | 1051 | 103 | 100 | 86 | 1102 |
| Congested slow flow (T6) | 2351 | 224 | 208 | 151 | 1293 |

**Realistic sensors: heading error and exit-announcement timing [s], median |error| (signed mean; + = late):**

| scenario | dr_calibrated |heading err.| | dr_raw announce | dr_calibrated announce | dr_filtered announce | route_imu announce | route_hold announce |
|---|---|---|---|---|---|---|
| Free flow | 1.24° | 19 (-3) | 2 (-0) | 1 (-0) | 1 (+0) | 1 (-1) |
| Portal slowdown (T1) | 1.52° | 18 (-3) | 2 (+1) | 1 (+0) | 1 (+1) | 18 (+17) |
| Tunnel speed limit (T2) | 1.55° | 22 (-6) | 2 (-0) | 2 (-0) | 2 (+0) | 12 (-11) |
| Stop-and-go (T3) | 3.81° | 126 (-106) | 11 (-13) | 10 (-11) | 9 (-9) | 217 (-225) |
| Exit queue (T5) | 2.43° | 56 (+29) | 10 (+12) | 9 (+6) | 9 (+8) | 27 (-26) |
| Congested slow flow (T6) | 3.08° | 59 (-52) | 17 (+11) | 16 (+9) | 16 (+10) | 117 (-111) |

**Sweep: portal speed drop (T1, no jitter), error at C [m], median:**

| drop | time in tunnel [s] | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|---|
| 0 km/h | 150 | 746 | 74 | 68 | 28 | 22 |
| 5 km/h | 152 | 760 | 74 | 69 | 29 | 55 |
| 10 km/h | 154 | 782 | 77 | 71 | 30 | 193 |
| 20 km/h | 159 | 785 | 104 | 87 | 26 | 551 |
| 30 km/h | 168 | 932 | 80 | 82 | 31 | 806 |

**Sweep: number of stops (T3), error at C [m], median:**

| stops | time in tunnel [s] | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|---|
| 0 | 350 | 3354 | 219 | 219 | 157 | ≥889 §6 |
| 1 | 404 | 3810 | 221 | 193 | 140 | ≥889 §9 |
| 2 | 437 | 4471 | 241 | 206 | 114 | ≥889 §10 |
| 4 | 527 | 6147 | 238 | 215 | 115 | ≥889 §10 |

## Synthetic demo route

**Scenario facts (medians):**

| scenario | time in tunnel [s] | GPS outage [s] | standing [s] | mean speed in tunnel [km/h] |
|---|---|---|---|---|
| Free flow | 103 | 107 | 0 | 68 |
| Portal slowdown (T1) | 107 | 112 | 0 | 66 |
| Tunnel speed limit (T2) | 117 | 122 | 0 | 60 |
| Stop-and-go (T3) | 361 | 369 | 103 | 20 |
| Exit queue (T5) | 226 | 231 | 40 | 31 |
| Congested slow flow (T6) | 251 | 257 | 0 | 28 |

**Ideal sensors: error at C [m]:**

| scenario | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Free flow | 0 | 0 | 0 | 0 | 17 |
| Portal slowdown (T1) | 0 | 0 | 0 | 0 | 245 |
| Tunnel speed limit (T2) | 0 | 0 | 0 | 0 | 66 |
| Stop-and-go (T3) | 1 | 4 | 4 | 4 | ≥782 §1 |
| Exit queue (T5) | 0 | 0 | 0 | 0 | ≥782 §1 |
| Congested slow flow (T6) | 1 | 3 | 2 | 2 | ≥782 §1 |

**Realistic sensors: error at C [m], median (p90):**

| scenario | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Free flow | 282 (463) | 29 (56) | 17 (37) | 17 (40) | 18 (45) |
| Portal slowdown (T1) | 305 (501) | 40 (63) | 18 (41) | 16 (44) | 253 (339) |
| Tunnel speed limit (T2) | 369 (583) | 34 (67) | 21 (48) | 20 (52) | 89 (197) |
| Stop-and-go (T3) | 958 (4508) | 88 (277) | 58 (242) | 52 (267) | ≥782 (782) §19 |
| Exit queue (T5) | 583 (2375) | 74 (129) | 42 (97) | 46 (103) | ≥782 (782) §20 |
| Congested slow flow (T6) | 1272 (2377) | 93 (189) | 70 (172) | 75 (188) | 726 (782) §8 |

**Realistic sensors: maximum error in the tunnel [m], median:**

| scenario | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Free flow | 282 | 29 | 17 | 17 | 47 |
| Portal slowdown (T1) | 305 | 40 | 18 | 16 | 253 |
| Tunnel speed limit (T2) | 368 | 34 | 21 | 20 | 89 |
| Stop-and-go (T3) | 958 | 88 | 58 | 52 | 1321 |
| Exit queue (T5) | 583 | 74 | 42 | 46 | 989 |
| Congested slow flow (T6) | 1272 | 93 | 70 | 75 | 726 |

**Realistic sensors: heading error and exit-announcement timing [s], median |error| (signed mean; + = late):**

| scenario | dr_calibrated |heading err.| | dr_raw announce | dr_calibrated announce | dr_filtered announce | route_imu announce | route_hold announce |
|---|---|---|---|---|---|---|
| Free flow | 0.44° | 5 (+1) | 1 (+0) | 0 (+0) | 1 (+0) | 0 (+0) |
| Portal slowdown (T1) | 0.66° | 7 (+1) | 1 (+0) | 1 (+0) | 1 (+0) | 12 (+13) |
| Tunnel speed limit (T2) | 0.46° | 10 (+1) | 1 (+1) | 1 (+0) | 1 (+0) | 4 (-5) |
| Stop-and-go (T3) | 0.97° | 82 (-78) | 5 (-19) | 5 (-18) | 9 (-23) | 179 (-179) |
| Exit queue (T5) | 0.63° | 40 (+36) | 7 (+13) | 4 (+5) | 5 (+7) | 27 (-26) |
| Congested slow flow (T6) | 0.93° | 40 (-15) | 7 (+3) | 5 (+2) | 7 (+3) | 56 (-59) |

**Sweep: portal speed drop (T1, no jitter), error at C [m], median:**

| drop | time in tunnel [s] | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|---|
| 0 km/h | 103 | 330 | 33 | 21 | 19 | 11 |
| 5 km/h | 103 | 332 | 34 | 21 | 19 | 27 |
| 10 km/h | 105 | 343 | 35 | 22 | 20 | 152 |
| 20 km/h | 110 | 393 | 55 | 26 | 24 | 346 |
| 30 km/h | 119 | 436 | 49 | 21 | 14 | 546 |

**Sweep: number of stops (T3), error at C [m], median:**

| stops | time in tunnel [s] | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|---|
| 0 | 237 | 1377 | 97 | 75 | 80 | 575 §4 |
| 1 | 293 | 1740 | 76 | 47 | 47 | ≥782 §7 |
| 2 | 324 | 2241 | 63 | 47 | 49 | ≥782 §10 |
| 4 | 420 | 3542 | 62 | 39 | 32 | ≥782 §10 |
