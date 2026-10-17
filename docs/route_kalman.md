# Route-constrained Kalman filter (step 4, first version)

*Superseded in part (2026-10-17): `route_kf` now also estimates the yaw residual (step 4.1, D52, [route_kalman_yaw.md](route_kalman_yaw.md)). The first version below is reproducible with `yaw_state = False`, `turn_noise = 1`.*

Step 4 of [estimator_plan.md](estimator_plan.md), decision D51 (2026-10-16). A new phone-only estimator
`route_kf` next to `route_imu`, with the scope the user agreed:
* a new estimator, not a replacement;
* the calibration and its portal freeze unchanged; the filter replaces only the 5 s speed blend and the
  integration;
* nominal tuning values, never read from the simulator (PD6);
* no standstill oracle.

Data: [route_kalman/](route_kalman/) (development runs, D47; 20 paired seeds). Module:
`positioning/route_kalman.py`.

## The filter

State x = [d, v, b]: distance along the route, speed, forward offset.
* **Prediction**, every IMU sample: d += v·dt + ½(a − b)·dt², v += (a − b)·dt, with a the
  grade-compensated forward specific force. b is a random walk (0.05 mg/√s). The acceleration noise
  is 0.005 m/s²/√Hz: sensor noise plus model error while driving. In turns it grows by the lateral
  acceleration times a nominal yaw uncertainty of 0.5°.
* **Speed updates**, every GPS fix: GPS speed with the phone's reported speed accuracy as σ (solution
  1c). b is learned from how the GPS speed and the integrated IMU diverge, over all fixes (solution 1e),
  not from the last fix. No speed updates in the portal freeze zone (D46).
* **Position**: each fix resets d (as in `route_imu`), gated at 4σ against multipath jumps (at most 3
  fixes in a row). It never updates v or b.
* After an outage the first fix resets d and v; b is kept. The v ≥ 0 clamp stays (no standstill
  information, P5). `position_std_m` reports the 1σ along-route uncertainty.

### Three problems found during validation (all fixed before the evaluation)

1. **The calibration jumps under the filter.** The GPS + IMU calibration re-solves after every fix. Its
   forward offset jumps by **0.85 mg rms from fix to fix** (−2.2 to +0.9 mg in one approach): the
   endpoint form of the levelling, with a new last fix every second. A filter that models b as slowly
   varying averages these jumps and misses the value the freeze locks in.
   * **Fix (D51):** the alignment stage reports how each re-solve moves the forward channel's gravity
     reading, `VehicleImu.offset_shift` = −g·(new up · old forward) + g·Δφ_cal, and the filter moves b
     with it.
   * Verified: reported vs. true change 0.003–0.008 mg rms, against jumps of 0.85 mg rms.
   * It is phone-internal information. Other estimators ignore the field and stay bit-identical.
2. **Position updates corrupted the offset.** Phone GPS position errors are correlated over tens of
   seconds (simulator: 2.5 m, τ 30 s). A slowly wandering position error looks like ~0.3 mg of
   acceleration. Used as normal measurements, they gave b the wrong sign in half the realistic runs.
   Position now resets d only.
3. **A gate on the speed updates locked the filter out.** With a 4σ gate, the updates that should correct
   a wrong offset were exactly the ones rejected, and b never converged. Speed (Doppler) errors are
   white, so the speed is not gated.

A diagnostic mistake of mine, for the record: `CalibrationErrorConfig(enabled=True, pitch_deg=0.1)`
keeps the default yaw error of 2° and roll of 0.5°. With that, b looked only 78 % converged. With the
pitch alone it converges (below).

## Results (development runs, paired, 20 seeds)

Error 5 km into the tunnel (error sources) or at C (benchmark), median (p90) ✗ gross errors (> 200 m).

### Error-source benchmark (5 km flat tunnel)

