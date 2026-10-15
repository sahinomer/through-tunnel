# Calibration error: how a wrong phone orientation propagates

Study of 2026-10-13 (decision D34). It measures how calibration error affects positioning. It does
not try to correct it: no new calibration or correction methods were added. Reproduce with:

```bash
uv run python -m throughtunnel.evaluation.calibration_study --seeds 10
```

## 1. What is modelled

* **Actual vs assumed orientation.** The actual phone mounting (`ImuConfig.mount`) alone drives the
  sensor simulation. The orientation an estimator *uses* is separate:
  * `dr_raw` declares it ("aligned");
  * `dr_calibrated`, `dr_filtered` and `route_imu` estimate it from approach-phase GPS: levelling from
    gravity, yaw from GPS-vs-IMU acceleration.
* **Calibration error** (`ScenarioConfig.calibration`; UI: *Calibration error (assumed orientation)*).
  It is a constant rotation applied to the orientation each estimator uses. The assumed vehicle axes
  are its own axes rotated by `R_err = Rz(yaw) Ry(pitch) Rx(roll)`, in vehicle axes:
  * + yaw: the assumed forward axis points to the left of the true one;
  * + pitch: the assumed forward axis points nose-down;
  * + roll: the assumed up axis tilts to the right.

  Default when enabled: 2° / 0.5° / 0.5°, an order-of-magnitude assumption for an online smartphone
  calibration.
* **Why a residual, not a wrong prior.** The calibrated estimators *estimate* the orientation. A wrong
  orientation *handed to* them would simply be re-estimated, and only `dr_raw` would notice. Real
  self-calibration leaves residuals for reasons this simulator does not model:
  * vehicle body pitch under load, acceleration or braking during calibration;
  * a road grade that differs between calibration and tunnel;
  * the phone shifting in its holder.

  The injected residual stands in for all of these without modelling the cause.
* **Information policy.** The error is an experiment setting applied by the harness. Since D40
  (2026-10-15) it rotates the orientation of the *alignment stage*, the step between the
  observations and the estimators; originally it was an estimator argument
  (`Estimator(..., calibration_error=R)`), with bit-identical results. It is not an observation, so
  the estimators cannot observe or correct it. The sensor data is identical with or without the error (tested). Only positioning
  re-runs.

## 2. Experiment

For each preset (Eisenhower 2.7 km nearly straight, Seattle 3.0 km, synthetic 2.0 km curvy) and each
of 10 sensor/GPS seeds, the scenario is simulated **once**, on the preset drive. All five estimators
then run on these identical observations: once without calibration error, and once per case:
* yaw ±1–5°;
* pitch 0.05–0.5°;
* roll 2–5°;
* the default combination.

So every comparison is paired: drive, sensor noise and bias, GPS errors and outage are the same; only
the assumed orientation differs. Reported quantities:
* the error at the tunnel exit C;
* the paired shift of the along-track error at C, i.e. what the calibration error adds;
* the error vs. time since GPS loss.

Full tables: appendix.

## 3. Results

### 3.1 Error at C, best estimator and naive reference [m, median of 10 runs]

| calibration error | Eisenhower `route_imu` | Seattle `route_imu` | Synthetic `route_imu` | `route_hold` (E / S / Syn) |
|---|---|---|---|---|
| none | 25 | 28 | 19 | 329 / 22 / 11 |
| yaw +2° | 61 | 39 | 29 | unchanged |
| yaw +5° | 126 | 42 | 45 | unchanged |
| roll +5° | 25 | 28 | 19 | unchanged |
| pitch +0.05° | 90 | 106 | 57 | unchanged |
| pitch +0.1° | 162 | 209 | 107 | unchanged |
| pitch +0.25° | 378 | 516 | 257 | unchanged |
| pitch +0.5° | 737 | 1019 | 506 | unchanged |
| default (2°, 0.5°, 0.5°) | 781 | 1002 | 523 | unchanged |

### 3.2 Along-track shift at C added by the error (paired, median) [m]

| calibration error | Eisenhower | Seattle | Synthetic | prediction |
|---|---|---|---|---|
| pitch +0.1°, `dr_calibrated` | −134 | −182 | −78 | −½·g·sin θ·τ² |
| pitch +0.1°, `route_imu` | −143 | −206 | −100 | same + speed lag carried in from the approach |
| yaw +2°, `dr_calibrated` | −31 | +19 | −20 | sin δ·∬a_lat (−34 / +24 / −17 with ideal sensors) |
| yaw −2°, `dr_calibrated` | +31 | −19 | +20 | sign-symmetric |
| roll +5°, all | −2 … +9 | | | ≈ 0 |

