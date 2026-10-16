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
