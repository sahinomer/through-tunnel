# Error-source benchmark: generated tables

Error sources: one at a time, before estimator work · commit `e69543f` · 2026-10-15 15:54 UTC · 18 conditions × 2 traffic cases × 20 runs. One scenario: the benchmark's 5 km tunnel, flat road. Each condition adds one error source to an error-free setup (paired: same drive and traffic per run). Cells: median (p90) error [m]. ✗n = n runs with a gross error (> 200 m in the tunnel or at C). † = reference estimator.

## Free flow: error 5 km into the tunnel

| condition | DR raw IMU (assumed aligned mount) | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + last GPS speed (naive) | Route + vehicle speed (reference) † |
|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 154 (253) ✗9 | 0 (0) |
| Accelerometer noise | 3 (7) | 7 (13) | 7 (13) | 7 (15) | 154 (253) ✗9 | 0 (0) |
| Accelerometer bias | 1593 (2825) ✗19 | 0 (0) | 0 (0) | 0 (0) | 154 (253) ✗9 | 0 (0) |
| Accelerometer bias drift | 108 (182) ✗2 | 77 (155) ✗2 | 78 (157) ✗2 | 85 (169) ✗2 | 154 (253) ✗9 | 0 (0) |
| Gyroscope noise | 4 (8) | 8 (14) | 8 (16) | 0 (0) | 154 (253) ✗9 | 0 (0) |
| Gyroscope bias | 487 (807) ✗16 | 0 (0) | 0 (0) | 0 (0) | 154 (253) ✗9 | 0 (0) |
| Gyroscope bias drift | 35 (59) | 15 (40) | 15 (42) | 0 (0) | 154 (253) ✗9 | 0 (0) |
| Tilted dashboard mount | 1805 (1936) ✗20 | 0 (0) | 0 (0) | 0 (0) | 154 (253) ✗9 | 0 (0) |
| Calibration error: pitch 0.1° | 526 (559) ✗20 | 526 (559) ✗20 | 542 (576) ✗20 | 588 (625) ✗20 | 154 (253) ✗9 | 0 (0) |
| Calibration error: pitch 0.5° | 2572 (2721) ✗20 | 2572 (2721) ✗20 | 2643 (2791) ✗20 | 2617 (2777) ✗20 | 154 (253) ✗9 | 0 (0) |
| Calibration error: yaw 2° | 56 (62) | 56 (62) | 57 (63) | 58 (66) | 154 (253) ✗9 | 0 (0) |
| Calibration error: roll 0.5° | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 154 (253) ✗9 | 0 (0) |
| GPS position error | 3 (4) | 3 (4) | 3 (4) | 1 (3) | 154 (254) ✗9 | 1 (3) |
| GPS speed noise | 54 (95) | 117 (223) ✗3 | 95 (174) ✗2 | 98 (185) ✗2 | 214 (282) ✗12 | 4 (9) |
| GPS degradation before the portal (150 m, 8 m) | 121 (188) ✗1 | 264 (457) ✗13 | 170 (317) ✗8 | 184 (344) ✗9 | 202 (353) ✗10 | 5 (9) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 140 (209) ✗4 | 286 (538) ✗14 | 175 (383) ✗9 | 188 (412) ✗9 | 216 (412) ✗10 | 11 (25) |
| All realistic (= benchmark setting) | 1720 (3021) ✗20 | 316 (512) ✗16 | 217 (393) ✗11 | 231 (420) ✗11 | 226 (462) ✗12 | 6 (17) |
| Hard: realistic + tilted mount + calibration error | 9815 (12486) ✗20 | 2518 (2947) ✗20 | 2640 (2835) ✗20 | 2610 (2828) ✗20 | 226 (462) ✗12 | 6 (17) |

### Free flow: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Accelerometer noise | 0 | 0 | 2 | 3 | 5 | 7 | 258 s |
| Accelerometer bias | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Accelerometer bias drift | 1 | 2 | 12 | 26 | 54 | 85 | 258 s |
| Gyroscope noise | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Gyroscope bias | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Gyroscope bias drift | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Tilted dashboard mount | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Calibration error: pitch 0.1° | 8 | 28 | 101 | 215 | 375 | 588 | 258 s |
| Calibration error: pitch 0.5° | 42 | 139 | 499 | 1066 | 1813 | 2617 | 258 s |
| Calibration error: yaw 2° | 0 | 0 | 6 | 37 | 58 | 58 | 258 s |
| Calibration error: roll 0.5° | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| GPS position error | 1 | 1 | 1 | 1 | 1 | 1 | 258 s |
| GPS speed noise | 2 | 6 | 19 | 37 | 69 | 98 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 6 | 12 | 36 | 73 | 123 | 184 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 13 | 17 | 41 | 74 | 123 | 188 | 258 s |
| All realistic (= benchmark setting) | 5 | 15 | 38 | 84 | 137 | 231 | 258 s |
| Hard: realistic + tilted mount + calibration error | 44 | 145 | 501 | 1057 | 1801 | 2610 | 258 s |

