# Uncertainty consistency check (step 6.1): is the filters' σ honest?

Diagnostic of 2026-10-17, step 6.1 of [estimator_plan.md](estimator_plan.md). **No estimator was changed.**
The uncertainty-aware announcement (3d, step 6.2) will rely on the 1σ along-route uncertainty that
`route_kf` and `route_kf_yaw` report (`position_std_m`). Before that, this checks whether it is honest: the
true along-track error should lie within ±1σ in about 68 % of the runs and within ±2σ in about 95 %.

Generated tables: [uncertainty_study/tables.md](uncertainty_study/tables.md). Per-run data:
`uncertainty_study/runs.csv`. Module: `evaluation/uncertainty_study.py`.

    uv run python -m throughtunnel.evaluation.uncertainty_study --out docs/uncertainty_study

Also in this step, in the UI (user request): the along-track error plot shows each Kalman filter's own ±2σ
as a band in its colour, and the summary table has the filter's σ at C and when it announced. An honest σ
keeps the error line inside the band about 95 % of the time.

## Method

* **Cases:** error-source conditions on the 5 km flat tunnel (floor, realistic, GPS speed noise,
  accelerometer bias drift, calibration pitch 0.1°, calibration yaw 2°) and benchmark scenarios (2 km flat,
  5 km +3 % climb and underwater, map grade on), free flow and stop-and-go, 20 seeds each.
* **Checkpoints:** the true announcement time (300 m before C: what an announcement policy would rely
  on), C, 0.5–4 km into the tunnel, and every output sample of the GPS outage.
* **Measures:** coverage within ±1σ / ±2σ; rms z (z = error / σ; honest ≈ 1, above 1 = overconfident,
  below 1 = too conservative); median |error| vs. median σ.

## Findings

At the announcement point, `route_kf` (`route_kf_yaw` is similar):

| case | coverage ±1σ / ±2σ | rms z | median \|error\| / median σ |
|---|---|---|---|
| realistic 5 km, free | 70 % / 95 % | 1.0 | 73 m / 156 m |
| 5 km climb, free | 70 % / 95 % | 0.9 | 91 m / 156 m |
| **2 km flat, free** | **65 % / 85 %** | **1.2** | 18 m / 24 m |
| 5 km underwater, free | 100 % / 100 % | 0.3 | 27 m / 156 m |
| **realistic 5 km, stop-and-go** | 100 % / 100 % | **0.3** | 190 m / **1695 m** |
| GPS speed noise, stop-and-go | 100 % / 100 % | 0.2 | 169 m / 1695 m |
| error-free sensors, stop-and-go | 100 % / 100 % | 0.0 | 3 m / 1594 m |

### 1. Free flow: honest, slightly overconfident in the shorter tunnel

* On the realistic 5 km tunnel σ is consistent: 70 % / 95 % coverage, rms z 1.0, at the announcement
  point and through the tunnel (rms z 0.9–1.1 from 0.5 km to C).
* **2 km tunnel: mildly overconfident** (65 % / 85 %, rms z 1.2). This is the side that matters for "late is
  worse": a policy using ±2σ would have its error outside the band in about 15 % of runs instead of 5 %.
* Underwater: too conservative (rms z 0.3). The grade-change feedback of the map grade
  ([map_grade_study.md](map_grade_study.md)) corrects the position, which the filter does not model.

### 2. Stop-and-go: σ is 5–10 times too large

* At the announcement point σ is 1.6–1.7 km, while the real errors are 170–290 m median (`route_kf`; up to
  490 m for `route_kf_yaw`), and even the
  capped worst cases (782 m) stay within 1σ. rms z 0.2–0.3.
* It starts honest and becomes more conservative over time: rms z ≈ 1.0 at 0.5 km, 0.4 at 4 km.
* **Cause: the filter's own noise budget** (computed from its model, matching the reported σ):

  | term | free flow (255 s) | stop-and-go (740 s) |
  |---|---|---|
  | offset random walk, 0.05 mg/√s (grows like t^2.5) | ~114 m | **~1630 m** |
  | offset uncertainty at GPS loss (grows like t²) | ~80 m | ~690 m |
  | acceleration noise | ~12 m | ~58 m |
  | total | ~140 m (reported 151) | ~1770 m (reported 1838) |

  The offset random walk grows without bound. The real offset changes are bounded: the simulated bias drift
  is a bounded process, and the v ≥ 0 clamp resets negative speed errors at every stop (P5). The linear
  filter models neither, so over a 12-minute stop-and-go outage its σ runs far ahead of the truth.
* **Conservative where the calibration is good.** With error-free sensors or a calibration error the filter
  has fully learned (pitch, and yaw for `route_kf_yaw`), the errors are 0–5 m while σ is 130–150 m (free)
  and 1.6 km (stop-and-go). The nominal process noise assumes errors that are not there. This is
  conservative by design (PD6: nominal tuning, not matched to the simulator).

### 3. What this means for the announcement policy (6.2)

* **Free flow:** σ can be used as it is. The 2 km overconfidence suggests k > 2 for the "not late" side, or
  a small floor on σ.
* **Stop-and-go:** σ errs on the safe side (it would never make an announcement late), but it is far too
  large to time anything: "estimate + 2σ reaches the target" would fire 3+ km early, at the tunnel
  entrance. Even an honest σ would be 200–400 m there, so stop-and-go would always get the hedged
  announcement. That is the right product behaviour: the phone does not know where it is within ±300 m. But
  the *timing* of the hedged announcement needs either a better σ or a cap.

## Options before or within 6.2 (for discussion)

1. **Bounded offset drift in the filter:** model the offset as a constant (the calibration residual) plus a
   bounded first-order drift instead of an unbounded random walk. This addresses the main cause and makes σ
   more honest in long outages. Costs: a 5th state, a change to both filters' estimates (small; needs the
   dev runs), and nominal drift parameters that must not simply copy the simulator's (0.5 mg, τ 300 s;
   PD6 risk of matched tuning). The clamp part stays unmodelled, so stop-and-go would remain conservative.
2. **Use σ as it is, and cap the policy:** σ only decides precise vs. hedged; the hedged announcement fires
   at most a fixed lead before the target. Simplest; σ's size beyond the threshold no longer matters.
3. **Calibrate σ empirically** (scale it to the simulated errors): rejected, it would tune the filter
   to the simulator.

## Limits

* 20 seeds per case: coverage moves in steps of 5 %.
* Only the along-track σ is checked; the filters report no cross-track uncertainty (the route constrains it).
* The checkpoints use the true times. The policy will use σ at the estimate's own times; same σ, earlier or
  later by the timing error.