The pitch shifts are almost deterministic: min–max over the 10 runs is within ±3% of the median.

### 3.3 Growth over time (Eisenhower, `route_imu`, median error [m])

| time since GPS loss | none | yaw +2° | pitch +0.1° | pitch +0.5° | ½·g·sin(0.5°)·τ² |
|---|---|---|---|---|---|
| 15 s | 2 | 6 | 4 | 16 | 10 |
| 30 s | 3 | 13 | 12 | 52 | 38 |
| 60 s | 6 | 28 | 41 | 183 | 154 |
| 90 s | 13 | 44 | 87 | 392 | 346 |
| 120 s | 23 | 59 | 149 | 677 | 616 |

## 4. Findings

1. **Pitch error dominates, by orders of magnitude.**
   * *Mechanism:* a nose-down forward axis lets gravity leak into the forward channel as −g·sin θ.
     That is 0.17 m/s² (17 mg) per degree: a constant forward specific-force error.
   * *Effect:* the speed error grows linearly, and the along-track position error quadratically as
     −½·g·sin θ·τ², where τ is the time since the last fix. The measured shifts follow this closely,
     and the tests confirm it within 2% on a straight road.
   * *Size:* 0.05° (0.9 mg, a tenth of the simulated accelerometer bias) already adds 40–100 m at C.
     0.5° adds 0.4–1 km.
2. **The current headline accuracy needs an unrealistically good pitch calibration.**
   * The best estimator ends the tunnel 20–30 m off. Keeping the added error below that requires a
     pitch residual of about **0.02°**. The added error scales linearly with the angle: 0.05° adds
     40–100 m.
   * On the simulated flat road with a rigid, static mount, the gravity levelling achieves this: that
     is exactly how it cancels the accelerometer bias.
   * Real conditions easily exceed it:
     * 1% of grade difference between approach and tunnel is 0.57°;
     * the vehicle body pitches by a few tenths of a degree when accelerating, braking or loaded.
   * **This is the same weakness as the flat-road caveat (roadmap R1), now quantified.** A grade change
     acts like a pitch calibration error of the same angle: 3% ≈ 1.7°, i.e. kilometres of error after
     two minutes. **R1 will likely make the IMU-based results much worse unless the method changes.**
3. **Every IMU-integrating estimator is affected about equally; the route constraint does not help.**
   * All of them integrate the same forward channel, and none observes speed inside the tunnel.
   * Calibration error produces along-track error. The route constraint removes cross-track and
     heading error, which this does not create.
   * The GPS-blended estimators (`dr_filtered`, `route_imu`) are slightly **more** affected, +5–28%:
     * during the approach, their 5 s speed filter settles to a lag of about 4·g·sin θ;
     * that lag is carried into the tunnel as an initial speed error;
     * on curvy routes, plain dead reckoning also "loses" part of the shortfall to cross-track error,
       while the route estimator keeps all of it along the route.
4. **The inertial advantage over the naive reference disappears at about 0.1° of pitch.**
   * The naive `route_hold` ignores the IMU, so it is immune to calibration error.
   * On the fixed preset drives used here, its error depends on the drive: 22 m on Seattle and 11 m on
     the synthetic route (it already beats `route_imu` there without any calibration error), but 329 m
     on Eisenhower. The fair yardstick is its result across varied drives (results.md): median
     59–95 m, p90 147–195 m.
   * At 0.1° of pitch residual, the best inertial estimator is already at 107–209 m, no better than
     the naive reference. At 0.25° (257–516 m) it is clearly worse. On Eisenhower, the drive where the
     naive does badly, the crossover is at about 0.25°.
   * So the advantage of inertial dead reckoning holds only with a pitch calibration well below 0.1°.
