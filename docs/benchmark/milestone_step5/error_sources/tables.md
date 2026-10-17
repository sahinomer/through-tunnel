# Error-source benchmark: generated tables

 · commit `0b4ee46` · 2026-10-17 17:43 UTC · 18 conditions × 2 traffic cases × 20 runs. One scenario: the benchmark's 5 km tunnel, flat road. Each condition adds one error source to an error-free setup (paired: same drive and traffic per run). Cells: median (p90) error [m]. ✗n = n runs with a gross error (> 200 m in the tunnel or at C). † = reference estimator.

## Free flow: error 5 km into the tunnel

| condition | DR raw IMU (assumed aligned mount) | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + IMU Kalman filter (distance, speed, offset) | Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | Route + IMU Kalman filter + map curves | Route + last GPS speed (naive) | Route + vehicle speed (reference) † | Route + IMU + standstill oracle: speed reset ‡ | Route + IMU + standstill oracle: speed reset + offset ‡ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 1 (1) | 0 (1) | 2 (2) | 154 (253) ✗9 | 0 (0) | 0 (0) | 0 (0) |
| Accelerometer noise | 3 (7) | 7 (13) | 8 (14) | 9 (15) | 7 (22) | 5 (22) | 2 (4) | 154 (253) ✗9 | 0 (0) | 9 (15) | 9 (15) |
| Accelerometer bias | 1593 (2825) ✗19 | 0 (0) | 0 (1) | 0 (0) | 1 (1) | 0 (1) | 2 (2) | 154 (253) ✗9 | 0 (0) | 0 (0) | 0 (0) |
| Accelerometer bias drift | 108 (182) ✗2 | 81 (162) ✗2 | 83 (169) ✗2 | 90 (182) ✗2 | 92 (145) ✗2 | 92 (143) ✗2 | 9 (14) | 154 (253) ✗9 | 0 (0) | 90 (182) ✗2 | 90 (182) ✗2 |
| Gyroscope noise | 4 (8) | 8 (14) | 8 (16) | 0 (0) | 1 (1) | 0 (1) | 2 (3) | 154 (253) ✗9 | 0 (0) | 0 (0) | 0 (0) |
| Gyroscope bias | 487 (807) ✗16 | 0 (0) | 0 (0) | 0 (0) | 1 (1) | 0 (1) | 2 (2) | 154 (253) ✗9 | 0 (0) | 0 (0) | 0 (0) |
| Gyroscope bias drift | 35 (59) | 15 (42) | 15 (41) | 0 (0) | 0 (1) | 0 (1) | 3 (4) | 154 (253) ✗9 | 0 (0) | 0 (0) | 0 (0) |
| Tilted dashboard mount | 1805 (1936) ✗20 | 0 (0) | 0 (0) | 0 (0) | 1 (1) | 0 (1) | 2 (2) | 154 (253) ✗9 | 0 (0) | 0 (0) | 0 (0) |
| Calibration error: pitch 0.1° | 526 (559) ✗20 | 526 (559) ✗20 | 580 (622) ✗20 | 628 (675) ✗20 | 0 (1) | 0 (1) | 2 (2) | 154 (253) ✗9 | 0 (0) | 628 (675) ✗20 | 628 (675) ✗20 |
| Calibration error: pitch 0.5° | 2572 (2721) ✗20 | 2572 (2721) ✗20 | 2795 (2968) ✗20 | 2777 (2969) ✗20 | 0 (1) | 0 (1) | 2 (2) | 154 (253) ✗9 | 0 (0) | 2777 (2969) ✗20 | 2777 (2969) ✗20 |
| Calibration error: yaw 2° | 56 (62) | 56 (62) | 64 (71) | 67 (75) | 64 (85) | 0 (2) | 49 (52) | 154 (253) ✗9 | 0 (0) | 67 (75) | 67 (75) |
| Calibration error: roll 0.5° | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 1 (1) | 0 (1) | 2 (2) | 154 (253) ✗9 | 0 (0) | 0 (0) | 0 (0) |
| GPS position error | 3 (4) | 3 (4) | 3 (4) | 1 (3) | 1 (3) | 1 (3) | 2 (3) | 154 (254) ✗9 | 1 (3) | 1 (3) | 1 (3) |
| GPS speed noise | 54 (95) | 112 (244) ✗3 | 116 (228) ✗4 | 102 (245) ✗4 | 86 (185) ✗2 | 97 (200) ✗2 | 9 (17) | 214 (282) ✗12 | 4 (9) | 102 (245) ✗4 | 102 (245) ✗4 |
| GPS degradation before the portal (150 m, 8 m) | 121 (188) ✗1 | 121 (188) ✗1 | 6 (14) | 4 (8) | 4 (7) | 4 (8) | 2 (4) | 202 (353) ✗10 | 5 (9) | 4 (8) | 4 (8) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 140 (209) ✗4 | 170 (366) ✗7 | 129 (239) ✗3 | 133 (242) ✗7 | 31 (71) | 36 (86) | 3 (6) | 216 (412) ✗10 | 11 (25) | 133 (242) ✗7 | 133 (242) ✗7 |
| All realistic (= benchmark setting) | 1720 (3021) ✗20 | 167 (306) ✗8 | 117 (240) ✗4 | 103 (257) ✗4 | 80 (324) ✗4 | 84 (253) ✗4 | 12 (23) | 226 (462) ✗12 | 6 (17) | 103 (257) ✗4 | 103 (257) ✗4 |
| Hard: realistic + tilted mount + calibration error | 9815 (12486) ✗20 | 2601 (2711) ✗20 | 2786 (2961) ✗20 | 2760 (2961) ✗20 | 361 (584) ✗17 | 157 (309) ✗7 | 45 (64) | 226 (462) ✗12 | 6 (17) | 2760 (2961) ✗20 | 2760 (2961) ✗20 |

