# Roadmap and task tracking

Last reviewed: 2026-10-13, cleanup phase (see §0.1); §0 is the first positioning phase; §1 is the pre-positioning review. This file tracks status, remaining work and open
decisions. Decisions live in [decisions.md](decisions.md), and the proposed positioning architecture in
[positioning_design.md](positioning_design.md). The earlier [readiness_review.md](readiness_review.md) is
kept for history; its items are mapped to the tasks below.

Legend:
* `[x]` done and validated
* `[~]` partially done (gap stated)
* `[ ]` to do
* *(decision)* waiting for a decision

## 0. Update after the first positioning phase (2026-10-12)

The user delegated the open choices (PD1–PD8 adopted, see decisions.md). Implemented and tested
(136 tests):

* **Observation boundary** (`observations.py`) + import-boundary test.
* **A–D scenarios**: schema v4; presets with approach and recovery; four-click selection in the UI;
  U-turn selections rejected.
* **Phone GPS**: time-correlated errors, randomised loss before B, delayed reacquisition.
* **Estimator contract, causal runner, shared announcer.**
* **Mount alignment and calibration component.**
* **Five estimators** (raw, calibrated and GPS-blended dead reckoning; route-constrained with
  filtered IMU speed; naive last-GPS-speed reference).
* **Evaluation and Monte-Carlo report**: `python -m throughtunnel.evaluation.report`.
* **UI**: tunnel band, GPS track, estimate overlays with toggles, errors tab.

Initial results: [results.md](results.md). The best estimator (route + filtered IMU speed) ends the
tunnel at 16–34 m median error and announced the old mid-tunnel exit 0.1–0.6 s late (median), under
the simplifying assumptions. With the D32 announcement (300 m before C, i.e. near the end of the
outage) its median timing error is 0.7–1.4 s.

