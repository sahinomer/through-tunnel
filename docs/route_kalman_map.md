# Curves inside the tunnel as position fixes: `route_kf_map` (step 5)

Step 5 of [estimator_plan.md](estimator_plan.md), decision D55 (2026-10-17). Revisited after being deprioritised
(user: "it might be good spot to revisit it"), because the remaining large failures (long stop-and-go
tunnels) come from the estimator having no information inside the tunnel. A new phone-only estimator
`route_kf_map`: `route_kf` plus map-feature fixes. **The benchmark flatters this method** (below, "Limits"):
read the gains as what map curves are worth *in curved tunnels with an accurate map*.

Data: [route_kalman_map/](route_kalman_map/): both dev subsets and all flat-road scenarios (tunnel lengths
0.5–5 km and the three presets), 20 paired seeds. Modules: `positioning/map_heading.py`,
`positioning/route_kalman.py` (`map_fixes`).

## The idea

Inside the tunnel the gyro measures how far the car has turned since GPS loss; the map knows how the
route's direction changes along it. Where the road curves, matching the two gives the position along the
curve: precision ≈ heading error / curvature (on an 800 m arc, 0.15° of gyro drift ≈ 2 m).

## The filter

* **Two more states** on top of `route_kf`'s [d, v, b]: the heading error h of the gyro heading integrated
  since GPS loss, and the residual β of the calibration's vertical gyro bias (h' = β).
* **Heading measurement** every 25 m *driven*: z = ψ_gyro − ψ_map(d̂) = h + κ(d̂)·(d − d̂). On straights it
  calibrates h and β; on curves it corrects d, and through the filter's correlations v and b. So the offset b
  becomes observable inside the tunnel for the first time.
* **Smoothed map heading** (`map_heading.py`): heading at the polyline's segment midpoints, interpolated and
  averaged over 60 m. `RouteMap.heading_at` steps ~1° per 15 m vertex on an 800 m arc.
* **Measurement noise from evidence.** The smoothed map heading matches the driven heading to 0.1–0.4° rms
  inside the benchmark tunnels (worst 1.3°), with errors correlated over 20–330 m (exact map). σ = 1° per 25 m
  adds up to ~0.3° per correlation length instead of overcounting correlated errors.
* **Position only where the road curves** (radius below 2 km). On straighter road a 0.5° systematic map
  heading error would mean hundreds of metres; there the measurement only calibrates h and β.
* Gate 4σ, at most 3 rejections in a row (lane changes, a wrong curve). Nominal values (PD6): heading at GPS
  loss σ 0.5°, gyro-bias residual σ 5 mdps, its random walk 0.3 mdps/√s, gyro angle random walk 10 mdps/√Hz.
* One implementation (`map_fixes` switch, like `yaw_state`); `route_kf` and `route_kf_yaw` are bit-identical
  to before (verified).

### Two problems found in validation (both fixed before the evaluation)

1. **A run-away trigger.** The first version measured every 25 m of *estimated* travel. An update moves the
   estimate, so the next update was due at once: in one Eisenhower stop-and-go run the same heading information
   was applied more than ten times within two seconds, the estimate ran 258 m ahead and then 771 m behind. The
   trigger now counts distance driven (integrated speed). Test: one measurement per 25 m driven.
2. **A steady drift on the nearly straight tunnel.** On Eisenhower (radius ~45 km in places) the map heading
   has small systematic errors (±0.5°, correlated over ~165 m). With such a weak curvature every update nudged
   d the same way, ~10 m at a time, 300 m in total. Fixed by the 2 km radius threshold. Test: on a perfectly
   straight tunnel `route_kf_map` equals `route_kf` exactly until C.

## Results

Median error at C (benchmark) or 5 km in (error sources) ✗ gross errors (> 200 m), 20 paired runs:

