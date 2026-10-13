# Sensor-factor study: generated tables

20 runs per condition (sensor/GPS seeds 0–19), preset drive. ‡ = supplementary condition. Values are medians over the runs unless stated.

## Eisenhower Tunnel, I-70 (westbound)

Dead-reckoning time from GPS loss to C: 125 s.

**Horizontal error at C [m], median (p90):**

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | 0.3 (0.4) | 0.0 (0.1) | 0.3 (0.3) | 1.3 (1.3) | 335.6 (340.2) |
| IMU noise only | 1.4 (3.6) | 3.2 (5.7) | 3.3 (6.2) | 2.4 (4.0) | 335.6 (340.2) |
| IMU bias only | 437.1 (767.4) | 0.1 (0.1) | 0.2 (0.3) | 1.3 (1.3) | 335.6 (340.2) |
| Calibration error only | 712.2 (712.2) | 712.3 (712.3) | 767.5 (767.5) | 767.8 (767.8) | 335.6 (340.2) |
| Noise + bias + calibration | 608.3 (1280.5) | 710.3 (721.9) | 765.4 (778.1) | 765.7 (778.4) | 335.6 (340.2) |
| Accelerometer noise only ‡ | 1.0 (2.2) | 2.1 (3.7) | 2.1 (3.7) | 2.4 (4.0) | 335.6 (340.2) |
| Gyroscope noise only ‡ | 0.7 (3.3) | 1.8 (4.9) | 1.7 (5.5) | 1.3 (1.3) | 335.6 (340.2) |
| Accelerometer bias only ‡ | 403.9 (750.4) | 0.1 (0.2) | 0.2 (0.3) | 1.3 (1.3) | 335.6 (340.2) |
| Gyroscope bias only ‡ | 142.9 (220.3) | 0.0 (0.1) | 0.3 (0.3) | 1.3 (1.3) | 335.6 (340.2) |
| GPS errors only ‡ | 33.5 (55.1) | 54.9 (75.0) | 37.1 (59.0) | 34.8 (53.0) | 330.2 (362.5) |
| Noise + bias + GPS errors (results.md) ‡ | 459.8 (772.7) | 54.8 (75.9) | 38.3 (59.9) | 34.0 (54.6) | 330.2 (362.5) |
| Noise + bias + GPS + calibration ‡ | 642.9 (1288.5) | 717.6 (769.7) | 771.4 (824.8) | 772.3 (824.5) | 330.2 (362.5) |

**Along-track / cross-track error at C [m], median of absolute values:**

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 1 | 326 / 78 |
| IMU noise only | 1 / 1 | 2 / 2 | 2 / 2 | 2 / 1 | 326 / 78 |
| IMU bias only | 408 / 117 | 0 / 0 | 0 / 0 | 0 / 1 | 326 / 78 |
| Calibration error only | 706 / 92 | 706 / 92 | 761 / 99 | 763 / 88 | 326 / 78 |
| Noise + bias + calibration | 599 / 138 | 704 / 92 | 759 / 99 | 761 / 87 | 326 / 78 |
| Accelerometer noise only ‡ | 1 / 0 | 2 / 0 | 2 / 0 | 2 / 1 | 326 / 78 |
| Gyroscope noise only ‡ | 0 / 1 | 0 / 2 | 0 / 2 | 0 / 1 | 326 / 78 |
| Accelerometer bias only ‡ | 401 / 52 | 0 / 0 | 0 / 0 | 0 / 1 | 326 / 78 |
| Gyroscope bias only ‡ | 15 / 142 | 0 / 0 | 0 / 0 | 0 / 1 | 326 / 78 |
| GPS errors only ‡ | 15 / 19 | 45 / 28 | 33 / 9 | 35 / 1 | 321 / 77 |
| Noise + bias + GPS errors (results.md) ‡ | 428 / 123 | 46 / 27 | 32 / 9 | 34 / 1 | 321 / 77 |
| Noise + bias + GPS + calibration ‡ | 635 / 129 | 712 / 97 | 766 / 101 | 767 / 88 | 321 / 77 |

**Growth exponent p of the median error, e(t) ∝ t^p, between 30 s and 90 s after GPS loss** (1 = constant speed or heading error, 1.5 = random walk of speed or heading, 2 = constant acceleration or turn-rate error; – = below 0.5 m):

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | – | – | – | – | 1.5 |
| IMU noise only | – | – | – | – | 1.5 |
| IMU bias only | 2.0 | – | – | – | 1.5 |
| Calibration error only | 1.9 | 1.9 | 1.7 | 1.7 | 1.5 |
| Noise + bias + calibration | 1.9 | 1.9 | 1.7 | 1.7 | 1.5 |
| Accelerometer noise only ‡ | – | – | – | – | 1.5 |
| Gyroscope noise only ‡ | – | – | – | – | 1.5 |
| Accelerometer bias only ‡ | 2.0 | – | – | – | 1.5 |
| Gyroscope bias only ‡ | 1.9 | – | – | – | 1.5 |
| GPS errors only ‡ | 0.9 | 1.2 | 1.2 | 1.4 | 1.5 |
| Noise + bias + GPS errors (results.md) ‡ | 1.8 | 1.2 | 1.2 | 1.4 | 1.5 |
| Noise + bias + GPS + calibration ‡ | 1.9 | 1.9 | 1.7 | 1.7 | 1.5 |

