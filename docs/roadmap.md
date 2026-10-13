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
| R1 | Road grade: elevation profile, pitch in truth and IMU; grade sensitivity of the estimators (D24) | [ ] **raised: most important caveat of the current results (results.md §3.1)** |
| R2 | Stop-and-go / slow traffic inside the tunnel (D24) | [ ] |
| R3 | Map uncertainty: scale error, lateral offsets, local distortions of the estimator's map (D21, D24) | [ ] |
| R4 | GPS detail: entrance degradation ramp, dropouts, multipath outliers, reacquisition transients, latency (D16) | [ ] |
| R5 | IMU error extensions: bias instability/random walk, temperature drift, scale factor, misalignment, vibration + anti-aliasing, timestamp jitter, separate accel/gyro clocks, device profiles (D07) | [ ] |
| R6 | Optional external vehicle-speed experiment, separate from the main solution (D20) | [ ] |
| R7 | Estimator tuning mismatch (PD6) | [ ] |
| R8 | Scenario library: curved vs straight, 0.5–5 km tunnels, different mounts and driver styles | [ ] |
| R9 | Re-check road smoothing defaults on new real roads (D03) | [ ] |

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
