# Error-source benchmark: generated tables

step 1: portal freeze 200 · commit `1811edd+dirty` · 2026-10-16 09:53 UTC · 5 conditions × 2 traffic cases × 20 runs. One scenario: the benchmark's 5 km tunnel, flat road. Each condition adds one error source to an error-free setup (paired: same drive and traffic per run). Cells: median (p90) error [m]. ✗n = n runs with a gross error (> 200 m in the tunnel or at C). † = reference estimator.

## Free flow: error 5 km into the tunnel

| condition | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + vehicle speed (reference) † |
|---|---|---|---|---|
| Error-free (algorithm floor) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| GPS speed noise | 112 (244) ✗3 | 116 (228) ✗3 | 102 (245) ✗4 | 4 (9) |
| GPS degradation before the portal (150 m, 8 m) | 121 (188) ✗1 | 6 (14) | 4 (8) | 5 (9) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 170 (367) ✗7 | 129 (239) ✗3 | 133 (242) ✗7 | 11 (25) |
| All realistic (= benchmark setting) | 167 (306) ✗8 | 117 (240) ✗4 | 103 (257) ✗4 | 6 (17) |

### Free flow: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| GPS speed noise | 3 | 7 | 21 | 47 | 77 | 102 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 4 | 4 | 4 | 4 | 4 | 4 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 15 | 20 | 37 | 57 | 87 | 133 | 258 s |
| All realistic (= benchmark setting) | 6 | 11 | 24 | 47 | 70 | 103 | 258 s |

### Free flow: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| GPS speed noise | 4 | 9 | 25 | 48 | 79 | 116 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 7 | 7 | 7 | 7 | 6 | 6 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 19 | 26 | 41 | 61 | 92 | 129 | 258 s |
| All realistic (= benchmark setting) | 9 | 13 | 31 | 53 | 78 | 117 | 258 s |

### Free flow: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.003 | 0.02 | 0.000 | 0.001 | 0.000 |
| GPS speed noise | 0.24 | 0.014 | 0.295 | 2.20 | 0.054 | 0.089 | 0.054 |
| GPS degradation before the portal (150 m, 8 m) | 0.00 | 0.000 | 0.003 | 0.02 | 0.000 | 0.001 | 0.000 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.33 | 0.019 | 0.058 | 0.17 | 0.101 | 0.083 | 0.101 |
| All realistic (= benchmark setting) | 0.22 | 0.281 | 0.314 | 1.77 | 0.047 | 0.098 | 0.047 |

## Stop-and-go: error 5 km into the tunnel

| condition | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + vehicle speed (reference) † |
|---|---|---|---|---|
| Error-free (algorithm floor) | 3 (3) | 1 (1) | 0 (1) | 0 (0) |
| GPS speed noise | 391 (1059) ✗15 | 386 (915) ✗14 | 393 (782) ✗14 | 4 (9) |
| GPS degradation before the portal (150 m, 8 m) | 159 (596) ✗8 | 8 (13) | 4 (11) | 4 (13) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 314 (1072) ✗19 | 266 (1217) ✗13 | 289 (782) ✗13 | 10 (36) |
| All realistic (= benchmark setting) | 561 (2100) ✗18 | 420 (2356) ✗17 | 385 (782) ✗16 | 7 (17) |

### Stop-and-go: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 738 s |
| GPS speed noise | 7 | 22 | 94 | 166 | 260 | 393 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 3 | 3 | 3 | 3 | 3 | 4 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 16 | 45 | 92 | 170 | 242 | 289 | 738 s |
| All realistic (= benchmark setting) | 10 | 24 | 74 | 151 | 308 | 385 | 738 s |

### Stop-and-go: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 1 | 1 | 738 s |
| GPS speed noise | 8 | 26 | 93 | 163 | 288 | 386 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 7 | 7 | 7 | 7 | 8 | 8 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 28 | 50 | 93 | 155 | 223 | 266 | 738 s |
| All realistic (= benchmark setting) | 12 | 26 | 79 | 159 | 324 | 420 | 738 s |

### Stop-and-go: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.003 | 0.02 | 0.003 | 0.001 | 0.003 |
| GPS speed noise | 0.24 | 0.014 | 0.295 | 2.20 | 0.058 | 0.091 | 0.058 |
| GPS degradation before the portal (150 m, 8 m) | 0.00 | 0.000 | 0.003 | 0.02 | 0.003 | 0.001 | 0.003 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.33 | 0.019 | 0.058 | 0.17 | 0.107 | 0.083 | 0.107 |
| All realistic (= benchmark setting) | 0.24 | 0.281 | 0.314 | 2.05 | 0.055 | 0.107 | 0.055 |
