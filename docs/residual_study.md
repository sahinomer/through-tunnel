# Residual diagnostic (step 2): the 42 m residual and the stop-and-go floor

Diagnostic of 2026-10-16, step 2 of [estimator_plan.md](estimator_plan.md). **No estimator was changed.**
Two errors remained with error-free sensors:
* the map-grade study's unexplained residual: Eisenhower, stop-and-go, +2 % climb, 42 m at C, "a steady
  offset of ~3·10⁻⁴ m/s², present even at standstill", with the gravity constant explaining −14 m and a
  second term unidentified;
* the error-source benchmark's 12–13 m stop-and-go floor.

Both are now fully explained. They must be understood before standstill detection (step 3), because
zero-velocity updates would remove a steady offset without telling where it came from.

Generated tables: [residual_study/tables.md](residual_study/tables.md). Per-run data:
`residual_study/runs.csv`. Module: `evaluation/residual_study.py`.

    uv run python -m throughtunnel.evaluation.residual_study --out docs/residual_study

## Method

* **Cases:** the map-grade study's ideal-sensor runs with residuals (Eisenhower +2 %, synthetic −2 %,
  Seattle underwater V 4 %), each with its flat road, in free flow and stop-and-go. Ideal IMU and GPS,
  map grade on, traffic seed 0, as in that study.
