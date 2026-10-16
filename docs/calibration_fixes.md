# Calibration fixes F1–F3 (step 2.1): gravity, interval timing, grade in the yaw fit

Step 2.1 of [estimator_plan.md](estimator_plan.md), decision D48 (2026-10-16). The residual diagnostic
([residual_study.md](residual_study.md)) explained the error-free-sensor residuals by three systematic
terms. This step removes them in the calibration and the map-grade correction. They are fixed now,
before standstill detection (step 3), because zero-velocity updates would hide them.

Data: [calibration_fixes/](calibration_fixes/): the residual diagnostic rerun on the new code, and the
development runs (D47).

## What changed

| Fix | Term | Change | Where |
|---|---|---|---|
| **F1** | T1, gravity constant | The map-grade correction uses WGS84 normal gravity at the route's latitude instead of 9.80665 m/s² | `map_grade.py` (`GradeCompensation.gravity`; `use_normal_gravity = False` restores the old value) |
| **F2** | T2a, half-sample lag | IMU samples stand for contiguous time (each from the previous one's end to t + h/2); a sample that straddles a fix is split between the two intervals; after a start or gap the interval begins at the fix | `mount_estimation.py` (`add_imu` takes the sample time) |
| **F3** | T2b, yaw leak | The yaw fit's predicted forward specific force includes g·sin(φᵢ − φ̄), the gravity of the grade change the levelling has not absorbed (zero without map grade; zero mean, so the levelling still absorbs φ̄ = φ_cal) | `mount_estimation.py` (`solve`) |

**Design note on F1.** The first idea was to take g from the calibration: the magnitude of the mean
specific force. That would be worse on a real phone. An accelerometer bias along the up axis is not
calibrated away, and at a typical 10 mg it would make g up to 1 % wrong; the standard value is only
0.05 % off. Normal gravity at the GPS latitude is what inertial navigation uses. Its remaining errors
(altitude −0.03 % per km, local anomalies) are not simulated: the simulator uses the same formula, so
here F1 is exact ([limitations.md](limitations.md)).

**A bug found in validation.** The first version of F2 gave the first sample after a fix with no
adjacent sample (at the start, or after a gap) no time weight. So the first interval missed 1.5 samples
at its start: 0.22 mg in that interval, up to 0.003 mg in the levelling. That is the same size as the
error F2 removes. It showed as a slightly worse error-free floor in the dev run (p90 1 → 4 m) and was
traced to the first interval of the worst seed. Now the coverage is contiguous. A test covers the start
case, and the stale dev run was discarded.

## Results

### Error-free sensors (the residual diagnostic rerun)

Along-track error at C [m], `dr_calibrated` / `route_imu`, before (old defaults) → after:

| case | freeze off | freeze on |
|---|---|---|
| Eisenhower +2 %, stop-and-go (the "42 m") | 42 / 41 → **1.4 / 1.4** | −1.4 / −1.5 → 3.7 / 1.6 |
| synthetic −2 %, stop-and-go | 24 / 29 → **0.4 / 0.2** | 23 / 28 → 0.4 / 0.1 |
| Eisenhower flat, stop-and-go (floor) | 6.9 / 6.8 → 2.2 / 1.8 | 0.8 / −0.3 → 1.7 / −0.2 |
| synthetic flat, stop-and-go (floor) | 3.7 / 3.9 → 1.1 / 0.7 | 1.1 / −0.1 → 1.1 / −0.2 |
| Seattle flat, stop-and-go (floor) | 4.7 / 4.1 → 0.5 / −0.1 | 1.5 / −0.5 → 0.1 / −0.7 |
| Seattle V 4 %, stop-and-go | 13 / 11 → 6.7 / 6.0 | 7.5 / 4.1 → 7.0 / 5.3 |
| all free-flow cases | ≤ 2.7 | ≤ 0.5 |

* **The levelling offset** (T2 = g(p + φ_cal)) is ≤ 0.004 mg in every case, with or without the
  freeze. Before it was up to 0.10 mg.
* **The yaw error with perfect sensors** is ≤ 0.01° (was 0.34° on the Eisenhower ramp).
* **The freeze no longer matters for these terms.** The results with it off and on now agree within a
  few metres; before, the freeze hid T2 only because the braking and the ramp lay within 200 m of B.
* **What remains: Seattle V 4 %, 5–7 m.** None of F1–F3 targets it. The likely cause is the position
  feedback at the V's grade changes (map-grade study, mechanism 2). The ±0.010° yaw error left on
  Seattle leaks ~0.002 mg through its approach's lateral acceleration. Both are small.

### Realistic sensors (development runs, D47)

[error_sources_dev/compare.md](calibration_fixes/error_sources_dev/compare.md) and
[benchmark_dev/compare.md](calibration_fixes/benchmark_dev/compare.md) against the baselines; the tables
below against step 1.

**Error-source dev subset (5 km flat tunnel):** route + IMU and `dr_filtered` are unchanged in every
condition. Medians and p90 are within 1 m of step 1; one gross-error count moves by one run
(`dr_filtered`, GPS speed noise, free flow: ✗3 → ✗4). The realistic handover state is dominated by GPS
speed noise (0.22 mg), and these terms are ≤ 0.004 mg on a flat road. Floor: 0 (0–1) m.

**Benchmark dev subset:** error at C, median (p90) ✗ gross errors, step 1 → + F1–F3:

| scenario | route + IMU | DR filtered |
|---|---|---|
| 0.5 km and 5 km flat (free, stop-and-go) | unchanged | unchanged |
| 5 km +3 % climb, free | 109 (268) ✗4 → **93 (247) ✗4** | 106 (249) ✗4 → 110 (244) ✗5 |
| 5 km +3 % climb, stop-and-go | 297 (782) ✗13 → **501 (782) ✗17 ⚠** | 341 (7833) ✗15 → 506 (8661) ✗18 ⚠ |
| 5 km underwater, free | 42 (93) → 44 (95) | 72 (103) → 71 (96) |
| 5 km underwater, stop-and-go | 767 (782) ✗13 → **613 (782) ✗14** | 990 (8761) ✗15 → 639 (7987) ✗15 |

**Why the climb in stop-and-go got worse: F1 removed a bias that had been masking the clamp.**
* The benchmark's synthetic routes lie at latitude 0°, where standard gravity is **0.27 %** too high
  (the presets at 40–48° N: 0.05 %).
* On the 3 % climb, the old value over-subtracted the grade by 0.27 % × g × 3 % = 8·10⁻⁴ m/s². That
  put every estimate behind: about 27 m after 258 s in free flow.
* Measured in free flow: **all 20 runs moved ahead by the same 26.7 m** (predicted 26.6 m), and the
  median improved (109 → 93 m).
* In stop-and-go the same correction (~58 m over 738 s) moves the runs ahead, and runs that are ahead
  keep creeping through every stop: the one-sided v ≥ 0 clamp (P5). Runs ahead: 15 → 16 of 20; the
  positive tail grows (median of the positive errors 288 → 521 m).
* **The old gravity error had been partly cancelling the clamp's forward bias.** The estimator is now
  unbiased in free flow and the stop handling is exposed. It is the same mechanism as the underwater
  flag of step 1, and the target of step 3.
* Underwater stop-and-go improves (767 → 613 m). The V profile has both grade signs, so its F1 effect
  largely cancels; the gain comes from fewer capped runs (10 → 8).

## Limits

* The ideal-sensor cases use one traffic seed each (deterministic mechanisms).
* F3 needs map grade. Without it, a grade change in the calibration window still biases the yaw.
* F1 is exact in the simulation by construction; on a real road altitude and anomalies remain (up to
  ~20 m in a long stop-and-go outage at Eisenhower's 3.4 km altitude, limitations.md).