| case | `route_kf` | **`route_kf_map`** | `route_kf_yaw` | `route_kf_yaw_map` |
|---|---|---|---|---|
| realistic 5 km, free | 80 ✗4 | **12** | 84 ✗4 | 7 |
| realistic 5 km, stop-and-go | 241 ✗13 | **30 ✗1** | 299 ✗12 | 31 ✗1 |
| 5 km climb, stop-and-go | 319 ✗13 | **36 ✗1** | 373 ✗14 | 37 |
| 5 km underwater, stop-and-go | 322 ✗15 | **78 ✗5** | 493 ✗15 | 81 ✗5 |
| 2 km, stop-and-go | 65 ✗3 | **9** | 58 ✗4 | 9 |
| Seattle SR99, stop-and-go | 132 ✗8 | **21** | 127 ✗8 | 20 |
| Eisenhower, free | 43 | **22** | 86 ✗5 | 41 ✗3 |
| Eisenhower, stop-and-go | 133 ✗7 | **20 ✗8** | 211 ✗11 | 86 ✗8 |
| GPS speed noise, stop-and-go | 172 ✗9 | **6** | 175 ✗9 | 6 |
| calibration yaw 2°, stop-and-go | 203 ✗10 | 20 | 2 | 8 |
| hard, free / stop-and-go | 361 ✗17 / 782 ✗20 | 45 / 42 ✗11 | 157 ✗7 / 399 ✗16 | 10 / 32 ✗1 |
| error-free sensors, free / stop-and-go | 1 / 3 | 2 / 8 | 0 / 3 | 2 / 8 |

The uncertainty-aware announcement ([announcement_policy.md](announcement_policy.md)) changes with it, because
σ now shrinks at every curve (flat roads, `route_kf` → `route_kf_map`):

| case | precise | good (±3 s) | median timing |
|---|---|---|---|
| 5 km, free | 0 → 100 % | 10 → 100 % | −13.1 → −1.6 s |
| 3 km, free | 0 → 100 % | 35 → 100 % | −3.8 → −0.9 s |
| Seattle, free | 0 → 100 % | 45 → 100 % | −3.4 → −1.2 s |
| 2 km, stop-and-go | 0 → 95 % | 0 → 10 % | −88 → −4.8 s |
| Seattle, stop-and-go | 0 → 95 % | 0 → 10 % | −71 → −6.3 s |
| Eisenhower, both | unchanged | unchanged | unchanged |

Late announcements stay at 0–5 %.

## Findings

1. **In curved tunnels the error becomes bounded.** Realistic 5 km: 80 → 12 m in free flow, 241 → 30 m in
   stop-and-go, gross errors 13 → 1. Stop-and-go was the largest remaining failure; with curves it is solved
   without any standstill information.
2. **The announcement becomes precise** in curved tunnels, and stop-and-go announcements come seconds early
   instead of a minute and a half.
3. **On the nearly straight Eisenhower it helps less, and not with the gross errors**: medians 43 → 22 m and
   133 → 20 m, but stop-and-go gross errors 7 → 8. A few curves near its ends give some fixes; the long straight
   middle gives none (by design, finding 2 of the validation).
4. **Small costs where nothing was wrong:** with error-free sensors or a fully learned calibration error, 1–3 m
   becomes 2–8 m (the map heading errors).
5. **The two map variants tie under realistic conditions.** `route_kf_yaw_map` is better only with an injected
   calibration yaw error (hard stop-and-go ✗1 vs. ✗11; calibration yaw 2° 8 vs. 20 m) and worse on Eisenhower's
   short approach (41 ✗3 vs. 22 m, 86 vs. 20 m), the yaw state's known weakness. **Registered: `route_kf_map`**
   (realistic conditions and simplicity, as agreed); `RouteKalmanYawMap` stays in the code, unregistered.

## Limits (why the benchmark flatters this method)

* **The map is exact.** The simulated road is generated from the same polyline the estimator gets; the only
  heading mismatch is the smoothing (0.1–0.4°). A real map can draw a tunnel's curve metres off, and the fix
  inherits that error (R3, not modelled).
* **Every ladder tunnel has two S-arcs by construction**, so the method always has curves to work with. Real
  long mountain tunnels are often essentially straight, where it gives nothing (Eisenhower shows the effect).
* **No lane changes** in the simulation. A lane change turns the car by a few degrees for a few seconds and
  back; the gate should absorb it, but this is not tested.
* The nominal values (measurement σ, 2 km radius threshold, 25 m step) are reasoned from the map check, not
  optimised; the map check itself was made on the benchmark's own (exact) maps.
* σ consistency (step 6.1) was not rechecked for `route_kf_map`; the announcement results suggest it is not
  overconfident (late ≤ 5 %), and it is due at the milestone rerun.