### Free flow: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Accelerometer noise | 0 | 1 | 2 | 4 | 6 | 9 | 258 s |
| Accelerometer bias | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Accelerometer bias drift | 1 | 3 | 14 | 29 | 57 | 90 | 258 s |
| Gyroscope noise | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Gyroscope bias | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Gyroscope bias drift | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Tilted dashboard mount | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Calibration error: pitch 0.1° | 13 | 36 | 118 | 239 | 407 | 628 | 258 s |
| Calibration error: pitch 0.5° | 65 | 181 | 581 | 1178 | 1970 | 2777 | 258 s |
| Calibration error: yaw 2° | 1 | 2 | 9 | 42 | 64 | 67 | 258 s |
| Calibration error: roll 0.5° | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| GPS position error | 1 | 1 | 1 | 1 | 1 | 1 | 258 s |
| GPS speed noise | 3 | 7 | 21 | 47 | 77 | 102 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 4 | 4 | 4 | 4 | 4 | 4 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 15 | 20 | 37 | 57 | 87 | 133 | 258 s |
| All realistic (= benchmark setting) | 6 | 11 | 24 | 47 | 70 | 103 | 258 s |
| Hard: realistic + tilted mount + calibration error | 63 | 181 | 581 | 1158 | 1941 | 2760 | 258 s |

### Free flow: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Accelerometer noise | 0 | 1 | 2 | 4 | 6 | 8 | 258 s |
| Accelerometer bias | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Accelerometer bias drift | 1 | 3 | 13 | 27 | 53 | 83 | 258 s |
| Gyroscope noise | 0 | 1 | 1 | 2 | 5 | 8 | 258 s |
| Gyroscope bias | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Gyroscope bias drift | 0 | 1 | 2 | 4 | 10 | 15 | 258 s |
| Tilted dashboard mount | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Calibration error: pitch 0.1° | 13 | 36 | 116 | 219 | 383 | 580 | 258 s |
| Calibration error: pitch 0.5° | 65 | 181 | 581 | 1095 | 1903 | 2795 | 258 s |
| Calibration error: yaw 2° | 1 | 2 | 9 | 40 | 62 | 64 | 258 s |
| Calibration error: roll 0.5° | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| GPS position error | 3 | 3 | 3 | 3 | 3 | 3 | 258 s |
| GPS speed noise | 4 | 9 | 25 | 48 | 80 | 116 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 7 | 7 | 7 | 6 | 6 | 6 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 19 | 26 | 41 | 61 | 92 | 129 | 258 s |
| All realistic (= benchmark setting) | 9 | 13 | 31 | 53 | 78 | 117 | 258 s |
| Hard: realistic + tilted mount + calibration error | 63 | 181 | 582 | 1072 | 1875 | 2786 | 258 s |

