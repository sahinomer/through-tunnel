# Error-source benchmark: generated tables

step 1: portal freeze 500 · commit `1811edd+dirty` · 2026-10-16 10:00 UTC · 5 conditions × 2 traffic cases × 20 runs. One scenario: the benchmark's 5 km tunnel, flat road. Each condition adds one error source to an error-free setup (paired: same drive and traffic per run). Cells: median (p90) error [m]. ✗n = n runs with a gross error (> 200 m in the tunnel or at C). † = reference estimator.

## Free flow: error 5 km into the tunnel

| condition | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + vehicle speed (reference) † |
|---|---|---|---|---|
| Error-free (algorithm floor) | 2 (2) | 2 (3) | 0 (1) | 0 (0) |
| GPS speed noise | 101 (229) ✗3 | 94 (317) ✗3 | 81 (334) ✗3 | 4 (9) |
| GPS degradation before the portal (150 m, 8 m) | 121 (188) ✗1 | 7 (15) | 4 (8) | 5 (9) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 140 (208) ✗4 | 20 (40) | 11 (25) | 11 (25) |
| All realistic (= benchmark setting) | 156 (292) ✗8 | 151 (281) ✗7 | 139 (302) ✗7 | 6 (17) |

### Free flow: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 0 | 0 | 0 | 258 s |
| GPS speed noise | 3 | 6 | 18 | 33 | 53 | 81 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 4 | 4 | 4 | 4 | 4 | 4 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 11 | 11 | 11 | 11 | 11 | 11 | 258 s |
| All realistic (= benchmark setting) | 6 | 8 | 22 | 45 | 86 | 139 | 258 s |

### Free flow: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 1 | 1 | 2 | 2 | 258 s |
| GPS speed noise | 4 | 9 | 24 | 43 | 66 | 94 | 258 s |
| GPS degradation before the portal (150 m, 8 m) | 7 | 7 | 7 | 7 | 7 | 7 | 258 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 19 | 19 | 19 | 20 | 20 | 20 | 258 s |
| All realistic (= benchmark setting) | 11 | 15 | 27 | 50 | 93 | 151 | 258 s |

### Free flow: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.003 | 0.17 | 0.000 | 0.009 | 0.000 |
| GPS speed noise | 0.22 | 0.013 | 0.276 | 3.55 | 0.073 | 0.212 | 0.073 |
| GPS degradation before the portal (150 m, 8 m) | 0.00 | 0.000 | 0.003 | 0.17 | 0.000 | 0.009 | 0.000 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.00 | 0.000 | 0.003 | 0.17 | 0.000 | 0.009 | 0.000 |
| All realistic (= benchmark setting) | 0.24 | 0.274 | 0.277 | 3.95 | 0.088 | 0.192 | 0.088 |

## Stop-and-go: error 5 km into the tunnel

| condition | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + vehicle speed (reference) † |
|---|---|---|---|---|
| Error-free (algorithm floor) | 6 (8) | 6 (7) | 1 (5) | 0 (0) |
| GPS speed noise | 363 (1306) ✗14 | 379 (1345) ✗13 | 386 (782) ✗12 | 4 (9) |
| GPS degradation before the portal (150 m, 8 m) | 157 (599) ✗8 | 11 (17) | 5 (11) | 4 (13) |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 182 (620) ✗8 | 26 (41) | 11 (34) | 10 (36) |
| All realistic (= benchmark setting) | 779 (2486) ✗20 | 493 (2432) ✗19 | 509 (782) ✗17 | 7 (17) |

### Stop-and-go: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 0 | 1 | 1 | 1 | 738 s |
| GPS speed noise | 10 | 26 | 74 | 142 | 214 | 386 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 3 | 3 | 3 | 4 | 5 | 5 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 8 | 8 | 8 | 9 | 9 | 11 | 738 s |
| All realistic (= benchmark setting) | 10 | 46 | 97 | 283 | 367 | 509 | 738 s |

### Stop-and-go: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0 | 0 | 1 | 2 | 4 | 6 | 738 s |
| GPS speed noise | 10 | 29 | 85 | 148 | 236 | 379 | 738 s |
| GPS degradation before the portal (150 m, 8 m) | 7 | 7 | 8 | 9 | 9 | 11 | 738 s |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 21 | 22 | 22 | 24 | 24 | 26 | 738 s |
| All realistic (= benchmark setting) | 14 | 47 | 100 | 284 | 363 | 493 | 738 s |

### Stop-and-go: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Error-free (algorithm floor) | 0.00 | 0.000 | 0.003 | 0.17 | 0.003 | 0.009 | 0.003 |
| GPS speed noise | 0.22 | 0.013 | 0.276 | 3.55 | 0.077 | 0.217 | 0.077 |
| GPS degradation before the portal (150 m, 8 m) | 0.00 | 0.000 | 0.003 | 0.17 | 0.003 | 0.009 | 0.003 |
| GPS degradation, harsh (500 m, 20 m, 10 % jumps) | 0.00 | 0.000 | 0.003 | 0.17 | 0.003 | 0.009 | 0.003 |
| All realistic (= benchmark setting) | 0.25 | 0.274 | 0.277 | 3.87 | 0.089 | 0.194 | 0.089 |