| condition | traffic | route + IMU | **route_kf** | DR filtered |
|---|---|---|---|---|
| error-free (floor) | free | 0 (0) | 1 (1) | 0 (0) |
| | stop-and-go | 0 (0) | 3 (7) | 0 (0) |
| GPS speed noise | free | 102 (245) ✗4 | **85 (182) ✗2** | 116 (228) ✗4 |
| | stop-and-go | 393 (782) ✗14 | **182 (604) ✗9** | 386 (915) ✗14 |
| GPS degradation (150 m) | free | 4 (8) | 4 (7) | 6 (14) |
| | stop-and-go | 3 (12) | 6 (15) | 7 (14) |
| GPS degradation, harsh | free | 133 (242) ✗7 | **31 (71)** | 129 (239) ✗3 |
| | stop-and-go | 289 (782) ✗13 | **57 (220) ✗3** | 266 (1216) ✗13 |
| calibration pitch 0.1° | free | 628 (675) ✗20 | **3 (4)** | 580 (622) ✗20 |
| | stop-and-go | 977 (1376) ✗20 | **5 (6)** | 900 (1283) ✗20 |
| accelerometer bias drift | free | 90 (182) ✗2 | 92 (145) ✗2 | 83 (169) ✗2 |
| | stop-and-go | 353 (782) ✗15 | 306 (782) ✗14 | 328 (1913) ✗15 |
| **realistic** | free | 103 (257) ✗4 | **85 (283) ✗4** | 117 (240) ✗4 |
| | stop-and-go | 385 (782) ✗16 | **188 (782) ✗9** | 420 (2355) ✗17 |

### Benchmark dev subset (map grade on for sloped roads)

| scenario | route + IMU | **route_kf** | announcement > 15 s off (IMU / KF) |
|---|---|---|---|
| 0.5 km flat, free | 6 (12) | 6 (19) | 0 / 0 |
| 0.5 km flat, stop-and-go | 18 (92) ✗1 | 11 (59) ✗1 | 0 / 0 |
| 5 km flat, free | 103 (257) ✗4 | **85 (283) ✗4** | 1 / 2 |
| 5 km flat, stop-and-go | 385 (782) ✗16 | **188 (782) ✗9** | 16 / 13 |
| 5 km +3 % climb, free | 93 (247) ✗4 | 103 (268) ✗4 | 1 / 0 |
| 5 km +3 % climb, stop-and-go | 501 (782) ✗17 | **228 (782) ✗12** | 16 / 14 |
| 5 km underwater, free | 44 (95) | 40 (86) | 0 / 0 |
| 5 km underwater, stop-and-go | 613 (782) ✗14 | **312 (782) ✗15** | 14 / 15 |

## Findings

1. **A constant calibration residual is now handled: the largest single risk.** A 0.1° pitch residual
   cost `route_imu` 628 m (free) and 977 m (stop-and-go) after 5 km. The filter estimates it from the
   approach and ends at 3 and 5 m. The benchmark injects no calibration error (listed as optimistic in
   its configuration), so its tables do not show this gain. Real calibrations do leave residuals.
2. **Stop-and-go roughly halves**, without any standstill information: realistic 385 → 188 m (gross
   errors 16 → 9), climb 501 → 228 m, GPS speed noise alone 393 → 182 m.
   * With a smaller handover offset, less error creeps through the stops (P5).
   * The clamp still decides the tails: p90 at the route-end cap and the underwater runaways remain
     (underwater gross errors 14 → 15).
3. **Free flow gains less and is mixed.** Realistic 103 → 85 m median, but p90 257 → 283 m and the climb
   93 → 103 m.
   * In the realistic setting the remaining offset is small (endpoint noise, ~0.2 mg), and b is not
     estimated much better than that.
   * The handover speed error is slightly larger than the 5 s blend's (0.056 vs 0.047 m/s): the filter
     trusts the IMU more.
4. **Harsh degradation: 133 → 31 m, partly flattering.** The filter down-weights the degraded fixes by
   their reported speed accuracy (1c). In the simulation that accuracy equals the injected noise exactly;
   a real phone reports it less faithfully.
5. **The yaw residual is the next limit.** Pitch alone: b found to within 0.01 mg, 3 m at C. With a 2°
   yaw error added: b 0.4 mg off, 69 m at C (`route_imu`: 553 m). In turns the yaw residual leaks
   lateral acceleration into the forward channel, which b cannot separate. Estimating yaw online
   (solution 6b, step 5) targets this.
6. **Small costs:** the error-free floor goes from 0 to 1–3 m (the filter's process noise lets small
   approach errors in), and the 0.5 km flat p90 rises from 12 to 19 m.

## Limits and open points

* **Tuning by reasoning, not optimised.** The model-error noise trades how fast b is learned against how
  much model error is absorbed. With error-free sensors b was not fully converged in a short approach.
  A deliberate tuning-mismatch study (R7) is still open.
* The reported speed accuracy flatters solution 1c (point 4).
* Development runs only. The full benchmarks are due at the milestone after the filter.
* Not yet used: `position_std_m` for uncertainty-aware announcements (3d), and a soft portal trust curve
  instead of the hard freeze.
