# Route Kalman filter with a yaw state, `route_kf_yaw` (step 4.1)

Step 4.1 of [estimator_plan.md](estimator_plan.md), decision D52 (2026-10-17). A new phone-only estimator
`route_kf_yaw` next to `route_kf`: the same filter, with the calibration's yaw residual ψ as a 4th state.
`route_kf` is unchanged (D51). First built as a change of `route_kf` in place; after the results the user
decided to keep both as separate estimators, so that the trade-off stays visible and both can be compared
in the UI. It follows the yaw diagnostic
([yaw_study.md](yaw_study.md)): with a calibration yaw error, the filter's offset b absorbed the leak of the
approach curves (2°: 0.37 mg, stop-and-go 204 m vs. `route_imu`'s 96 m).

Data: [route_kalman_yaw/](route_kalman_yaw/): development runs of both filters against `milestone_step4`
(D47, 20 paired seeds) and a paired check on 60 fresh seeds. Modules: `positioning/route_kalman.py`,
`positioning/alignment.py` (`yaw_shift`), `evaluation/route_kf_check.py`.

## The change

* **State [d, v, b, ψ].** Prediction with â = a − b − ψ·f_lat, where f_lat is the measured lateral channel.
  ψ is learned from the GPS speed updates like b. On the approach curves the leak ψ·f_lat varies with the
  lateral acceleration while b stays constant, so the two separate. ψ is carried into the tunnel and
  corrects the leak there too. The filter stays linear: ψ enters with the known coefficient f_lat.
* **Tuning (nominal, PD6):** ψ prior 3° (a GPS-based mount calibration over a short approach), random walk
  0.01°/√s (a phone settling in its holder). `route_kf`'s turn noise (lateral acceleration × a nominal
  0.5°) is not used: ψ's own uncertainty carries it.
* **`VehicleImu.yaw_shift`** (alignment stage). Found in a first check: with realistic sensors the
  calibration's yaw jumps **0.45–0.68° rms from one re-solve to the next** (up to 4°). That is larger than
  the residual the state is meant to find (0.3°). As with `offset_shift` (D51), the stage now reports each
  re-solve's change of the leak factor, F_new · L_old. Verified against the true change: 0.0003° rms,
  max 0.003°. Other estimators ignore it and stay bit-identical.
* **One implementation, two estimators.** `RouteKalman` (`route_kf`: `yaw_state = False`, `turn_noise = 1`)
  and its subclass `RouteKalmanYaw` (`route_kf_yaw`: `yaw_state = True`, `turn_noise = 0`). With ψ off the
  4-state code is the first version bit for bit (verified on three runs to the micrometre, a test, and
  the dev reruns: `route_kf` unchanged against the milestone).

## Validation (before the benchmarks)

5 seeds per case, ψ after the last fix before GPS loss vs. the true yaw residual of the axes in use:

| case | true yaw | ψ (± filter σ) | b error | error at C |
|---|---|---|---|---|
| error-free sensors | 0.00° | −0.01 to 0.00° (± 0.12°) | 0.00 mg | 0–3 m |
| calibration yaw 2°, error-free otherwise | 2.00° | 1.99–2.00° (± 0.12°) | 0.00 mg | 0–2 m |
| realistic | −0.55 to +0.64° | −0.26 to +0.55° (± 0.32°) | −0.0 to +0.6 mg | 29–335 m |

