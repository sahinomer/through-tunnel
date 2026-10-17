# Yaw diagnostic (step 4.1): what the calibration's yaw residual does to the filter

Diagnostic of 2026-10-17, the first part of step 4.1 of [estimator_plan.md](estimator_plan.md). **No estimator
was changed.** Two open points of the milestone after step 4 ([benchmark/README.md](benchmark/README.md)):
* with a 2° calibration yaw error, `route_kf` is worse than `route_imu` in stop-and-go (204 vs. 96 m);
* `route_kf`'s free-flow p90 at 2–3 km is worse than `route_imu`'s (72 vs. 46 m, 134 vs. 77 m).

Both were suspected to come from the yaw leak: a yaw residual ψ of the calibrated axes puts ≈ ψ · f_lat
into the forward channel. Before building a yaw state (solution 6b), this checks whether that is the
cause, and how much a perfect yaw state could gain.

Generated tables: [yaw_study/tables.md](yaw_study/tables.md). Per-run data: `yaw_study/runs.csv`. Module:
`evaluation/yaw_study.py`.

    uv run python -m throughtunnel.evaluation.yaw_study --out docs/yaw_study

## Method

* **Counterfactual "yaw oracle"** (not an estimator): the leak is removed from the alignment stage's
  forward channel, sample by sample, using the truth:

      leak_i = (F_i · L) · (L · f_i)     F_i: forward axis the stage uses at sample i (calibration error
                                         included), L: true left axis, f_i: error-free specific force

  Everything else (noise, bias, pitch residual, re-solve shifts) is untouched. The difference to the
  unmodified estimator is what the leak costs.
* **Variants:** `route_imu` with and without the leak; `route_kf` unmodified, with the leak removed only
  before GPS loss (`+yaw_approach`: b learned without it), only after (`+yaw_tunnel`), and everywhere
  (`+yaw`: the ceiling of a perfect yaw state).
* **Cases:** error-source conditions floor, calibration pitch 0.1° (control), calibration yaw 2°, hard,
  GPS speed noise and realistic. Also the benchmark's flat 2, 3 and 5 km ladder tunnels (realistic
  sensors). Free flow and stop-and-go, 20 paired seeds. The 5 km ladder *is* the realistic condition
  (same configuration), so those two rows are identical.
* **Rerun check:** the unmodified variants reproduce the milestone's `runs.csv` exactly (720 runs,
  difference 0 m).

## Findings

Error at C, median (p90) ✗ gross errors (> 200 m), 20 runs:

| case | route_imu | route_imu +yaw | **route_kf** | +yaw approach | +yaw tunnel | +yaw everywhere |
|---|---|---|---|---|---|---|
| calibration yaw 2°, free | 67 (75) | 0 (1) | **65 (85)** | 59 (66) | 117 (139) | 1 (2) |
| calibration yaw 2°, stop-and-go | 96 (114) | 3 (5) | **204 (247) ✗10** | 78 (106) | 211 (254) ✗11 | 11 (26) |
| hard, free | 2760 (2960) ✗20 | 2821 (3034) ✗20 | **255 (430) ✗12** | 124 (289) ✗8 | 195 (393) ✗10 | 159 (360) ✗8 |
| hard, stop-and-go | 3390 (3752) ✗20 | 3392 (3754) ✗20 | **782 (782) ✗18** | 358 (782) ✗15 | 782 (782) ✗18 | 360 (782) ✗15 |
| GPS speed noise, free | 102 (245) ✗4 | 82 (273) ✗3 | **85 (182) ✗2** | 54 (129) ✗1 | 77 (181) ✗2 | 58 (134) ✗1 |
| GPS speed noise, stop-and-go | 393 (782) ✗14 | 399 (782) ✗14 | **182 (604) ✗9** | 115 (543) ✗8 | 179 (585) ✗9 | 120 (550) ✗8 |
| realistic, free (= 5 km ladder) | 103 (257) ✗4 | 82 (244) ✗4 | **85 (283) ✗4** | 102 (219) ✗3 | 95 (253) ✗4 | 107 (213) ✗3 |
| realistic, stop-and-go | 385 (782) ✗16 | 369 (782) ✗16 | **188 (782) ✗9** | 274 (782) ✗15 | 187 (782) ✗9 | 275 (782) ✗15 |
| 2 km ladder, free | 25 (46) | 23 (47) | **20 (72)** | 17 (47) | 18 (68) | 19 (46) |
| 3 km ladder, free | 46 (77) | 43 (79) | **28 (134)** | 34 (92) | 27 (124) | 38 (90) |

Floor and calibration pitch 0.1°: unchanged by the oracle (within 4 m). Stop-and-go ladders: in the tables.

### 1. A calibration yaw error corrupts the filter's offset on the approach (confirmed)

* With 2° injected, `route_kf`'s b is 0.37 mg off at GPS loss, in every run. With the leak removed
  on the approach, the error is 0.00 mg.
* Mechanism: the approach has three curves of 150–400 m radius (1–2.5 m/s² at 70 km/h). The filter learns
  b from GPS speed while the leak (3–9 mg on those curves) is in the forward channel, and its turn noise
  assumes a 0.5° yaw residual, so b absorbs the leak. In stop-and-go (740 s to C instead of 255 s) a
  wrong b costs far more than the leak itself, which `route_imu` (no b) only sees inside the tunnel.