5. **Yaw error is moderate and depends on the tunnel's curves.**
   * *Mechanism:* the forward channel picks up sin δ·a_lat, so the speed error equals sin δ times the
     lateral acceleration integrated since the last fix.
   * It depends on **where** the curves are, not on the net heading change. A curve early in the
     outage leaks a speed error that lasts the rest of the outage. This is why the nearly straight
     Eisenhower route (−6° net heading change, but an early curve) shows the largest yaw shift.
   * The effect is linear in δ and changes sign with it. 2° adds about 20–45 m, 5° adds 45–110 m.
   * The heading is not affected: the yaw rate is measured about the up axis, which a yaw error does
     not tilt.
   * The spread between seeds comes from residual lateral specific-force errors that the rotated axis
     also mixes in.
6. **Roll error is negligible on a flat road** (≤ about 10 m at 5°). It only tilts the assumed up axis, which
   scales the yaw rate by cos φ; nothing leaks into the forward channel, and the lateral channel is
   not integrated. It would matter with banking or pitch/roll rates, which are not modelled.
7. **`dr_raw` is not a useful indicator here.** Its own uncorrected accelerometer bias produces
   300–750 m. An added pitch error sometimes *reduces* its total error at C by partly cancelling that
   bias. This is a coincidence of signs; its p90 grows.

## 5. Limitations of this study

* The error is constant, injected and not tied to a cause. Real residuals vary with the drive (body
  pitch with acceleration, load) and in time (holder shift). There is no random per-drive draw, and the
  error is applied during the approach as well.
* One drive per preset, 10 sensor seeds. The calibration effects are nearly deterministic, so 10 runs
  are enough for the shifts; the percentiles are indicative.
* A static pitch error would be removed by the levelling if it were present in the data. The injected
  residual represents conditions the simulator does not produce (see §1). Simulating those causes
  (R1 grade; body pitch; mount shift) would replace the injection with physics.

## Appendix: full output of the study

#### Eisenhower Tunnel, I-70 (westbound)

Tunnel B–C crossed in 125 s (preset drive); net heading change -6°; ∫a_lat dt = -3.0 m/s (∫|a_lat| dt = 10.9 m/s). 10 runs (sensor/GPS seeds 0–9), same drive; every case uses the identical observations. Computed in 204 s.

Horizontal error at C [m], median (p90):

| calibration error | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| none | 522 (784) | 52 (76) | 26 (61) | 25 (62) | 329 (349) |
| yaw +1° | 520 (770) | 60 (90) | 40 (82) | 39 (82) | 329 (349) |
| yaw +2° | 519 (754) | 70 (106) | 62 (103) | 61 (103) | 329 (349) |
| yaw −2° | 540 (812) | 42 (80) | 36 (61) | 24 (60) | 329 (349) |
| yaw +5° | 492 (715) | 103 (153) | 126 (165) | 126 (165) | 329 (349) |
| pitch +0.05° | 519 (726) | 106 (138) | 90 (134) | 90 (134) | 329 (349) |
| pitch +0.1° | 469 (673) | 164 (205) | 161 (206) | 162 (207) | 329 (349) |
| pitch +0.25° | 395 (794) | 358 (406) | 377 (424) | 378 (424) | 329 (349) |
| pitch +0.5° | 424 (1122) | 697 (739) | 737 (786) | 737 (786) | 329 (349) |
| roll +2° | 520 (785) | 54 (74) | 28 (61) | 25 (62) | 329 (349) |
| roll +5° | 519 (785) | 57 (70) | 29 (62) | 25 (62) | 329 (349) |
| typical (2°, 0.5°, 0.5°) | 438 (1157) | 721 (771) | 780 (828) | 781 (829) | 329 (349) |

Along-track shift at C caused by the calibration error (paired) [m], median [min, max]:

