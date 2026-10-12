# Design notes: vehicle simulation (milestone 1)

This document records the technical decisions, models, conventions, assumptions and known limitations
of the simulator. It is meant to be read alongside the code. Every claim about accuracy below is
enforced by a test in `tests/`.

## 1. Architecture

```
            ┌────────────── core (pure Python / numpy, no UI imports) ──────────────┐
RouteProvider ──► RawRoute ──► RoadPath ──► SpeedProfile ──► Longitudinal ──► GroundTruth
 (OSRM, synthetic)  (lat/lon     (smooth      (spatial plan,    (time domain,     (all kinematic
                    polyline)    arc-length    seeded RNG)       jerk-limited)     quantities)
                                 spline)
            └── ScenarioConfig (route + parameters + seed) ──► run_scenario() ──► SimulationResult ┘
                                                                     │
                                                    app/ (NiceGUI) ◄─┘  rendering only
```

* **One pure entry point:** `run_scenario(ScenarioConfig) -> SimulationResult`. There is no hidden or
  global state, so identical config gives identical arrays (tested bit-for-bit).
* **The UI is a client of the core.** `app/` imports the core; nothing in the core imports `app/`.
  The playback clock (`app/playback.py`) and the figure builders (`app/plots.py`) are plain Python
  and unit-tested.
* **Ground truth is separate from observations.** `GroundTruth` is the simulator's hidden state. Milestone 2
  adds a `sensors/` package that reads `GroundTruth` and emits an observation stream (`ImuStream`:
  timestamps, accel[N,3], gyro[N,3], frame metadata). A recorded-phone loader will produce the same
  type, so positioning code written against `ImuStream` works on both. Positioning code will never
  import `GroundTruth`, and a test will enforce that import boundary once the package exists.

## 2. Technology decisions

| Decision | Choice | Alternatives considered and why not |
|---|---|---|
| UI | **NiceGUI 3** (FastAPI and Vue under the hood) with its built-in Leaflet map and Plotly | **Dash + dash-leaflet**: dash-leaflet's last release targets Dash 3, while Dash is now 4.x, so there is a compatibility risk on Python 3.14 and a heavy dependency tree. **Streamlit**: its rerun-the-script model is a poor fit for smooth 20 Hz playback. **Custom FastAPI + JS**: more code in two languages; NiceGUI already runs on FastAPI if REST endpoints are needed later. |
| Playback | Server-driven `ui.timer` (20 Hz) with incremental Leaflet and Plotly updates (`setLatLng`, `addLatLng`, `Plotly.relayout` on the cursor shape only) | Re-sending figures each frame is too heavy. Client-side JS playback would be smoother but duplicates interpolation logic in JS. |
| Routing | **OSRM HTTP API** (public demo server, configurable URL) | **OSMnx + networkx** would give OSM tags and offline graphs, but pulls in geopandas/shapely/pyproj and depends on Overpass, which was overloaded (HTTP 504) during development. The fetched geometry is stored in scenario files, so scenarios never need the network again. |
| Geodesy | Own WGS84 geodetic↔ECEF↔ENU (~60 lines, exact, tested) | pyproj or pymap3d: unnecessary dependencies for one well-known transform. |
| Numerics | numpy, scipy (sparse solve, B-splines, FFT convolution) | |
| Config / persistence | pydantic v2 models → JSON | Validation of ranges and lossless JSON round-trip for free. |

## 3. Coordinate frames and conventions

| Item | Convention |
|---|---|
| Navigation frame | Local **ENU** tangent plane anchored at the first route vertex (x East, y North, z Up). |
| Body frame | **ISO 8855** vehicle axes: x forward, y left, z up. |
| Yaw ψ | Angle from East to body-x, counter-clockwise positive, **unwrapped** (continuous). |
| Bearing | Compass heading = (90° − ψ) mod 360, clockwise from North (display only). |
| Signs | Curvature κ, yaw rate and lateral acceleration are **positive for a left turn**. |
| Units | SI everywhere internally (m, s, rad). km/h and degrees only in UI labels and config fields named `*_kmh`. |

