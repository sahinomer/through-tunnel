# Roadmap and task tracking

Last reviewed: 2026-10-12, before the positioning phase. This file tracks status, remaining work and open
decisions. Decisions live in [decisions.md](decisions.md), and the proposed positioning architecture in
[positioning_design.md](positioning_design.md). The earlier [readiness_review.md](readiness_review.md) is
kept for history; its items are mapped to the tasks below.

Legend:
* `[x]` done and validated
* `[~]` partially done (gap stated)
* `[ ]` to do
* *(decision)* waiting for a decision

## 1. Verified status (checked against code and tests, not just documentation)

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

### 1.3 Planned earlier, not implemented
* `[ ]` Data export (CSV/NPZ of observations and truth). Original milestone 3 item.
* `[ ]` Recorded phone-data loader producing `ImuStream` (brief §6, original milestone 3).
* `[ ]` Import-boundary test for positioning (design.md §1). Blocked by PD1.
* `[ ]` Batch / Monte-Carlo command-line runner (readiness review §1.4).
* superseded: tunnel extents from OSM `tunnel=yes` (readiness review §1.1), replaced by D11/D12.
* superseded: finding a real tunnel with an internal exit, replaced by D14.

## 2. Plan

### Phase P: essential prerequisites for initial positioning
| ID | Task | Depends | Status |
|---|---|---|---|
| P1 | Neutral observation module (`ImuStream` moved, `GnssFix/GnssStream`, `RouteMap`, `NavigationEvent`, `Observations`) + subprocess import-boundary test (PD1) | – | [ ] |
| P2 | A–D scenario model: four points; OSRM multi-waypoint route; B/C distances on the map polyline and on the truth path; navigation event (distance after B, lead); validation (B–C 0.5–5 km, approach long enough, U-turn/detour); schema v4 + legacy migration (PD7); update tests and presets | P1 | [ ] |
| P3 | A–D map UI: 4 sequential clicks, B–C thick translucent grey under the route, A–D and event markers, event/lead sliders, distinguishable phases (D13) | P2 | [ ] |
| P4 | Phone-position truth at arbitrary times (reference point + lever arm, exact via `motion.at`) (PD2) | – | [ ] |
| P5 | GPS phone-location simulation, essential subset (D16, PD4): ~1 Hz fixes with correlated error, speed/bearing/accuracy; availability A–B on, B–C off, after C + delay; randomised loss point; ideal kept; seeds; GPS display (fixes on the map, a GPS plot); tests | P1, P2, P4 | [ ] |
| P6 | Observations builder: `SimulationResult` → `Observations` (measured IMU and GPS, `RouteMap` from the **original polyline**). Leakage tests | P1, P2, P5 | [ ] |
| P7 | Estimator base class, `StateEstimate`, `EstimateTrack`, causal runner + causality test | P6 | [ ] |
| P8 | Evaluation core: truth at estimate times, along/cross/total error vs time and distance, error at C (PD3) + tests | P4, P7 | [ ] |
| P9 | Visualisation of estimates: split `page.py` into components; multi-track browser player; per-estimator toggles; error plot tab | P7, P8 | [ ] |

### Phase A: positioning algorithms and comparison experiments
| ID | Task | Depends | Status |
|---|---|---|---|
| A1 | Mount alignment component: levelling from gravity + yaw misalignment (declared or estimated, PD5); observability check | P7 | [ ] *(decision PD5)* |
| A2 | **B0 baseline**: GPS-reset + 2-D vehicle dead reckoning (positioning_design §4) + validation (zero-error, single-source analytic growth) | A1, P8 | [ ] |
| A3 | Error-accumulation study: single error sources vs the analytic budget; summary in docs | A2 | [ ] |
| A4 | Causal preprocessing components (low-pass, decimation); B0 on preprocessed inputs; comparison | A2 | [ ] |
| A5 | Approach-phase calibration against GPS: forward bias/levelling, gyro bias (causal) | A2 | [ ] |
| A6 | Route-constrained estimator (along-track dead reckoning on the route map) + naive reference "last GPS speed along the route" | A2, P6 | [ ] |
| A7 | Yaw-rate vs map-curvature matching (along-track correction in curved tunnels) | A6 | [ ] |
| A8 | Probabilistic estimator (e.g. EKF on the route; particle filter if justified) with covariance. Only after A2–A6 are measured (D22) | A6 | [ ] |
| A9 | Exit announcement: shared Announcer (PD8) + timing-error evaluation (D14) | P8, A2 | [ ] |
| A10 | GPS recovery handling (reacquisition, outlier gating, convergence) + recovery metrics | P5, A2 | [ ] |
| A11 | Experiment runner: N estimators × Monte-Carlo seeds on identical observations (D19); tables; uncertainty calibration (NEES/coverage) | P8 | [ ] |

### Phase R: realism and robustness experiments (backlog)
| ID | Task | Status |
|---|---|---|
| R1 | Road grade: elevation profile, pitch in truth and IMU; grade sensitivity of the estimators (D24) | [ ] |
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
| F1 | Final scenario suite and Monte-Carlo evaluation; result tables and plots | [ ] |
| F2 | Write-up: approach, assumptions, what was simulated and how, results, limitations, next steps with real devices | [ ] |
| F3 | AI-usage note (from the correction log in §5) | [ ] |
| F4 | README: run the simulator, reproduce the results | [~] (simulator part done) |
| F5 | Optional screen recording | [ ] |
| F6 | Data export / reproducibility bundle | [ ] |
| F7 | Optional: recorded-phone loader and a small real-data trial | [ ] |
| F8 | Live-demo readiness: fast scenario creation and parameter changes (reviewers will ask live) | [~] |
| F9 | Optional CI (pytest + ruff) and a committed browser smoke test | [ ] |

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
   300 m and 0 m).
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
