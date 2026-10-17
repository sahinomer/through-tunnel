# Yaw diagnostic: tables

Commit `c9eb9ec`, 2026-10-17 10:44 UTC; 20 seeds per case. Error at C, median (p90) [m], ✗ = gross errors (> 200 m in the tunnel or at C). +yaw = the yaw leak removed from the forward channel using the truth (counterfactual, not an estimator).

Rerun check against the milestone (unmodified variants): error_sources: 480 runs, max difference 0.0e+00 m; benchmark: 240 runs, max difference 0.0e+00 m

## 1. Error at C

| case | source | route_imu | route_imu+yaw | route_kf | route_kf+yaw_approach | route_kf+yaw_tunnel | route_kf+yaw |
|---|---|---|---|---|---|---|---|
| floor/free | error_sources | 0 (0) ✗0 | 0 (0) ✗0 | 1 (1) ✗0 | 1 (2) ✗0 | 0 (1) ✗0 | 1 (2) ✗0 |
| floor/stop_and_go | error_sources | 0 (0) ✗0 | 0 (0) ✗0 | 3 (7) ✗0 | 7 (14) ✗0 | 3 (7) ✗0 | 7 (14) ✗0 |
| cal_pitch_0.1/free | error_sources | 628 (675) ✗20 | 628 (675) ✗20 | 3 (4) ✗0 | 3 (3) ✗0 | 3 (4) ✗0 | 3 (3) ✗0 |
| cal_pitch_0.1/stop_and_go | error_sources | 977 (1376) ✗20 | 977 (1376) ✗20 | 5 (6) ✗0 | 4 (6) ✗0 | 5 (6) ✗0 | 4 (6) ✗0 |
| cal_yaw_2/free | error_sources | 67 (75) ✗0 | 0 (1) ✗0 | 65 (85) ✗0 | 59 (66) ✗0 | 117 (139) ✗0 | 1 (2) ✗0 |
| cal_yaw_2/stop_and_go | error_sources | 96 (114) ✗0 | 3 (5) ✗0 | 204 (247) ✗10 | 78 (106) ✗0 | 211 (254) ✗11 | 11 (26) ✗0 |
| hard/free | error_sources | 2760 (2960) ✗20 | 2821 (3034) ✗20 | 255 (430) ✗12 | 124 (289) ✗8 | 195 (393) ✗10 | 159 (360) ✗8 |
| hard/stop_and_go | error_sources | 3390 (3752) ✗20 | 3392 (3754) ✗20 | 782 (782) ✗18 | 358 (782) ✗15 | 782 (782) ✗18 | 360 (782) ✗15 |
| gps_speed/free | error_sources | 102 (245) ✗4 | 82 (273) ✗3 | 85 (182) ✗2 | 54 (129) ✗1 | 77 (181) ✗2 | 58 (134) ✗1 |
| gps_speed/stop_and_go | error_sources | 393 (782) ✗14 | 399 (782) ✗14 | 182 (604) ✗9 | 115 (543) ✗8 | 179 (585) ✗9 | 120 (550) ✗8 |
| realistic/free | error_sources | 103 (257) ✗4 | 82 (244) ✗4 | 85 (283) ✗4 | 102 (219) ✗3 | 95 (253) ✗4 | 107 (213) ✗3 |
| realistic/stop_and_go | error_sources | 385 (782) ✗16 | 369 (782) ✗16 | 188 (782) ✗9 | 274 (782) ✗15 | 187 (782) ✗9 | 275 (782) ✗15 |
| ladder_2km/free | benchmark | 25 (46) ✗0 | 23 (47) ✗0 | 20 (72) ✗0 | 17 (47) ✗0 | 18 (68) ✗0 | 19 (46) ✗0 |
| ladder_2km/stop_and_go | benchmark | 87 (451) ✗4 | 86 (451) ✗4 | 51 (240) ✗3 | 49 (387) ✗3 | 49 (241) ✗3 | 49 (388) ✗3 |
| ladder_3km/free | benchmark | 46 (77) ✗0 | 43 (79) ✗0 | 28 (134) ✗0 | 34 (92) ✗0 | 27 (124) ✗0 | 38 (90) ✗0 |
| ladder_3km/stop_and_go | benchmark | 167 (782) ✗8 | 161 (782) ✗8 | 98 (450) ✗6 | 95 (644) ✗8 | 95 (448) ✗6 | 99 (647) ✗8 |
| ladder_5km/free | benchmark | 103 (257) ✗4 | 82 (244) ✗4 | 85 (283) ✗4 | 102 (219) ✗3 | 95 (253) ✗4 | 107 (213) ✗3 |
| ladder_5km/stop_and_go | benchmark | 385 (782) ✗16 | 369 (782) ✗16 | 188 (782) ✗9 | 274 (782) ✗15 | 187 (782) ✗9 | 275 (782) ✗15 |

## 2. Yaw residual and forward offset at GPS loss (route_kf)

|yaw| = yaw residual of the stage's forward axis at loss (calibration error included). b error = filter offset after the last fix before loss − true offset at loss. f_lat rms = lateral specific force over the last 60 s before loss.