### Free flow: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Accelerometer noise | 0 | 0 | 2 | 3 | 5 | 7 | 258 s |
| Accelerometer bias | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Accelerometer bias drift | 1 | 2 | 12 | 24 | 51 | 78 | 258 s |
| Gyroscope noise | 0 | 0 | 1 | 3 | 5 | 8 | 258 s |
| Gyroscope bias | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Gyroscope bias drift | 0 | 0 | 2 | 4 | 9 | 15 | 258 s |
| Tilted dashboard mount | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| Calibration error: pitch 0.1° | 8 | 28 | 99 | 197 | 353 | 542 | 258 s |
| Calibration error: pitch 0.5° | 42 | 139 | 497 | 985 | 1761 | 2643 | 258 s |
| Calibration error: yaw 2° | 0 | 0 | 6 | 36 | 56 | 57 | 258 s |
| Calibration error: roll 0.5° | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| GPS position error | 3 | 3 | 3 | 3 | 3 | 3 | 258 s |
| GPS speed noise | 3 | 7 | 22 | 37 | 66 | 95 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 9 | 16 | 36 | 66 | 115 | 170 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 20 | 28 | 51 | 69 | 118 | 175 | 258 s |
| All realistic (= benchmark setting) | 14 | 18 | 39 | 79 | 139 | 217 | 258 s |
| Hard: realistic + tilted mount + calibration error | 45 | 145 | 499 | 972 | 1745 | 2640 | 258 s |

### Free flow: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.003 | 0.01 | 0.000 | 0.000 | 0.000 |
| Accelerometer noise | 0.02 | 0.001 | 0.013 | 0.01 | 0.001 | 0.000 | 0.001 |
| Accelerometer bias | 0.00 | 0.299 | 0.003 | 0.00 | 0.000 | 0.000 | 0.000 |
| Accelerometer bias drift | 0.15 | 0.015 | 0.023 | 0.01 | 0.006 | 0.000 | 0.006 |
| Gyroscope noise | 0.00 | 0.000 | 0.004 | 0.78 | 0.000 | 0.009 | 0.000 |
| Gyroscope bias | 0.00 | 0.000 | 0.002 | 0.07 | 0.000 | 0.000 | 0.000 |
| Gyroscope bias drift | 0.00 | 0.000 | 0.002 | 0.85 | 0.000 | 0.007 | 0.000 |
| Tilted dashboard mount | 0.00 | 0.000 | 0.003 | 0.01 | 0.000 | 0.000 | 0.000 |
| Calibration error: pitch 0.1° | 1.74 | 0.100 | 0.003 | 0.01 | 0.079 | 0.000 | 0.079 |
| Calibration error: pitch 0.5° | 8.70 | 0.500 | 0.003 | 0.01 | 0.393 | 0.000 | 0.393 |
| Calibration error: yaw 2° | 0.00 | 0.000 | 2.002 | 0.01 | 0.004 | 0.000 | 0.004 |
| Calibration error: roll 0.5° | 0.00 | 0.000 | 0.003 | 0.01 | 0.000 | 0.000 | 0.000 |
| GPS position error | 0.00 | 0.000 | 0.003 | 0.01 | 0.000 | 0.000 | 0.000 |
| GPS speed noise | 0.23 | 0.013 | 0.292 | 1.66 | 0.048 | 0.106 | 0.048 |
| GPS degradation before the portal (150 m, 8 m) | 0.50 | 0.029 | 0.003 | 0.02 | 0.117 | 0.129 | 0.117 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.55 | 0.032 | 0.050 | 0.17 | 0.144 | 0.182 | 0.144 |
| All realistic (= benchmark setting) | 0.60 | 0.298 | 0.306 | 1.96 | 0.112 | 0.172 | 0.112 |
| Hard: realistic + tilted mount + calibration error | 8.83 | 0.500 | 1.874 | 2.45 | 0.403 | 0.178 | 0.403 |

## Stop-and-go: error 5 km into the tunnel

