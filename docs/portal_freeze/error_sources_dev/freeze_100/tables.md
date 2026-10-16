# Error-source benchmark: generated tables

step 1: portal freeze 100 · commit `1811edd+dirty` · 2026-10-16 09:46 UTC · 5 conditions × 2 traffic cases × 20 runs. One scenario: the benchmark's 5 km tunnel, flat road. Each condition adds one error source to an error-free setup (paired: same drive and traffic per run). Cells: median (p90) error [m]. ✗n = n runs with a gross error (> 200 m in the tunnel or at C). † = reference estimator.

## Free flow: error 5 km into the tunnel

| condition | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + vehicle speed (reference) † |
|---|---|---|---|---|
| Error-free (algorithm floor) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| GPS speed noise | 83 (187) ✗1 | 93 (254) ✗4 | 95 (273) ✗4 | 4 (9) |
| GPS degradation before the portal (150 m, 8 m) | 112 (198) ✗2 | 43 (60) | 46 (64) | 5 (9) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 144 (327) ✗6 | 118 (201) ✗2 | 112 (214) ✗4 | 11 (25) |
| All realistic (= benchmark setting) | 184 (349) ✗9 | 150 (374) ✗5 | 147 (403) ✗5 | 6 (17) |

### Free flow: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| GPS speed noise | 2 | 7 | 18 | 37 | 63 | 95 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 4 | 4 | 8 | 17 | 31 | 46 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 12 | 14 | 29 | 44 | 74 | 112 | 258 s |
| All realistic (= benchmark setting) | 3 | 8 | 20 | 42 | 84 | 147 | 258 s |

### Free flow: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| GPS speed noise | 3 | 8 | 23 | 39 | 62 | 93 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 7 | 8 | 11 | 16 | 28 | 43 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 23 | 29 | 38 | 45 | 75 | 118 | 258 s |
| All realistic (= benchmark setting) | 9 | 12 | 27 | 46 | 88 | 150 | 258 s |

### Free flow: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.003 | 0.02 | 0.000 | 0.000 | 0.000 |
| GPS speed noise | 0.24 | 0.014 | 0.293 | 1.87 | 0.051 | 0.080 | 0.051 |
| GPS degradation before the portal (150 m, 8 m) | 0.12 | 0.007 | 0.002 | 0.02 | 0.020 | 0.028 | 0.020 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.33 | 0.019 | 0.052 | 0.17 | 0.099 | 0.103 | 0.099 |
| All realistic (= benchmark setting) | 0.29 | 0.269 | 0.313 | 1.97 | 0.038 | 0.068 | 0.038 |

## Stop-and-go: error 5 km into the tunnel

| condition | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + vehicle speed (reference) † |
|---|---|---|---|---|
| Error-free (algorithm floor) | 4 (16) | 2 (14) | 2 (15) | 0 (0) |
| GPS speed noise | 316 (1154) ✗16 | 309 (1094) ✗14 | 307 (782) ✗13 | 4 (9) |
| GPS degradation before the portal (150 m, 8 m) | 215 (671) ✗11 | 86 (608) ✗6 | 94 (629) ✗6 | 4 (13) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 391 (1224) ✗17 | 196 (1462) ✗10 | 215 (782) ✗10 | 10 (36) |
| All realistic (= benchmark setting) | 543 (2038) ✗19 | 432 (2017) ✗15 | 447 (782) ✗15 | 7 (17) |

### Stop-and-go: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 1 | 1 | 2 | 738 s |
| GPS speed noise | 9 | 27 | 75 | 167 | 260 | 307 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 4 | 13 | 23 | 43 | 73 | 94 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 14 | 35 | 65 | 112 | 173 | 215 | 738 s |
| All realistic (= benchmark setting) | 9 | 27 | 102 | 227 | 343 | 447 | 738 s |

### Stop-and-go: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 1 | 1 | 2 | 738 s |
| GPS speed noise | 9 | 28 | 84 | 171 | 245 | 309 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 8 | 13 | 23 | 38 | 67 | 86 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 27 | 38 | 66 | 102 | 163 | 196 | 738 s |
| All realistic (= benchmark setting) | 15 | 28 | 101 | 216 | 348 | 432 | 738 s |

### Stop-and-go: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.003 | 0.02 | 0.003 | 0.000 | 0.003 |
| GPS speed noise | 0.24 | 0.014 | 0.293 | 1.87 | 0.057 | 0.083 | 0.057 |
| GPS degradation before the portal (150 m, 8 m) | 0.12 | 0.007 | 0.002 | 0.02 | 0.021 | 0.029 | 0.021 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.33 | 0.019 | 0.051 | 0.17 | 0.102 | 0.104 | 0.102 |
| All realistic (= benchmark setting) | 0.27 | 0.270 | 0.311 | 1.93 | 0.047 | 0.073 | 0.047 |
