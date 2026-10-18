# Portal freeze (step 1): no GPS learning right before the tunnel

Step 1 of [estimator_plan.md](estimator_plan.md), solutions 1a + 2a, decision D46 (2026-10-16).
The handover diagnostic ([gps_loss_state.md](gps_loss_state.md)) showed that the state handed over at
GPS loss is set by the GPS speed errors of the **last** approach fixes: the levelling's forward offset
is (δv_last − δv_first)/T, and the 5 s blend hands over the last few speed errors. Degraded fixes right
before the portal therefore do the most damage.

Data: [portal_freeze/](portal_freeze/) (development runs, agreed testing strategy: `--dev` subsets,
20 paired seeds; the full benchmarks are rerun at milestones). The runs were made on the working tree
of this commit (`meta.json` says `1811edd+dirty`).

## What changed

* **The freeze zone** (`positioning/portal.py`): from 200 m before the tunnel entrance B to the exit C,
  looked up at each fix's position projected onto the route. The route map knows where the tunnel is.
* **1a, calibration:** inside the zone the GPS + IMU alignment adds no fixes and no IMU data. It keeps
  the orientation solved before the zone. After C it calibrates again.
* **2a, handover:** inside the zone `route_imu` and `dr_filtered` stop pulling speed (and, for
  `dr_filtered`, heading) towards the fixes. The IMU carries them from the last trusted state. Position
  still follows the fixes, because the degraded positions are only metres off.
* **Unchanged:**
  * `dr_calibrated` resets to every fix by design (only its calibration freezes);
  * `route_hold` (the naive reference) and `route_vspeed` (the reference) are untouched.
* **Switch:** `FREEZE_BEFORE_ENTRANCE_M = None` restores the previous behaviour. Verified: with the
  freeze off, all 800 records of the error-source dev subset are identical to the baseline.

## Results

### Error-source dev subset: freeze distance sweep

The 5 km flat tunnel, route + IMU, error 5 km in: median (p90) [m], ✗n = runs with a gross error
(> 200 m), 20 runs each. The GPS degradation in the simulation covers the last 150 m (normal) or 500 m
(harsh) before B.

| condition | traffic | off (baseline) | 100 m | **200 m** | 500 m |
|---|---|---|---|---|---|
| GPS speed noise only | free | 98 (185) ✗2 | 95 (273) ✗4 | 102 (245) ✗4 | 81 (334) ✗3 |
| | stop-and-go | 196 (782) ✗10 | 307 (782) ✗13 | 393 (782) ✗14 | 386 (782) ✗12 |
| GPS degradation (150 m) | free | 184 (344) ✗9 | 46 (64) | **4 (8)** | 4 (8) |
| | stop-and-go | 354 (782) ✗13 | 94 (629) ✗6 | **4 (11)** | 5 (11) |
| GPS degradation, harsh (500 m) | free | 188 (412) ✗9 | 112 (214) ✗4 | 133 (242) ✗7 | 11 (25) |
| | stop-and-go | 373 (782) ✗14 | 215 (782) ✗10 | 289 (782) ✗13 | 11 (34) |
| **realistic** | free | 231 (420) ✗11 | 147 (403) ✗5 | **103 (257) ✗4** | 139 (302) ✗7 |
| | stop-and-go | 482 (804) ✗16 | 447 (782) ✗15 | 385 (782) ✗16 | 509 (782) ✗17 |
| floor (error-free) | free | 0 (0) | 0 (0) | 0 (0) | 0 (1) |
| | stop-and-go | 13 (17) | 2 (15) | **0 (1)** | 1 (5) |

`dr_filtered` behaves the same (realistic free flow: 217 → 117 m, gross errors 11 → 4). The reference
is unchanged in every cell. Handover state in the realistic setting (route + IMU, medians):

| freeze | forward offset, free / stop-and-go [mg] | handover speed error, free / stop-and-go [m/s] |
|---|---|---|
| off | 0.60 / 0.64 | 0.112 / 0.119 |
| 100 m | 0.29 / 0.27 | 0.038 / 0.047 |
| 200 m | 0.22 / 0.24 | 0.047 / 0.055 |
| 500 m | 0.24 / 0.25 | 0.088 / 0.089 |