| condition | DR raw IMU (assumed aligned mount) | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + last GPS speed (naive) | Route + vehicle speed (reference) † |
|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 2 (3) | 13 (16) | 12 (15) | 13 (17) | 782 (782) ✗20 | 0 (0) |
| Accelerometer noise | 12 (24) | 25 (86) | 26 (87) | 28 (94) | 782 (782) ✗20 | 0 (0) |
| Accelerometer bias | 4155 (20879) ✗20 | 12 (16) | 12 (15) | 13 (16) | 782 (782) ✗20 | 0 (0) |
| Accelerometer bias drift | 515 (1977) ✗13 | 328 (1910) ✗15 | 328 (1914) ✗15 | 354 (782) ✗15 | 782 (782) ✗20 | 0 (0) |
| Gyroscope noise | 5 (15) | 27 (37) | 26 (36) | 13 (16) | 782 (782) ✗20 | 0 (0) |
| Gyroscope bias | 1309 (2476) ✗18 | 12 (17) | 12 (16) | 13 (18) | 782 (782) ✗20 | 0 (0) |
| Gyroscope bias drift | 37 (172) ✗1 | 68 (165) ✗2 | 67 (165) ✗2 | 13 (17) | 782 (782) ✗20 | 0 (0) |
| Tilted dashboard mount | 2003 (2982) ✗20 | 13 (16) | 12 (15) | 13 (17) | 782 (782) ✗20 | 0 (0) |
| Calibration error: pitch 0.1° | 871 (1256) ✗20 | 869 (1253) ✗20 | 877 (1260) ✗20 | 953 (1354) ✗20 | 782 (782) ✗20 | 0 (0) |
| Calibration error: pitch 0.5° | 3272 (3621) ✗20 | 3272 (3621) ✗20 | 3297 (3652) ✗20 | 3290 (3642) ✗20 | 782 (782) ✗20 | 0 (0) |
| Calibration error: yaw 2° | 70 (79) | 76 (86) | 79 (89) | 82 (95) | 782 (782) ✗20 | 0 (0) |
| Calibration error: roll 0.5° | 2 (3) | 13 (16) | 12 (15) | 13 (17) | 782 (782) ✗20 | 0 (0) |
| GPS position error | 3 (5) | 13 (18) | 12 (17) | 13 (18) | 782 (782) ✗20 | 1 (3) |
| GPS speed noise | 96 (220) ✗4 | 301 (898) ✗13 | 210 (829) ✗10 | 196 (782) ✗10 | 782 (782) ✗20 | 4 (9) |
| GPS degradation before the portal (150 m, 8 m) | 159 (595) ✗8 | 435 (1892) ✗15 | 325 (1618) ✗13 | 354 (782) ✗13 | 782 (782) ✗20 | 4 (13) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 181 (615) ✗8 | 472 (2097) ✗17 | 337 (1762) ✗13 | 373 (782) ✗14 | 782 (782) ✗20 | 10 (36) |
| All realistic (= benchmark setting) | 4481 (20810) ✗20 | 562 (3914) ✗19 | 470 (3314) ✗17 | 482 (804) ✗16 | 782 (782) ✗20 | 7 (17) |
| Hard: realistic + tilted mount + calibration error | 85684 (126598) ✗20 | 3260 (3656) ✗20 | 3294 (3669) ✗20 | 3277 (3654) ✗20 | 782 (782) ✗20 | 7 (17) |

### Stop-and-go: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 1 | 3 | 5 | 9 | 13 | 738 s |
| Accelerometer noise | 1 | 2 | 6 | 13 | 22 | 28 | 738 s |
| Accelerometer bias | 0 | 1 | 3 | 5 | 9 | 13 | 738 s |
| Accelerometer bias drift | 4 | 15 | 56 | 152 | 287 | 354 | 738 s |
| Gyroscope noise | 0 | 1 | 3 | 5 | 9 | 13 | 738 s |
| Gyroscope bias | 0 | 1 | 2 | 5 | 9 | 13 | 738 s |
| Gyroscope bias drift | 0 | 1 | 3 | 5 | 9 | 13 | 738 s |
| Tilted dashboard mount | 0 | 1 | 3 | 5 | 9 | 13 | 738 s |
| Calibration error: pitch 0.1° | 43 | 114 | 300 | 516 | 727 | 953 | 738 s |
| Calibration error: pitch 0.5° | 215 | 557 | 1290 | 1877 | 2627 | 3290 | 738 s |
| Calibration error: yaw 2° | 1 | 2 | 10 | 53 | 80 | 82 | 738 s |
| Calibration error: roll 0.5° | 0 | 1 | 3 | 5 | 9 | 13 | 738 s |
| GPS position error | 1 | 2 | 3 | 6 | 9 | 13 | 738 s |
| GPS speed noise | 6 | 20 | 54 | 92 | 139 | 196 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 16 | 33 | 87 | 185 | 261 | 354 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 16 | 45 | 98 | 192 | 272 | 373 | 738 s |
| All realistic (= benchmark setting) | 25 | 55 | 126 | 210 | 340 | 482 | 738 s |
| Hard: realistic + tilted mount + calibration error | 195 | 550 | 1294 | 1872 | 2652 | 3277 | 738 s |