**Findings raised for attention** (per the user's request to flag findings that affect credibility):

1. **Flat-road assumption.** The calibrated estimators depend on approach-phase levelling cancelling
   the accelerometer bias. A grade change between approach and tunnel breaks this: 3 % gives
   0.29 m/s², which is ~1 km after 90 s. Until R1 is done, the IMU-based numbers are optimistic.
   **Recommended next.**
2. **The naive speed-hold looks good or bad depending on the drive.** Single-drive comparisons
   mislead, so results must vary the drive (now `--vary-drive`).
3. **Map ≈ truth geometry** (R3): route-constrained results are optimistic until map errors are modelled.

Problems found and fixed during this phase:
* The A–D click flow crashed the vehicle simulation on a U-turn selection.
* The gyro-bias end-point estimator produced a 470 m tail.
* A tab handler error appeared on every page load.

**Next (suggested order):**
1. R1 road grade (+ grade-aware levelling, or at least the sensitivity analysis).
2. R3 map errors.
3. A8 probabilistic estimator with covariance (then NEES/coverage in A11).
4. R2 stop-and-go.
5. Split `page.py` (P9). *Done 2026-10-13, §0.1 task 2.*
6. F2/F3 write-up.

## 0.1 Cleanup and refinement phase (from 2026-10-13)

Working mode set by the user: **one task at a time**; each task is completed, validated, summarised and
committed, then work stops for review. No automatic follow-up improvements. Findings go into the notes.

**Task 1: simplified exit announcement (D32), done.** The navigation event inside B–C with two
announcements (300 m before and at the event) was replaced by one announcement a configurable distance
`d` before the physical tunnel exit C (default 300 m, 0 ≤ d ≤ B–C length). One shared Announcer, one
trigger per estimator per run, from the estimate only. Schema v5 (older files migrate). Validation:
positioning outputs and error metrics are bit-identical before and after on all three presets × five
estimators; only the announcement metric changed. Results tables regenerated.

**Limitations of the simplified announcement (L-ANN; documented, not requirements):**
1. *Interpretation of the brief.* "Call out an exit inside the tunnel at the right moment" is read as:
   the call-out happens inside the tunnel, without GPS, for a maneuver at the tunnel exit C. **No exit
   ramp or junction inside the tunnel is modelled.** In real long urban tunnels with internal exits
   (e.g. Stockholm Norra länken, Madrid M-30, Boston I-93), the maneuver itself lies in the outage: the
   app must also time the "now" instruction and later decide whether the driver took the exit. That
   is not evaluated; route-constrained estimators assume the vehicle stays on the route.
2. *What is not lost.* d ranges over the whole tunnel, so the announcement can be placed at any time into
   the outage (d = B–C length is at B, d = 0 at C). The timing error is essentially the along-track
   error at that point divided by speed, the same quantity the old event measured. The old defaults
   (event at mid-tunnel, leads 300 m / 0 m) correspond to d = L/2 + 300 m and d = L/2.
3. *One sample per run.* Each run gives one timing error per estimator (previously two). Multi-stage
   prompts (e.g. 1 km / 400 m / now) are not represented; a sweep over d (one run per value) would give
   timing error vs. time-into-outage. Possible experiment, not implemented.
4. *Trigger rule.* A pure distance threshold. Real apps schedule prompts by estimated time-to-maneuver
   (speed-dependent) and account for speech duration; early and late errors are not equally harmful
   (late can mean a missed exit). We report |error| percentiles and the signed mean.
5. *Small d.* Near d = 0 a lagging estimator may only reach C − d after GPS returns (3–5 s after C), so
   its "announcement" then reflects GPS reacquisition rather than dead reckoning.

**Task 2: UI page split (P9), done.** `app/page.py` went from 989 to 383 lines and now only
orchestrates (state, layout, simulation/positioning runs, playback). New components:
* `controls.py`: parameter panels (drive/road, exit announcement, phone mount, IMU and GPS errors),
  each converting its controls to/from the config models;
* `map_view.py`: the Leaflet map, its layers and the browser track player;
* `route_picker.py`: the A–B–C–D click selection, OSRM routing and validation;
* `readouts.py`: pure HTML builders (scenario summary, live readouts).

The split preserves behaviour. Validation: one scripted interaction sequence was run through the old
and the new page (preset load, mount yaw, gyro bias, GPS σ, mount preset, announcement distance,
estimator toggle, clicked route, seek). The two pages gave identical outputs at all 9 steps:
scenario config, positioning summary, route info, live readouts, sensor and axes labels, map layer set.
The real server serves the page without errors. The comparison script was a one-off and is not in the
repository; new tests cover the readout builders and the panel → simulation wiring (145 tests). The
browser-side map animation was not re-checked in a real browser: its JavaScript calls are unchanged.
Minor differences:
* Choosing a mount preset now only resets the mount controls; before, it also reset the IMU/GPS error
  controls to their last applied values (identical except for an un-applied edit).
* Two empty, never-filled labels were removed (`gps_label`; `tunnel_info` in task 1).

**Task 3: configurable calibration error and controlled study (D34), done.** Details and tables:
[calibration_error.md](calibration_error.md).
* *Model:* the actual mount drives the sensors. The orientation each estimator uses is rotated by a
  configurable yaw/pitch/roll error, injected by the harness rather than given as an observation.
  Default off; UI panel; schema v6.
* *Unchanged:* with the error off, positioning outputs are bit-identical; the sensor data is
  identical with the error on (both tested).
* *Not done:* no correction methods, by request.
* *Study:* 3 presets × 10 seeds, paired runs (identical observations with and without the error);
  `python -m throughtunnel.evaluation.calibration_study`.
* *Findings:*
  * Pitch error dominates. Gravity leaks into the forward channel at 17 mg per degree, giving an
    along-track error of −½·g·sin θ·τ². 0.05° adds 40–100 m at C; 0.5° adds 0.4–1 km.
  * All IMU-integrating estimators are hit about equally. The route constraint does not help, and GPS
    blending makes it slightly worse (the approach speed lag is carried into the tunnel).
  * Yaw error is moderate and depends on where the curves are: sin δ·∬a_lat, 20–45 m at 2°.
  * Roll error is negligible on a flat road.
  * At about 0.1° of pitch residual, the best inertial estimator is no better than the naive
    reference.

**Finding raised for attention (credibility): pitch calibration.** The headline accuracy (20–30 m at
C) requires a pitch residual of about 0.02°. The simulation achieves this only because the road is
flat and the mount and body are rigid. A grade difference of 1% between approach and tunnel equals a
0.57° pitch error, i.e. hundreds of metres. This quantifies the R1 caveat: **implementing road grade
will likely degrade the IMU-based results substantially unless the method changes.** Vehicle body
pitch (acceleration, braking, load) is a further unmodelled source of the same error (R11).

**Task 4: sensor-factor baseline study, done.** Details, figures and data:
[factor_study.md](factor_study.md).
* *Design:* 5 requested conditions (ideal; IMU noise; IMU bias; calibration error; combined) plus
  supplementary ones (accelerometer vs gyroscope, GPS errors). 3 presets × 20 runs. Identical drive,
  seeds and GPS outage in every condition.
* *Anchor:* the "noise + bias + GPS" condition reproduces `results.md` §2.2 exactly.
* *Findings:*
  * With perfect sensors the inertial methods are exact. The naive reference is not (model error up
    to 336 m).
  * IMU noise is harmless (1–5 m) and matches random-walk theory.
  * The calibrated estimators remove the IMU bias completely. That is optimistic: flat road, constant
    bias.
  * **The realistic results are limited by GPS errors (hand-over and calibration from noisy GPS), not
    by the IMU.**
  * Calibration error (0.5° pitch) dominates everything.
  * Negative and unexpected results:
    * calibration turns noise into bias, so the calibrated estimators are worse than raw under noise
      only or GPS errors only;
    * with large lags the exit announcement is effectively missed (18–21 s late, after the exit);
    * combined errors do not simply add.

**Finding raised for attention.** Improving the estimators should start with how approach-phase GPS
is used (calibration from noisy GPS, hand-over state). That, not the IMU model, limits the current
accuracy. Pitch calibration and grade (R1) remain the dominant risk.

**Task 5: road slope (R1, D36), implementation done; experiment not yet.**
* *Model:* an editable elevation profile (points dragged vertically, smooth C2 curve, grade limit
  enforced, templates) and 3-D vehicle kinematics (height, pitch, pitch rate, vertical acceleration).
  The IMU follows automatically.
* *Checks:*
  * flat roads are bit-identical to before (IMU, GPS, truth and all estimator tracks);
  * on an underwater profile, numerical differentiation of the phone pose matches the IMU;
  * the real-browser drag works (point clamped at exactly the 6% limit, re-simulation, no console
    errors).
* *First sanity numbers* (ideal sensors, synthetic route, `dr_calibrated` at C):
  * steady 2% climb along the whole route: ≈ 0 m (the levelling absorbs it);
  * 3% climb only in the tunnel: +1.2 km;
  * underwater V: −0.74 km (the speed error recovers on the climb, the position error does not).
* *Noted for the experiment:* `route_imu` is clamped at the route end D when it runs far ahead, which
  caps its error. Its +0.73 km on the tunnel climb is therefore not comparable with plain dead
  reckoning.
* *Simplifications:* no banking; the driver ignores the grade; presets stay flat (no offline
  elevation data); the profile is defined over map distance (a few metres from the driven distance).

**Task 6: road-slope experiment, done.** Details, figures and data: [slope_study.md](slope_study.md).
* *Design:* 8 profiles (flat; steady 2 % climb; tunnel climb +1/+2/+4 %; descent −2 %; underwater
  V 2/4 %) × 3 presets. Ideal sensors (one run) plus realistic sensors (20 paired runs).
* *Findings:*
  * What matters is the grade *change* after calibration. A steady climb along the whole route costs
    nothing; the same grade only in the tunnel costs 0.4–1.0 km per 1 % at C.
  * The mechanism is gravity leakage, predicted within about 1 %, linear and sign-symmetric. It is
    equivalent to a pitch calibration error of atan(Δgrade).
  * **Heading is unaffected** (≤ 0.06° ideal; unchanged median with realistic sensors), but in plain
    dead reckoning the speed error still becomes lateral error on curves.
  * Negative results:
    * on descents the estimate stops (speed clamped at 0);
    * the underwater V hides a large position error behind a near-zero speed error at C;
    * on climbs `route_imu` overruns to the route end D (capped "error");
    * announcements are 27–58 s early on climbs and 19–26 s late on descents.
  * Only `route_hold` is immune.

**Finding raised for attention (credibility, most important so far).** The inertial headline accuracy
needs the tunnel grade to match the approach grade within about 0.03–0.07 %. **As implemented, the
approach-calibrated IMU speed is not usable in sloped tunnels.** Grade handling (barometer or map
elevation, or treating slow forward-acceleration offsets as unobservable) is a prerequisite for any
inertial along-track claim. Turn information survives and remains useful.

**Task 7: traffic research** ([traffic_research.md](traffic_research.md)), then **task 8: traffic model
and study, done** ([traffic_study.md](traffic_study.md)).
* *Model:* T1, T2, T3, T5 and T6 are built from two shared primitives (speed zones, real stops), anchored
  to B/C and seeded. Motion stays jerk-limited; stops end with a constant-jerk manoeuvre. Free flow is
  bit-identical to before.
* *Study:* 3 presets × 6 scenarios, ideal sensors and 20 paired realistic runs, plus sweeps of the
  portal speed drop and the number of stops.
* *Findings:*
  * The constant-speed baseline fails from a systematic speed change of about 5 km/h. Stops, queues and
    congestion put it 0.7–1.9 km ahead, and it announces the exit 3–4 min early.
  * The IMU follows traffic (0–7 m with ideal sensors, even with stops). With realistic sensors its
    error grows with outage *time* (traffic lengthens outages 2–3.6×), not with stops.
  * Unexpected: the speed clamp v ≥ 0 acts as a *one-sided* zero-velocity update. Negative speed errors
    are wiped at stops; positive ones creep forward while the vehicle stands still, causing a long
    "ahead" tail.
  * At low speed, small position errors become large announcement-timing errors.

**Finding raised for attention.** Traffic lengthens outages, and grade leakage grows with the square of
the outage time. A congested *and* sloped tunnel would cost the IMU methods kilometres (not simulated).
Improvement candidates, none implemented:
* standstill detection (a proper two-sided zero-velocity update);
* bounding time-driven along-track drift;
* grade information.

**Task 9: simulator scope frozen (D38), done.**
* *Added* two optional realism effects, both off by default and controllable in the UI:
  * IMU bias drift (Gauss-Markov per axis);
  * GPS degradation before the portal (correlated error ramp + multipath jumps).

  Everything else not simulated is listed with its expected direction in
  [limitations.md](limitations.md).
* *A bug found by the check:* preset files had no drift size, so enabling drift did nothing. Fixed:
  loaded files get the per-sensor default. Regression test added.
* *Realism check* ([realism_check.md](realism_check.md)): no conclusion changes.
  * GPS degradation moves the IMU estimates by 24–87 m in free flow (the hand-over dominance is
    confirmed).
  * Drift adds p90 tails of 0.3–0.6 km in long stop-and-go outages.

**Task 10: map grade for the estimators (D39), done.**
* *Model:* the map optionally provides the road grade (assumed exact, user decision; map grade errors
  are listed in [limitations.md](limitations.md)). Every IMU estimator removes the gravity leakage of
  the grade change since calibration. UI switch *Map data (estimators)*; only positioning re-runs.
* *Validation (ideal sensors):* sloped tunnels go from 0.9–2.2 km to 0.2–7.6 m at C; flat roads are
  bit-identical. Details: [map_grade_study.md](map_grade_study.md).
* *Study (20 paired seeds, free flow + stop-and-go):* in free flow, sloped tunnels return to the
  flat-road result (median within ±2 m, p90 ≤ +8 m). Stop-and-go on +2 % drops from 11–21 km to
  52–228 m median, but p90 tails grow by up to +0.7 km: a position error at a grade change feeds back
  into the speed (pulls back at grade increases, pushes away at decreases). That also makes the V
  profiles 3–23 m *better* than flat. Open: a 42 m ideal-sensor residual in long outages, only partly
  a gravity-model mismatch.
* *Found during validation:* map heights differentiated over map distance give false grade dips at
  polyline corners (driven path cuts them), which biased the calibration grade. The map now carries
  the grade itself.
* *Backlog (user, 2026-10-15):* UI polish: group the road grade and the other map data for the
  estimators in one place.

**Task 11: refactor, positioning pipeline with an alignment stage (D40), done.** User request: the
estimators must receive finished data, with no calibration-error argument.
* *Structure:* observations → alignment stage (declared / GPS + IMU, swappable) → estimator. The
  calibration error rotates the stage's orientation. The solver moved to `mount_estimation.py`.
* *Validation:* bit-identical tracks on 21 cases. The only differences are millimetres after GPS
  reacquisition with map grade on, from a latent bug the stage fixes: the grade lookup at the first
  fix after an outage searched near the estimator's own drifted position and could be clamped to a
  wrong point. Positioning is ~30 % faster (one alignment per run instead of four).
* *Not changed:* the holder shift (a physical mount change after calibration) stays out, by user
  decision (R11).

**Observation (UI behaviour, pre-existing, not fixed):** NiceGUI runs *async* change handlers as
background tasks, so the "loading" guard that marks values set from code is already reset when they run.
Handlers registered with `on_value_change` / `on_change` (switches, mount-preset select) therefore
also fire after a scenario load. This is harmless in the normal flow: the result is cleared at that
moment, so only the controls are re-read. However, if a loaded file has a preset mount label with
modified angles, the preset handler would probably overwrite the displayed angles. That case is
deduced from the code, not reproduced. A fix would be a synchronous guard or comparing values.
**Backlog: F10** (user decision 2026-10-13: fix during UI polishing).

**Observation (test tooling, not fixed):** driving page handlers in NiceGUI's `user_simulation` logs
`AttributeError: 'AppConfig' object has no attribute 'reconnect_timeout'` from NiceGUI's own outbox
(test harness vs. installed NiceGUI version); the handlers still complete. The map's JS
`initialized()` never fires there, so the default preset does not auto-load. Relevant if UI flow tests
are committed (F9).

## 1. Verified status (checked against code and tests, not just documentation)

*Pre-positioning review (kept as history; statuses below in §2 are current).*

### 1.1 Implemented and validated

**Vehicle simulation**
* Real OSM road geometry via OSRM, or synthetic test roads.
* Road processing (fillets + Whittaker) with diagnostics.
* Driver speed planning: smooth random variation, curve limit, accel/decel passes with margin.
* Jerk-limited longitudinal dynamics with exact integration and exact evaluation at any time.
* Ground truth at 50/100/200 Hz: position, speed, accelerations, jerk, yaw, yaw rate/accel,
  curvature, ENU and body vectors.
* Three presets (Seattle SR 99, Eisenhower, synthetic track) with cached geometry.

**Phone sensor simulation**
* Accelerometer (specific force, WGS84 normal gravity, lever arm, optional Earth rotation/Coriolis)
  and gyroscope, in Android phone axes.
* Phone mounting by Euler angles and lever arm, with presets.
* Separate constant IMU rate (default 200 Hz, 10–2000 Hz), sampled exactly between simulation steps.
* Imperfections: white noise (noise density) + constant bias, four switches, magnitudes in datasheet
  units.
* Ideal stream kept; applied errors recorded; independent seeded streams; optional sensor seed.

**Separation of truth and observations**
* `SimulationResult.imu` (measured) is the observation.
* Truth, `imu_ideal` and `imu_errors` are hidden state.
* `ImuStream` carries no truth fields (tested).

**Reproducibility**
* Scenario JSON holds the fetched geometry, all parameters and seeds.
* Bit-identical replay is tested; schema versioning and migration (v1/v2 → v3).

**UI**
* Map route selection (2 clicks) and presets.
* Smooth client-side playback; truth and IMU plots (measured vs ideal) with a synced cursor.
* Driver, road, mounting and IMU-error controls; save/load.

**Automated tests: 96, no network.** They cover:
* geodesy and road geometry;
* kinematic self-consistency and controlled scenarios;
* driver limits on all presets and styles;
* IMU physics: gravity, mounting, end-to-end numerical differentiation, lever arm, Earth rotation;
* IMU rate (exact in-between samples, not sample-and-hold) and error statistics (σ, whiteness, Allan
  deviation, independence, determinism);
* migration;
* playback logic, figure builders, and page construction (NiceGUI user simulation).

### 1.2 Implemented with known gaps (reconciled with the docs)
* `[~]` **Scenario structure.** A route has two points, and the whole route is treated as GPS-denied
  (D10). This is superseded by A–D (D11) but **not yet implemented**. The 0.5–5 km check (and two tests)
  apply to the whole route, not to B–C.
* `[~]` **Presets** run tunnel portal to portal: they have no approach or recovery section.
* `[~]` **Observation boundary.** `ImuStream` is defined in `sensors/imu.py`, which imports `GroundTruth`. The
  "positioning must not import truth" test promised in design.md §1 cannot work until the types move
  (PD1).
* `[~]` **Truth reference point** = rear axle. There is no phone-position truth (needed for GPS and
  evaluation, PD2).
* `[~]` **Validation evidence.** Some numbers in design.md are one-off measurements, not tests:
  * the smoother comparison table (only the default row is tested);
  * the jitter study figures;
  * the ~0.06 m/s² lever-arm magnitude;
  * the real-tunnel deviation/radius ranges (tests use looser bounds).

  The browser-level checks were ad-hoc Playwright scripts that are **not in the repository**.
* `[~]` **UI scale.** `app/page.py` is ~720 lines, and the browser track player draws one vehicle only.
  *(2026-10-13: player draws N tracks; page split into components, §0.1 task 2.)*

### 1.3 Planned earlier, not implemented
* `[ ]` Data export (CSV/NPZ of observations and truth). Original milestone 3 item.
* `[ ]` Recorded phone-data loader producing `ImuStream` (brief §6, original milestone 3).
* `[ ]` Import-boundary test for positioning (design.md §1). Blocked by PD1.
* `[ ]` Batch / Monte-Carlo command-line runner (readiness review §1.4).
* superseded: tunnel extents from OSM `tunnel=yes` (readiness review §1.1), replaced by D11/D12.
* superseded: finding a real tunnel with an internal exit, replaced by D14 (itself replaced by D32).

## 2. Plan

### Phase P: essential prerequisites for initial positioning
| ID | Task | Depends | Status |
|---|---|---|---|
| P1 | Neutral observation module (`ImuStream` moved, `GnssFix/GnssStream`, `RouteMap`, `NavigationEvent`, `Observations`) + subprocess import-boundary test (PD1) | – | [x] (`NavigationEvent` removed by D32) |
| P2 | A–D scenario model: four points; OSRM multi-waypoint route; B/C distances on the map polyline and on the truth path; navigation event (distance after B, lead); validation (B–C 0.5–5 km, approach long enough, U-turn/detour); schema v4 + legacy migration (PD7); update tests and presets | P1 | [x] (event → one announcement distance before C, schema v5, D32) |
| P3 | A–D map UI: 4 sequential clicks, B–C thick translucent grey under the route, A–D and event markers, event/lead sliders, distinguishable phases (D13) | P2 | [x] (now one "announce before exit C" slider and one marker, D32) |
| P4 | Phone-position truth at arbitrary times (reference point + lever arm, exact via `motion.at`) (PD2) | – | [x] |
| P5 | GPS phone-location simulation, essential subset (D16, PD4): ~1 Hz fixes with correlated error, speed/bearing/accuracy; availability A–B on, B–C off, after C + delay; randomised loss point; ideal kept; seeds; GPS display (fixes on the map, a GPS plot); tests | P1, P2, P4 | [x] essential subset |
| P6 | Observations builder: `SimulationResult` → `Observations` (measured IMU and GPS, `RouteMap` from the **original polyline**). Leakage tests | P1, P2, P5 | [x] |
| P7 | Estimator base class, `StateEstimate`, `EstimateTrack`, causal runner + causality test | P6 | [x] |
| P8 | Evaluation core: truth at estimate times, along/cross/total error vs time and distance, error at C (PD3) + tests | P4, P7 | [x] |
| P9 | Visualisation of estimates: split `page.py` into components; multi-track browser player; per-estimator toggles; error plot tab | P7, P8 | [x] overlays, toggles, errors tab done; page split into components (2026-10-13, §0.1) |
### Phase A: positioning algorithms and comparison experiments
| ID | Task | Depends | Status |
|---|---|---|---|
| A1 | Mount alignment component: levelling from gravity + yaw misalignment (declared or estimated, PD5); observability check | P7 | [x] estimated; *declared* only in `dr_raw` |
| A2 | **B0 baseline**: GPS-reset + 2-D vehicle dead reckoning (positioning_design §4) + validation (zero-error, single-source analytic growth) | A1, P8 | [x] |
| A3 | Error-accumulation study: single error sources vs the analytic budget; summary in docs | A2 | [~] analytic single-source tests + results.md §3; no separate study |
| A4 | Causal preprocessing components (low-pass, decimation); B0 on preprocessed inputs; comparison | A2 | [~] GPS blending (causal complementary filter) done; IMU low-pass not needed so far (white noise negligible) |
| A5 | Approach-phase calibration against GPS: forward bias/levelling, gyro bias (causal) | A2 | [x] levelling with GPS-predicted acceleration; gyro bias by weighted regression |
| A6 | Route-constrained estimator (along-track dead reckoning on the route map) + naive reference "last GPS speed along the route" | A2, P6 | [x] |
| A7 | Yaw-rate vs map-curvature matching (along-track correction in curved tunnels) | A6 | [ ] |
| A8 | Probabilistic estimator (e.g. EKF on the route; particle filter if justified) with covariance. Only after A2–A6 are measured (D22) | A6 | [ ] |
| A9 | Exit announcement: shared Announcer (PD8) + timing-error evaluation (D14 → D32) | P8, A2 | [~] one announcement d before C, fired once from the estimate; timing evaluation; distance threshold only (limitations L-ANN, §0.1) |
| A10 | GPS recovery handling (reacquisition, outlier gating, convergence) + recovery metrics | P5, A2 | [~] recovery = reset to first fix + recovery metric; no gating (needs R4) |
| A11 | Experiment runner: N estimators × Monte-Carlo seeds on identical observations (D19); tables; uncertainty calibration (NEES/coverage) | P8 | [~] Monte Carlo + `evaluation.report`; no covariance yet, so no NEES |
### Phase R: realism and robustness experiments (backlog)
| ID | Task | Status |
|---|---|---|
| R1 | Road grade: elevation profile, pitch in truth and IMU; grade sensitivity of the estimators (D24) | [x] model + editor (D36) and study ([slope_study.md](slope_study.md)); map-grade option in the estimators (D39, [map_grade_study.md](map_grade_study.md)) |
| R2 | Stop-and-go / slow traffic inside the tunnel (D24) | [x] research, model T1/T2/T3/T5/T6 (D37) and study ([traffic_study.md](traffic_study.md)); T4 skipped by decision |
| R3 | Map uncertainty: scale error, lateral offsets, local distortions of the estimator's map (D21, D24) | [ ] |
| R4 | GPS detail: entrance degradation ramp, dropouts, multipath outliers, reacquisition transients, latency (D16) | [~] degradation ramp + multipath jumps before B (D38, optional); others in [limitations.md](limitations.md) |
| R5 | IMU error extensions: bias instability/random walk, temperature drift, scale factor, misalignment, vibration + anti-aliasing, timestamp jitter, separate accel/gyro clocks, device profiles (D07) | [~] bias drift (Gauss-Markov, D38, optional); others in [limitations.md](limitations.md) |
| R6 | Optional external vehicle-speed experiment, separate from the main solution (D20) | [ ] |
| R7 | Estimator tuning mismatch (PD6) | [ ] |
| R8 | Scenario library: curved vs straight, 0.5–5 km tunnels, different mounts and driver styles | [ ] |
| R9 | Re-check road smoothing defaults on new real roads (D03) | [ ] |
| R10 | Calibration error: injected orientation residual + controlled study (D34, calibration_error.md) | [x] model + study; no correction methods (by request); applied in the alignment stage since D40 |
| R11 | Calibration error from physical causes instead of injection: body pitch under acceleration/braking/load, phone shifting in the holder, grade during calibration (with R1); random per-drive residuals | [ ] |

### Phase F: final evaluation and deliverables
| ID | Task | Status |
|---|---|---|
| F1 | Final scenario suite and Monte-Carlo evaluation; result tables and plots | [~] initial results in results.md |
| F2 | Write-up: approach, assumptions, what was simulated and how, results, limitations, next steps with real devices | [ ] |
| F3 | AI-usage note (from the correction log in §5) | [ ] |
| F4 | README: run the simulator, reproduce the results | [~] simulator + positioning usage |
| F5 | Optional screen recording | [ ] |
| F6 | Data export / reproducibility bundle | [ ] |
| F7 | Optional: recorded-phone loader and a small real-data trial | [ ] |
| F8 | Live-demo readiness: fast scenario creation and parameter changes (reviewers will ask live) | [~] |
| F9 | Optional CI (pytest + ruff) and a committed browser smoke test | [ ] |
| F10 | UI polish: async change handlers bypass the loading guard (values set from code also trigger them; a loaded preset mount label with modified angles is probably overwritten). Fix with a synchronous guard or value comparison + a regression test. See §0.1 | [ ] backlog |

## 3. What to do now vs. later

**Next implementation round (in this order):** P1 → P4 → P2 → P3 → P5 → P6 → P7 → P8 → A1 → A2 →
P9 → A3.

Adjustments to the suggested order, and why:
1. **Define the A–D scenario first (P2/P3).** GPS availability, the navigation event and evaluation are
   all defined relative to B and C, so this is the foundation of "GPS simulation and initialisation".
2. **Create the neutral observation types before GPS (P1).** Then `GnssStream` starts life on the right
   side of the boundary, and we don't repeat the `ImuStream` problem. The runner and estimator
   interface stay in step 2 (P7).
3. **Build the evaluation core with the baseline, not after visualisation (P8 before P9).** B0's own
   validation tests (zero-error, analytic error growth) need the error metrics, and the plots consume
   the same aligned errors.
4. **Mount alignment (A1) belongs to the baseline.** Phone-axis measurements cannot be interpreted
   without it.
5. **The navigation event's data model goes into the scenario now (P2)**, so the schema changes once.
   Announcement logic and evaluation stay late (A9).
6. **GPS reacquisition after C (fixes resume after a delay) is cheap and goes into P5.** Detailed
   recovery behaviour and metrics stay in A10/R4.
7. **A trivial "last GPS speed along the route" reference estimator comes with A6.** It is the naive
   benchmark that inertial methods must beat.

**Can safely wait:** everything in phase R, A7–A8, A10 details, F1–F9. Also export (F6) and the recorded-
data loader (F7), unless real phone data becomes available early.

## 4. Open decisions (need input)
1. Accept or adjust PD1–PD8 ([decisions.md](decisions.md)).
2. **PD5:** in the first baseline, is the phone's yaw misalignment *declared* (aligned-mount scenarios
   only) or *estimated* during the approach?
