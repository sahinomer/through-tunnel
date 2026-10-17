# Benchmark baselines

The benchmark (D43, `evaluation/benchmark.py`) is the fixed yardstick for every estimator: 48 scenarios
× 20 runs with the realism options on. Each later estimator change is compared against a saved
baseline on exactly the same runs:

    uv run python -m throughtunnel.evaluation.benchmark --quick --out out/dev --compare docs/benchmark/baseline

**During development (D47)** each change runs the development subsets, ~6 min each instead of 32–42:

    uv run python -m throughtunnel.evaluation.benchmark --dev --out out/dev/<step> --compare docs/benchmark/baseline
    uv run python -m throughtunnel.evaluation.error_sources --dev --out out/dev/<step>_es --compare docs/benchmark/error_sources

* `--dev` (benchmark): the 0.5 and 5 km flat tunnels, the 5 km climb and underwater tunnels, and (since D54)
  the Eisenhower tunnel on a flat road, both traffic cases; map grade on only; the calibrated estimators, the reference and (since D49) the two standstill
  oracle variants; 20 seeds.
* `--dev` (error sources): floor, GPS speed noise, degradation (normal, harsh), realistic; since D52 also
  calibration pitch 0.1°, calibration yaw 2° and hard.
* On unchanged code both reproduce the baselines exactly.
* The full set is rerun at milestones.

| Baseline | Commit | Estimators | Tables |
|---|---|---|---|
| `baseline/` | `36904cb` (2026-10-15) | the 5 phone-only estimators before any estimator work, + the reference | [tables](baseline/tables.md) · [configuration](baseline/config.md) |
| `error_sources/` (D45) | `e69543f` (2026-10-15) | the same estimators; one error source at a time on the 5 km flat tunnel | [tables](error_sources/tables.md) · [configuration](error_sources/config.md) |
| `milestone_step4/` | `00ab89b` (2026-10-16) | both benchmarks in full after steps 1–4 (portal freeze, calibration fixes, standstill oracle ‡, Kalman filter `route_kf`) | benchmark: [tables](milestone_step4/benchmark/tables.md) · [vs. baseline](milestone_step4/benchmark/compare.md) · [configuration](milestone_step4/benchmark/config.md); error sources: [tables](milestone_step4/error_sources/tables.md) · [vs. baseline](milestone_step4/error_sources/compare.md) |
| `milestone_step5/` | `0b4ee46` (2026-10-17) | both benchmarks in full after steps 4.1–6.2 and D54 (yaw state `route_kf_yaw`, uncertainty-aware announcement, wider filter priors, map curve fixes `route_kf_map`) + the σ consistency check | benchmark: [tables](milestone_step5/benchmark/tables.md) · [vs. milestone_step4](milestone_step5/benchmark/compare.md) · [configuration](milestone_step5/benchmark/config.md); error sources: [tables](milestone_step5/error_sources/tables.md) · [vs. milestone_step4](milestone_step5/error_sources/compare.md); [σ consistency](milestone_step5/uncertainty/tables.md) |

Each baseline directory holds, next to its results, the configuration it ran with: `config.md` (readable,
including where the setup is optimistic) and `config.json` (the complete effective configuration of every
scenario). They are as important as the results: a number means nothing without its settings.

**Note on the profiles:** the labels "+3 % climb" and "−4 % / +4 % underwater" are the design grades.
The actual steepest grades are 3.1–3.4 % and 3.1–4.5 % (`config.md`). The 0.5 km underwater tunnel dips
only 5 m, because its descent is too short for the 400 m grade transitions to reach 4 %.

## Failure states (D44)

Per run and estimator:
* **Gross error** (failure): the estimate was more than **200 m** from the true position at some time
  in the tunnel or at C, **ahead or behind**. The position is unusable for guidance.
* **Announcement off** (failure): the exit announcement was more than **15 s** early or late, or never
  fired. The driver gets the instruction at the wrong time. In practice it is never missing: a late
  estimate is pushed past the announcement point when GPS returns, so it is late.
* **Capped at D** (data-quality flag, not a failure): the estimate reached the route end D before the
  vehicle reached C. A route estimate stops at D, so its error is a lower bound (exactly 782 / 881 /
  889 m = the C–D distance). Every capped run is also a gross error.

The first version counted only "capped at D" (plus a missed announcement, which never happens) as a
failure. That is one-sided: an estimate 1 km behind never counted. For the best phone-only estimator
with map grade, 7 % of runs failed by that definition and 21 % have a gross error.

## What the first baseline says