### Benchmark dev subset (guard scenarios, map grade on, freeze 200 m)

Error at C, median (p90), ✗ gross errors, baseline → freeze, route + IMU
([compare.md](portal_freeze/benchmark_dev/compare.md) has all estimators):

| scenario | free flow | stop-and-go |
|---|---|---|
| 0.5 km flat | 5 (15) → 6 (12) | 18 (220) ✗3 → 18 (92) ✗1 |
| 5 km flat | 231 (420) ✗11 → **103 (257) ✗4** | 482 (804) ✗16 → 385 (782) ✗16 |
| 5 km +3 % climb | 223 (436) ✗12 → **109 (268) ✗4** | 427 (811) ✗17 → 297 (782) ✗13 |
| 5 km underwater | 44 (107) → 42 (93) | 490 (782) ✗14 → **767 (782) ✗13 ⚠** |

## Findings

1. **The prediction held.** The handover diagnostic predicted realistic free flow ≈ 220 → 110 m and
   harsh degradation 200 → 129 m from the formula. Measured: 231 → 103 m and 188 → 133 m. In free flow
   the gross errors fall from 11 to 4 of 20 on the 5 km flat and climb tunnels.
2. **Degradation inside the zone is removed completely**: 150 m degradation 184 → 4 m (free) and
   354 → 4 m (stop-and-go). The harsh case starts 500 m before B, so a 200 m freeze removes only part of
   it; a 500 m freeze removes it all.
3. **The freeze distance is a trade-off.**
   * Longer freezes cost:
     * a shorter calibration, so a larger endpoint noise;
     * more time on the IMU, so the speed error carried to B grows. At 500 m it is 0.088 m/s against
       0.047 m/s at 200 m, and realistic free flow is 139 m against 103 m.
   * Shorter freezes leave degraded fixes in.
   * **200 m is the best of the three in the realistic setting.** But the simulated degradation length
     (150 m) was chosen by us, so this is partly circular. In reality the right distance depends on the
     portal and is unknown. I keep 200 m as the default and report the sensitivity.
4. **Without degradation the freeze neither helps nor hurts on average, but costs speed accuracy.**
   With GPS speed noise only, the offset keeps the same size (free flow 0.235 → 0.237 mg): freezing
   makes a different fix the endpoint. The handover speed is about 10 s older (demo preset, clean GPS:
   0.063 → 0.111 m/s for `dr_filtered` and `route_imu`). This is the remaining endpoint noise of
   ordinary GPS speed: the case for fitting the offset over all fixes (1e) or the filter's offset state.
5. **The stop-and-go floor vanishes**: 13 → 0 m with error-free sensors. The tiny positive offset
   behind it (handover study) is learned in the last 200 m before the portal. This is a strong lead for
   step 2: probably how the stop-and-go traffic shapes the end of the approach (to be checked there).
6. **Regression flag, underwater stop-and-go: 490 → 767 m median, gross errors 14 → 13.** The freeze
   shrinks the large negative errors (worst −1081 → −752 m) but more runs end ahead, and those hit the
   route-end cap (capped runs 6 → 10; flat stop-and-go: ahead 9 → 16 of 20). Likely mechanism (not
   verified run by run): the one-sided v ≥ 0 clamp (P5).
   * A negative speed error is reset at every stop.
   * A positive one, from the offset or the in-tunnel bias drift, keeps creeping.
   * With smaller handover offsets, the drift and this rectification decide the sign more often, and
     both push ahead.

   In stop-and-go the median of |error| is dominated by the sign and the cap, so it moves a lot between
   draws (GPS speed noise only: 196 → 393 m with the same offset size). This is the target of step 3
   (two-sided standstill handling).

## Limits

* The degradation model knows nothing about the freeze, but its length (150 m) was chosen by us. With a
  degradation longer than the freeze the gain shrinks (harsh case).
* The handover now ages about 10 s (200 m at 70 km/h); in slow traffic before the portal it ages more.
* Development runs only (8 benchmark scenarios, 5 error-source conditions). The full benchmarks are
  rerun at the next milestone.