### Free flow: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.002 | 0.00 | 0.000 | 0.002 | 0.000 |
| Accelerometer noise | 0.02 | 0.001 | 0.013 | 0.00 | 0.003 | 0.002 | 0.003 |
| Accelerometer bias | 0.00 | 0.299 | 0.002 | 0.02 | 0.000 | 0.002 | 0.000 |
| Accelerometer bias drift | 0.17 | 0.015 | 0.021 | 0.00 | 0.016 | 0.002 | 0.016 |
| Gyroscope noise | 0.00 | 0.000 | 0.006 | 0.75 | 0.000 | 0.020 | 0.000 |
| Gyroscope bias | 0.00 | 0.000 | 0.002 | 0.08 | 0.000 | 0.002 | 0.000 |
| Gyroscope bias drift | 0.00 | 0.000 | 0.003 | 0.98 | 0.000 | 0.016 | 0.000 |
| Tilted dashboard mount | 0.00 | 0.000 | 0.002 | 0.00 | 0.000 | 0.002 | 0.000 |
| Calibration error: pitch 0.1° | 1.74 | 0.100 | 0.002 | 0.00 | 0.237 | 0.002 | 0.237 |
| Calibration error: pitch 0.5° | 8.70 | 0.500 | 0.002 | 0.00 | 1.186 | 0.002 | 1.186 |
| Calibration error: yaw 2° | 0.00 | 0.000 | 1.999 | 0.00 | 0.037 | 0.002 | 0.037 |
| Calibration error: roll 0.5° | 0.00 | 0.000 | 0.002 | 0.00 | 0.000 | 0.002 | 0.000 |
| GPS position error | 0.00 | 0.000 | 0.002 | 0.00 | 0.000 | 0.002 | 0.000 |
| GPS speed noise | 0.24 | 0.014 | 0.297 | 2.20 | 0.054 | 0.088 | 0.054 |
| GPS degradation before the portal (150 m, 8 m) | 0.00 | 0.000 | 0.002 | 0.00 | 0.000 | 0.002 | 0.000 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.33 | 0.019 | 0.056 | 0.00 | 0.100 | 0.084 | 0.100 |
| All realistic (= benchmark setting) | 0.22 | 0.281 | 0.316 | 1.74 | 0.047 | 0.097 | 0.047 |
| Hard: realistic + tilted mount + calibration error | 8.81 | 0.535 | 1.860 | 1.97 | 1.139 | 0.078 | 1.139 |

## Stop-and-go: error 5 km into the tunnel