The flat-earth (tangent-plane) approximation is accurate to well under a metre over the ≤ 10 km extent
of a scenario. The tangent plane drops below the Earth's surface by about 2 m at 5 km, which the
flat-road model ignores anyway.

## 4. Road geometry: from map polyline to a drivable path

**Problem.** An OSM way is made of straight chords between nodes. Following it literally makes the
heading jump at every node (an infinite yaw rate and lateral acceleration spike) with zero curvature in
between. Real node spacing is also uneven and slightly jittered, so a naive smoothing filter
turns the node pattern into a fake oscillating yaw rate. The first prototype showed exactly this.

**Pipeline** (`road.py`; each step is a pure function of the input and `RoadConfig`):

1. **lat/lon → ENU.**
2. **Clean-up.** Merge vertices closer than 0.5 m. Remove direction-reversal "spikes" (turn > 150° with
   a leg shorter than 25 m), which are snapping or digitising artefacts.
3. **Corner fillets.** Replace every vertex with a tangent circular arc whose radius is the largest that
   (a) cuts the corner by at most `max_corner_cut_m` (4 m) and (b) fits within half of each adjacent
   segment. When nodes are evenly spaced on a curve, the fillets meet at segment midpoints and recover
   the true radius. At an isolated intersection corner the radius is bounded by the cut; for a 90° turn
   that gives R ≈ 11 m, which is car-like.
4. **Whittaker smoothing** on a uniform 1 m resampling: minimise Σ wᵢ|pᵢ − rᵢ|² + λ Σ|Δ³pᵢ|².
   The third difference approximates d³r/ds³, whose normal component is dκ/ds. The smoother
   therefore prefers clothoid-like curvature transitions, which is how roads are actually designed. It
   acts as a low-pass filter with a steep ω⁻⁶ roll-off; λ is set from a cutoff wavelength (`smoothing_wavelength_m`,
   150 m). A **deviation corridor** (1 m from the filleted path) is enforced by iteratively re-weighting
   points that violate it, so sharp corners are not over-smoothed.
5. **Arc-length quintic spline.** The smoothed points are re-parametrised by true arc length
   (|dr/ds| − 1 < 1e-6 on all presets). This gives continuous heading, curvature and dκ/ds analytically.

**Why not just a Gaussian filter.** Measured on an R = 300 m arc mapped like a hand-digitised way
(uneven node spacing 2–34 m, 0.3 m jitter; the `uneven_jittered_circle` test fixture). Smoothing is
applied after filleting, and κ·R is evaluated well inside the arc:

| Method | κ·R inside the arc (ideal 1.00) | Max deviation |
|---|---|---|
| Fillets only | −0.33 … 6.94 | 0.50 m |
| Fillets + Gaussian (σ = 4 m) | 0.03 … 3.39 | 0.55 m |
| Fillets + Gaussian (σ = 8 m) | 0.21 … 1.69 | 0.68 m |
| Fillets + Whittaker (λc = 60 m) | 0.46 … 1.49 | 0.62 m |
| **Fillets + Whittaker (λc = 150 m, 1 m corridor), default** | **0.94 … 1.09** | **0.74 m** |

Douglas–Peucker simplification was tried and dropped. It made the vertex spacing more uneven and
therefore increased the ripple.

**Numerical note.** With λ ≈ 2·10⁸ the system is badly conditioned. Computing the right-hand side as
`P @ r` with a pre-multiplied penalty matrix cancels catastrophically, producing about 0.1 mm of noise
and a spurious 1e-8 /m curvature on a perfectly straight road. Solving for the correction
d = p − r with the right-hand side evaluated as −λ·D³ᵀ(D³r) avoids this.

