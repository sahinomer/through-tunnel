# Error-source benchmark: generated tables

step 1: portal freeze off · commit `1811edd+dirty` · 2026-10-16 09:39 UTC · 5 conditions × 2 traffic cases × 20 runs. One scenario: the benchmark's 5 km tunnel, flat road. Each condition adds one error source to an error-free setup (paired: same drive and traffic per run). Cells: median (p90) error [m]. ✗n = n runs with a gross error (> 200 m in the tunnel or at C). † = reference estimator.

## Free flow: error 5 km into the tunnel

| condition | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + vehicle speed (reference) † |
|---|---|---|---|---|
| Error-free (algorithm floor) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| GPS speed noise | 117 (223) ✗3 | 95 (174) ✗2 | 98 (185) ✗2 | 4 (9) |
| GPS degradation before the portal (150 m, 8 m) | 264 (457) ✗13 | 170 (317) ✗8 | 184 (344) ✗9 | 5 (9) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 286 (538) ✗14 | 175 (383) ✗9 | 188 (412) ✗9 | 11 (25) |
| All realistic (= benchmark setting) | 316 (512) ✗16 | 217 (393) ✗11 | 231 (420) ✗11 | 6 (17) |

### Free flow: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| GPS speed noise | 2 | 6 | 19 | 37 | 69 | 98 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 6 | 12 | 36 | 73 | 123 | 184 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 13 | 17 | 41 | 74 | 123 | 188 | 258 s |
| All realistic (= benchmark setting) | 5 | 15 | 38 | 84 | 137 | 231 | 258 s |

### Free flow: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| GPS speed noise | 3 | 7 | 22 | 37 | 66 | 95 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 9 | 16 | 36 | 66 | 115 | 170 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 20 | 28 | 51 | 69 | 118 | 175 | 258 s |
| All realistic (= benchmark setting) | 14 | 18 | 39 | 79 | 139 | 217 | 258 s |

### Free flow: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.003 | 0.01 | 0.000 | 0.000 | 0.000 |
| GPS speed noise | 0.23 | 0.013 | 0.292 | 1.66 | 0.048 | 0.106 | 0.048 |
| GPS degradation before the portal (150 m, 8 m) | 0.50 | 0.029 | 0.003 | 0.02 | 0.117 | 0.129 | 0.117 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.55 | 0.032 | 0.050 | 0.17 | 0.144 | 0.182 | 0.144 |
| All realistic (= benchmark setting) | 0.60 | 0.298 | 0.306 | 1.96 | 0.112 | 0.172 | 0.112 |

## Stop-and-go: error 5 km into the tunnel

| condition | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + vehicle speed (reference) † |
|---|---|---|---|---|
| Error-free (algorithm floor) | 13 (16) | 12 (15) | 13 (17) | 0 (0) |
| GPS speed noise | 301 (898) ✗13 | 210 (829) ✗10 | 196 (782) ✗10 | 4 (9) |
| GPS degradation before the portal (150 m, 8 m) | 435 (1892) ✗15 | 325 (1618) ✗13 | 354 (782) ✗13 | 4 (13) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 472 (2097) ✗17 | 337 (1762) ✗13 | 373 (782) ✗14 | 10 (36) |
| All realistic (= benchmark setting) | 562 (3914) ✗19 | 470 (3314) ✗17 | 482 (804) ✗16 | 7 (17) |

### Stop-and-go: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 1 | 3 | 5 | 9 | 13 | 738 s |
| GPS speed noise | 6 | 20 | 54 | 92 | 139 | 196 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 16 | 33 | 87 | 185 | 261 | 354 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 16 | 45 | 98 | 192 | 272 | 373 | 738 s |
| All realistic (= benchmark setting) | 25 | 55 | 126 | 210 | 340 | 482 | 738 s |

### Stop-and-go: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 1 | 3 | 5 | 9 | 12 | 738 s |
| GPS speed noise | 7 | 20 | 55 | 93 | 143 | 210 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 17 | 35 | 87 | 173 | 247 | 325 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 32 | 54 | 103 | 181 | 242 | 337 | 738 s |
| All realistic (= benchmark setting) | 27 | 57 | 132 | 207 | 339 | 470 | 738 s |

### Stop-and-go: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.003 | 0.01 | 0.001 | 0.000 | 0.001 |
| GPS speed noise | 0.17 | 0.010 | 0.245 | 1.95 | 0.055 | 0.217 | 0.055 |
| GPS degradation before the portal (150 m, 8 m) | 0.40 | 0.023 | 0.003 | 0.02 | 0.093 | 0.294 | 0.093 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.46 | 0.027 | 0.048 | 0.17 | 0.133 | 0.467 | 0.133 |
| All realistic (= benchmark setting) | 0.64 | 0.312 | 0.272 | 1.88 | 0.119 | 0.418 | 0.119 |