| condition | DR raw IMU (assumed aligned mount) | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + IMU Kalman filter (distance, speed, offset) | Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | Route + IMU Kalman filter + map curves | Route + last GPS speed (naive) | Route + vehicle speed (reference) † | Route + IMU + standstill oracle: speed reset ‡ | Route + IMU + standstill oracle: speed reset + offset ‡ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 2 (3) | 2 (3) | 0 (0) | 0 (0) | 3 (7) | 3 (6) | 8 (11) | 782 (782) ✗20 | 0 (0) | 0 (0) | 0 (1) |
| Accelerometer noise | 12 (24) | 25 (86) | 24 (87) | 26 (94) | 14 (61) ✗2 | 13 (64) ✗2 | 7 (10) | 782 (782) ✗20 | 0 (0) | 11 (21) | 9 (20) |
| Accelerometer bias | 4155 (20879) ✗20 | 3 (3) | 1 (1) | 0 (0) | 4 (8) | 3 (6) | 8 (11) | 782 (782) ✗20 | 0 (0) | 0 (0) | 0 (1) |
| Accelerometer bias drift | 515 (1977) ✗13 | 328 (1926) ✗15 | 328 (1913) ✗15 | 353 (782) ✗15 | 306 (782) ✗14 | 308 (782) ✗13 | 27 (86) | 782 (782) ✗20 | 0 (0) | 271 (458) ✗11 | 67 (143) |
| Gyroscope noise | 5 (15) | 24 (38) | 25 (39) | 0 (0) | 3 (11) | 3 (6) | 8 (14) | 782 (782) ✗20 | 0 (0) | 0 (0) | 0 (1) |
| Gyroscope bias | 1309 (2476) ✗18 | 2 (3) | 0 (0) | 0 (0) | 3 (7) | 3 (6) | 8 (11) | 782 (782) ✗20 | 0 (0) | 0 (0) | 0 (1) |
| Gyroscope bias drift | 37 (172) ✗1 | 66 (163) ✗2 | 65 (162) ✗2 | 0 (0) | 4 (7) | 3 (6) | 10 (19) | 782 (782) ✗20 | 0 (0) | 0 (0) | 0 (1) |
| Tilted dashboard mount | 2003 (2982) ✗20 | 2 (3) | 0 (0) | 0 (0) | 3 (7) | 3 (6) | 8 (11) | 782 (782) ✗20 | 0 (0) | 0 (0) | 0 (1) |
| Calibration error: pitch 0.1° | 871 (1256) ✗20 | 871 (1256) ✗20 | 900 (1283) ✗20 | 977 (1376) ✗20 | 3 (7) | 3 (6) | 8 (11) | 782 (782) ✗20 | 0 (0) | 977 (1376) ✗20 | 130 (236) ✗5 |
| Calibration error: pitch 0.5° | 3272 (3621) ✗20 | 3272 (3621) ✗20 | 3364 (3756) ✗20 | 3354 (3745) ✗20 | 2 (6) | 3 (7) | 8 (11) | 782 (782) ✗20 | 0 (0) | 3354 (3745) ✗20 | 543 (931) ✗20 |
| Calibration error: yaw 2° | 70 (79) | 67 (78) | 90 (106) | 96 (114) | 203 (246) ✗10 | 2 (7) | 20 (30) | 782 (782) ✗20 | 0 (0) | 8 (16) | 9 (17) |
| Calibration error: roll 0.5° | 2 (3) | 2 (3) | 0 (0) | 0 (0) | 4 (8) | 3 (6) | 8 (10) | 782 (782) ✗20 | 0 (0) | 0 (0) | 0 (1) |
| GPS position error | 3 (5) | 3 (6) | 3 (4) | 1 (3) | 4 (7) | 3 (5) | 8 (11) | 782 (782) ✗20 | 1 (3) | 1 (3) | 1 (3) |
| GPS speed noise | 96 (220) ✗4 | 391 (1059) ✗15 | 386 (915) ✗14 | 393 (782) ✗14 | 172 (664) ✗9 | 175 (782) ✗9 | 6 (10) | 782 (782) ✗20 | 4 (9) | 120 (429) ✗8 | 27 (75) |
| GPS degradation before the portal (150 m, 8 m) | 159 (595) ✗8 | 159 (595) ✗8 | 7 (14) | 3 (12) | 6 (15) | 5 (12) | 8 (10) | 782 (782) ✗20 | 4 (13) | 3 (12) | 3 (11) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 181 (615) ✗8 | 316 (1072) ✗19 | 266 (1216) ✗13 | 289 (782) ✗13 | 57 (221) ✗3 | 75 (274) ✗4 | 7 (11) | 782 (782) ✗20 | 10 (36) | 227 (310) ✗11 | 34 (61) |
| All realistic (= benchmark setting) | 4481 (20810) ✗20 | 561 (2099) ✗18 | 420 (2355) ✗17 | 385 (782) ✗16 | 241 (782) ✗13 | 299 (782) ✗12 | 30 (94) ✗1 | 782 (782) ✗20 | 7 (17) | 131 (607) ✗9 | 103 (199) ✗2 |
| Hard: realistic + tilted mount + calibration error | 85684 (126598) ✗20 | 3267 (3646) ✗20 | 3399 (3768) ✗20 | 3390 (3752) ✗20 | 782 (782) ✗20 | 399 (782) ✗16 | 42 (295) ✗11 | 782 (782) ✗20 | 7 (17) | 3390 (3752) ✗20 | 543 (946) ✗20 |

### Stop-and-go: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| Accelerometer noise | 1 | 2 | 5 | 10 | 20 | 26 | 738 s |
| Accelerometer bias | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| Accelerometer bias drift | 4 | 19 | 59 | 155 | 261 | 353 | 738 s |
| Gyroscope noise | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| Gyroscope bias | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| Gyroscope bias drift | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| Tilted dashboard mount | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| Calibration error: pitch 0.1° | 55 | 133 | 322 | 540 | 748 | 977 | 738 s |
| Calibration error: pitch 0.5° | 276 | 632 | 1372 | 1938 | 2694 | 3354 | 738 s |
| Calibration error: yaw 2° | 3 | 6 | 18 | 65 | 94 | 96 | 738 s |
| Calibration error: roll 0.5° | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| GPS position error | 1 | 1 | 1 | 1 | 1 | 1 | 738 s |
| GPS speed noise | 7 | 22 | 94 | 166 | 259 | 393 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 3 | 3 | 3 | 3 | 3 | 3 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 16 | 45 | 92 | 170 | 242 | 289 | 738 s |
| All realistic (= benchmark setting) | 10 | 24 | 74 | 151 | 309 | 385 | 738 s |
| Hard: realistic + tilted mount + calibration error | 258 | 640 | 1369 | 1960 | 2700 | 3390 | 738 s |