3. GPS defaults: position σ and correlation time; degradation-zone length before B; reacquisition delay
   after C (fixed or random).
4. Estimator output rate and the required state fields (proposal: 20 Hz; position, speed, heading,
   mode; covariance optional).
5. Navigation event defaults: position (e.g. middle of B–C) and announcement lead distances (e.g.
   300 m and 0 m). *Resolved: D26, then D32 (one announcement 300 m before C).*
6. Recovery-time definition (proposal: error < 10 m for ≥ 5 s).
7. Which real roads to use for A–D presets (any road; B–C need not be a real tunnel, D11).
8. Whether to commit a browser smoke-test script (needs a local Edge/Chrome).

## 5. AI-assistance correction log (input for F3)
Places where AI-generated work had to be corrected, found by measurement, tests or review:
* An Ornstein–Uhlenbeck speed process produced jittery, jerk-saturated acceleration. It was replaced by
  a smooth Gaussian process.
* Planning at 100 % of the accel/decel limits overshot the lateral limit by up to 33 % at sharp
  corners. Planning now uses 80 %.
* The Whittaker smoother's right-hand side suffered catastrophic cancellation (spurious curvature on a
  straight road).
* A smoother comparison table in the design notes was written from memory and was wrong. It was
  re-measured.
* Marker jitter was first suspected to be physics. Measurement showed a 16 Hz render cadence; fixed in
  rendering only.