| calibration error | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| yaw +1° | -19 [-29, -4] | -15 [-20, -11] | -22 [-26, -17] | -23 [-27, -17] | +0 [+0, +0] |
| yaw +2° | -38 [-57, -8] | -31 [-40, -22] | -45 [-53, -34] | -45 [-53, -34] | +0 [+0, +0] |
| yaw −2° | +38 [+8, +58] | +31 [+23, +41] | +45 [+34, +53] | +45 [+35, +54] | +0 [+0, +0] |
| yaw +5° | -93 [-142, -19] | -75 [-99, -55] | -111 [-131, -84] | -111 [-131, -85] | +0 [+0, +0] |
| pitch +0.05° | -67 [-68, -65] | -67 [-68, -66] | -71 [-72, -70] | -72 [-72, -70] | +0 [+0, +0] |
| pitch +0.1° | -134 [-136, -131] | -134 [-135, -132] | -143 [-144, -140] | -143 [-144, -140] | +0 [+0, +0] |
| pitch +0.25° | -335 [-340, -327] | -336 [-338, -329] | -357 [-360, -351] | -358 [-361, -351] | +0 [+0, +0] |
| pitch +0.5° | -669 [-680, -654] | -671 [-676, -659] | -714 [-720, -701] | -716 [-721, -702] | +0 [+0, +0] |
| roll +2° | -1 [-2, +1] | -1 [-1, +0] | -1 [-1, +0] | +0 [+0, +0] | +0 [+0, +0] |
| roll +5° | -2 [-4, +2] | -1 [-3, +1] | -1 [-3, +2] | +0 [+0, +0] | +0 [+0, +0] |
| typical (2°, 0.5°, 0.5°) | -702 [-730, -682] | -702 [-715, -690] | -756 [-770, -745] | -758 [-771, -747] | +0 [+0, +0] |

Horizontal error vs. time since GPS loss [m], median (p90):

| time since GPS loss | dr_calibrated: none | dr_calibrated: yaw +2° | dr_calibrated: pitch +0.1° | dr_calibrated: pitch +0.5° | dr_calibrated: typical (2°, 0.5°, 0.5°) | route_imu: none | route_imu: yaw +2° | route_imu: pitch +0.1° | route_imu: pitch +0.5° | route_imu: typical (2°, 0.5°, 0.5°) | ½·g·sin(0.1°)·τ² | ½·g·sin(0.5°)·τ² |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 15 s | 5 (8) | 6 (9) | 5 (9) | 11 (16) | 14 (19) | 2 (4) | 6 (9) | 4 (7) | 16 (20) | 21 (25) | 2 | 10 |
| 30 s | 9 (16) | 14 (20) | 14 (20) | 42 (51) | 50 (58) | 3 (9) | 13 (19) | 12 (19) | 52 (58) | 63 (68) | 8 | 38 |
| 60 s | 20 (30) | 32 (42) | 45 (57) | 164 (179) | 178 (195) | 6 (18) | 28 (42) | 41 (53) | 183 (195) | 205 (219) | 31 | 154 |
| 90 s | 34 (48) | 51 (68) | 89 (110) | 363 (389) | 382 (414) | 13 (36) | 44 (69) | 87 (112) | 392 (417) | 425 (451) | 69 | 346 |
| 120 s | 49 (72) | 67 (101) | 152 (189) | 639 (683) | 662 (714) | 23 (58) | 59 (98) | 149 (191) | 677 (722) | 720 (762) | 123 | 616 |

#### Seattle SR 99 Tunnel (northbound)

Tunnel B–C crossed in 150 s (preset drive); net heading change -7°; ∫a_lat dt = -2.3 m/s (∫|a_lat| dt = 27.7 m/s). 10 runs (sensor/GPS seeds 0–9), same drive; every case uses the identical observations. Computed in 308 s.

Horizontal error at C [m], median (p90):

| calibration error | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| none | 746 (1070) | 74 (100) | 68 (92) | 28 (72) | 22 (54) |
| yaw +1° | 757 (1078) | 73 (104) | 72 (94) | 38 (80) | 22 (54) |
| yaw +2° | 769 (1086) | 81 (112) | 73 (100) | 39 (83) | 22 (54) |
| yaw −2° | 735 (1052) | 72 (112) | 74 (99) | 31 (84) | 22 (54) |
| yaw +5° | 800 (1108) | 91 (152) | 72 (127) | 42 (123) | 22 (54) |
| pitch +0.05° | 729 (992) | 112 (166) | 116 (164) | 106 (164) | 22 (54) |
| pitch +0.1° | 687 (917) | 203 (261) | 214 (264) | 209 (268) | 22 (54) |
| pitch +0.25° | 542 (1093) | 481 (552) | 510 (569) | 516 (579) | 22 (54) |
| pitch +0.5° | 553 (1548) | 955 (1034) | 1011 (1079) | 1019 (1088) | 22 (54) |
| roll +2° | 742 (1071) | 76 (99) | 72 (99) | 28 (72) | 22 (54) |
| roll +5° | 736 (1074) | 83 (105) | 85 (113) | 28 (72) | 22 (54) |
| typical (2°, 0.5°, 0.5°) | 510 (1531) | 929 (1011) | 994 (1055) | 1002 (1064) | 22 (54) |