* Removing the leak on the approach alone: stop-and-go 204 → 78 m, better than `route_imu`'s 96 m.
  Everywhere: 11 m. **All 20 runs improve, in both traffic cases.**
* The tunnel leak alone (`+yaw_tunnel`) does not help the filter: with b already wrong it is even worse
  in free flow (117 m; likely two errors that partly cancelled no longer do). **Both parts are needed**, and a yaw
  state learned on the approach and carried into the tunnel provides both.
* `hard` (2° yaw + 0.5° pitch + 0.5° roll, tilted mount): 255 → 159 m (free), 782 → 360 m
  (stop-and-go), 12 of 20 runs better in each.

### 2. The natural yaw residual is not what limits the realistic runs (refuted)

* In the realistic setting the calibration leaves a yaw residual of 0.32° median, 0.68° p90 (GPS speed
  noise in its yaw fit). Its approach leak moves b by 0.22 mg rms, as much as the error from GPS noise.
* **But removing it does not help.** Paired, route_kf with the leak removed everywhere is better in
  9 of 20 runs in free flow (median change +5 m) and 6 of 20 in stop-and-go (median change 0 m). The
  medians even rise (85 → 107 m, 188 → 275 m; gross errors in stop-and-go 9 → 15), the p90 falls in
  free flow (283 → 213 m). Mixed, within the noise of 20 runs.
* The reason: the calibration fitted its yaw to the same noisy GPS speeds the filter learns b from. The
  leak is therefore partly *anti*-correlated with the GPS error in b (correlation −0.17 realistic, −0.34
  GPS speed noise alone). Removing the true leak also removes this partial compensation. b's rms error
  barely changes: 0.35 → 0.30 mg (realistic), 0.27 → 0.22 mg (GPS speed noise).
* The correlation between |yaw residual| and the filter's error seen in the milestone data (0.61, free flow)
  is a common cause: GPS speed noise drives both.
* **The free-flow tails at 2–3 km are not a yaw effect.** The worst runs stay bad without any leak:
  seed 11: 381 → 292 m, seed 18: 323 → 308 m (5 km). Only seed 13 is a yaw run (278 → 35 m).

### 3. What does limit the realistic free flow: learning b from an 80 s approach

* Realistic, 5 km free flow, rms at GPS loss: true forward offset 0.43 mg, filter's b error 0.35 mg. The
  filter only removes a small part of the offset. With 0.2 m/s GPS speed noise at 1 Hz over ~80 s, a fit
  of b cannot be better than ~0.1 mg (slope of 80 points), and the filter's process noise widens that.
* This is a limit of the approach information, not of yaw. A yaw state cannot remove it; position fixes
  inside the tunnel (map features, step 5) bound it.

### 4. Where yaw is observable (correction to the plan's solution 6b)

With a yaw residual ψ the two horizontal channels read:
* forward: f_x + ψ·f_lat (+ b). Against GPS speed, ψ separates from b where f_lat varies: **curves on the
  approach**. This is what the diagnostic shows. It keeps the filter linear (a 4th state with a known
  coefficient, the measured lateral channel).
* lateral: f_lat − ψ·f_x. Against the map's v²·κ, ψ shows **whenever the car accelerates or brakes**,
  on straights too, without GPS. Inside the 5 km tunnel the forward acceleration is 0.30 m/s² rms in
  stop-and-go (0.10 m/s² in free flow). By noise alone that resolves ψ to a few hundredths of a degree.
  The real limits are model errors: the lateral bias and its drift (needs its own state), the v and d
  errors in v²κ, and road bank (not simulated, so a simulation result would be optimistic).

The plan's "6b needs curves" holds only for the first route. The benchmark's approach is curvy, which
makes the first route work here; on a straight approach only the second one would observe ψ.

## What this means for step 4.1

* **A yaw state is worth building for robustness, not for the realistic benchmark numbers.** It addresses a
  calibration yaw error the approach data does not explain: a mount that shifted after the calibration, or
  a calibration done on older data. There the ceiling is large: 204 → 11 m in stop-and-go and 65 → 1 m in
  free flow with 2°, and the `hard` condition roughly halves. The benchmark injects no calibration error,
  so its numbers should stay about the same. If they get worse, the extra state is costing noise and the
  tuning needs attention.
* For the natural residual a filter state learns nothing the calibration did not already fit: same data,
  same GPS noise. Expect neutral.
* **Proposed scope:** ψ as a 4th filter state, observed through the forward channel against GPS speed on
  the approach (route 1 above), and carried into the tunnel. The lateral-channel measurement (route 2) is
  kept for a later sub-step, only if needed: it is the larger change (EKF, lateral bias state, bank
  caveat).
* **The free-flow tails need step 5**, not 4.1 (finding 3).
* **Dev subset:** the error-source dev conditions (D47) do not include `cal_yaw_2`, `hard` or
  `cal_pitch_0.1`, so a dev run of 4.1 would not show the target at all. Proposed: add the three.

## Limits

* The oracle removes the leak with the true axes, which no estimator has; the gains above are ceilings.
* 20 runs per case: p90 is about the 2nd-worst run, and medians move by tens of metres between paired
  variants that are statistically the same (finding 2).
* One approach geometry (the synthetic preset's, three curves). Its curvature makes route 1 work. On a
  straight approach ψ would be unobservable before the tunnel.
