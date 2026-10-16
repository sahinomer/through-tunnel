# Standstill oracle (step 3a): what is knowing standstill worth?

Step 3 of [estimator_plan.md](estimator_plan.md), decision D49 (2026-10-16).

> **This is an oracle experiment, not a phone-only result.** Standstill is taken from the true motion.
> It measures the value of the information, not a detector. A real source would be a phone detector
> (vehicle vibration or engine audio, future research, roadmap R12) or the car itself. The estimators
> that use it are marked ‡ and kept out of the phone-only set.

## Why an oracle

The user decided against simulating vibration or engine audio to build a standstill detector. Such a
model could not be validated within the case study, and a detector tested only against it would prove
nothing. So the question is turned around: if standstill were known perfectly, how much would it gain?
* If little, detection research is not worth it.
* If a lot, the follow-up sensitivity study (detection delay, missed stops, false standstills during
  real slow-downs) shows how good a detector would have to be.

## What was built

* **Observation:** `StandstillStream` (`observations.py`). It holds the exact moments the car starts and
  stops standing still, from the true speed (exactly 0 during traffic stops), at the simulation rate of
  100 Hz (`sensors/standstill.py`).
* **Boundary**, as for the car's speed reading (D41): the runner delivers the stream only to estimators
  that declare `uses_standstill`. `ORACLE_ESTIMATORS` is a separate registry; `MAIN_ESTIMATORS`
  (phone-only) excludes it. Tested: a non-declaring estimator receives nothing.
* **Two variants of `route_imu`** (user choice: `route_imu` only, both variants):
  * **(a) `route_imu_stop`, speed reset.** While the car stands, the speed is exactly 0 and the route
    distance is held, in both directions. The phone-only estimators only have the v ≥ 0 clamp, which
    resets a negative speed error at a stop and lets a positive one creep (P5).
  * **(b) `route_imu_zupt`, speed reset + offset re-measurement.** During each stop the
    grade-compensated forward specific force is averaged. At a true standstill it is exactly the forward
    offset (calibration pitch residual + accelerometer bias + drift). That offset is subtracted until the
    next stop (zero-velocity update, solutions 3a/4a).
* **Without stops both variants equal `route_imu` exactly** (tested; free flow in all runs below).

## Results (development runs, D47; paired, 20 seeds)

Route + IMU vs. the two oracle variants in the same runs. Error 5 km into the tunnel (error sources) or
at C (benchmark): median (p90), ✗ = gross errors (> 200 m). Free flow is identical in every case (no
stops) and is left out.

### Error-source benchmark, 5 km flat tunnel, stop-and-go

| condition | route + IMU | (a) speed reset ‡ | (b) + offset ‡ |
|---|---|---|---|
| error-free (floor) | 0 (0) | 0 (0) | 0 (1) |
| GPS speed noise | 393 (782) ✗14 | 120 (429) ✗8 | **27 (75)** |
| GPS degradation (150 m) | 3 (12) | 3 (12) | 3 (11) |
| GPS degradation, harsh | 289 (782) ✗13 | 227 (310) ✗11 | **34 (61)** |
| calibration pitch 0.1° | 977 (1376) ✗20 | 977 (1376) ✗20 | **130 (236) ✗5** |
| accelerometer bias drift | 353 (782) ✗15 | 271 (458) ✗11 | **67 (143)** |
| **realistic** | 385 (782) ✗16 | 131 (607) ✗9 | **103 (199) ✗2** |

### Benchmark dev subset, stop-and-go (map grade on for sloped roads)

| scenario | route + IMU | (a) speed reset ‡ | (b) + offset ‡ |
|---|---|---|---|
| 0.5 km flat | 18 (92) ✗1 | 6 (17) | 5 (14) |
| 5 km flat | 385 (782) ✗16 | 131 (607) ✗9 | **103 (199) ✗2** |
| 5 km +3 % climb | 501 (782) ✗17 | 144 (782) ✗9 | **128 (199) ✗2** |
| 5 km underwater V | 613 (782) ✗14 | 132 (782) ✗10 | 127 (782) ✗9 |