* **Variants:** portal freeze (D46) off / on × the estimators' gravity constant: standard (9.80665) /
  local (the simulator's normal gravity at the tunnel).
* **Decomposition.** Standing on a grade φ, the calibrated forward axis (tilted by p from the true
  forward axis) reads g·sin(φ + p). The estimator subtracts G·sin(φ − φ_cal), where φ_cal is the mean
  map grade the calibration reports. What is left:

      r = (g − G)·sin(φ − φ_cal)              T1: gravity constant
        + g·[sin(φ + p) − sin(φ − φ_cal)]     T2: levelling ≠ reported grade, ≈ g·(p + φ_cal)

  Both terms are integrated twice over the outage and compared with `dr_calibrated` at C. T2 is then
  split into two causes found in the data (below), T2a and T2b.

## Findings

### 1. The 42 m is T2 + T1

Eisenhower +2 %, stop-and-go, along-track error at C (`dr_calibrated`):

| freeze | gravity | T1 predicted | T2 predicted | measured |
|---|---|---|---|---|
| off | standard | −11 m | **+46 m** | **+42 m** |
| off | local | 0 | +46 m | +56 m (the map-grade study's "56 m with matched gravity") |
| on | standard | −12 m | +1 m | −1 m |
| on | local | 0 | +1 m | +4 m |

**The unidentified term is T2: the levelling absorbed 0.042 mg more tilt than the grade it reports.**
The remaining difference (measured − predicted, +5 to +10 m) is the stop handling: a positive speed
error keeps creeping during stops, a negative one is reset (P5).

### 2. T2 has two causes, and both are now identified

T2 per case, in mg. "Rest" is the part T2a and T2b do not explain: at most 0.002 mg in all 24 cases
([tables](residual_study/tables.md)).

| case | T2 = g(p + φ_cal) | T2a: half-sample lag | T2b: yaw leak | rest | yaw error |
|---|---|---|---|---|---|
| Eisenhower +2 %, free | +0.102 | −0.000 | **+0.103** | −0.001 | 0.34° |
| Eisenhower +2 %, stop-and-go | +0.042 | +0.005 | **+0.039** | −0.002 | 0.15° |
| Eisenhower flat, stop-and-go | +0.005 | **+0.005** | −0.000 | −0.000 | 0.00° |
| synthetic flat, stop-and-go | +0.004 | **+0.004** | −0.000 | −0.000 | 0.00° |
| Seattle flat, stop-and-go | +0.002 | **+0.003** | −0.001 | −0.000 | 0.01° |
| Seattle V 4 %, stop-and-go | +0.008 | +0.003 | +0.006 | −0.001 | −0.04° |

* **T2a, half-sample lag: the stop-and-go floor.**
  * Each GPS interval's IMU mean takes the samples after the previous fix up to and including the fix
    time, so it lags the interval by half a sample (h/2 = 2.5 ms).
  * Over the approach this sums to −(h/2)·(a_last − a_first)/T.
  * In stop-and-go the car is already braking when the calibration ends (≈ −1.4 m/s² at the last fix,
    T ≈ 68 s). That gives 0.005 mg, which over a 7–8 min outage is the 12–13 m floor.
  * In free flow the last fix sees little acceleration, so the term vanishes.
* **T2b, yaw leak: the large Eisenhower term.**
  * The ramp of the +2 % climb starts before B, inside the calibration window.
  * The alignment's yaw fit compares the predicted vehicle acceleration with the horizontal specific
    force. It does not model the gravity the changing grade adds (up to 9 mg at the last fixes), so the
    yaw estimate is off by 0.34° with perfect sensors.
  * The levelling then removes the predicted lateral acceleration along a slightly wrong axis. The
    approach's mean lateral acceleration (−0.17 m/s², from its curves) leaks into the forward tilt:
    0.0060 rad × 0.170 m/s² / g = 0.103 mg (measured 0.102).
  * On the flat road the same approach gives a yaw error of 0.000°.

### 3. T1, the gravity constant, is the synthetic −2 % residual

* The estimators use standard gravity; the simulator uses normal gravity at the latitude (≈ 0.05 % less
  at 40° N).
* The grade correction is therefore scaled wrong by 0.05 %: −0.010 mg on Eisenhower +2 % and +0.051 mg
  on the synthetic −2 % (its calibration absorbed a slight downhill).
* Synthetic −2 % stop-and-go: 23–29 m at C with standard gravity, 0–2 m with local gravity.
* **The freeze does not change T1.**

### 4. The portal freeze removes T2 here, but only by coincidence

With the freeze on, T2 drops to ≤ 0.002 mg in every case and the floors to 0–8 m. Both causes lie in the
last 200 m before B in these scenarios: the braking in stop-and-go and the start of the climb's ramp.
**A grade change or braking 300 m before the portal would bring them back.** The causes belong in the
calibration itself.

### 5. Size against the realistic errors

All terms are ≤ 0.11 mg. The realistic handover offsets are 0.2–0.6 mg (GPS speed noise, after the
freeze ≈ 0.24 mg). So today they are small. But they are **systematic**: they do not average out over
runs, and they grow with conditions:
* T2b grows with the grade change near the portal and the curvature of the approach;
* T2a grows with braking at the end of the calibration;
* T1 grows with the grade change in the tunnel.

## Possible fixes (for discussion, not implemented)

| Fix | Term | How | Effort | Note |
|---|---|---|---|---|
| F1 | T1 | Take gravity from the calibration: the magnitude of the mean specific force the levelling already computes, instead of the standard constant | small | Phone data only, no leakage |
| F2 | T2a | Time the interval means correctly: half weight for the boundary samples (trapezoid), or shift by h/2 | very small | In `mount_estimation.py` |
| F3 | T2b | With map grade: remove g·sin(φ_i − φ̄) from the forward specific force before the yaw fit, so the grade change no longer biases yaw | small–medium | Without map grade the bias stays (the grade is unknown then) |

Expected effect: the ideal-sensor residuals go to near zero with or without the freeze. On the
realistic dev subsets probably little change (the terms are ≤ 0.11 mg), except sloped stop-and-go (F1).
Their value is correctness and robustness for approaches the freeze does not cover.

## Limits

* One traffic seed per case (as in the map-grade study). The mechanisms are deterministic, so one run
  per case suffices to identify them, but not to give their spread.
* T2b scales with the approach's mean lateral acceleration. Approaches with balanced left and right
  curves hide it, so its size in other geometries can differ.