**Median horizontal error vs. time since GPS loss [m]:**

| condition | estimator | 15 s | 30 s | 60 s | 90 s | 120 s |
|---|---|---|---|---|---|---|
| Ideal sensors, correct calibration | dr_raw | 0.0 | 0.1 | 0.1 | 0.2 | 0.3 |
| Ideal sensors, correct calibration | dr_calibrated | 0.0 | 0.0 | 0.1 | 0.1 | 0.0 |
| Ideal sensors, correct calibration | dr_filtered | 0.0 | 0.0 | 0.1 | 0.2 | 0.3 |
| Ideal sensors, correct calibration | route_imu | 0.1 | 0.1 | 0.4 | 0.1 | 0.2 |
| Ideal sensors, correct calibration | route_hold | 9.8 | 46.9 | 152.7 | 252.6 | 322.2 |
| IMU noise only | dr_raw | 0.1 | 0.2 | 0.5 | 0.7 | 1.2 |
| IMU noise only | dr_calibrated | 0.1 | 0.3 | 0.9 | 1.7 | 3.0 |
| IMU noise only | dr_filtered | 0.1 | 0.4 | 1.0 | 1.8 | 3.0 |
| IMU noise only | route_imu | 0.1 | 0.2 | 0.7 | 1.2 | 1.9 |
| IMU noise only | route_hold | 9.8 | 46.9 | 152.7 | 252.6 | 322.2 |
| IMU bias only | dr_raw | 6.5 | 25.2 | 99.3 | 223.0 | 397.7 |
| IMU bias only | dr_calibrated | 0.0 | 0.1 | 0.1 | 0.1 | 0.1 |
| IMU bias only | dr_filtered | 0.0 | 0.0 | 0.1 | 0.1 | 0.2 |
| IMU bias only | route_imu | 0.1 | 0.1 | 0.4 | 0.1 | 0.2 |
| IMU bias only | route_hold | 9.8 | 46.9 | 152.7 | 252.6 | 322.2 |
| Calibration error only | dr_raw | 13.5 | 47.4 | 172.6 | 373.8 | 651.9 |
| Calibration error only | dr_calibrated | 13.5 | 47.4 | 172.6 | 373.8 | 651.9 |
| Calibration error only | dr_filtered | 20.2 | 60.7 | 199.0 | 413.4 | 704.7 |
| Calibration error only | route_imu | 20.4 | 60.8 | 199.2 | 413.7 | 705.0 |
| Calibration error only | route_hold | 9.8 | 46.9 | 152.7 | 252.6 | 322.2 |
| Noise + bias + calibration | dr_raw | 11.7 | 40.9 | 148.7 | 321.3 | 559.7 |
| Noise + bias + calibration | dr_calibrated | 13.4 | 47.0 | 171.8 | 372.1 | 649.3 |
| Noise + bias + calibration | dr_filtered | 20.0 | 60.2 | 198.1 | 411.7 | 702.0 |
| Noise + bias + calibration | route_imu | 20.2 | 60.4 | 198.3 | 412.0 | 702.3 |
| Noise + bias + calibration | route_hold | 9.8 | 46.9 | 152.7 | 252.6 | 322.2 |
| Accelerometer noise only ‡ | dr_raw | 0.0 | 0.1 | 0.2 | 0.6 | 1.0 |
| Accelerometer noise only ‡ | dr_calibrated | 0.1 | 0.2 | 0.6 | 1.2 | 1.9 |
| Accelerometer noise only ‡ | dr_filtered | 0.1 | 0.2 | 0.6 | 1.2 | 2.0 |
| Accelerometer noise only ‡ | route_imu | 0.1 | 0.2 | 0.7 | 1.2 | 1.9 |
| Accelerometer noise only ‡ | route_hold | 9.8 | 46.9 | 152.7 | 252.6 | 322.2 |
| Gyroscope noise only ‡ | dr_raw | 0.0 | 0.1 | 0.2 | 0.4 | 0.6 |
| Gyroscope noise only ‡ | dr_calibrated | 0.1 | 0.2 | 0.6 | 1.0 | 1.6 |
| Gyroscope noise only ‡ | dr_filtered | 0.1 | 0.2 | 0.7 | 1.0 | 1.6 |
| Gyroscope noise only ‡ | route_imu | 0.1 | 0.1 | 0.4 | 0.1 | 0.2 |
| Gyroscope noise only ‡ | route_hold | 9.8 | 46.9 | 152.7 | 252.6 | 322.2 |
| Accelerometer bias only ‡ | dr_raw | 5.9 | 23.1 | 92.0 | 206.6 | 367.1 |
| Accelerometer bias only ‡ | dr_calibrated | 0.0 | 0.1 | 0.1 | 0.1 | 0.1 |
| Accelerometer bias only ‡ | dr_filtered | 0.0 | 0.0 | 0.1 | 0.1 | 0.2 |
| Accelerometer bias only ‡ | route_imu | 0.1 | 0.1 | 0.4 | 0.1 | 0.2 |
| Accelerometer bias only ‡ | route_hold | 9.8 | 46.9 | 152.7 | 252.6 | 322.2 |
| Gyroscope bias only ‡ | dr_raw | 2.4 | 8.7 | 32.5 | 72.4 | 130.5 |
| Gyroscope bias only ‡ | dr_calibrated | 0.0 | 0.0 | 0.1 | 0.1 | 0.0 |
| Gyroscope bias only ‡ | dr_filtered | 0.0 | 0.0 | 0.1 | 0.2 | 0.3 |
| Gyroscope bias only ‡ | route_imu | 0.1 | 0.1 | 0.4 | 0.1 | 0.2 |
| Gyroscope bias only ‡ | route_hold | 9.8 | 46.9 | 152.7 | 252.6 | 322.2 |
| GPS errors only ‡ | dr_raw | 5.3 | 8.4 | 15.9 | 23.8 | 32.1 |
| GPS errors only ‡ | dr_calibrated | 5.6 | 9.4 | 21.2 | 34.7 | 51.3 |
| GPS errors only ‡ | dr_filtered | 3.8 | 5.9 | 12.7 | 22.2 | 34.5 |
| GPS errors only ‡ | route_imu | 2.4 | 4.3 | 13.2 | 21.2 | 32.4 |
| GPS errors only ‡ | route_hold | 9.2 | 46.3 | 151.2 | 249.4 | 317.2 |
| Noise + bias + GPS errors (results.md) ‡ | dr_raw | 8.5 | 32.2 | 113.0 | 241.5 | 419.3 |
| Noise + bias + GPS errors (results.md) ‡ | dr_calibrated | 5.6 | 9.6 | 21.1 | 34.8 | 51.4 |
| Noise + bias + GPS errors (results.md) ‡ | dr_filtered | 3.9 | 6.2 | 13.1 | 22.1 | 35.4 |
| Noise + bias + GPS errors (results.md) ‡ | route_imu | 2.5 | 4.6 | 13.4 | 21.6 | 31.4 |
| Noise + bias + GPS errors (results.md) ‡ | route_hold | 9.2 | 46.3 | 151.2 | 249.4 | 317.2 |
| Noise + bias + GPS + calibration ‡ | dr_raw | 12.1 | 43.2 | 156.8 | 338.8 | 590.1 |
| Noise + bias + GPS + calibration ‡ | dr_calibrated | 15.1 | 49.5 | 176.0 | 378.9 | 661.3 |
| Noise + bias + GPS + calibration ‡ | dr_filtered | 21.8 | 62.6 | 202.6 | 419.6 | 710.0 |
| Noise + bias + GPS + calibration ‡ | route_imu | 21.4 | 63.0 | 203.6 | 420.6 | 710.9 |
| Noise + bias + GPS + calibration ‡ | route_hold | 9.2 | 46.3 | 151.2 | 249.4 | 317.2 |