With a calibration yaw error the state finds it exactly. With realistic sensors ψ is only as good as the GPS
speeds it is learned from (±0.32°, the filter's own σ is honest), the same information the calibration's
yaw fit already used. As the diagnostic predicted, it cannot improve on the natural residual.

## Results

### Error-source benchmark (5 km flat tunnel, dev subset, 20 paired seeds)

Error 5 km in, median (p90) ✗ gross errors (> 200 m). `cal_pitch_0.1`, `cal_yaw_2` and `hard` are new in
the dev subset (D52).

| condition | traffic | route + IMU | route_kf | **route_kf_yaw** |
|---|---|---|---|---|
| error-free (floor) | free | 0 (0) | 1 (1) | 0 (1) |
| | stop-and-go | 0 (0) | 3 (7) | 3 (6) |
| **calibration yaw 2°** | free | 67 (75) | 65 (85) | **0 (2)** |
| | stop-and-go | 96 (114) | 204 (247) ✗10 | **2 (8)** |
| **hard** (tilted mount + calibration error) | free | 2760 (2961) ✗20 | 255 (430) ✗12 | **204 (400) ✗11** |
| | stop-and-go | 3390 (3752) ✗20 | 782 (782) ✗18 | **403 (782) ✗17** |
| calibration pitch 0.1° | free | 628 (675) ✗20 | 3 (4) | 0 (1) |
| | stop-and-go | 977 (1376) ✗20 | 5 (6) | 2 (5) |
| GPS speed noise | free | 102 (245) ✗4 | 85 (182) ✗2 | 97 (215) ✗3 |
| | stop-and-go | 393 (782) ✗14 | 182 (604) ✗9 | 178 (782) ✗9 |
| GPS degradation (150 m) | free | 4 (8) | 4 (7) | 4 (8) |
| | stop-and-go | 3 (12) | 6 (15) | 5 (12) |
| GPS degradation, harsh | free | 133 (242) ✗7 | 31 (71) | 36 (86) |
| | stop-and-go | 289 (782) ✗13 | 57 (220) ✗3 | 75 (272) ✗4 |
| **realistic** | free | 103 (257) ✗4 | 85 (283) ✗4 | 89 (244) ✗3 |
| | stop-and-go | 385 (782) ✗16 | 188 (782) ✗9 | **402 (782) ✗12 ⚠** |

### Benchmark dev subset (map grade on for sloped roads)

| scenario | route + IMU | route_kf | **route_kf_yaw** |
|---|---|---|---|
| 0.5 km flat, free | 6 (12) | 6 (19) | 6 (17) |
| 0.5 km flat, stop-and-go | 18 (92) ✗1 | 11 (59) ✗1 | 12 (95) ✗1 |
| 5 km flat, free | 103 (257) ✗4 | 85 (283) ✗4 | 89 (244) ✗3 |
| 5 km flat, stop-and-go | 385 (782) ✗16 | 188 (782) ✗9 | **402 (782) ✗12 ⚠** |
| 5 km +3 % climb, free | 93 (247) ✗4 | 103 (268) ✗4 | 104 (237) ✗3 |
| 5 km +3 % climb, stop-and-go | 501 (782) ✗17 | 228 (782) ✗12 | **467 (782) ✗13 ⚠** |
| 5 km underwater, free | 44 (95) | 40 (86) | 38 (93) |
| 5 km underwater, stop-and-go | 613 (782) ✗14 | 312 (782) ✗15 | **531 (782) ✗13 ⚠** |

`route_kf` is unchanged against the milestone in every cell (dev reruns; `compare.md` lists only the
estimators the milestone has, so `route_kf_yaw` is in `tables.md`). Compared with `route_kf`, its three
stop-and-go medians would be flagged (⚠). They are not three independent results: the three
roads share the approach, its GPS noise and the seeds.

### Fresh seeds (realistic 5 km, seeds 20–79, paired)

The dev seeds 0–19 were used throughout development, so the flag was checked on 60 new seeds:
[route_kalman_yaw/fresh_seeds/tables.md](route_kalman_yaw/fresh_seeds/tables.md).

| traffic | route_kf | route_kf_yaw | paired (route_kf_yaw): worse / better / same | sign test |
|---|---|---|---|---|
| free | 142 (285) ✗19 | 139 (302) ✗16 | 33 / 27 / 0 | p = 0.52 |
| stop-and-go | 355 (782) ✗41 | 503 (782) ✗45 | 29 / 18 / 13 | p = 0.14 |

## Findings

1. **`route_kf_yaw` handles a calibration yaw error.** 2° costs 0–2 m instead of 65 / 204 m: the
   diagnostic's ceiling is reached (1 / 11 m). *Caveat:* the simulation injects the error after the
   calibration, so the approach data contradicts it and the filter re-reads the truth from that data.
   The gain is real only to the extent that real phones end up with a yaw error the approach data can
   reveal: the phone shifting in its holder during the approach (R11, not simulated), or a weaker mount
   calibration than ours. That is plausible but not shown here. For pitch (step 4) the case is stronger:
   the levelling cannot separate pitch from bias, while yaw and ψ use the same information. The `hard` condition
   improves to 204 m (free) and 403 m (stop-and-go); its remaining error is not yaw (roll and tilted-mount
   effects, not examined here).
2. **Realistic free flow: neutral on the ladder; no gain under realistic conditions anywhere.** *Correction
   (2026-10-17, step 6.2, [announcement_policy.md](announcement_policy.md)): on the Eisenhower preset, not in the dev
   subsets, `route_kf_yaw` fails: ψ −7° to −14° learned on the approach, 250 m median and 12 of 20 gross errors in free
   flow vs. `route_kf`'s 75 m and 2. Diagnosis pending.* (85 → 89 m dev, 142 → 139 m
   fresh seeds), as predicted: with realistic sensors ψ has no information the calibration's yaw fit did not
   already use.
