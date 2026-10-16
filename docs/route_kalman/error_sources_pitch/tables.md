# Error-source benchmark: generated tables

step 4: route_kf v1, pitch · commit `8e07c8b+dirty` · 2026-10-16 13:20 UTC · 1 conditions × 2 traffic cases × 20 runs. One scenario: the benchmark's 5 km tunnel, flat road. Each condition adds one error source to an error-free setup (paired: same drive and traffic per run). Cells: median (p90) error [m]. ✗n = n runs with a gross error (> 200 m in the tunnel or at C). † = reference estimator.

## Free flow: error 5 km into the tunnel

| condition | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + IMU Kalman filter (distance, speed, offset) |
|---|---|---|---|
| Calibration error: pitch 0.1° | 580 (622) ✗20 | 628 (675) ✗20 | 3 (4) |

### Free flow: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Calibration error: pitch 0.1° | 13 | 36 | 118 | 239 | 407 | 628 | 258 s |

### Free flow: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Calibration error: pitch 0.1° | 13 | 36 | 116 | 219 | 383 | 580 | 258 s |

### Free flow: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Calibration error: pitch 0.1° | 1.74 | 0.100 | 0.002 | 0.00 | 0.237 | 0.002 | 0.237 |

## Stop-and-go: error 5 km into the tunnel

| condition | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + IMU Kalman filter (distance, speed, offset) |
|---|---|---|---|
| Calibration error: pitch 0.1° | 900 (1283) ✗20 | 977 (1376) ✗20 | 5 (6) |

### Stop-and-go: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Calibration error: pitch 0.1° | 55 | 133 | 322 | 540 | 748 | 977 | 738 s |

### Stop-and-go: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Calibration error: pitch 0.1° | 55 | 133 | 320 | 495 | 718 | 900 | 738 s |

### Stop-and-go: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Calibration error: pitch 0.1° | 1.74 | 0.100 | 0.002 | 0.00 | 0.269 | 0.002 | 0.269 |