### Stop-and-go: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| Accelerometer noise | 1 | 2 | 5 | 9 | 18 | 24 | 738 s |
| Accelerometer bias | 0 | 0 | 0 | 0 | 1 | 1 | 738 s |
| Accelerometer bias drift | 4 | 19 | 57 | 144 | 247 | 328 | 738 s |
| Gyroscope noise | 0 | 1 | 4 | 9 | 17 | 25 | 738 s |
| Gyroscope bias | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| Gyroscope bias drift | 0 | 1 | 7 | 22 | 47 | 65 | 738 s |
| Tilted dashboard mount | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| Calibration error: pitch 0.1° | 55 | 133 | 320 | 495 | 718 | 900 | 738 s |
| Calibration error: pitch 0.5° | 276 | 632 | 1373 | 1948 | 2674 | 3364 | 738 s |
| Calibration error: yaw 2° | 3 | 6 | 18 | 61 | 89 | 90 | 738 s |
| Calibration error: roll 0.5° | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| GPS position error | 3 | 3 | 3 | 3 | 3 | 3 | 738 s |
| GPS speed noise | 8 | 26 | 92 | 163 | 288 | 386 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 7 | 7 | 7 | 7 | 7 | 7 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 28 | 50 | 93 | 154 | 223 | 266 | 738 s |
| All realistic (= benchmark setting) | 12 | 26 | 79 | 159 | 325 | 420 | 738 s |
| Hard: realistic + tilted mount + calibration error | 258 | 640 | 1368 | 1965 | 2681 | 3399 | 738 s |

### Stop-and-go: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.002 | 0.00 | 0.003 | 0.002 | 0.003 |
| Accelerometer noise | 0.02 | 0.001 | 0.013 | 0.00 | 0.005 | 0.002 | 0.005 |
| Accelerometer bias | 0.00 | 0.299 | 0.002 | 0.02 | 0.003 | 0.002 | 0.003 |
| Accelerometer bias drift | 0.14 | 0.015 | 0.021 | 0.00 | 0.019 | 0.002 | 0.019 |
| Gyroscope noise | 0.00 | 0.000 | 0.006 | 0.75 | 0.003 | 0.019 | 0.003 |
| Gyroscope bias | 0.00 | 0.000 | 0.002 | 0.08 | 0.003 | 0.002 | 0.003 |
| Gyroscope bias drift | 0.00 | 0.000 | 0.003 | 0.97 | 0.003 | 0.017 | 0.003 |
| Tilted dashboard mount | 0.00 | 0.000 | 0.002 | 0.00 | 0.003 | 0.002 | 0.003 |
| Calibration error: pitch 0.1° | 1.74 | 0.100 | 0.002 | 0.00 | 0.269 | 0.002 | 0.269 |
| Calibration error: pitch 0.5° | 8.70 | 0.500 | 0.002 | 0.00 | 1.332 | 0.002 | 1.332 |
| Calibration error: yaw 2° | 0.00 | 0.000 | 1.999 | 0.00 | 0.038 | 0.002 | 0.038 |
| Calibration error: roll 0.5° | 0.00 | 0.000 | 0.002 | 0.00 | 0.003 | 0.002 | 0.003 |
| GPS position error | 0.00 | 0.000 | 0.002 | 0.00 | 0.003 | 0.002 | 0.003 |
| GPS speed noise | 0.24 | 0.014 | 0.297 | 2.20 | 0.058 | 0.090 | 0.058 |
| GPS degradation before the portal (150 m, 8 m) | 0.00 | 0.000 | 0.002 | 0.00 | 0.003 | 0.002 | 0.003 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.33 | 0.019 | 0.056 | 0.00 | 0.107 | 0.084 | 0.107 |
| All realistic (= benchmark setting) | 0.24 | 0.281 | 0.316 | 2.03 | 0.055 | 0.106 | 0.055 |
| Hard: realistic + tilted mount + calibration error | 8.81 | 0.535 | 1.860 | 1.86 | 1.270 | 0.079 | 1.270 |