**Diagnostics** reported in the UI and API: raw and smoothed length, vertices, removed
duplicates/spikes, max/RMS deviation from the map polyline, minimum turn radius, and warnings (length
outside 0.5–5 km, large deviation, very tight turn). On the real tunnel presets the max deviation is
0.7–0.9 m and the minimum radius is 700–900 m.

## 5. Vehicle motion model

The vehicle is constrained to the path (single lane, no slip). Its state is arc length s, speed v and
acceleration a, and everything else is derived from them.

**5.1 Speed planning (spatial, `speed_profile.py`).**
1. *Preferred speed* = cruise speed + a smooth random variation: a stationary Gaussian process with
   squared-exponential covariance (std `speed_variability_kmh`, length scale
   `speed_correlation_length_m`). This is generated as white noise convolved with a Gaussian kernel.
   The first version used an Ornstein–Uhlenbeck process. OU paths are nowhere differentiable, so
   their slope turned into jittery, jerk-saturated acceleration: ±1 m/s², with the jerk limit active
   60% of the time. A smooth process fixed this (a_long std went from 0.37 to 0.05 m/s² in the SR 99
   tunnel).
2. *Curve limit* v ≤ √(a_lat,max / |κ|), with |κ| max-filtered over ±15 m so the driver is already at
   curve speed when the curve begins.
3. *Speed floor* `min_speed_kmh` (the vehicle never stops). It never overrides the curve limit: a
   hairpin is crawled through, not taken too fast.
4. *Forward/backward passes* enforce the acceleration and deceleration limits (anticipatory braking).
   They use only `planning_margin` (80%) of the limits. With 100%, the jerk-limited tracker had no
   authority left to catch up when it lagged, and overshot the lateral limit by up to 33% at sharp urban
   corners. The overshoot is now ≤ 5%.

**5.2 Longitudinal dynamics (time domain, `longitudinal.py`, dt = 1/rate).**
A jerk-limited tracker models the driver and powertrain:

```
a_cmd = clip(a_ref(s_p) + K_v · (v_ref(s_p) − v), −a_dec, +a_acc)      s_p = s + v·T_p (preview)
j     = clip(K_a · (a_cmd − a), −j_max, +j_max)
```

The jerk is held constant over each step and the state is integrated **exactly** (cubic in time). This
makes a = dv/dt and v = ds/dt hold to machine precision at every sample: the ground truth is
self-consistent by construction, not by numerical differentiation. The hard limits on acceleration,
deceleration and jerk are never exceeded (clipping). The lateral limit is approximate (≤ 5–6% overshoot
on sharp corners, ~0% in tunnels).

**5.3 Ground truth (`truth.py`).** Everything is evaluated from (s, v, a, j) and the path:
position r(s), yaw ψ(s), yaw rate κv, yaw acceleration κ′v² + κa, lateral acceleration κv²,
`acc_enu = a·t̂ + κv²·n̂`, `acc_body = (a, κv², 0)` and `omega_body = (0, 0, κv)`. Roll and pitch
are zero (flat road).

**Driver presets** (comfort-oriented passenger-car values):

| | cruise | σ speed | a_lat,max | a_acc | a_dec | jerk |
|---|---|---|---|---|---|---|
| calm | 60 km/h | 2 km/h | 1.5 m/s² | 1.0 | 2.0 | 1.2 m/s³ |
| normal | 70 km/h | 4 km/h | 2.0 m/s² | 1.5 | 2.5 | 2.0 m/s³ |
| sporty | 85 km/h | 6 km/h | 3.0 m/s² | 2.5 | 3.5 | 3.5 m/s³ |

## 6. Reproducibility

* A `ScenarioConfig` contains the **route geometry as fetched** (not just the endpoints), every
  parameter, the sample rate and the seed. Saved JSON reproduces runs bit-for-bit, offline, and
  independently of later OSM edits.
* Randomness comes from **named streams**: `rng_stream(seed, "driver")` =
  `SeedSequence([seed, crc32(name)])`. Adding a random consumer later (e.g. accelerometer noise in
  M3) cannot change the realisation of existing ones, and toggling one sensor's noise will not change
  another's.