Announcement more than 15 s off (stop-and-go, 5 km): route + IMU 14–16 of 20; (a) 8–9; (b) 6–10.

## Findings

1. **Knowing standstill is worth a lot in stop-and-go.** On the realistic 5 km stop-and-go, perfect
   standstill with offset re-measurement takes route + IMU from 385 to 103 m, with gross errors from 16
   to 2 of 20. That is about the free-flow level after step 1 (103 m). The climb behaves the same
   (501 → 128 m, gross errors 17 → 2).
2. **Both parts matter, for different errors.**
   * **(a), the two-sided speed reset**, removes the one-sided clamp's creep: 385 → 131 m, gross errors
     16 → 9. Both regression flags of steps 1 and 2b came from that creep. With (a), the climb case
     (501 m after 2b) drops to 144 m.
   * **(b), the offset measured at each stop**, removes what the reset cannot: a steady offset that
     builds a speed error between stops.
     * With a calibration pitch of 0.1°, (a) changes nothing (977 m) and (b) gives 130 m.
     * With GPS speed noise only, the handover offset is removed: 393 → 27 m.
3. **Bias drift limits (b), but it still pays off.** The drift moves the offset between stops (in one run
   from +0.36 to −0.34 mg in 3 minutes). A value measured at one stop can then be wrong by the next.
   In single runs (b) was worse than (a). Over 20 runs it is clearly better (drift alone: 271 → 67 m),
   but a filter with a drift model (step 4, 4c) should weight the stop measurements instead of taking
   the last one.
4. **The announcement improves less than the position.** In stop-and-go, 6–10 of 20 runs are still more
   than 15 s off with (b). At low speed a small position error is a large time error (traffic study),
   and the error is measured at the announcement point, not at C.
5. **Remaining: runaway runs in the underwater V with stop-and-go** (5–6 of 20 run more than 600 m
   ahead, with or without the oracle; route + IMU alone: 10).
   * The runaway seeds largely coincide (5, 6, 9, 15), so the cause is not the stops.
   * Likely the map-grade position feedback at the V's grade changes in long outages (map-grade study,
     mechanism 2). Not verified run by run.
   * With (b) there is a second risk: a stop cannot tell a real offset from a grade-lookup error caused
     by a position error. On a grade change it can measure a wrong offset (two of the six runaways with
     (b) are new seeds).
   * Grade changes as position fixes (3b, step 5) target this.

## Limits

* **Perfect oracle.** It reports every stop at the exact moment, with no false standstills. The
  sensitivity study follows: delays, missed stops, and false standstills tied to real slow-downs (user:
  "false standstill should be logical like when slow down, not randomly"); ranges to be agreed.
* **The simulator has no vibration.** A standing car's IMU shows only noise and bias, which makes the
  offset measurement at a stop cleaner than with a running engine.
* Stops are 10–60 s (traffic model T3). Short creeping stops in dense traffic are not modelled.
* Development runs only; the full benchmarks are rerun at the next milestone.

## Sensitivity (step 3b): how good would a detector have to be?

Decision D50 (2026-10-16). The oracle gets an error model (`StandstillOracleConfig`, schema v11; perfect
by default), tied to the real motion as the user asked ("false standstill should be logical like when
slow down, not randomly"):
* **delay:** every report starts and ends late;
* **missed stops:** each stop is dropped with a probability, drawn per stop from the run's seed (nested:
  the 10 % misses are a subset of the 30 % misses);
* **slow threshold:** standstill is reported whenever the true speed is below it. A detector cannot tell
  creeping from standing, so it fires early while braking and releases late while pulling away.
  * At 3 km/h: about 2.3 s early and 1 s late.
  * At 5 km/h: about 3 s early and 1.4 s late.

The parameters are configuration only, not in the UI (agreed): the question is statistical, and
sliders would make the oracle look like a tunable feature. In the UI the oracle estimators are now
hidden by default (still selectable).