### Stop-and-go: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 1 | 3 | 5 | 9 | 12 | 738 s |
| Accelerometer noise | 1 | 2 | 6 | 12 | 21 | 26 | 738 s |
| Accelerometer bias | 0 | 1 | 3 | 5 | 8 | 12 | 738 s |
| Accelerometer bias drift | 4 | 15 | 55 | 141 | 271 | 328 | 738 s |
| Gyroscope noise | 0 | 1 | 5 | 10 | 18 | 26 | 738 s |
| Gyroscope bias | 0 | 1 | 2 | 5 | 8 | 12 | 738 s |
| Gyroscope bias drift | 0 | 2 | 10 | 24 | 45 | 67 | 738 s |
| Tilted dashboard mount | 0 | 1 | 3 | 5 | 9 | 12 | 738 s |
| Calibration error: pitch 0.1° | 43 | 114 | 297 | 474 | 697 | 877 | 738 s |
| Calibration error: pitch 0.5° | 215 | 557 | 1290 | 1883 | 2602 | 3297 | 738 s |
| Calibration error: yaw 2° | 1 | 2 | 10 | 51 | 78 | 79 | 738 s |
| Calibration error: roll 0.5° | 0 | 1 | 3 | 5 | 9 | 12 | 738 s |
| GPS position error | 3 | 3 | 4 | 6 | 9 | 12 | 738 s |
| GPS speed noise | 7 | 20 | 55 | 93 | 143 | 210 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 17 | 35 | 87 | 173 | 247 | 325 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 32 | 54 | 103 | 181 | 242 | 337 | 738 s |
| All realistic (= benchmark setting) | 27 | 57 | 132 | 207 | 339 | 470 | 738 s |
| Hard: realistic + tilted mount + calibration error | 195 | 550 | 1293 | 1880 | 2625 | 3294 | 738 s |

### Stop-and-go: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.003 | 0.01 | 0.001 | 0.000 | 0.001 |
| Accelerometer noise | 0.02 | 0.001 | 0.011 | 0.01 | 0.002 | 0.000 | 0.002 |
| Accelerometer bias | 0.00 | 0.299 | 0.003 | 0.00 | 0.001 | 0.000 | 0.001 |
| Accelerometer bias drift | 0.13 | 0.015 | 0.019 | 0.01 | 0.005 | 0.000 | 0.005 |
| Gyroscope noise | 0.00 | 0.000 | 0.006 | 0.77 | 0.001 | 0.009 | 0.001 |
| Gyroscope bias | 0.00 | 0.000 | 0.021 | 0.07 | 0.001 | 0.000 | 0.001 |
| Gyroscope bias drift | 0.00 | 0.000 | 0.004 | 0.99 | 0.001 | 0.006 | 0.001 |
| Tilted dashboard mount | 0.00 | 0.000 | 0.003 | 0.01 | 0.001 | 0.000 | 0.001 |
| Calibration error: pitch 0.1° | 1.74 | 0.100 | 0.003 | 0.01 | 0.078 | 0.000 | 0.078 |
| Calibration error: pitch 0.5° | 8.70 | 0.500 | 0.003 | 0.01 | 0.385 | 0.000 | 0.385 |
| Calibration error: yaw 2° | 0.00 | 0.000 | 2.003 | 0.01 | 0.006 | 0.000 | 0.006 |
| Calibration error: roll 0.5° | 0.00 | 0.000 | 0.003 | 0.01 | 0.001 | 0.000 | 0.001 |
| GPS position error | 0.00 | 0.000 | 0.003 | 0.01 | 0.001 | 0.000 | 0.001 |
| GPS speed noise | 0.17 | 0.010 | 0.245 | 1.95 | 0.055 | 0.217 | 0.055 |
| GPS degradation before the portal (150 m, 8 m) | 0.40 | 0.023 | 0.003 | 0.02 | 0.093 | 0.294 | 0.093 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.46 | 0.027 | 0.048 | 0.17 | 0.133 | 0.467 | 0.133 |
| All realistic (= benchmark setting) | 0.64 | 0.312 | 0.272 | 1.88 | 0.119 | 0.418 | 0.119 |
| Hard: realistic + tilted mount + calibration error | 9.08 | 0.546 | 1.915 | 2.24 | 0.427 | 0.397 | 0.427 |
