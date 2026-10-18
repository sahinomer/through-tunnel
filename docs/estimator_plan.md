# Estimator work: problems, candidate solutions, plan (state point 2026-10-15)

State point at the end of the session of 2026-10-15, to resume the estimator phase. **Update
2026-10-16:** the order is agreed; steps 0 (handover diagnostic), 1 (portal freeze, D46), 2 (residual diagnostic), 2.1
(calibration fixes, D48), 3.1 (standstill oracle, D49), 3.2 (oracle sensitivity, D50) and 4 (Kalman filter, first version,
D51) are done,
see "Order" below. **Update 2026-10-17:** order after step 4 agreed with the user: 4.1 (yaw) → 5 (map features) → 3d
(announcements). Step 4.1 is done ([yaw_study.md](yaw_study.md), [route_kalman_yaw.md](route_kalman_yaw.md), D52):
`route_kf_yaw` next to `route_kf`. Step 5 is deprioritised but kept as a viable solution, so step 6 (3d) is next.
**Update 2026-10-17 (evening):** steps 6.1, 6.2, the Eisenhower fix (D54) and step 5 (`route_kf_map`, D55) are
done; **milestone after step 5 rerun** (`0b4ee46`, [benchmark/README.md](benchmark/README.md#milestone-after-step-5-2026-10-17-milestone_step5)):
all scenarios with map grade, `route_kf_map` 8 m median, 3 % gross errors, 89 % good announcements (flattered:
exact map, curved ladder tunnels). **Update 2026-10-18:** UI polish before the write-up (user): 7.1 sensor-error presets done (D56: Error-free · Good · Realistic · Hard, Realistic at startup); 7.2 estimator tooltips on the checkboxes next (short "pipeline" notes, alternatives to choose from); then 8, the write-up (structure first). User's working mode: discuss first, one step at a time, compare every change
against the benchmarks.

## Where we are

* **The simulator is frozen** (D38, final with D41). The optional effects (bias drift, GPS degradation
  before the portal, the car-speed sensor) are in place.
* **The pipeline:** observations → alignment stage → estimator (D40). The car-speed reading reaches only
  the reference estimator (D41/D42).
* **Estimators:**
  * phone-only (`MAIN_ESTIMATORS`): `dr_raw`, `dr_calibrated`, `dr_filtered`, `route_imu`, `route_hold`;
  * reference (`REFERENCE_ESTIMATORS`): `route_vspeed` (route + calibrated car speed), the ceiling.
* **Two baselines**, each with its configuration saved next to it ([benchmark/README.md](benchmark/README.md)):
  * `docs/benchmark/baseline/` (D43/D44): 48 scenarios (tunnel length ladder 0.5–5 km + 3 presets ×
    flat / +3 % climb / underwater × free flow / stop-and-go), realism on, map grade off/on;
  * `docs/benchmark/error_sources/` (D45): one error source at a time on the 5 km flat tunnel, free
    flow and stop-and-go, with the state handed over at GPS loss.
* **Key numbers** (best phone-only estimator):
  * map grade on, all 48 scenarios: 39 m median, 544 m p90, 21 % gross errors (> 200 m);
  * reference: 5 m median, 0 % gross errors;
  * realistic, 5 km flat: 217–231 m (free flow), 470–482 m (stop-and-go);
  * error-free sensors: 0 m (free flow), 12–13 m (stop-and-go).
* **Central finding:** the state handed over at GPS loss decides the error. In free flow the along-track
  error 5 km in is ½ · forward offset · t² + speed error · t (correlation 0.99–1.00 per run; bias drift
  excepted). In stop-and-go the v ≥ 0 clamp breaks this formula ([handover_study.md](handover_study.md)).
* **Step 0 (diagnostic, 2026-10-16, [handover_study.md](handover_study.md)):** the forward offset is
  exactly (δv_last − δv_first)/T. The levelling's Δv_GPS terms telescope, so only the GPS speed errors of
  the first and last approach fix count (T = 82–84 s here). The handover speed is the 5 s blend of the
  last GPS speed errors. P1 and P2 are therefore one mechanism, and the offset term dominates in free
  flow.

## Problems (from both benchmarks)

| # | Problem | Evidence |
|---|---|---|
| P1 | The calibration absorbs the last, degraded GPS fixes before the tunnel | GPS degradation alone: 170–190 m after 5 km (0.5 mg forward offset, 0.12 m/s speed); harsh degradation barely worse, so the last fixes do the damage |
| P2 | Speed and heading handed over at GPS loss are noisy | GPS speed noise alone ≈ 95 m; handover speed error 0.05–0.14 m/s |
| P3 | A pitch residual cannot be observed after the calibration | 0.1° = 1.7 mg ≈ 550 m after 5 km |
| P4 | Accelerometer bias drift grows inside the tunnel | 80 m (free flow), 330–350 m (stop-and-go) |
| P5 | Stops are handled one-sidedly (v ≥ 0 clamp: negative errors wiped, positive ones creep) | 12–13 m floor in stop-and-go with error-free sensors; long "ahead" tails |
| P6 | Yaw residual leaks lateral acceleration into the forward channel on curves | 2° ≈ 57–80 m |

Handled already or out of scope: grade (map grade, D39); constant biases, tilted mount and roll (the
calibration removes them).

## Candidate solutions

### P1: the calibration absorbs degraded fixes

| Solution | How | Expected gain | Effort | Catch |
|---|---|---|---|---|
| **1a. Freeze the calibration before the portal** | The map knows B: stop updating the calibration a set distance before B (e.g. 200 m) and keep the last clean result | the degradation part, if the freeze lies before it; realistic 5 km free flow ≈ 220 → 110 m predicted (step 0) | small | Hard-coded distance; the freeze fix is another noisy endpoint, so the speed-noise part stays |
| 1e. Fit the offset over all fixes | Least-squares slope of (GPS speed − integrated forward IMU) over the approach instead of the endpoint difference; handover speed from the fitted line | speed-noise offset term about ÷4 (theory, √(6/N)) | medium | A small version of the filter's offset state (3d); combinable with 1a |
| **1b. Consistency gating** | Reject GPS intervals whose speed change disagrees with the acceleration the IMU measured | most of it, adaptive | medium | Threshold; noisy at low speed |
| 1c. Weight by reported accuracy | Down-weight fixes with poor reported accuracy | some in reality; in the simulation for speed | small | Correction 2026-10-16: the simulated degradation *is* in the reported speed accuracy (only the position jumps are not, D38), so 1c works here, flatteringly (the reported accuracy equals the injected noise). Best inside a fit over all fixes (1e) or the filter: weighting intervals of the endpoint form barely helps |
| 1d. Long-term robust calibration | Robust (median) fit over the whole drive | partial | medium | Slower if the phone moves |

### P2: noisy handover state

| Solution | How | Expected gain | Effort | Catch |
|---|---|---|---|---|
| **2a. Hand over from the last trusted state** | With 1a: carry the state from the last clean fix forward with the IMU instead of taking the degraded last GPS speed | large share of the degradation part | small | Same distance choice as 1a |
| 2b. Better speed fusion | Kalman fusion of GPS speed and IMU instead of the fixed 5 s blend | ~30–50 % of the speed-noise part | medium | Belongs in the filter |
| 2c. Heading from the map at B | Dead-reckoning estimators snap heading to the route direction at the entrance | cross-track part | small | Route estimators already do this |

### P3: pitch residual unobservable

| Solution | How | Expected gain | Effort | Catch |
|---|---|---|---|---|
| **3a. Zero-velocity updates at stops** | At a standstill the forward channel reads exactly the offset: measure and remove it | large, **only when the car stops** | medium | Needs standstill detection (P5) |
| **3b. Map features as position fixes** | Curves (turn rate vs. map curvature, A7) and grade changes give along-track fixes inside the tunnel | bounds the error in curved / sloped tunnels | medium–large | Useless in a straight flat tunnel |
| 3c. Separate bias from pitch with map grade | Known grade changes on the approach make tilt and bias distinguishable | partial, sloped approaches only | medium | Depends on the profile |
| 3d. Offset as a filter state | Honest uncertainty; lets 3a/3b correct it | enabler | part of the filter | — |

### P4: bias drift in the tunnel

| Solution | How | Expected gain | Effort | Catch |
|---|---|---|---|---|
| **4a. Zero-velocity updates** (= 3a) | Re-measure the offset at every stop | most of the stop-and-go part | with 3a | No help in free flow |
| 4b. Map-feature fixes (= 3b) | Position fixes from curves and grade changes | bounds it | with 3b | Geometry-dependent |
| 4c. Drift in the filter model | Uncertainty grows honestly | enabler for 4a/4b and the announcement | filter | — |

### P5: one-sided stops

| Solution | How | Expected gain | Effort | Catch |
|---|---|---|---|---|
| **5a. Standstill detection** | IMU goes quiet → speed exactly 0 (both directions); triggers 3a/4a | removes the creep; enables 3a/4a | small–medium | **The simulation has no vibration**: detection is unrealistically easy here (engine idle vibration in reality). The result is optimistic; add to limitations.md |

### P6: yaw residual on curves

| Solution | How | Expected gain | Effort | Catch |
|---|---|---|---|---|
| 6a. Predict the leak from the map | Lateral acceleration = v²·curvature is known from the map: subtract its leak into the forward channel | most of the 57–80 m on curves | small | Route estimators only; needs the yaw error itself (the leak is ψ·v²κ), so it comes with 6b |
| 6b. Estimate yaw online | Two routes (corrected 2026-10-17, [yaw_study.md](yaw_study.md)): (1) the forward channel against GPS speed separates ψ·f_lat from b on approach curves; (2) the lateral channel against v²·curvature reads −ψ·f_x whenever the car accelerates or brakes, also on straights inside the tunnel | same, adaptive | medium | (1) needs approach curves; (2) needs a lateral bias state, road bank unmodelled |

### Beyond the sensor errors (first benchmark)

* **Grade without map data:** solved by map grade (D39); a barometer would be the phone-only
  alternative (not simulated).
* **The announcement:** uncertainty-aware timing becomes possible once a filter gives a covariance
  (3d/4c). 85–89 % of the bad announcements come from gross position errors, so better positions fix
  most of them.
* **Using the tunnel length (discussed 2026-10-16, for 3d).** The map knows B and C.
  * *Predicting the uncertainty before B (most valuable):* tunnel length and current speed give the
    outage time; with the filter's model, the uncertainty at the announcement point can be predicted
    before entering. A long tunnel in slow traffic then gets an earlier, hedged instruction instead of a
    precise but possibly wrong one. Needs a consistency check of `position_std_m` first.
  * *Hold at C while GPS is absent:* no fix yet means the car is very likely still inside, so the estimate
    could be held at C (plus a reacquisition margin) instead of running toward D. Prevents the capped
    runs, but flatters "error at C" for free; judge it by announcement timing and the maximum error
    inside the tunnel. Does not fix an early announcement.
  * The length says nothing about the position *inside* the tunnel; that is step 5.

## Order (agreed with the user on 2026-10-16)

**Naming:** steps are numbered 0, 1, 2, 2.1, 3, 3.1 …; letters (1a, 2b, 3a, 3c …) are only the solution
IDs of the tables above. Commit messages, decisions D48–D50 and run labels written before 2026-10-16
evening used letters for steps: "step 2b" = 2.1, "step 3a" = 3.1, "step 3b" = 3.2.

0. **Done (2026-10-16): handover diagnostic** ([handover_study.md](handover_study.md)). Agreed order
   with the user: 0 → 1 → 42 m residual → standstill → filter → map features.
1. **Done (2026-10-16): portal freeze (1a + 2a, D46, [portal_freeze.md](portal_freeze.md)).** Realistic
   5 km free flow 231 → 103 m (predicted ~110), gross errors 11 → 4 of 20; degradation inside the
   200 m zone removed. Remaining in free flow: the endpoint noise of ordinary GPS speed (1e or the
   filter). Flagged: underwater stop-and-go 490 → 767 m median (gross 14 → 13); more runs end ahead,
   likely the one-sided clamp (step 3).
2. **Diagnosed (2026-10-16): the 42 m residual and the 12–13 m stop-and-go floor**
   ([residual_study.md](residual_study.md)). Both are explained, with at most 0.002 mg left over:
   * the stop-and-go floor is a half-sample timing lag of the calibration's interval means while
     braking (T2a);
   * the 42 m is a yaw error from the grade ramp in the calibration window, leaking lateral
     acceleration into the levelling (T2b, +46 m), plus the gravity constant (T1, −11 m);
   * T1 alone is the synthetic −2 % residual (23–29 m).
   The freeze removes T2a and T2b here only because both happen within 200 m of B.
   **2.1. Done (2026-10-16): calibration fixes F1–F3 (D48, [calibration_fixes.md](calibration_fixes.md)).**
   Normal gravity at the route's latitude, exact interval timing, map grade in the yaw fit.
   * Ideal sensors: every case within 7 m at C (42 → 1.4 m), with or without the freeze.
   * Realistic flat roads unchanged.
   * Sloped roads: climb free flow 109 → 93 m, underwater stop-and-go 767 → 613 m.
   * Flagged: climb stop-and-go 297 → 501 m. The old gravity error had masked the clamp's forward
     creep, which makes step 3 more urgent.
3. **Standstill, as an oracle (user decision, D49).** No vibration model; standstill is given from the
   true motion, labelled ‡ oracle, and kept out of the phone-only set. Vibration and engine audio are
   future research (roadmap R12).
   * **3.1. Done (2026-10-16): perfect oracle ([standstill_oracle.md](standstill_oracle.md)).**
     Realistic 5 km stop-and-go: 385 → 131 m with the two-sided speed reset alone, and → 103 m with the
     offset also measured at each stop. Gross errors 16 → 9 → 2. The clamp creep behind the two
     regression flags of steps 1 and 2b is gone.
   * Remaining: runaway runs in the underwater V stop-and-go, independent of the oracle (likely
     map-grade feedback).
   * **3.2. Done (2026-10-16): sensitivity (D50).**
     * Missed stops are harmless (30 % missed: 126 m).
     * Timing is critical with the naive use: a release 0.5 s late makes the offset variant worse than
       no oracle, and 1 s removes the speed reset's gain. A 3 km/h threshold acts like a 1 s release
       delay.
   * **3.3. Parked (user, 2026-10-16): "trim and replay" for the oracle variants.** Not built: it would refine
     an assumption, not a phone model; the filter (step 4) is more valuable. The idea carries into the filter as
     a standstill measurement with a validity window. (The idea: exclude the stop's margins from the
     offset and re-integrate the last M seconds at release, to tolerate delays up to M.)
4. **Route-constrained Kalman filter** (state: distance, speed, forward offset). **First version done
   (2026-10-16, D51, [route_kalman.md](route_kalman.md)):** pitch 0.1° 628 → 3 m, realistic stop-and-go
   385 → 188 m, realistic free 103 → 85 m (tails mixed). Next limit: the yaw residual (6b).
   **Milestone rerun done (2026-10-16, `00ab89b`, [benchmark/README.md](benchmark/README.md#milestone-after-step-4-2026-10-16-milestone_step4)):**
   all scenarios with map grade: Route + IMU 39 → 31 m median, filter 30 m; gross errors 21 % → 15 %. Flagged:
   calibration yaw 2° in stop-and-go, filter 204 m vs. Route + IMU 96 m (yaw leak). The home for 2b, 3d,
   4c and the 3a/3b updates; honest uncertainty for the announcement.
   **4.1. Yaw in the filter (6b).** *Diagnostic done (2026-10-17, [yaw_study.md](yaw_study.md)), with a
   counterfactual that removes the true yaw leak:*
   * Confirmed: with a 2° calibration yaw error, b absorbs the approach curves' leak (0.37 mg). Without
     the leak, stop-and-go 204 → 11 m and free flow 65 → 1 m; `hard` roughly halves. All 20 runs improve.
   * Refuted: the natural yaw residual (0.3° median) does not cause the realistic results or the free-flow
     tails at 2–3 km. Removing it is neutral (it partly compensates the GPS noise it was fitted to).
     Realistic free flow is limited by learning b from the approach (true offset 0.43 mg rms, filter
     error 0.35 mg); that is for step 5.
   * *Filter done (2026-10-17, D52, [route_kalman_yaw.md](route_kalman_yaw.md)):* a separate estimator
     `route_kf_yaw` (user decision: keep both filters, compare them in the UI). ψ as a 4th state, learned on
     the approach curves, carried into the tunnel; the stage reports the calibration's yaw jumps
     (`yaw_shift`, 0.45–0.68° rms per re-solve). Against `route_kf`: calibration yaw 2° 65 → 0 m (free),
     204 → 2 m (stop-and-go); `hard` 782 → 403 m (stop-and-go); realistic free neutral; realistic
     stop-and-go leans worse (fresh seeds 355 → 503 m, p = 0.14; a reshuffle under the clamp, P5).
     `route_kf` stays the headline phone-only filter, `route_kf_yaw` the robustness variant. The
     lateral-channel measurement is not built.
5. **Map-feature fixes (3b). Done (2026-10-17, D55, [route_kalman_map.md](route_kalman_map.md)): `route_kf_map`.**
   Revisited after step 6 (user). Heading of the gyro vs. the smoothed map heading every 25 m driven; position
   only where the radius is below 2 km. Realistic 5 km: 80 → 12 m (free), 241 → 30 m (stop-and-go, gross
   13 → 1); announcements in curved tunnels become precise. Eisenhower (nearly straight): medians halve, gross
   errors unchanged. `route_kf_yaw_map` tied and was not registered. Flatters itself in this benchmark (exact
   map, S-arcs in every ladder tunnel, no lane changes). *Earlier (kept for the record):* deprioritised, kept
   as a viable solution (user decision, 2026-10-17); the announcement (step 6) came first. Reasons:
   * the gain depends entirely on the tunnel's geometry: none in a straight tunnel. From general knowledge,
     long mountain tunnels (Mont Blanc, Fréjus, Gotthard road tunnel) are essentially straight, while urban
     tunnels (Seattle SR99, Boston's Central Artery) curve;
   * the method trusts the map's curve geometry metre for metre, and how accurately maps draw curves
     *inside* tunnels is unknown here (map errors are not modelled, R3);
   * our benchmark would flatter it: every ladder tunnel has two S-arcs by construction, the map is exact,
     and the simulated car never changes lanes;
   * simplicity: a 6-state filter whose gain depends on geometry and an unverified map is hard to defend
     without real data.

   Revisit when there is real drive data, evidence on map quality in tunnels, or a product focus on urban
   tunnels. Those curve, and stop-and-go, the worst remaining failure, is mostly urban: there this method
   would help most. Lane changes are not the main risk (a few degrees for a few seconds, net zero, gateable).
   *Design kept (proposed 2026-10-17, not built):*
   * a new estimator `route_kf_map` on top of `route_kf`, with two more states: the heading error of the
     integrated gyro and the gyro-bias residual (realistic: 1.7 mdps after the calibration, plus drift);
   * heading measurement in the tunnel every ~10 m driven: integrated gyro heading minus a smoothed map
     heading at d̂ (`heading_at` is piecewise constant per polyline segment). On straights it calibrates the
     heading drift; on curves it corrects d, and through the filter's correlations v and b;
   * precision ≈ heading error / curvature: ~2 m on an 800 m arc;
   * grade changes (pitch gyro vs. the map's grade profile) as a later sub-step: gentler signal, and the
     pitch gyro bias is not calibrated;
   * checks: a nearly straight dev control (Eisenhower, 18.5° of turning over 2.7 km) and a straight-route
     test where it must equal `route_kf`.

   6a (predict the yaw leak from the map) is dropped from this step: `route_kf_yaw` (D52) covers the need.
6. **Uncertainty-aware announcement (3d).** Applies to every tunnel and targets the product output. User
   decisions (2026-10-17): a late announcement is worse than an early one; only the Kalman filters report σ,
   so the policy applies to them; σ shown in the UI.
   * **6.1. Done (2026-10-17): consistency check ([uncertainty_study.md](uncertainty_study.md)).** UI: ±2σ band
     on the along-track error plot, σ at C and at the announcement in the summary table. Free flow: σ honest
     on 5 km (70 % / 95 % within ±1σ / ±2σ), mildly overconfident on 2 km (65 % / 85 %). Stop-and-go: σ 5–10×
     too large (1.7 km vs. 170–290 m real), from the unbounded offset random walk (t^2.5) and the unmodelled
     clamp. Options for 6.2: a bounded offset drift in the filter, or use σ only to choose precise vs.
     hedged and cap the hedged lead.
   * **6.2. Done (2026-10-17, D53, [announcement_policy.md](announcement_policy.md)): a simple policy** (user: simple
     over refined). Fires at d̂ + min(2σ, 300 m) ≥ target; precise if σ ≤ 30 m, else hedged; only for the
     Kalman filters; the plain announcement kept next to it. Late announcements nearly gone (free flow late
     > 3 s: up to 50 % → 0 %, Eisenhower 30 → 20 %; stop-and-go late > 15 s: up to 25 % → ≤ 5 %); precise up
     to 2 km in free flow; price: earliness, 1–1.5 min in stop-and-go. Not done: the tunnel-length
     prediction (6.3), a time-based cap, the bounded offset drift; "hold at C" stays a separate item.
   * **Flag from 6.2: the Eisenhower approach.** `route_kf_yaw` learns ψ −7° to −14° there (truth ~0°) and
     fails (250 m median, 12/20 gross, free flow); `route_kf`'s offset is 0.7–3 mg off (ladder ~0.3 mg).
     Grade and sideslip ruled out. Proposed next: a diagnostic of that approach (both filters).
   * **Diagnosed (2026-10-17, [calibration_start_study.md](calibration_start_study.md)):** the filters start
     learning when the calibration is first solved, with priors for a *converged* calibration (1 mg, 3°).
     Eisenhower's approach is short and weakly excited: the calibration is ready only 42 s before loss and its
     first solutions are off by up to 37 mg / 26°. Wide priors (10 mg / 10°, counterfactual): Eisenhower
     `route_kf` 75 → 43 m (free), 276 → 133 m (stop-and-go); `route_kf_yaw` 250 → 86 m; elsewhere b unchanged,
     stop-and-go medians reshuffled (clamp). Fix options to agree: wider priors (simplest), start after the
     calibration settles, or a calibration covariance. Proposed: Eisenhower in the dev scenarios.
   * **Fixed (2026-10-17, D54): wider priors (10 mg, 10°) in both filters; Eisenhower in the dev scenarios.**
     `route_kf_yaw` better or neutral everywhere (Eisenhower 250 → 86 m, hard 204 → 157 m). `route_kf`:
     Eisenhower 75 → 43 m (gross 2 → 0), but slightly worse in free flow on longer approaches (2–3 km:
     +2–4 m, p 0.01–0.02) and clearly worse with a 2° yaw error (hard 255 → 361 m): the narrow prior had
     shielded b from the yaw leak. Kept; refinement noted (b uncertainty growing with re-solve size).

Each step is checked against both baselines with `--compare` before the next, on the development
subsets (`--dev`, D47); the full benchmarks are rerun at milestones.

## Open items carried over

* **Calibration duration: longer is better (user, 2026-10-17).** The calibration start diagnostic showed the
  shortest approach (Eisenhower, calibration ready 42 s before GPS loss) gives the worst offset; the longer
  ones (63–86 s) are fine. Design consequences: calibrate continuously over the whole drive, not only the
  approach (solution 1d), and treat a just-solved calibration as uncertain (D54). For the write-up: our
  drives start only ~1–2 min before the tunnel, so the approach calibration is pessimistic compared with
  real drives (limitations.md), as long as the phone stays put in its holder.

* The unexplained 42 m residual with ideal sensors in long outages ([map_grade_study.md](map_grade_study.md),
  open items): now step 2, together with the 12–13 m stop-and-go floor.
* Thresholds kept as they are (user, 2026-10-16): gross error 200 m, announcement off 15 s,
  announcement good ±3 s, regression 10 % and 5 m. With 20 runs a p90 is about the 2nd-worst run, so
  p90 regression flags are hints, not verdicts.
* Optional: rerun the baseline with a longer route after C, so capped errors (§) become real values.
* Optional: save each benchmark job when it finishes, so a run interrupted by low memory (as happened
  once) loses at most the jobs in progress.
* The benchmarks are optimistic in three ways ([benchmark/baseline/config.md](benchmark/baseline/config.md)):
  an aligned mount, no injected calibration error, an exact map. The error-source benchmark's *hard*
  condition quantifies the first two.

## How to resume

1. Read this file and [benchmark/README.md](benchmark/README.md) (section "Milestone after step 4").
2. **Comparisons are iterative (user, 2026-10-16):** each step is compared with the *previous* reference,
   not with the first baseline. The current reference is `docs/benchmark/milestone_step5/` (benchmark, error
   sources and σ consistency, commit `0b4ee46`, 2026-10-17); before it `milestone_step4/` (`00ab89b`). Raw per-run results (`runs.csv` + `meta.json` + configuration) are
   kept for every saved run, so any other comparison can be produced later with `--compare` / `--from-csv`.
3. For each agreed step, discuss first, then:
   * implement;
   * run `uv run python -m throughtunnel.evaluation.benchmark --dev --out out/dev/<step> --compare
     docs/benchmark/milestone_step5/benchmark`;
   * run `uv run python -m throughtunnel.evaluation.error_sources --dev --out out/dev/<step>_es --compare
     docs/benchmark/milestone_step5/error_sources` (D47);
   * write up, commit, and stop for review.