**Exit-announcement timing error [s], median of absolute values (main conditions):**

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | 0.0 | 0.0 | 0.0 | 0.0 | 12.6 |
| IMU noise only | 0.0 | 0.1 | 0.1 | 0.1 | 12.6 |
| IMU bias only | 14.5 | 0.0 | 0.0 | 0.0 | 12.6 |
| Calibration error only | 17.9 | 17.9 | 17.9 | 19.0 | 12.6 |
| Noise + bias + calibration | 17.4 | 17.9 | 17.9 | 19.3 | 12.6 |

## Seattle SR 99 Tunnel (northbound)

Dead-reckoning time from GPS loss to C: 151 s.

**Horizontal error at C [m], median (p90):**

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | 0.0 (0.1) | 0.4 (0.4) | 0.4 (0.5) | 0.5 (0.5) | 2.0 (3.2) |
| IMU noise only | 2.4 (4.2) | 4.5 (6.1) | 4.7 (6.8) | 2.4 (3.5) | 2.0 (3.2) |
| IMU bias only | 618.0 (1091.6) | 0.3 (0.3) | 0.3 (0.4) | 0.5 (0.5) | 2.0 (3.2) |
| Calibration error only | 937.7 (943.9) | 937.6 (943.8) | 990.2 (996.9) | 999.3 (1005.9) | 2.0 (3.2) |
| Noise + bias + calibration | 798.2 (1692.2) | 938.1 (946.4) | 990.9 (999.6) | 1000.0 (1008.4) | 2.0 (3.2) |
| Accelerometer noise only ‡ | 0.8 (3.4) | 2.1 (3.6) | 2.4 (3.7) | 2.4 (3.5) | 2.0 (3.2) |
| Gyroscope noise only ‡ | 1.6 (3.5) | 3.6 (5.4) | 3.5 (6.1) | 0.5 (0.5) | 2.0 (3.2) |
| Accelerometer bias only ‡ | 575.2 (1068.6) | 0.3 (0.3) | 0.3 (0.4) | 0.5 (0.5) | 2.0 (3.2) |
| Gyroscope bias only ‡ | 183.9 (285.8) | 0.4 (0.4) | 0.4 (0.5) | 0.5 (0.5) | 2.0 (3.2) |
| GPS errors only ‡ | 34.4 (68.1) | 67.1 (115.8) | 63.0 (95.7) | 32.7 (70.4) | 19.5 (56.4) |
| Noise + bias + GPS errors (results.md) ‡ | 639.8 (1069.9) | 64.5 (115.6) | 61.1 (93.3) | 31.6 (72.1) | 19.5 (56.4) |
| Noise + bias + GPS + calibration ‡ | 809.5 (1722.6) | 935.1 (1015.8) | 993.4 (1057.6) | 1002.4 (1065.8) | 19.5 (56.4) |