Along-track shift at C caused by the calibration error (paired) [m], median [min, max]:

| calibration error | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| yaw +1° | +7 [-7, +28] | +10 [+8, +15] | +9 [+7, +14] | +10 [+8, +16] | +0 [+0, +0] |
| yaw +2° | +14 [-13, +55] | +19 [+16, +29] | +18 [+13, +28] | +20 [+16, +31] | +0 [+0, +0] |
| yaw −2° | -15 [-56, +13] | -19 [-29, -15] | -18 [-28, -13] | -20 [-32, -16] | +0 [+0, +0] |
| yaw +5° | +35 [-32, +137] | +48 [+39, +73] | +44 [+33, +71] | +50 [+40, +77] | +0 [+0, +0] |
| pitch +0.05° | -91 [-94, -84] | -91 [-92, -89] | -96 [-97, -94] | -103 [-105, -102] | +0 [+0, +0] |
| pitch +0.1° | -182 [-188, -168] | -182 [-184, -179] | -192 [-194, -188] | -206 [-209, -204] | +0 [+0, +0] |
| pitch +0.25° | -455 [-470, -419] | -455 [-459, -447] | -479 [-485, -470] | -512 [-518, -504] | +0 [+0, +0] |
| pitch +0.5° | -899 [-939, -835] | -910 [-918, -895] | -958 [-969, -941] | -990 [-1004, -968] | +0 [+0, +0] |
| roll +2° | +3 [-0, +6] | +3 [-1, +4] | +3 [-1, +4] | +0 [+0, +0] | +0 [+0, +0] |
| roll +5° | +9 [-1, +16] | +7 [-2, +10] | +8 [-3, +12] | +0 [+0, +0] | +0 [+0, +0] |
| typical (2°, 0.5°, 0.5°) | -868 [-952, -812] | -888 [-897, -876] | -937 [-947, -924] | -967 [-985, -953] | +0 [+0, +0] |

Horizontal error vs. time since GPS loss [m], median (p90):

| time since GPS loss | dr_calibrated: none | dr_calibrated: yaw +2° | dr_calibrated: pitch +0.1° | dr_calibrated: pitch +0.5° | dr_calibrated: typical (2°, 0.5°, 0.5°) | route_imu: none | route_imu: yaw +2° | route_imu: pitch +0.1° | route_imu: pitch +0.5° | route_imu: typical (2°, 0.5°, 0.5°) | ½·g·sin(0.1°)·τ² | ½·g·sin(0.5°)·τ² |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 15 s | 5 (8) | 5 (9) | 5 (8) | 10 (15) | 9 (15) | 2 (6) | 3 (6) | 3 (7) | 15 (19) | 15 (19) | 2 | 10 |
| 30 s | 10 (13) | 10 (14) | 13 (17) | 39 (48) | 39 (48) | 4 (8) | 4 (8) | 8 (17) | 48 (57) | 48 (57) | 8 | 38 |
| 60 s | 21 (30) | 22 (32) | 36 (49) | 156 (173) | 150 (168) | 8 (17) | 8 (21) | 34 (50) | 175 (193) | 172 (188) | 31 | 154 |
| 90 s | 37 (47) | 43 (56) | 77 (102) | 345 (376) | 329 (360) | 13 (31) | 19 (42) | 76 (102) | 380 (410) | 368 (394) | 69 | 346 |
| 120 s | 55 (72) | 65 (84) | 132 (170) | 612 (664) | 588 (640) | 19 (49) | 28 (63) | 134 (173) | 659 (703) | 641 (680) | 123 | 616 |

#### Synthetic demo route

Tunnel B–C crossed in 103 s (preset drive); net heading change -39°; ∫a_lat dt = -13.4 m/s (∫|a_lat| dt = 45.1 m/s). 10 runs (sensor/GPS seeds 0–9), same drive; every case uses the identical observations. Computed in 240 s.

Horizontal error at C [m], median (p90):

