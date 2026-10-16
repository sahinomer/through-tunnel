# Error-source benchmark: generated tables

step 3b: oracle delay0.5 · commit `1c56b9f+dirty` · 2026-10-16 12:30 UTC · 1 conditions × 2 traffic cases × 20 runs. One scenario: the benchmark's 5 km tunnel, flat road. Each condition adds one error source to an error-free setup (paired: same drive and traffic per run). Cells: median (p90) error [m]. ✗n = n runs with a gross error (> 200 m in the tunnel or at C). † = reference estimator.

## Free flow: error 5 km into the tunnel

| condition | Route + filtered IMU speed | Route + IMU + standstill oracle: speed reset ‡ | Route + IMU + standstill oracle: speed reset + offset ‡ |
|---|---|---|---|
| All realistic (= benchmark setting) | 103 (257) ✗4 | 103 (257) ✗4 | 103 (257) ✗4 |

### Free flow: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| All realistic (= benchmark setting) | 6 | 11 | 24 | 47 | 70 | 103 | 258 s |

### Free flow: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| All realistic (= benchmark setting) | nan | nan | nan | nan | nan | nan | nan s |

### Free flow: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| All realistic (= benchmark setting) | nan | nan | nan | nan | nan | nan | 0.047 |

## Stop-and-go: error 5 km into the tunnel

| condition | Route + filtered IMU speed | Route + IMU + standstill oracle: speed reset ‡ | Route + IMU + standstill oracle: speed reset + offset ‡ |
|---|---|---|---|
| All realistic (= benchmark setting) | 385 (782) ✗16 | 164 (579) ✗9 | 528 (847) ✗20 |

### Stop-and-go: error growth, Route + filtered IMU speed (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| All realistic (= benchmark setting) | 10 | 24 | 74 | 151 | 309 | 385 | 738 s |

### Stop-and-go: error growth, DR calibrated + GPS-blended speed/heading (median [m])

The error d km into the tunnel equals the error at C of a d km tunnel.

| condition | 0.5 km | 1 km | 2 km | 3 km | 4 km | 5 km | time to 5 km |
|---|---|---|---|---|---|---|---|
| All realistic (= benchmark setting) | nan | nan | nan | nan | nan | nan | nan s |

### Stop-and-go: state handed over at the tunnel entrance (median |value|)

Forward offset = what the calibrated forward accelerometer channel reads with the car level and still (gravity leak + accelerometer bias): the acceleration error the estimators integrate. The levelling tilts the axes to cancel the bias, so the pitch misalignment alone can be large while the offset is small. Alignment = the GPS + IMU calibration at GPS loss vs. the true mount (injected calibration error included). Speed and heading errors = the estimate at the last output before GPS loss vs. the truth.

| condition | forward offset [mg] | pitch misalignment [°] | yaw misalignment [°] | gyro-bias error [mdps] | speed error, DR filtered [m/s] | heading error, DR filtered [°] | speed error, route + IMU [m/s] |
|---|---|---|---|---|---|---|---|
| All realistic (= benchmark setting) | nan | nan | nan | nan | nan | nan | 0.055 |