| case | |yaw| median (p90) [deg] | f_lat rms median [m/s²] | |b error| median (p90) [mg] | same, leak removed on the approach |
|---|---|---|---|---|
| floor/free | 0.00 (0.00) | 0.79 | 0.00 (0.00) | 0.00 (0.00) |
| floor/stop_and_go | 0.00 (0.00) | 0.78 | 0.00 (0.00) | 0.00 (0.00) |
| cal_pitch_0.1/free | 0.00 (0.00) | 0.79 | 0.01 (0.01) | 0.01 (0.01) |
| cal_pitch_0.1/stop_and_go | 0.00 (0.00) | 0.78 | 0.01 (0.01) | 0.01 (0.01) |
| cal_yaw_2/free | 2.00 (2.00) | 0.79 | 0.37 (0.41) | 0.00 (0.01) |
| cal_yaw_2/stop_and_go | 2.00 (2.00) | 0.78 | 0.37 (0.41) | 0.00 (0.01) |
| hard/free | 1.86 (2.52) | 0.79 | 0.47 (0.86) | 0.43 (0.81) |
| hard/stop_and_go | 1.86 (2.52) | 0.78 | 0.43 (0.94) | 0.44 (0.76) |
| gps_speed/free | 0.30 (0.65) | 0.79 | 0.19 (0.43) | 0.13 (0.36) |
| gps_speed/stop_and_go | 0.30 (0.65) | 0.78 | 0.19 (0.43) | 0.13 (0.36) |
| realistic/free | 0.32 (0.68) | 0.79 | 0.18 (0.69) | 0.25 (0.51) |
| realistic/stop_and_go | 0.32 (0.68) | 0.78 | 0.16 (0.64) | 0.21 (0.49) |
| ladder_2km/free | 0.32 (0.68) | 0.79 | 0.18 (0.69) | 0.25 (0.51) |
| ladder_2km/stop_and_go | 0.32 (0.68) | 0.78 | 0.16 (0.64) | 0.21 (0.49) |
| ladder_3km/free | 0.32 (0.68) | 0.79 | 0.18 (0.69) | 0.25 (0.51) |
| ladder_3km/stop_and_go | 0.32 (0.68) | 0.78 | 0.16 (0.64) | 0.21 (0.49) |
| ladder_5km/free | 0.32 (0.68) | 0.79 | 0.18 (0.69) | 0.25 (0.51) |
| ladder_5km/stop_and_go | 0.32 (0.68) | 0.78 | 0.16 (0.64) | 0.21 (0.49) |

## 3. Free-flow tails: the three worst route_kf runs per free-flow case

| case | seed | |yaw| [deg] | b error [mg] | route_imu | route_kf | route_kf+yaw_approach | route_kf+yaw |
|---|---|---|---|---|---|---|---|
| floor/free | 8 | 0.00 | -0.00 | 0 | 1 | 1 | 1 |
| floor/free | 6 | 0.00 | -0.00 | 0 | 1 | 1 | 1 |
| floor/free | 15 | 0.00 | -0.00 | 0 | 1 | 2 | 2 |
| cal_pitch_0.1/free | 16 | 0.00 | +0.01 | 623 | 4 | 2 | 2 |
| cal_pitch_0.1/free | 5 | 0.00 | +0.01 | 657 | 4 | 3 | 3 |
| cal_pitch_0.1/free | 2 | 0.00 | +0.01 | 634 | 4 | 3 | 3 |
| cal_yaw_2/free | 12 | 2.00 | +0.43 | 68 | 101 | 60 | 1 |
| cal_yaw_2/free | 3 | 2.00 | +0.45 | 67 | 88 | 60 | 1 |
| cal_yaw_2/free | 7 | 2.00 | +0.39 | 62 | 85 | 54 | 1 |
| hard/free | 19 | 2.26 | -1.12 | 2466 | 569 | 145 | 89 |
| hard/free | 6 | 1.81 | -1.11 | 2389 | 517 | 262 | 211 |
| hard/free | 4 | 1.35 | -0.55 | 2591 | 421 | 208 | 169 |
| gps_speed/free | 13 | 1.03 | +0.54 | 95 | 270 | 54 | 20 |
| gps_speed/free | 18 | 0.12 | +0.54 | 269 | 216 | 186 | 189 |
| gps_speed/free | 4 | 0.60 | +0.42 | 386 | 178 | 35 | 17 |
| realistic/free | 11 | 1.09 | -0.38 | 9 | 381 | 321 | 292 |
| realistic/free | 18 | 0.18 | +0.74 | 375 | 323 | 303 | 308 |
| realistic/free | 13 | 1.04 | +0.64 | 114 | 278 | 69 | 35 |
| ladder_2km/free | 11 | 1.09 | -0.38 | 10 | 82 | 66 | 60 |
| ladder_2km/free | 18 | 0.18 | +0.74 | 87 | 76 | 73 | 74 |
| ladder_2km/free | 13 | 1.04 | +0.64 | 41 | 71 | 28 | 24 |
| ladder_3km/free | 11 | 1.09 | -0.38 | 13 | 159 | 131 | 120 |
| ladder_3km/free | 18 | 0.18 | +0.74 | 161 | 140 | 133 | 134 |
| ladder_3km/free | 13 | 1.04 | +0.64 | 71 | 133 | 49 | 39 |
| ladder_5km/free | 11 | 1.09 | -0.38 | 9 | 381 | 321 | 292 |
| ladder_5km/free | 18 | 0.18 | +0.74 | 375 | 323 | 303 | 308 |
| ladder_5km/free | 13 | 1.04 | +0.64 | 114 | 278 | 69 | 35 |