**Along-track / cross-track error at C [m], median of absolute values:**

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 2 / 0 |
| IMU noise only | 1 / 1 | 2 / 3 | 2 / 4 | 2 / 0 | 2 / 0 |
| IMU bias only | 543 / 259 | 0 / 0 | 0 / 0 | 0 / 0 | 2 / 0 |
| Calibration error only | 883 / 316 | 883 / 316 | 932 / 334 | 969 / 245 | 2 / 0 |
| Noise + bias + calibration | 749 / 329 | 883 / 316 | 933 / 334 | 969 / 245 | 2 / 0 |
| Accelerometer noise only ‡ | 1 / 0 | 2 / 1 | 2 / 1 | 2 / 0 | 2 / 0 |
| Gyroscope noise only ‡ | 1 / 1 | 1 / 3 | 1 / 3 | 0 / 0 | 2 / 0 |
| Accelerometer bias only ‡ | 541 / 196 | 0 / 0 | 0 / 0 | 0 / 0 | 2 / 0 |
| Gyroscope bias only ‡ | 60 / 173 | 0 / 0 | 0 / 0 | 0 / 0 | 2 / 0 |
| GPS errors only ‡ | 21 / 24 | 42 / 37 | 35 / 50 | 33 / 0 | 20 / 0 |
| Noise + bias + GPS errors (results.md) ‡ | 566 / 271 | 41 / 37 | 34 / 50 | 32 / 0 | 20 / 0 |
| Noise + bias + GPS + calibration ‡ | 752 / 348 | 868 / 333 | 933 / 354 | 972 / 246 | 20 / 0 |

**Growth exponent p of the median error, e(t) ∝ t^p, between 30 s and 90 s after GPS loss** (1 = constant speed or heading error, 1.5 = random walk of speed or heading, 2 = constant acceleration or turn-rate error; – = below 0.5 m):

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | – | – | – | – | – |
| IMU noise only | – | – | – | – | – |
| IMU bias only | 2.0 | – | – | – | – |
| Calibration error only | 1.9 | 1.9 | 1.8 | 1.8 | – |
| Noise + bias + calibration | 1.9 | 1.9 | 1.8 | 1.8 | – |
| Accelerometer noise only ‡ | – | – | – | – | – |
| Gyroscope noise only ‡ | – | – | – | – | – |
| Accelerometer bias only ‡ | 2.0 | – | – | – | – |
| Gyroscope bias only ‡ | 2.0 | – | – | – | – |
| GPS errors only ‡ | 0.8 | 1.0 | 1.3 | 1.2 | 1.6 |
| Noise + bias + GPS errors (results.md) ‡ | 1.8 | 1.0 | 1.2 | 1.2 | 1.6 |
| Noise + bias + GPS + calibration ‡ | 1.9 | 1.9 | 1.8 | 1.8 | 1.6 |

**Median horizontal error vs. time since GPS loss [m]:**

