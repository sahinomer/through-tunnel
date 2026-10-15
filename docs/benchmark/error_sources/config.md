# Error-source benchmark configuration

The settings behind `runs.csv` in this directory (commit `e69543f`). 36 scenarios × 20 runs. Seed rule: run k: scenario seed 1000 + k; IMU, GPS and traffic seed k (same drive in every condition). The complete effective configuration of every scenario is in `config.json`.

## Phone IMU

| setting | value |
|---|---|
| Phone mount | differs by scenario (below) |
| Sample rate | 200 Hz |
| Accelerometer noise | differs by scenario (below) |
| Accelerometer bias | differs by scenario (below) |
| Accelerometer bias drift | differs by scenario (below) |
| Gyroscope noise | differs by scenario (below) |
| Gyroscope bias | differs by scenario (below) |
| Gyroscope bias drift | differs by scenario (below) |
| Gravity / Earth rotation | wgs84 / off |
| Calibration error (injected) | differs by scenario (below) |

## Phone GPS

| setting | value |
|---|---|
| Fix rate | 1 Hz |
| Position error | differs by scenario (below) |
| Speed noise | differs by scenario (below) |
| Loss before B | random, up to 30 m before B |
| Reacquisition after C | 3 s + 0–2 s random |
| Degradation before the portal | differs by scenario (below) |

## Drive and traffic

| setting | value |
|---|---|
| Driver | normal, cruise 70 km/h, ±4 km/h |
| Traffic | differs by scenario (below) |
| Simulation rate | 100 Hz |

## Route and map

| setting | value |
|---|---|
| Tunnel B–C / announcement | 5000 m / 300 m before C |
| Road profile | flat |
| Map | route polyline, exact; map grade off and on for sloped roads (both evaluated) |
| Car speed reading (reference only) | +2 % scale error, 10 Hz |

### Phone mount by scenario

| value | scenarios |
|---|---|
| aligned (yaw 0°, pitch 0°, roll 0°), lever arm (0.0, 0.0, 0.0) m | floor, acc_noise, acc_bias, acc_drift, gyro_noise, gyro_bias, gyro_drift, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_position, gps_speed, gps_degr, gps_degr_harsh, realistic |
| dash_portrait_tilted (yaw -90°, pitch 0°, roll 75°), lever arm (0.0, 0.0, 0.0) m | mount_dash, hard |

### Accelerometer noise by scenario

| value | scenarios |
|---|---|
| off | floor, acc_bias, acc_drift, gyro_noise, gyro_bias, gyro_drift, mount_dash, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_position, gps_speed, gps_degr, gps_degr_harsh |
| 180 µg/√Hz | acc_noise, realistic, hard |

### Accelerometer bias by scenario

| value | scenarios |
|---|---|
| off | floor, acc_noise, acc_drift, gyro_noise, gyro_bias, gyro_drift, mount_dash, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_position, gps_speed, gps_degr, gps_degr_harsh |
| 10 mg, direction random per seed | acc_bias, realistic, hard |

### Accelerometer bias drift by scenario

| value | scenarios |
|---|---|
| off | floor, acc_noise, acc_bias, gyro_noise, gyro_bias, gyro_drift, mount_dash, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_position, gps_speed, gps_degr, gps_degr_harsh |
| on: 0.5 mg, τ 300 s | acc_drift, realistic, hard |

### Gyroscope noise by scenario

| value | scenarios |
|---|---|
| off | floor, acc_noise, acc_bias, acc_drift, gyro_bias, gyro_drift, mount_dash, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_position, gps_speed, gps_degr, gps_degr_harsh |
| 7 mdps/√Hz | gyro_noise, realistic, hard |

### Gyroscope bias by scenario

| value | scenarios |
|---|---|
| off | floor, acc_noise, acc_bias, acc_drift, gyro_noise, gyro_drift, mount_dash, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_position, gps_speed, gps_degr, gps_degr_harsh |
| 0.1 °/s, direction random per seed | gyro_bias, realistic, hard |

### Gyroscope bias drift by scenario

| value | scenarios |
|---|---|
| off | floor, acc_noise, acc_bias, acc_drift, gyro_noise, gyro_bias, mount_dash, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_position, gps_speed, gps_degr, gps_degr_harsh |
| on: 5 mdps, τ 300 s | gyro_drift, realistic, hard |

### Calibration error (injected) by scenario

| value | scenarios |
|---|---|
| none (only the natural residual of the approach calibration) | floor, acc_noise, acc_bias, acc_drift, gyro_noise, gyro_bias, gyro_drift, mount_dash, gps_position, gps_speed, gps_degr, gps_degr_harsh, realistic |
| yaw 0°, pitch 0.1°, roll 0° | cal_pitch_0.1 |
| yaw 0°, pitch 0.5°, roll 0° | cal_pitch_0.5 |
| yaw 2°, pitch 0°, roll 0° | cal_yaw_2 |
| yaw 0°, pitch 0°, roll 0.5° | cal_roll_0.5 |
| yaw 2°, pitch 0.5°, roll 0.5° | hard |

### Position error by scenario

| value | scenarios |
|---|---|
| 0 m correlated (τ 30 s) + 0 m white | floor, acc_noise, acc_bias, acc_drift, gyro_noise, gyro_bias, gyro_drift, mount_dash, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_speed, gps_degr, gps_degr_harsh |
| 2.5 m correlated (τ 30 s) + 0.5 m white | gps_position, realistic, hard |

### Speed noise by scenario

| value | scenarios |
|---|---|
| 0 m/s | floor, acc_noise, acc_bias, acc_drift, gyro_noise, gyro_bias, gyro_drift, mount_dash, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_position, gps_degr, gps_degr_harsh |
| 0.2 m/s | gps_speed, realistic, hard |

### Degradation before the portal by scenario

| value | scenarios |
|---|---|
| off | floor, acc_noise, acc_bias, acc_drift, gyro_noise, gyro_bias, gyro_drift, mount_dash, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_position, gps_speed |
| on: last 150 m before B, up to 8 m extra error at B, 5 % jump probability | gps_degr, realistic, hard |
| on: last 500 m before B, up to 20 m extra error at B, 10 % jump probability | gps_degr_harsh |

### Traffic by scenario

| value | scenarios |
|---|---|
| free flow | floor, acc_noise, acc_bias, acc_drift, gyro_noise, gyro_bias, gyro_drift, mount_dash, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_position, gps_speed, gps_degr, gps_degr_harsh, realistic, hard (free) |
| stop-and-go: 3 stops of 10–60 s, 30 km/h between, ±20 % variation | floor, acc_noise, acc_bias, acc_drift, gyro_noise, gyro_bias, gyro_drift, mount_dash, cal_pitch_0.1, cal_pitch_0.5, cal_yaw_2, cal_roll_0.5, gps_position, gps_speed, gps_degr, gps_degr_harsh, realistic, hard (stop_and_go) |

## Where this setup is optimistic

1. Each condition isolates one error source; interactions between sources show only in *realistic* and *hard*.
2. The map is exact and the road flat, so map errors and grade play no part here (see the benchmark).