* The true phone mounting leaked into the observation's metadata. Removed, and guarded by a test.
* The schema-v3 migration also hit configs built in code, silently making the presets ideal at 100 Hz.
  A suspiciously passing test exposed it.
* A UI control-ordering crash (axis label built before the sensor controls existed) was found by
  driving the browser. It is now caught by a page-construction test.
* This review: the claim "every accuracy number is enforced by a test" was overstated (§1.2).
* Positioning phase:
  * The A–D map flow crashed on a selection where OSRM turned back at a waypoint (0.01 m radius,
    vehicle stopped). Found by driving the UI; now rejected with guidance.
  * The gyro-bias calibration from approach end points had a heavy tail (up to 0.08 °/s, 470 m
    cross-track). Found in Monte Carlo; replaced by a weighted regression.
  * Several of my test expectations were physically wrong and were corrected by independent checks:
    * ½·b·t² is the along-track error only on a straight road; the exact vector integral is now
      tested.
    * The GPS course over ground differs from the vehicle heading in turns when the phone has a lever
      arm.
    * Cross-track error of route-constrained estimates on curves includes along-track error
      geometry.
  * A first ranking of estimators on a single drive was misleading (the naive method won on Seattle);
    caught by varying the drive.
* Calibration study (2026-10-13): a first draft claimed that the naive estimator "overtakes" the
  inertial ones at 0.05° of pitch. On the fixed preset drives the naive estimator already won
  without any error (it is drive-dependent). Corrected by comparing against its varied-drive results.
* Factor study (2026-10-13): the first figures hid overlapping conditions and showed artefacts at the
  end of the outage (a median over a changing subset of runs). Both were found by looking at the
  rendered figures and fixed. A suspected 2× discrepancy for gyroscope noise was a noisy 20-run
  median; the spread matched theory.