| condition | estimator | 15 s | 30 s | 60 s | 90 s | 120 s |
|---|---|---|---|---|---|---|
| Ideal sensors, correct calibration | dr_raw | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Ideal sensors, correct calibration | dr_calibrated | 0.0 | 0.0 | 0.1 | 0.1 | 0.2 |
| Ideal sensors, correct calibration | dr_filtered | 0.0 | 0.0 | 0.1 | 0.2 | 0.3 |
| Ideal sensors, correct calibration | route_imu | 0.1 | 0.0 | 0.1 | 0.1 | 0.2 |
| Ideal sensors, correct calibration | route_hold | 0.2 | 0.4 | 3.1 | 21.0 | 19.3 |
| IMU noise only | dr_raw | 0.1 | 0.2 | 0.7 | 1.0 | 1.6 |
| IMU noise only | dr_calibrated | 0.1 | 0.3 | 1.0 | 1.7 | 2.8 |
| IMU noise only | dr_filtered | 0.1 | 0.4 | 1.1 | 2.0 | 3.1 |
| IMU noise only | route_imu | 0.1 | 0.1 | 0.3 | 0.9 | 1.6 |
| IMU noise only | route_hold | 0.2 | 0.4 | 3.1 | 21.0 | 19.3 |
| IMU bias only | dr_raw | 6.4 | 25.0 | 98.0 | 218.1 | 388.8 |
| IMU bias only | dr_calibrated | 0.0 | 0.0 | 0.0 | 0.1 | 0.2 |
| IMU bias only | dr_filtered | 0.0 | 0.0 | 0.0 | 0.1 | 0.2 |
| IMU bias only | route_imu | 0.1 | 0.0 | 0.1 | 0.1 | 0.2 |
| IMU bias only | route_hold | 0.2 | 0.4 | 3.1 | 21.0 | 19.3 |
| Calibration error only | dr_raw | 9.5 | 38.7 | 149.4 | 327.9 | 589.9 |
| Calibration error only | dr_calibrated | 9.5 | 38.7 | 149.4 | 327.9 | 589.8 |
| Calibration error only | dr_filtered | 15.0 | 49.5 | 170.7 | 359.2 | 631.8 |
| Calibration error only | route_imu | 15.0 | 49.5 | 172.1 | 365.8 | 636.3 |
| Calibration error only | route_hold | 0.2 | 0.4 | 3.1 | 21.0 | 19.3 |
| Noise + bias + calibration | dr_raw | 8.4 | 33.6 | 128.1 | 280.1 | 503.1 |
| Noise + bias + calibration | dr_calibrated | 9.6 | 38.9 | 149.5 | 327.9 | 589.7 |
| Noise + bias + calibration | dr_filtered | 15.1 | 49.6 | 170.6 | 359.1 | 631.5 |
| Noise + bias + calibration | route_imu | 15.1 | 49.7 | 172.1 | 365.6 | 635.9 |
| Noise + bias + calibration | route_hold | 0.2 | 0.4 | 3.1 | 21.0 | 19.3 |
| Accelerometer noise only ‡ | dr_raw | 0.0 | 0.1 | 0.2 | 0.4 | 0.7 |
| Accelerometer noise only ‡ | dr_calibrated | 0.0 | 0.1 | 0.4 | 0.7 | 1.5 |
| Accelerometer noise only ‡ | dr_filtered | 0.1 | 0.1 | 0.4 | 1.0 | 1.6 |
| Accelerometer noise only ‡ | route_imu | 0.1 | 0.1 | 0.3 | 0.9 | 1.6 |
| Accelerometer noise only ‡ | route_hold | 0.2 | 0.4 | 3.1 | 21.0 | 19.3 |
| Gyroscope noise only ‡ | dr_raw | 0.0 | 0.1 | 0.3 | 0.5 | 0.9 |
| Gyroscope noise only ‡ | dr_calibrated | 0.0 | 0.2 | 0.6 | 1.5 | 2.2 |
| Gyroscope noise only ‡ | dr_filtered | 0.1 | 0.2 | 0.9 | 1.4 | 2.2 |
| Gyroscope noise only ‡ | route_imu | 0.1 | 0.0 | 0.1 | 0.1 | 0.2 |
| Gyroscope noise only ‡ | route_hold | 0.2 | 0.4 | 3.1 | 21.0 | 19.3 |
| Accelerometer bias only ‡ | dr_raw | 6.0 | 23.4 | 91.7 | 203.8 | 364.0 |
| Accelerometer bias only ‡ | dr_calibrated | 0.0 | 0.0 | 0.0 | 0.1 | 0.2 |
| Accelerometer bias only ‡ | dr_filtered | 0.0 | 0.0 | 0.0 | 0.1 | 0.2 |
| Accelerometer bias only ‡ | route_imu | 0.1 | 0.0 | 0.1 | 0.1 | 0.2 |
| Accelerometer bias only ‡ | route_hold | 0.2 | 0.4 | 3.1 | 21.0 | 19.3 |
| Gyroscope bias only ‡ | dr_raw | 1.9 | 7.5 | 29.7 | 67.0 | 115.1 |
| Gyroscope bias only ‡ | dr_calibrated | 0.0 | 0.0 | 0.0 | 0.1 | 0.2 |
| Gyroscope bias only ‡ | dr_filtered | 0.0 | 0.0 | 0.1 | 0.2 | 0.3 |
| Gyroscope bias only ‡ | route_imu | 0.1 | 0.0 | 0.1 | 0.1 | 0.2 |
| Gyroscope bias only ‡ | route_hold | 0.2 | 0.4 | 3.1 | 21.0 | 19.3 |
| GPS errors only ‡ | dr_raw | 5.5 | 8.9 | 14.7 | 21.0 | 27.4 |
| GPS errors only ‡ | dr_calibrated | 5.7 | 10.0 | 18.5 | 31.4 | 47.0 |
| GPS errors only ‡ | dr_filtered | 3.4 | 6.2 | 15.6 | 26.7 | 43.0 |
| GPS errors only ‡ | route_imu | 2.5 | 3.8 | 8.1 | 14.6 | 20.7 |
| GPS errors only ‡ | route_hold | 3.4 | 4.5 | 10.6 | 27.6 | 18.0 |
| Noise + bias + GPS errors (results.md) ‡ | dr_raw | 9.2 | 31.2 | 107.6 | 230.8 | 405.6 |
| Noise + bias + GPS errors (results.md) ‡ | dr_calibrated | 5.7 | 9.8 | 18.4 | 30.0 | 44.5 |
| Noise + bias + GPS errors (results.md) ‡ | dr_filtered | 3.3 | 6.5 | 15.3 | 25.5 | 40.5 |
| Noise + bias + GPS errors (results.md) ‡ | route_imu | 2.5 | 3.9 | 8.1 | 15.2 | 20.9 |
| Noise + bias + GPS errors (results.md) ‡ | route_hold | 3.4 | 4.5 | 10.6 | 27.6 | 18.0 |
| Noise + bias + GPS + calibration ‡ | dr_raw | 11.5 | 36.6 | 133.9 | 289.1 | 513.9 |
| Noise + bias + GPS + calibration ‡ | dr_calibrated | 10.2 | 38.7 | 147.8 | 325.6 | 589.2 |
| Noise + bias + GPS + calibration ‡ | dr_filtered | 14.8 | 48.3 | 170.2 | 361.1 | 636.7 |
| Noise + bias + GPS + calibration ‡ | route_imu | 14.7 | 48.2 | 171.5 | 367.2 | 639.7 |
| Noise + bias + GPS + calibration ‡ | route_hold | 3.4 | 4.5 | 10.6 | 27.6 | 18.0 |