| calibration error | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| none | 330 (452) | 33 (65) | 21 (41) | 19 (44) | 11 (45) |
| yaw +1° | 324 (441) | 34 (73) | 27 (50) | 25 (55) | 11 (45) |
| yaw +2° | 325 (430) | 36 (82) | 30 (60) | 29 (66) | 11 (45) |
| yaw −2° | 330 (473) | 44 (56) | 22 (39) | 21 (41) | 11 (45) |
| yaw +5° | 326 (414) | 63 (110) | 56 (92) | 45 (97) | 11 (45) |
| pitch +0.05° | 322 (422) | 58 (106) | 53 (86) | 57 (95) | 11 (45) |
| pitch +0.1° | 306 (389) | 99 (148) | 99 (131) | 107 (145) | 11 (45) |
| pitch +0.25° | 232 (470) | 225 (273) | 236 (269) | 257 (295) | 11 (45) |
| pitch +0.5° | 259 (675) | 436 (483) | 464 (499) | 506 (543) | 11 (45) |
| roll +2° | 329 (452) | 32 (67) | 21 (42) | 19 (44) | 11 (45) |
| roll +5° | 328 (454) | 32 (68) | 22 (43) | 19 (44) | 11 (45) |
| typical (2°, 0.5°, 0.5°) | 267 (696) | 455 (502) | 482 (519) | 523 (561) | 11 (45) |

Along-track shift at C caused by the calibration error (paired) [m], median [min, max]:

| calibration error | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| yaw +1° | -11 [-17, -2] | -10 [-12, -7] | -10 [-11, -7] | -9 [-11, -5] | +0 [+0, +0] |
| yaw +2° | -22 [-34, -4] | -20 [-23, -14] | -20 [-23, -14] | -18 [-22, -11] | +0 [+0, +0] |
| yaw −2° | +22 [+4, +34] | +20 [+14, +23] | +20 [+14, +23] | +18 [+11, +22] | +0 [+0, +0] |
| yaw +5° | -55 [-85, -11] | -51 [-58, -36] | -50 [-57, -34] | -45 [-54, -27] | +0 [+0, +0] |
| pitch +0.05° | -39 [-41, -37] | -39 [-40, -39] | -42 [-43, -41] | -50 [-51, -49] | +0 [+0, +0] |
| pitch +0.1° | -78 [-81, -74] | -78 [-80, -77] | -84 [-86, -83] | -100 [-101, -98] | +0 [+0, +0] |
| pitch +0.25° | -196 [-203, -185] | -196 [-199, -193] | -211 [-214, -207] | -250 [-254, -246] | +0 [+0, +0] |
| pitch +0.5° | -392 [-407, -370] | -391 [-398, -385] | -422 [-428, -414] | -499 [-506, -491] | +0 [+0, +0] |
| roll +2° | +1 [-0, +2] | +1 [-1, +2] | +2 [-1, +3] | +0 [+0, +0] | +0 [+0, +0] |
| roll +5° | +4 [-1, +6] | +3 [-2, +5] | +4 [-2, +6] | +0 [+0, +0] | +0 [+0, +0] |
| typical (2°, 0.5°, 0.5°) | -411 [-441, -393] | -410 [-421, -403] | -439 [-448, -433] | -514 [-521, -507] | +0 [+0, +0] |

Horizontal error vs. time since GPS loss [m], median (p90):

| time since GPS loss | dr_calibrated: none | dr_calibrated: yaw +2° | dr_calibrated: pitch +0.1° | dr_calibrated: pitch +0.5° | dr_calibrated: typical (2°, 0.5°, 0.5°) | route_imu: none | route_imu: yaw +2° | route_imu: pitch +0.1° | route_imu: pitch +0.5° | route_imu: typical (2°, 0.5°, 0.5°) | ½·g·sin(0.1°)·τ² | ½·g·sin(0.5°)·τ² |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 15 s | 5 (9) | 4 (10) | 4 (10) | 11 (15) | 12 (17) | 2 (4) | 2 (5) | 3 (6) | 15 (19) | 17 (21) | 2 | 10 |
| 30 s | 8 (14) | 9 (20) | 10 (21) | 42 (51) | 48 (57) | 3 (7) | 5 (12) | 10 (16) | 50 (57) | 55 (63) | 8 | 38 |
| 60 s | 17 (32) | 17 (39) | 36 (61) | 154 (179) | 161 (187) | 7 (17) | 11 (26) | 38 (53) | 179 (196) | 186 (205) | 31 | 154 |
| 90 s | 28 (55) | 30 (65) | 75 (118) | 332 (375) | 343 (387) | 16 (35) | 22 (49) | 81 (111) | 363 (387) | 370 (398) | 69 | 346 |
| 120 s | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 123 | 616 |
