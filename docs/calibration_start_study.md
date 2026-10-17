# Calibration start diagnostic: why the Kalman filters go wrong on Eisenhower

Diagnostic of 2026-10-17, after step 6.2 of [estimator_plan.md](estimator_plan.md). **No estimator was changed.**
Step 6.2 found that on the Eisenhower preset `route_kf_yaw` fails (free flow: 250 m median, 12 of 20 gross
errors, against `route_kf`'s 75 m and 2), and that even `route_kf`'s offset b is 0.7–3 mg off at GPS loss
(ladder: ~0.2 mg) ([announcement_policy.md](announcement_policy.md)).

Generated tables: [calibration_start_study/tables.md](calibration_start_study/tables.md). Per-run data:
`calibration_start_study/runs.csv`. Module: `evaluation/calibration_start_study.py`.

    uv run python -m throughtunnel.evaluation.calibration_start_study --out docs/calibration_start_study

## Method

* Four flat geometries (Eisenhower, Seattle SR99, the synthetic demo track, the 5 km ladder), free flow and
  stop-and-go, 20 seeds, realistic sensors as in the benchmark.
* Per run: when the GPS + IMU calibration is first solved, how wrong its forward offset and yaw are then, and
  at GPS loss.
* Both filters with their priors as they are (offset 1 mg, yaw 3°) and widened to 10 mg / 10°. The wide
  priors are a counterfactual, to test the hypothesis, not a tuning.
* Ruled out first: road grade (the flat variants are flat) and vehicle sideslip (not modelled).

## Findings

### 1. The cause: the filters trust a calibration that has only just been solved

A traced run (seed 10, free flow) showed the mechanism:
* GPS starts 66 s before loss, but the calibration is first solved only 41 s before loss. It needs 20 GPS
  intervals plus enough excitation (speed changes or turns) and agreement between GPS and IMU
  (`mount_estimation`).
* Its first solution leaves the forward channel 8.5 mg off; the following re-solves move it towards 0.
* The filter starts at that moment with b = 0 and a prior of 1 mg: "what a GPS-levelled calibration
  typically leaves". That describes a *converged* calibration, not a first solution, so b starts 8.5σ wrong.
* By design b follows the re-solves (`offset_shift`), so it keeps the initial error. The short rest of the
  approach (the portal freeze starts ~9 s before loss) cannot learn it away: at loss b is +2.7 mg against a
  true −0.35 mg, and the estimate ends 300 m behind.
* `route_kf_yaw` does the same with the yaw: the first solutions are up to 26° off, against a prior of 3°. It
  learns ψ −7° to −14° (truth ~0°), its b ends 8–14 mg off, and it fails.

### 2. Only Eisenhower is affected: its approach is short and weakly excited

| geometry | GPS before loss | calibration ready before loss | first solution: offset off by, median (max) | yaw off by, median (max) |
|---|---|---|---|---|
| **Eisenhower** | 67 s | **42 s** | 3.9 mg (**37 mg**) | 3.3° (**26.5°**) |
| 5 km ladder / demo track | 83 s | 63 s | 1.4 mg (3.3 mg) | 2.3° (11.3°) |
| Seattle SR99 | 106 s | 86 s | 1.7 mg (5.7 mg) | 0.7° (1.5°) |

On the longer approaches the filters have enough time after the first solution: b ends within 0.15–0.24 mg
whatever the prior.

### 3. A prior that describes a fresh calibration fixes most of it

| Eisenhower | `route_kf`: priors now → wide | `route_kf_yaw`: priors now → wide |
|---|---|---|
| \|b error\| at loss, median (max) | 0.71 (3.0) → 0.39 (2.0) mg | 1.92 (13.9) → 0.73 (2.6) mg |
| free flow, error at C | 75 (196) ✗2 → **43 (127)** | 250 (928) ✗12 → **86 (246) ✗5** |
| stop-and-go, error at C | 276 (796) ✗11 → **133 (549) ✗7** | 617 (1322) ✗16 → **211 (881) ✗11** |

* On the other three geometries the offset error is unchanged (0.15–0.28 mg either way), and free flow is
  unchanged within a few metres.
* **Stop-and-go reshuffles again.** Ladder, `route_kf`: 188 (✗9) → 241 m (✗13) with the same b error (0.16 vs.
  0.18 mg); demo track 45 → 58 m. Ladder, `route_kf_yaw`: 402 → 299 m. This is the sign lottery under the v ≥ 0
  clamp seen in step 4.1 ([route_kalman_yaw.md](route_kalman_yaw.md)): any change in b reshuffles which runs
  creep ahead. It is not a worse offset.
* Even with the wide priors, `route_kf_yaw` stays worse than `route_kf` on Eisenhower (86 vs. 43 m free flow):
  with a short, weakly excited approach the yaw state adds more uncertainty than it removes.

## Fix options (for discussion)

1. **Widen the priors to describe a fresh calibration** (simplest): e.g. 10 mg / 10°, in both filters, in
   place. It is a correction of a wrong assumption, not a new variant. Evidence: the first solutions here are
   off by up to 37 mg / 26°, so 10 mg / 10° is still not generous. Expected: Eisenhower as above, the rest
   neutral in b, stop-and-go medians reshuffled.
2. **Start learning only once the calibration has settled**, e.g. when its re-solves move the axes by less
   than a threshold. More code and another threshold; and on Eisenhower it leaves even less approach to learn
   from.
3. **Let the calibration report its own uncertainty** and initialise the filter from it. The most principled,
   the most work (`mount_estimation` would need a covariance).

## For the testing process

The dev subsets (D47) contain no preset, which is how this stayed hidden through steps 4 and 4.1. Proposed:
add Eisenhower (flat, both traffic cases) to the benchmark dev scenarios: a real geometry with a short approach.

## Limits

* 20 seeds per case; flat roads only (the sloped presets are not checked here).
* The wide priors are one counterfactual pair of values, not a tuned or optimal choice.

## Fix applied (D54, 2026-10-17): wider priors in both filters

User decision: option 1. Both filters start with offset 10 mg and yaw 10° (`offset_sigma0` / `yaw_sigma0`;
1 mg / 3° reproduce the first versions). Eisenhower joins the benchmark dev scenarios. Data:
[calibration_prior_fix/](calibration_prior_fix/): both dev subsets and all flat-road scenarios, against
`milestone_step4` (and, for `route_kf_yaw`, its step 4.1 runs), 20 paired seeds.

Error at C (benchmark) or 5 km in (error sources), median, old → new prior; paired: runs worse / better.

| case | `route_kf` | paired | `route_kf_yaw` | paired |
|---|---|---|---|---|
| **Eisenhower, free** | 75 ✗2 → **43 ✗0** | 5 / 14 | 250 ✗12 → **86 ✗5** | 4 / 16 |
| **Eisenhower, stop-and-go** | 276 ✗11 → **133 ✗7** | 5 / 14 | 617 ✗16 → **211 ✗11** | 4 / 15 |
| calibration pitch 0.1°, free | 3 → 0 | 0 / 20 | 0 → 0 | – |
| 2 km ladder, free | 20 → 22 | 14 / 3 (p 0.01) | 24 → 18 | 9 / 8 |
| 3 km ladder, free | 28 → 32 | 15 / 4 (p 0.02) | 45 → 28 | 9 / 7 |
| 5 km ladder, free | 85 → 80 | 14 / 5 (p 0.06) | 89 → 84 | 9 / 10 |
| 5 km ladder, stop-and-go | 188 ✗9 → 241 ✗13 | 9 / 7 (p 0.8) | 402 → 299 | 6 / 8 |
| Seattle, free / stop-and-go | 38 → 37 / 133 → 132 | – | 42 → 44 / 147 → 127 | – |
| **hard, free** | 255 ✗12 → **361 ✗17** | **19 / 1** | 204 ✗11 → 157 ✗7 | 6 / 14 |
| hard, stop-and-go | 782 ✗18 → 782 ✗20 | 8 / 0 | 403 → 399 | 7 / 10 |

* **`route_kf_yaw`: better or neutral everywhere.** With a yaw state, giving b and ψ room to move is the
  consistent model.
* **`route_kf`: a large gain on the short approach, a cost elsewhere.**
  * Eisenhower's gross errors in free flow disappear; the calibration-pitch case improves in every run.
  * In free flow on the longer approaches it is slightly but systematically worse (2–3 km: +2–4 m median,
    p 0.01–0.02), and with a 2° yaw error (`hard`) clearly worse (255 → 361 m, 19 of 20 runs).
  * Why: `route_kf` has no yaw state, so the yaw leak on the approach curves goes into b. The narrow prior
    held b near zero and thereby shielded it from that leak, an accidental protection. With the honest
    prior b absorbs more of it. The case it hurts is exactly the one `route_kf_yaw` exists for.
* Stop-and-go medians move in both directions (the clamp's sign lottery, P5), none of it significant.
* Kept as decided (option 1): the realistic gains on the real geometry outweigh 2–4 m on the ladders. A
  possible refinement, not built: let b's uncertainty grow with the size of each calibration re-solve (a
  calibration that still jumps is uncertain, one that has settled is not). That would keep the narrow prior's
  benefit on long approaches without its failure on short ones.