* Presets live inside the package (`throughtunnel/presets/*.json`), so the app and the tests run
  offline.

## 7. Validation (`uv run pytest`, 50 tests, no network)

| Property | Test |
|---|---|
| Geodesy | ECEF/ENU round trips (< 1e-10°), ENU distance = ECEF chord, ≈ haversine |
| Road | straight → κ = 0; circle → κR = 1 ± 3% and total heading change exact; 90° corner → continuous heading, 5 m < R < 30 m, bounded cut; uneven/jittered nodes → κR within ±12%; real tunnels → no curvature steps, deviation < 1.5 m; |r′(s)| = 1 |
| Self-consistency | ds/dt = v, dv/dt = a, da/dt = j, dψ/dt = yaw rate, each within its analytic discretisation bound |
| End-to-end kinematics | Second derivative of the ENU trajectory, rotated into the body frame, equals (a_long, a_lat) within 0.02 m/s². This is the check the M2 sensor model will rely on. |
| Turning | steady circle: yaw rate = v/R, a_lat = v²/R (±3%), signs positive for left turns |
| Straight acceleration | constant-acceleration phase: v linear, s quadratic, consistent integration |
| Driver limits | all presets × all styles + sharp urban corners: accel/decel/jerk limits exact, lateral ≤ 1.06×, never stops, speed genuinely varies |
| Driving smoothness | jerk limit active < 2% of the time in a tunnel |
| Random process | std, squared-exponential correlation, derivative std = σ/L |
| Reproducibility | same seed → identical arrays; different seed → different driver; JSON round trip → identical run; independent named RNG streams |
| App logic | playback clock (play/pause/seek/end/restart), figure decimation and cursor |

The UI was additionally driven end-to-end in a headless browser: the preset loads, play/pause advance
correctly in wall-clock time, seek lands on the requested time, the plot cursor matches the playback
time, clicking two map points produces an OSRM route, regeneration with another driver style works,
and saving then loading a scenario reproduces it exactly.

## 8. Assumptions

* The road is flat and level: z = 0, no grade, no banking, roll = pitch = 0. (The Eisenhower tunnel
  really has a ~1.6% grade, which is ignored.)
* Single lane: the vehicle drives on the smoothed OSM centreline (OSRM returns the carriageway
  geometry).
* No side-slip: the velocity is always along body-x. Kinematic constraint, no tyre model.
* No suspension, so no body roll or pitch under acceleration.
* The driver behaves reasonably (comfort limits above) and never stops.
* The entire selected route is the GPS-denied section in M1. The tunnel presets run portal to portal.
* Constant gravity and no Earth rotation (relevant only from M2: the Earth rate of 7.3e-5 rad/s can be
  added to the gyro model).

## 9. Known limitations and next steps

* **OSRM demo server:** rate-limited, no SLA, development use only. Routes from clicked points may snap
  to an unexpected carriageway. When extending the presets beyond the tunnel portals, endpoints snapped
  onto the opposite carriageway and produced detours, which is why the presets are portal-to-portal.
  A self-hosted OSRM, or via-points along the motorway, would allow approach sections with GPS before
  and after the tunnel.
* **Tunnel extent is not marked yet.** OSM `tunnel=yes` intervals could be stored as s-ranges (OSRM's
  intersection classes are cached in `RawRoute.metadata` for this) to switch GPS off only inside.
* **Lateral limit is soft** (≤ 5–6% overshoot at sharp corners). That is acceptable for "reasonable
  driver" realism, but it is not a hard guarantee.
* **Single vehicle, no traffic.** No stop-and-go or lane changes. The `DriverConfig` and scenario
  structure leave room for those.
* **Corner geometry at intersections** is synthetic: the fillet radius comes from the corner-cut
  bound, not from surveyed geometry.
* **Smoothing changes geometry slightly** (bounded and reported). It can be disabled
  (`smoothing_wavelength_m = 0`) to study the raw-polyline artefacts.
