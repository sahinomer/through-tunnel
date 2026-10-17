# Error-source benchmark: generated tables

 · commit `74d17ed+dirty` · 2026-10-17 12:15 UTC · 8 conditions × 2 traffic cases × 20 runs. One scenario: the benchmark's 5 km tunnel, flat road. Each condition adds one error source to an error-free setup (paired: same drive and traffic per run). Cells: median (p90) error [m]. ✗n = n runs with a gross error (> 200 m in the tunnel or at C). † = reference estimator.

## Free flow: error 5 km into the tunnel

| condition | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + IMU Kalman filter (distance, speed, offset) | Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | Route + vehicle speed (reference) † | Route + IMU + standstill oracle: speed reset ‡ | Route + IMU + standstill oracle: speed reset + offset ‡ |
|---|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 (0) | 0 (0) | 0 (0) | 1 (1) | 0 (1) | 0 (0) | 0 (0) | 0 (0) |
| Calibration error: pitch 0.1° | 526 (559) ✗20 | 580 (622) ✗20 | 628 (675) ✗20 | 3 (4) | 0 (1) | 0 (0) | 628 (675) ✗20 | 628 (675) ✗20 |
| Calibration error: yaw 2° | 56 (62) | 64 (71) | 67 (75) | 65 (85) | 0 (2) | 0 (0) | 67 (75) | 67 (75) |
| GPS speed noise | 112 (244) ✗3 | 116 (228) ✗4 | 102 (245) ✗4 | 85 (182) ✗2 | 97 (215) ✗3 | 4 (9) | 102 (245) ✗4 | 102 (245) ✗4 |
| GPS degradation before the portal (150 m, 8 m) | 121 (188) ✗1 | 6 (14) | 4 (8) | 4 (7) | 4 (8) | 5 (9) | 4 (8) | 4 (8) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 170 (366) ✗7 | 129 (239) ✗3 | 133 (242) ✗7 | 31 (71) | 36 (86) | 11 (25) | 133 (242) ✗7 | 133 (242) ✗7 |
| All realistic (= benchmark setting) | 167 (306) ✗8 | 117 (240) ✗4 | 103 (257) ✗4 | 85 (283) ✗4 | 89 (244) ✗3 | 6 (17) | 103 (257) ✗4 | 103 (257) ✗4 |
| Hard: realistic + tilted mount + calibration error | 2601 (2711) ✗20 | 2786 (2961) ✗20 | 2760 (2961) ✗20 | 255 (430) ✗12 | 204 (400) ✗11 | 6 (17) | 2760 (2961) ✗20 | 2760 (2961) ✗20 |

### Free flow: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Calibration error: pitch 0.1° | 13 | 36 | 118 | 239 | 407 | 628 | 258 s |
| Calibration error: yaw 2° | 1 | 2 | 9 | 42 | 64 | 67 | 258 s |
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
| Calibration error: pitch 0.1° | 13 | 36 | 116 | 219 | 383 | 580 | 258 s |
| Calibration error: yaw 2° | 1 | 2 | 9 | 40 | 62 | 64 | 258 s |
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
| Calibration error: pitch 0.1° | 1.74 | 0.100 | 0.002 | 0.00 | 0.237 | 0.002 | 0.237 |
| Calibration error: yaw 2° | 0.00 | 0.000 | 1.999 | 0.00 | 0.037 | 0.002 | 0.037 |
| GPS speed noise | 0.24 | 0.014 | 0.297 | 2.20 | 0.054 | 0.088 | 0.054 |
| GPS degradation before the portal (150 m, 8 m) | 0.00 | 0.000 | 0.002 | 0.00 | 0.000 | 0.002 | 0.000 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.33 | 0.019 | 0.056 | 0.00 | 0.100 | 0.084 | 0.100 |
| All realistic (= benchmark setting) | 0.22 | 0.281 | 0.316 | 1.74 | 0.047 | 0.097 | 0.047 |
| Hard: realistic + tilted mount + calibration error | 8.81 | 0.535 | 1.860 | 1.97 | 1.139 | 0.078 | 1.139 |

## Stop-and-go: error 5 km into the tunnel

| condition | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + IMU Kalman filter (distance, speed, offset) | Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | Route + vehicle speed (reference) † | Route + IMU + standstill oracle: speed reset ‡ | Route + IMU + standstill oracle: speed reset + offset ‡ |
|---|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 2 (3) | 0 (0) | 0 (0) | 3 (7) | 3 (6) | 0 (0) | 0 (0) | 0 (1) |
| Calibration error: pitch 0.1° | 871 (1256) ✗20 | 900 (1283) ✗20 | 977 (1376) ✗20 | 5 (6) | 2 (5) | 0 (0) | 977 (1376) ✗20 | 130 (236) ✗5 |
| Calibration error: yaw 2° | 67 (78) | 90 (106) | 96 (114) | 204 (247) ✗10 | 2 (8) | 0 (0) | 8 (16) | 9 (17) |
| GPS speed noise | 391 (1059) ✗15 | 386 (915) ✗14 | 393 (782) ✗14 | 182 (604) ✗9 | 178 (782) ✗9 | 4 (9) | 120 (429) ✗8 | 27 (75) |
| GPS degradation before the portal (150 m, 8 m) | 159 (595) ✗8 | 7 (14) | 3 (12) | 6 (15) | 5 (12) | 4 (13) | 3 (12) | 3 (11) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 316 (1072) ✗19 | 266 (1216) ✗13 | 289 (782) ✗13 | 57 (220) ✗3 | 75 (272) ✗4 | 10 (36) | 227 (310) ✗11 | 34 (61) |
| All realistic (= benchmark setting) | 561 (2099) ✗18 | 420 (2355) ✗17 | 385 (782) ✗16 | 188 (782) ✗9 | 402 (782) ✗12 | 7 (17) | 131 (607) ✗9 | 103 (199) ✗2 |
| Hard: realistic + tilted mount + calibration error | 3267 (3646) ✗20 | 3399 (3768) ✗20 | 3390 (3752) ✗20 | 782 (782) ✗18 | 403 (782) ✗17 | 7 (17) | 3390 (3752) ✗20 | 543 (946) ✗20 |

### Stop-and-go: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| Calibration error: pitch 0.1° | 55 | 133 | 322 | 540 | 748 | 977 | 738 s |
| Calibration error: yaw 2° | 3 | 6 | 18 | 65 | 94 | 96 | 738 s |
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
| Calibration error: pitch 0.1° | 55 | 133 | 320 | 495 | 718 | 900 | 738 s |
| Calibration error: yaw 2° | 3 | 6 | 18 | 61 | 89 | 90 | 738 s |
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
| Calibration error: pitch 0.1° | 1.74 | 0.100 | 0.002 | 0.00 | 0.269 | 0.002 | 0.269 |
| Calibration error: yaw 2° | 0.00 | 0.000 | 1.999 | 0.00 | 0.038 | 0.002 | 0.038 |
| GPS speed noise | 0.24 | 0.014 | 0.297 | 2.20 | 0.058 | 0.090 | 0.058 |
| GPS degradation before the portal (150 m, 8 m) | 0.00 | 0.000 | 0.002 | 0.00 | 0.003 | 0.002 | 0.003 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.33 | 0.019 | 0.056 | 0.00 | 0.107 | 0.084 | 0.107 |
| All realistic (= benchmark setting) | 0.24 | 0.281 | 0.316 | 2.03 | 0.055 | 0.106 | 0.055 |
| Hard: realistic + tilted mount + calibration error | 8.81 | 0.535 | 1.860 | 1.86 | 1.270 | 0.079 | 1.270 |
