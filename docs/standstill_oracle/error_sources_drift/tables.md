# Error-source benchmark: generated tables

step 3: standstill oracle, drift · commit `d0dc11a+dirty` · 2026-10-16 12:04 UTC · 1 conditions × 2 traffic cases × 20 runs. One scenario: the benchmark's 5 km tunnel, flat road. Each condition adds one error source to an error-free setup (paired: same drive and traffic per run). Cells: median (p90) error [m]. ✗n = n runs with a gross error (> 200 m in the tunnel or at C). † = reference estimator.

## Free flow: error 5 km into the tunnel

| condition | DR raw IMU (assumed aligned mount) | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + last GPS speed (naive) | Route + vehicle speed (reference) † | Route + IMU + standstill oracle: speed reset ‡ | Route + IMU + standstill oracle: speed reset + offset ‡ |
|---|---|---|---|---|---|---|---|---|
| Accelerometer bias drift | 108 (182) ✗2 | 81 (162) ✗2 | 83 (169) ✗2 | 90 (182) ✗2 | 154 (253) ✗9 | 0 (0) | 90 (182) ✗2 | 90 (182) ✗2 |

### Free flow: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Accelerometer bias drift | 1 | 3 | 14 | 29 | 57 | 90 | 258 s |

### Free flow: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Accelerometer bias drift | 1 | 3 | 13 | 27 | 53 | 83 | 258 s |

### Free flow: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Accelerometer bias drift | 0.17 | 0.015 | 0.021 | 0.00 | 0.016 | 0.002 | 0.016 |

## Stop-and-go: error 5 km into the tunnel

| condition | DR raw IMU (assumed aligned mount) | DR GPS-calibrated IMU | DR calibrated + GPS-blended speed/heading | Route + filtered IMU speed | Route + last GPS speed (naive) | Route + vehicle speed (reference) † | Route + IMU + standstill oracle: speed reset ‡ | Route + IMU + standstill oracle: speed reset + offset ‡ |
|---|---|---|---|---|---|---|---|---|
| Accelerometer bias drift | 515 (1977) ✗13 | 328 (1926) ✗15 | 328 (1913) ✗15 | 353 (782) ✗15 | 782 (782) ✗20 | 0 (0) | 271 (458) ✗11 | 67 (143) |

### Stop-and-go: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Accelerometer bias drift | 4 | 19 | 59 | 155 | 261 | 353 | 738 s |

### Stop-and-go: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| Accelerometer bias drift | 4 | 19 | 57 | 144 | 247 | 328 | 738 s |

### Stop-and-go: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| Accelerometer bias drift | 0.14 | 0.015 | 0.021 | 0.00 | 0.019 | 0.002 | 0.019 |