**Exit-announcement timing error [s], median of absolute values (main conditions):**

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | 0.0 | 0.0 | 0.0 | 0.0 | 0.8 |
| IMU noise only | 0.1 | 0.1 | 0.1 | 0.1 | 0.8 |
| IMU bias only | 18.4 | 0.0 | 0.0 | 0.0 | 0.8 |
| Calibration error only | 18.6 | 18.6 | 18.6 | 21.5 | 0.8 |
| Noise + bias + calibration | 18.6 | 18.6 | 18.6 | 21.5 | 0.8 |

## Synthetic demo route

Dead-reckoning time from GPS loss to C: 104 s.

**Horizontal error at C [m], median (p90):**

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | 0.0 (0.0) | 0.0 (0.1) | 0.0 (0.0) | 0.3 (0.3) | 13.5 (17.3) |
| IMU noise only | 1.1 (2.0) | 2.0 (3.3) | 2.3 (3.1) | 1.6 (2.7) | 13.5 (17.3) |
| IMU bias only | 272.7 (481.5) | 0.0 (0.1) | 0.0 (0.0) | 0.3 (0.3) | 13.5 (17.3) |
| Calibration error only | 441.5 (445.8) | 441.5 (445.9) | 474.3 (478.6) | 515.6 (519.9) | 13.5 (17.3) |
| Noise + bias + calibration | 380.2 (784.7) | 442.0 (447.4) | 474.9 (480.5) | 516.1 (521.9) | 13.5 (17.3) |
| Accelerometer noise only ‡ | 0.8 (1.5) | 1.2 (2.6) | 1.4 (2.5) | 1.6 (2.6) | 13.5 (17.3) |
| Gyroscope noise only ‡ | 0.7 (1.7) | 1.1 (2.9) | 1.2 (3.0) | 0.3 (0.3) | 13.5 (17.3) |
| Accelerometer bias only ‡ | 255.4 (474.5) | 0.0 (0.1) | 0.0 (0.0) | 0.3 (0.3) | 13.5 (17.3) |
| Gyroscope bias only ‡ | 80.2 (125.1) | 0.1 (0.1) | 0.0 (0.0) | 0.3 (0.3) | 13.5 (17.3) |
| GPS errors only ‡ | 21.1 (42.3) | 31.5 (56.7) | 18.2 (39.4) | 16.5 (42.7) | 17.7 (44.9) |
| Noise + bias + GPS errors (results.md) ‡ | 281.7 (462.9) | 29.3 (55.9) | 17.5 (37.0) | 16.8 (39.8) | 17.7 (44.9) |
| Noise + bias + GPS + calibration ‡ | 388.6 (789.3) | 455.2 (495.8) | 482.2 (506.3) | 523.0 (546.6) | 17.7 (44.9) |