Realistic 5 km tunnel, stop-and-go, error 5 km in, median (p90) ✗ gross errors, 20 paired runs
([sensitivity/](standstill_oracle/sensitivity/)); free flow is unchanged in every setting:

| oracle | route + IMU | (a) speed reset ‡ | (b) + offset ‡ |
|---|---|---|---|
| perfect | 385 (782) ✗16 | 131 (607) ✗9 | **103 (199) ✗2** |
| delay 0.5 s | 385 (782) ✗16 | 164 (579) ✗9 | 528 (847) ✗20 |
| delay 1 s | 385 (782) ✗16 | 389 (851) ✗16 | 1689 (2100) ✗20 |
| delay 2 s | 385 (782) ✗16 | 994 (1528) ✗20 | 3057 (3422) ✗20 |
| delay 3 s | 385 (782) ✗16 | 1553 (2185) ✗20 | 3405 (3766) ✗20 |
| missed 10 % | 385 (782) ✗16 | 155 (607) ✗10 | **84 (199) ✗2** |
| missed 30 % | 385 (782) ✗16 | 204 (685) ✗11 | **126 (221) ✗3** |
| below 1 km/h | 385 (782) ✗16 | 167 (577) ✗8 | 130 (293) ✗7 |
| below 3 km/h | 385 (782) ✗16 | 383 (845) ✗16 | 398 (673) ✗20 |
| below 5 km/h | 385 (782) ✗16 | 642 (1105) ✗18 | 697 (1005) ✗20 |
| combined: 1 s, 10 %, 3 km/h | 385 (782) ✗16 | 985 (1521) ✗20 | 2819 (3235) ✗20 |

### Findings

1. **Missed stops are harmless.** A missed stop only loses one reset and one measurement; nothing wrong
   is injected. With 30 % of the stops missed, (b) still gives 126 m. (At 10 %, 84 m is
   slightly better than perfect: run-to-run spread; the cause was not examined.)
2. **Timing is critical, above all the end of a stop.** With the naive use above, a late release breaks
   both variants. Verified on one run with 0.5 s delay:
   * when the oracle releases, the car already rolls at 0.26 m/s, but the estimator restarts from 0.05–0.08 m/s;
   * every stop therefore leaves a lasting speed error;
   * in (b) the stop's offset measurement also contains the start of the acceleration: +0.29 to
     +1.94 mg, against the real −0.03 to −0.22 mg.
   * Result: (b) is worse than no oracle already at 0.5 s (528 m), and (a) loses its whole gain at 1 s.
3. **A slow threshold acts mostly like a release delay.** Pulling away below 3 km/h takes about 1 s, so
   3 km/h behaves like the 1 s delay. The early report while braking costs little: the car is already
   slow, and the estimator's own speed is near zero.
4. **So, used naively, a detector would have to be nearly perfect:** release within ~0.25–0.5 s, below
   ~1 km/h. A real vibration or audio detector is unlikely to manage that.
5. **The naive use is the problem, not the information. A robust use is possible (proposed, not
   built): "trim and replay".**
   * Keep the last M seconds of forward IMU samples, M ≥ the worst expected delay (e.g. 3 s).
   * Leave the first and last M seconds of each stop out of the offset average.
   * At the release, re-integrate the buffered samples from speed 0 at t − M: if the car really stood
     still that adds only noise; if it was already moving, it recovers the true speed and distance.
   * This should tolerate release delays up to M and the slow threshold, turning "nearly perfect" into
     "right within a few seconds". It needs its own sweep to confirm.

### Limits of the sensitivity study

* One condition (realistic, 5 km flat tunnel, stop-and-go); the sloped dev scenarios were not swept.
* One setting per parameter except the combined case; interactions are not mapped.
* Stops in the traffic model start from smooth constant-jerk manoeuvres (speed and acceleration reach
  zero together); harsher real starts make release timing even more critical.
