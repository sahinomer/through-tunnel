# Error-source benchmark comparison

Baseline commit `00ab89b`, this run `1b280f4+dirty`. Median error 5 km into the tunnel [m], baseline → this run.

| estimator | floor / free | cal_pitch_0.1 / free | cal_yaw_2 / free | gps_speed / free | gps_degr / free | gps_degr_harsh / free | realistic / free | hard / free | floor / stop_and_go | cal_pitch_0.1 / stop_and_go | cal_yaw_2 / stop_and_go | gps_speed / stop_and_go | gps_degr / stop_and_go | gps_degr_harsh / stop_and_go | realistic / stop_and_go | hard / stop_and_go |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DR GPS-calibrated IMU | 0 → 0 | 526 → 526 | 56 → 56 | 112 → 112 | 121 → 121 | 170 → 170 | 167 → 167 | 2601 → 2601 | 2 → 2 | 871 → 871 | 67 → 67 | 391 → 391 | 159 → 159 | 316 → 316 | 561 → 561 | 3267 → 3267 |
| DR calibrated + GPS-blended speed/heading | 0 → 0 | 580 → 580 | 64 → 64 | 116 → 116 | 6 → 6 | 129 → 129 | 117 → 117 | 2786 → 2786 | 0 → 0 | 900 → 900 | 90 → 90 | 386 → 386 | 7 → 7 | 266 → 266 | 420 → 420 | 3399 → 3399 |
| Route + filtered IMU speed | 0 → 0 | 628 → 628 | 67 → 67 | 102 → 102 | 4 → 4 | 133 → 133 | 103 → 103 | 2760 → 2760 | 0 → 0 | 977 → 977 | 96 → 96 | 393 → 393 | 3 → 3 | 289 → 289 | 385 → 385 | 3390 → 3390 |
| Route + IMU Kalman filter (distance, speed, offset) | 1 → 1 | 3 → 0 | 65 → 64 | 85 → 86 | 4 → 4 | 31 → 31 | 85 → 80 | 255 → 361 | 3 → 3 | 5 → 3 | 204 → 203 | 182 → 172 | 6 → 6 | 57 → 57 | 188 → 241 | 782 → 782 |
| Route + IMU Kalman filter + yaw (distance, speed, offset, yaw) | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – |
| Route + vehicle speed (reference) | 0 → 0 | 0 → 0 | 0 → 0 | 4 → 4 | 5 → 5 | 11 → 11 | 6 → 6 | 6 → 6 | 0 → 0 | 0 → 0 | 0 → 0 | 4 → 4 | 4 → 4 | 10 → 10 | 7 → 7 | 7 → 7 |
| Route + IMU + standstill oracle: speed reset ‡ | 0 → 0 | 628 → 628 | 67 → 67 | 102 → 102 | 4 → 4 | 133 → 133 | 103 → 103 | 2760 → 2760 | 0 → 0 | 977 → 977 | 8 → 8 | 120 → 120 | 3 → 3 | 227 → 227 | 131 → 131 | 3390 → 3390 |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 0 → 0 | 628 → 628 | 67 → 67 | 102 → 102 | 4 → 4 | 133 → 133 | 103 → 103 | 2760 → 2760 | 0 → 0 | 130 → 130 | 9 → 9 | 27 → 27 | 3 → 3 | 34 → 34 | 103 → 103 | 543 → 543 |