**Along-track / cross-track error at C [m], median of absolute values:**

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 13 / 0 |
| IMU noise only | 1 / 1 | 1 / 1 | 1 / 1 | 2 / 0 | 13 / 0 |
| IMU bias only | 238 / 131 | 0 / 0 | 0 / 0 | 0 / 0 | 13 / 0 |
| Calibration error only | 411 / 162 | 411 / 162 | 441 / 176 | 515 / 11 | 13 / 0 |
| Noise + bias + calibration | 353 / 153 | 412 / 161 | 442 / 175 | 516 / 11 | 13 / 0 |
| Accelerometer noise only ‡ | 1 / 0 | 1 / 1 | 1 / 1 | 2 / 0 | 13 / 0 |
| Gyroscope noise only ‡ | 0 / 1 | 0 / 1 | 0 / 1 | 0 / 0 | 13 / 0 |
| Accelerometer bias only ‡ | 236 / 98 | 0 / 0 | 0 / 0 | 0 / 0 | 13 / 0 |
| Gyroscope bias only ‡ | 30 / 74 | 0 / 0 | 0 / 0 | 0 / 0 | 13 / 0 |
| GPS errors only ‡ | 11 / 16 | 22 / 22 | 14 / 10 | 17 / 0 | 18 / 0 |
| Noise + bias + GPS errors (results.md) ‡ | 232 / 121 | 19 / 22 | 13 / 10 | 17 / 0 | 18 / 0 |
| Noise + bias + GPS + calibration ‡ | 361 / 148 | 426 / 159 | 451 / 176 | 523 / 14 | 18 / 0 |

**Growth exponent p of the median error, e(t) ∝ t^p, between 30 s and 90 s after GPS loss** (1 = constant speed or heading error, 1.5 = random walk of speed or heading, 2 = constant acceleration or turn-rate error; – = below 0.5 m):

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | – | – | – | – | -1.9 |
| IMU noise only | – | – | – | – | -1.9 |
| IMU bias only | 1.9 | – | – | – | -1.9 |
| Calibration error only | 1.8 | 1.8 | 1.7 | 1.7 | -1.9 |
| Noise + bias + calibration | 1.8 | 1.8 | 1.7 | 1.7 | -1.9 |
| Accelerometer noise only ‡ | – | – | – | – | -1.9 |
| Gyroscope noise only ‡ | – | – | – | – | -1.9 |
| Accelerometer bias only ‡ | 1.9 | – | – | – | -1.9 |
| Gyroscope bias only ‡ | 2.0 | – | – | – | -1.9 |
| GPS errors only ‡ | 0.8 | 1.0 | 1.2 | 1.6 | -1.1 |
| Noise + bias + GPS errors (results.md) ‡ | 1.8 | 1.0 | 1.1 | 1.6 | -1.1 |
| Noise + bias + GPS + calibration ‡ | 1.7 | 1.8 | 1.7 | 1.7 | -1.1 |

**Median horizontal error vs. time since GPS loss [m]:**