All 48 scenarios, median (p90); † = reference (uses the car's speed):

| Estimator | map grade | error at C | gross error | announcement off | announcement good (±3 s) |
|---|---|---|---|---|---|
| Route + vehicle speed † | either | 5 m (14–15) | 0 % | 0 % | 99 % |
| Route + filtered IMU speed (best phone-only) | on | 39 m (544) | 21 % | 20 % | 59 % |
| | off | 782 m (889) | 69 % | 65 % | 20 % |
| DR calibrated + GPS-blended | on | 58 m (543) | 22 % | 19 % | 59 % |
| Route + last GPS speed (naive) | either | 435 m (881) | 58 % | 52 % | 24 % |

* **The reference sets the ceiling.** It holds 4–7 m median for every tunnel length, road profile and
  traffic case: car speed is worth about an order of magnitude.
* **Map grade is essential for the IMU estimators.** Without it, a sloped tunnel costs 0.8–25 km. With
  it, sloped roads match flat ones; the underwater V is even better (the grade-change feedback,
  [map_grade_study.md](../map_grade_study.md)).
* **The phone-only error grows with outage time.** On a flat road the best phone-only estimator goes
  from 5 m (0.5 km tunnel) to 231 m (5 km) in free flow, and to 482 m at 5 km in stop-and-go. Gross
  errors: 0 of 20 runs up to 2 km and 11 of 20 at 5 km in free flow; 3 of 20 at 0.5 km and 16 of 20
  at 5 km in stop-and-go.
* **The naive constant-speed estimator** is competitive in free flow on short tunnels, but has a gross
  error in every stop-and-go run, nearly all capped at D (it keeps driving while the car stands).
* **Announcements:** with map grade, the best phone-only estimators announce within ±3 s in 59 % of
  runs and are more than 15 s off in 19–20 %; 85–89 % of those runs also have a gross error. In
  stop-and-go, small position errors also become large timing errors at low speed (traffic study).

These are the numbers the estimator work has to improve: phone-only, with map grade, the 5 km and
stop-and-go cases.

## What the error-source benchmark says

The 5 km flat tunnel, error 5 km in for the best phone-only estimators (route + IMU / DR filtered),
median [m]. Each condition adds one error source to an error-free setup:

| Error source | free flow | stop-and-go | through (handover at GPS loss) |
|---|---|---|---|
| none (floor) | 0 | 12–13 | – |
| calibration pitch 0.1° / 0.5° | 540–590 / 2 600 | 880–950 / 3 300 | forward offset 1.7 / 8.7 mg |
| GPS degradation before the portal (normal / harsh) | 170–184 / 175–188 | 325–354 / 337–373 | forward offset 0.5 mg, speed 0.12–0.14 m/s |
| GPS speed noise | 95–98 | 196–210 | forward offset 0.2 mg, speed 0.05 m/s |
| accelerometer bias drift | 78–85 | 328–354 | changes inside the tunnel |
| calibration yaw 2° | 57–58 | 79–82 | lateral acceleration on curves |
| accelerometer noise | 7 | 26–28 | – |
| gyro noise / bias / drift, accelerometer bias, tilted mount, calibration roll, GPS position error | 0–15 | 12–67 | constant errors are calibrated away |
| all realistic (benchmark setting) | 217–231 | 470–482 | forward offset 0.6 mg, speed 0.11 m/s |
| hard (+ tilted mount + calibration error) | 2 610–2 640 | 3 280–3 300 | dominated by the 0.5° pitch |
| reference (car speed), realistic | 6 | 7 | – |

* **The handover state decides the error.** For the calibration and GPS conditions in free flow, the
  along-track error 5 km in is ½ · forward offset · t² + speed error · t from the state at GPS loss
  (correlation 0.99–1.00 per run). Only bias drift, which changes inside the tunnel, is not predicted
  this way (0.48). The tunnel phase adds almost nothing: the error is set before the tunnel.
  *Correction (2026-10-16, [handover_study.md](../handover_study.md)):* this was checked in free flow
  only. In stop-and-go the v ≥ 0 clamp resets negative speed errors at stops, and the formula
  overshoots 3–5×. The same diagnostic shows where the handover state comes from: the forward offset is
  (δv_last − δv_first)/T, set by the GPS speed errors of the first and last approach fix.
* **Unreliable GPS before the entrance hurts the GPS-calibrated estimators (confirmed).** Degraded
  fixes in the last 150 m before B corrupt the levelling (0.5 mg forward offset ≈ 0.03° pitch) and
  the handed-over speed (0.12 m/s). Alone, this costs 170–190 m after 5 km. The harsh version (500 m,
  20 m) is barely worse: the damage comes from the last fixes, not from how long the degradation lasts.
* **Calibration pitch is the single largest risk.** 0.1° = 1.7 mg costs ~550 m after 5 km; the
  estimators cannot observe it after the calibration.
* **What the calibration already handles.** Constant errors (accelerometer and gyro bias, a tilted
  mount, roll) are calibrated away almost completely.
* **Stop-and-go doubles the time-driven errors** (drift, offsets): 738 s instead of 258 s to 5 km. The
  floor itself is 12–13 m there (error-free sensors), so the algorithm alone loses some accuracy at
  stops.

## Milestone after step 4 (2026-10-16, `milestone_step4/`)

**Comparison policy (user, 2026-10-16):** later work is compared with the previous reference (now
this milestone), not with the first baseline. All raw results are kept, so any comparison can be
regenerated.

Both benchmarks in full (all 48 scenarios / 18 conditions, 20 seeds, every estimator) after the portal
freeze (D46), the calibration fixes (D48), the standstill oracle (D49/D50) and the Kalman filter (D51),
compared on the same runs with the baselines above. `compare.md` reports no regression in any scenario
family. ‡ = oracle (standstill from the truth, not phone-only), † = reference (car speed).

**All 48 scenarios, map grade on**, error at C median (p90), share of runs:

| estimator | error at C [m] | gross error | announcement off (> 15 s) | announcement good (±3 s) |
|---|---|---|---|---|
| Route + filtered IMU speed, **baseline** | 39 (544) | 21 % | 20 % | 59 % |
| Route + filtered IMU speed, now | 31 (413) | 16 % | 16 % | 65 % |
| **Route + IMU Kalman filter (new)** | **30 (325)** | **15 %** | **14 %** | 65 % |
| DR calibrated + GPS-blended, now (baseline: 58 (543), 22 %) | 51 (443) | 17 % | 16 % | 64 % |
| Route + IMU + standstill oracle: speed reset ‡ | 22 (142) | 7 % | 8 % | 71 % |
| Route + IMU + standstill oracle: speed reset + offset ‡ | 17 (87) | 3 % | 4 % | 78 % |
| Route + vehicle speed † | 5 (14) | 0 % | 0 % | 99 % |

**5 km flat tunnel** (error at C, median (p90) ✗ gross errors):

| | free flow | stop-and-go |
|---|---|---|
| Route + IMU, baseline | 231 (420) ✗11 | 482 (804) ✗16 |
| Route + IMU, now | 103 (257) ✗4 | 385 (782) ✗16 |
| Kalman filter | 85 (283) ✗4 | 188 (782) ✗9 |
| oracle: speed reset + offset ‡ | 103 (257) ✗4 | 103 (199) ✗2 |

**Error sources** (error 5 km in, median [m]; Route + IMU baseline → now / Kalman filter):

| condition | free flow | stop-and-go |
|---|---|---|
| realistic | 231 → 103 / **85** | 482 → 385 / **188** |
| calibration pitch 0.1° | 588 → 628 / **3** | 953 → 977 / **5** |
| calibration pitch 0.5° | 2617 → 2777 / **17** | 3290 → 3354 / **24** |
| hard (tilted mount + calibration error) | 2610 → 2760 / **255** | 3277 → 3390 / 782 (capped) |
| GPS degradation / harsh | 184 → 4 / 4; 188 → 133 / **31** | 354 → 3 / 6; 373 → 289 / **57** |
| GPS speed noise | 98 → 102 / 85 | 196 → 393 / 182 |
| bias drift | 85 → 90 / 92 | 354 → 353 / 306 |
| error-free floor | 0 → 0 / 1 | 13 → 0 / 3 |
| **calibration yaw 2°** | 58 → 67 / 65 | 82 → 96 / **204** |

What the milestone shows:
* **The phone-only error roughly halved** where it was largest. Realistic 5 km free flow went from 231 m
  to 103 m (Route + IMU) and 85 m (filter); stop-and-go from 482 m to 188 m (filter). Gross errors over
  all scenarios fell from 21 % to 15 %.
* **A calibration pitch residual is no longer the dominant risk** for the filter: 0.1° costs 3–5 m
  instead of 600–1000 m, and 0.5° costs 17–24 m instead of ~3 km. The `hard` condition drops from 2.8 km
  to 255 m in free flow.
* **The yaw residual is the new limit.** With a 2° yaw error the filter is worse than Route + IMU in
  stop-and-go (204 vs. 96 m): in turns the yaw residual leaks lateral acceleration into the forward
  channel, and the filter takes it for offset. Next candidate: yaw as a filter state (6b).
* **Free-flow tails are mixed.** The filter has better medians but worse p90 at 2–3 km (72 vs. 46 m,
  134 vs. 77 m) and similar at 5 km (283 vs. 257 m).
* **Route + IMU got slightly worse with an injected calibration pitch** (588 → 628 m). Likely, not
  verified: the portal freeze ends the speed blending about 10 s earlier, so the pitch error acts
  over a slightly longer stretch.
* **The oracle's ceiling stays well ahead**: 17 m median and 3 % gross errors over all scenarios,
  against the filter's 30 m and 15 %. Most of the gap is in stop-and-go, and a detector would need
  release timing within ~0.5 s to deliver it (D50).
* Still optimistic in this setup: an exact map, the reported speed accuracy equal to the injected noise
  (flatters the filter's weighting), and no vibration.


## Milestone after step 5 (2026-10-17, `milestone_step5/`)

**Reference for later work** (iterative comparison policy). Both benchmarks in full (48 scenarios / 18
conditions, 20 seeds, every estimator) at `0b4ee46`, compared with `milestone_step4`, plus the σ consistency
check (step 6.1) for all three Kalman filters. New since step 4: `route_kf_yaw` (D52), the uncertainty-aware
announcement (D53), wider filter priors (D54) and `route_kf_map` with map curve fixes (D55). `compare.md`
flags one regression: `route_kf`, flat stop-and-go, 61 → 70 m median (D54's prior; the clamp's sign lottery,
not significant on paired runs).

**All 48 scenarios, map grade on**, error at C median (p90), share of runs:

| estimator | error at C [m] | gross error | announcement off (> 15 s) | announcement good (±3 s) |
|---|---|---|---|---|
| Route + filtered IMU speed (step 4: 31 (413), 16 %) | 31 (413) | 16 % | 16 % | 65 % |
| Route + IMU Kalman filter `route_kf` (step 4: 30 (325), 15 %) | 29 (312) | 14 % | 15 % | 67 % |
| Kalman filter + yaw `route_kf_yaw` | 33 (387) | 17 % | 15 % | 63 % |
| **Kalman filter + map curves `route_kf_map`** | **8 (51)** | **3 %** | **3 %** | **89 %** |
| standstill oracle: speed reset + offset ‡ | 17 (87) | 3 % | 4 % | 78 % |
| Route + vehicle speed † | 5 (14) | 0 % | 0 % | 99 % |

**Selected scenarios** (error at C, median ✗ gross errors), `route_kf` / `route_kf_map`:

| scenario | free flow | stop-and-go |
|---|---|---|
| 5 km ladder, flat | 80 ✗4 / **12** | 241 ✗13 / **30 ✗1** |
| 5 km ladder, underwater | 40 / **11** | 322 ✗15 / **78 ✗5** |
| Seattle SR99, flat | 37 / **10** | 132 ✗8 / **21** |
| Eisenhower, flat (nearly straight) | 43 / **22** | 133 ✗7 / **20 ✗8** |
| Eisenhower, +3 % climb | 42 / **16** | 145 ✗8 / **77 ✗8** |

**Error sources** (5 km in, median ✗ gross), `route_kf` / `route_kf_yaw` / `route_kf_map`:

| condition | free flow | stop-and-go |
|---|---|---|
| realistic | 80 ✗4 / 84 ✗4 / **12** | 241 ✗13 / 299 ✗12 / **30 ✗1** |
| accelerometer bias drift | 92 ✗2 / 92 ✗2 / **9** | 306 ✗14 / 308 ✗13 / **27** |
| calibration pitch 0.5° | 0 / 0 / 2 | 2 / 3 / 8 |
| calibration yaw 2° | 64 / **0** / 49 | 203 ✗10 / **2** / 20 |
| hard | 361 ✗17 / 157 ✗7 / **45** | 782 ✗20 / 399 ✗16 / **42 ✗11** |

**σ consistency of `route_kf_map`** ([uncertainty/tables.md](milestone_step5/uncertainty/tables.md)): honest in free flow
(realistic 5 km: 75 % / 95 % within ±1σ / ±2σ), conservative in stop-and-go but far less than `route_kf` (σ 54 m
vs. 1.7 km at the announcement point). Overconfident with a calibration yaw error (no yaw state: error 35 m vs.
σ 13 m) and in a few underwater stop-and-go runs.

What the milestone shows:
* **Curves inside the tunnel are worth more than anything else phone-only.** `route_kf_map` brings all
  scenarios to 8 m median and 3 % gross errors, the level of the standstill oracle without the oracle, and
  89 % good announcements. Stop-and-go is solved in curved tunnels.
* **This result is flattered by the benchmark** (D55, limitations.md): the map is exact, every ladder tunnel has
  two S-arcs, and the car never changes lanes. Eisenhower, the one nearly straight tunnel, keeps its
  stop-and-go gross errors (✗8): there the curve fixes have little to work with.
* **What remains:** nearly straight tunnels in stop-and-go (only standstill information would help; oracle:
  24 m), the underwater V in stop-and-go (map-grade feedback), and a calibration yaw error for `route_kf_map`
  (no yaw state; `route_kf_yaw` handles it, but combining both was tied under realistic conditions and is
  not registered).
* The reference († car speed) stays far ahead: 5 m median, 0 % gross errors.
