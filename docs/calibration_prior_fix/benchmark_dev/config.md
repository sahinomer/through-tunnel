# Benchmark configuration

The settings behind `runs.csv` in this directory (commit `1b280f4+dirty`). 10 scenarios × 20 runs. Seed rule: run k: scenario seed 1000 + k; IMU, GPS and traffic seed k. The complete effective configuration of every scenario is in `config.json`.

## Phone IMU

| setting | value |
|---|---|
| Phone mount | aligned (yaw 0°, pitch 0°, roll 0°), lever arm (0.0, 0.0, 0.0) m |
| Sample rate | 200 Hz |
| Accelerometer noise | 180 µg/√Hz |
| Accelerometer bias | 10 mg, direction random per seed |
| Accelerometer bias drift | on: 0.5 mg, τ 300 s |
| Gyroscope noise | 7 mdps/√Hz |
| Gyroscope bias | 0.1 °/s, direction random per seed |
| Gyroscope bias drift | on: 5 mdps, τ 300 s |
| Gravity / Earth rotation | wgs84 / off |
| Calibration error (injected) | none (only the natural residual of the approach calibration) |

## Phone GPS

| setting | value |
|---|---|
| Fix rate | 1 Hz |
| Position error | 2.5 m correlated (τ 30 s) + 0.5 m white |
| Speed noise | 0.2 m/s |
| Loss before B | random, up to 30 m before B |
| Reacquisition after C | 3 s + 0–2 s random |
| Degradation before the portal | on: last 150 m before B, up to 8 m extra error at B, 5 % jump probability |

## Drive and traffic

| setting | value |
|---|---|
| Driver | differs by scenario (below) |
| Traffic | differs by scenario (below) |
| Simulation rate | 100 Hz |

## Route and map

| setting | value |
|---|---|
| Tunnel B–C / announcement | differs by scenario (below) |
| Road profile | differs by scenario (below) |
| Map | route polyline, exact; map grade off and on for sloped roads (both evaluated) |
| Car speed reading (reference only) | +2 % scale error, 10 Hz |
| Standstill oracle (‡ oracle estimators only) | perfect (from the truth) |

### Driver by scenario

| value | scenarios |
|---|---|
| normal, cruise 70 km/h, ±4 km/h | ladder_0.5km, ladder_5km |
| normal, cruise 80 km/h, ±4 km/h | eisenhower_tunnel (flat) |

### Traffic by scenario

| value | scenarios |
|---|---|
| free flow | eisenhower_tunnel, ladder_0.5km, ladder_5km (free) |
| stop-and-go: 3 stops of 10–60 s, 30 km/h between, ±20 % variation | eisenhower_tunnel, ladder_0.5km, ladder_5km (stop_and_go) |

### Tunnel B–C / announcement by scenario

| value | scenarios |
|---|---|
| 500 m / 300 m before C | ladder_0.5km (flat) |
| 5000 m / 300 m before C | ladder_5km |
| 2724 m / 300 m before C | eisenhower_tunnel (flat) |

### Road profile by scenario

| value | scenarios |
|---|---|
| flat | eisenhower_tunnel, ladder_0.5km, ladder_5km (flat) |
| steepest grade 3.2 %, height +0 … +150 m | ladder_5km (climb3) |
| steepest grade 4.3 %, height -80 … +0 m | ladder_5km (underwater) |

## Where this setup is optimistic

1. **The phone is mounted perfectly aligned** with the vehicle (and lever arm 0). Real holders tilt the phone. This mainly flatters `dr_raw`, whose aligned assumption is then exactly true; the calibrated estimators estimate the mount anyway.
2. **No calibration error is injected**: only the natural residual of the approach calibration (from noise, bias and GPS errors) remains. Real calibrations leave more, and a 0.1° pitch residual costs hundreds of metres in long outages (calibration_error.md), so the phone-only numbers are likely optimistic.
3. **The map is exact** (geometry and grade, user decision): this flatters the route-constrained and map-grade results (limitations.md).
4. Earth rotation is off.