| condition | estimator | 15 s | 30 s | 60 s | 90 s | 120 s |
|---|---|---|---|---|---|---|
| Ideal sensors, correct calibration | dr_raw | 0.0 | 0.0 | 0.0 | 0.0 | – |
| Ideal sensors, correct calibration | dr_calibrated | 0.0 | 0.0 | 0.1 | 0.0 | – |
| Ideal sensors, correct calibration | dr_filtered | 0.0 | 0.0 | 0.0 | 0.0 | – |
| Ideal sensors, correct calibration | route_imu | 0.1 | 0.0 | 0.1 | 0.3 | – |
| Ideal sensors, correct calibration | route_hold | 8.7 | 30.8 | 33.4 | 3.9 | – |
| IMU noise only | dr_raw | 0.1 | 0.2 | 0.5 | 1.0 | – |
| IMU noise only | dr_calibrated | 0.1 | 0.2 | 0.8 | 1.5 | – |
| IMU noise only | dr_filtered | 0.1 | 0.3 | 0.9 | 1.7 | – |
| IMU noise only | route_imu | 0.1 | 0.2 | 0.6 | 1.4 | – |
| IMU noise only | route_hold | 8.7 | 30.8 | 33.4 | 3.9 | – |
| IMU bias only | dr_raw | 6.4 | 24.8 | 93.5 | 204.0 | – |
| IMU bias only | dr_calibrated | 0.0 | 0.0 | 0.1 | 0.0 | – |
| IMU bias only | dr_filtered | 0.0 | 0.0 | 0.0 | 0.0 | – |
| IMU bias only | route_imu | 0.1 | 0.0 | 0.1 | 0.3 | – |
| IMU bias only | route_hold | 8.7 | 30.8 | 33.4 | 3.9 | – |
| Calibration error only | dr_raw | 12.1 | 45.4 | 155.7 | 331.5 | – |
| Calibration error only | dr_calibrated | 12.1 | 45.4 | 155.7 | 331.5 | – |
| Calibration error only | dr_filtered | 17.2 | 55.6 | 175.2 | 360.1 | – |
| Calibration error only | route_imu | 17.4 | 55.9 | 183.9 | 367.9 | – |
| Calibration error only | route_hold | 8.7 | 30.8 | 33.4 | 3.9 | – |
| Noise + bias + calibration | dr_raw | 10.9 | 40.4 | 135.1 | 286.7 | – |
| Noise + bias + calibration | dr_calibrated | 12.1 | 45.7 | 155.9 | 331.5 | – |
| Noise + bias + calibration | dr_filtered | 17.4 | 55.9 | 175.3 | 360.5 | – |
| Noise + bias + calibration | route_imu | 17.5 | 56.3 | 184.4 | 367.4 | – |
| Noise + bias + calibration | route_hold | 8.7 | 30.8 | 33.4 | 3.9 | – |
| Accelerometer noise only ‡ | dr_raw | 0.0 | 0.1 | 0.4 | 0.7 | – |
| Accelerometer noise only ‡ | dr_calibrated | 0.0 | 0.1 | 0.5 | 1.1 | – |
| Accelerometer noise only ‡ | dr_filtered | 0.1 | 0.2 | 0.6 | 1.2 | – |
| Accelerometer noise only ‡ | route_imu | 0.1 | 0.2 | 0.6 | 1.4 | – |
| Accelerometer noise only ‡ | route_hold | 8.7 | 30.8 | 33.4 | 3.9 | – |
| Gyroscope noise only ‡ | dr_raw | 0.0 | 0.1 | 0.4 | 0.6 | – |
| Gyroscope noise only ‡ | dr_calibrated | 0.0 | 0.1 | 0.4 | 0.7 | – |
| Gyroscope noise only ‡ | dr_filtered | 0.1 | 0.2 | 0.5 | 0.7 | – |
| Gyroscope noise only ‡ | route_imu | 0.1 | 0.0 | 0.1 | 0.3 | – |
| Gyroscope noise only ‡ | route_hold | 8.7 | 30.8 | 33.4 | 3.9 | – |
| Accelerometer bias only ‡ | dr_raw | 6.1 | 23.5 | 88.0 | 191.4 | – |
| Accelerometer bias only ‡ | dr_calibrated | 0.0 | 0.0 | 0.0 | 0.0 | – |
| Accelerometer bias only ‡ | dr_filtered | 0.0 | 0.0 | 0.0 | 0.0 | – |
| Accelerometer bias only ‡ | route_imu | 0.1 | 0.0 | 0.1 | 0.3 | – |
| Accelerometer bias only ‡ | route_hold | 8.7 | 30.8 | 33.4 | 3.9 | – |
| Gyroscope bias only ‡ | dr_raw | 1.8 | 6.7 | 26.7 | 60.4 | – |
| Gyroscope bias only ‡ | dr_calibrated | 0.0 | 0.0 | 0.1 | 0.0 | – |
| Gyroscope bias only ‡ | dr_filtered | 0.0 | 0.0 | 0.0 | 0.0 | – |
| Gyroscope bias only ‡ | route_imu | 0.1 | 0.0 | 0.1 | 0.3 | – |
| Gyroscope bias only ‡ | route_hold | 8.7 | 30.8 | 33.4 | 3.9 | – |
| GPS errors only ‡ | dr_raw | 4.7 | 7.5 | 13.3 | 18.7 | – |
| GPS errors only ‡ | dr_calibrated | 5.0 | 8.0 | 16.2 | 25.2 | – |
| GPS errors only ‡ | dr_filtered | 3.3 | 4.2 | 8.5 | 14.9 | – |
| GPS errors only ‡ | route_imu | 1.3 | 2.2 | 5.3 | 12.2 | – |
| GPS errors only ‡ | route_hold | 8.3 | 29.2 | 31.6 | 8.6 | – |
| Noise + bias + GPS errors (results.md) ‡ | dr_raw | 8.6 | 29.7 | 98.9 | 211.6 | – |
| Noise + bias + GPS errors (results.md) ‡ | dr_calibrated | 5.0 | 7.9 | 15.0 | 23.8 | – |
| Noise + bias + GPS errors (results.md) ‡ | dr_filtered | 3.3 | 4.3 | 8.0 | 14.3 | – |
| Noise + bias + GPS errors (results.md) ‡ | route_imu | 1.3 | 2.1 | 5.7 | 12.0 | – |
| Noise + bias + GPS errors (results.md) ‡ | route_hold | 8.3 | 29.2 | 31.6 | 8.6 | – |
| Noise + bias + GPS + calibration ‡ | dr_raw | 12.4 | 43.1 | 140.0 | 293.9 | – |
| Noise + bias + GPS + calibration ‡ | dr_calibrated | 13.2 | 48.1 | 161.4 | 342.3 | – |
| Noise + bias + GPS + calibration ‡ | dr_filtered | 17.8 | 57.0 | 178.6 | 365.7 | – |
| Noise + bias + GPS + calibration ‡ | route_imu | 17.8 | 56.7 | 187.6 | 370.7 | – |
| Noise + bias + GPS + calibration ‡ | route_hold | 8.3 | 29.2 | 31.6 | 8.6 | – |

**Exit-announcement timing error [s], median of absolute values (main conditions):**

| condition | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Ideal sensors, correct calibration | 0.0 | 0.0 | 0.0 | 0.1 | 0.2 |
| IMU noise only | 0.0 | 0.1 | 0.1 | 0.1 | 0.2 |
| IMU bias only | 5.8 | 0.0 | 0.0 | 0.1 | 0.2 |
| Calibration error only | 19.3 | 19.3 | 19.3 | 19.3 | 0.2 |
| Noise + bias + calibration | 18.3 | 19.3 | 19.3 | 19.3 | 0.2 |