3. **Realistic stop-and-go leans worse, but the evidence is weak.** Dev: 188 → 402 m. Fresh seeds: 355 → 503
   m median, gross errors 41 → 45 of 60, paired 29 worse vs. 18 better (p = 0.14), median paired change 0 m.
   * Mechanism (checked on the dev seeds): ψ learns from the same noisy GPS speeds as the calibration and,
     through the b–ψ coupling on the approach curves, moves b by up to ±0.4 mg per run, in random
     directions. b's rms error is unchanged (0.35 → 0.36 mg; fresh seeds 0.39 → 0.40 mg).
   * In stop-and-go the v ≥ 0 clamp (P5) makes the result depend on the *sign* of a small offset error. An
     estimate that falls behind is reset at every stop; one that runs ahead keeps moving through the stops
     and creeps on. Seed 13: b error +0.64 → +0.24 mg, closer to the truth at GPS loss, but on the wrong
     side of the in-tunnel bias drift: 40 m behind → 598 m ahead.
   * So the yaw state reshuffles which runs land on the creeping side. Dropping only the turn noise (no ψ)
     moved the same dev median 188 → 284 m with the same b rms, which shows how fragile this statistic is.
     The milestone's 188 m was itself a favourable draw (355 m on the fresh seeds).
   * This explanation is supported (equal b rms, the traced runs), not proven: a small systematic cost
     cannot be excluded. Both filters are in a failing regime there anyway (41–45 of 60 runs with gross
     errors); only stop handling (P5) changes that.
4. **The ψ term inside the tunnel is negligible** (≈0.03 mg). The lateral channel carries a ~2 mg offset
   (levelling residual), which ψ multiplies to almost nothing.

## Decision (user, 2026-10-17): two estimators

Both are kept, as separate phone-only estimators:
* **`route_kf`**: the headline phone-only filter. As good as or better under realistic conditions.
* **`route_kf_yaw`**: the robustness variant. Removes the calibration-yaw failure mode (204 → 2 m with 2°),
  no gain with realistic sensors, possibly a small cost in stop-and-go.

In the case study this is robustness against a calibration yaw error, not an accuracy gain. In the UI
both appear with their own colours. They differ visibly only with a calibration yaw error set (calibration
panel, e.g. 2°), best in stop-and-go.

Not built: applying ψ only when it is significant (e.g. |ψ| > 3σ) would avoid the reshuffle, but it is a
heuristic switch.

## Limits

* Tuning by reasoning (prior 3°, random walk 0.01°/√s), not optimised.
* ψ is observable here because the approach has three curves. On a straight approach it would stay at its
  prior and the leak in the tunnel's curves would go uncorrected (the lateral-channel measurement of
  [yaw_study.md](yaw_study.md) finding 4 would help there; not built).
* 20 dev seeds (60 fresh seeds for the realistic check only).
* The realism of the injected yaw error is the open question (finding 1); settling it needs the holder
  shift (R11), which the frozen simulator does not have.
