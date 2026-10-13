# Design notes: vehicle and smartphone IMU simulation

This document records the technical decisions, models, conventions, assumptions and known limitations
of the simulator **as implemented**. It is meant to be read alongside the code. Accuracy claims are
enforced by tests (`tests/`) unless marked as a *one-off measurement*; see the evidence note in §8.

Related documents:
* [decisions.md](decisions.md): decision log, including superseded decisions.
* [roadmap.md](roadmap.md): status, remaining tasks, open decisions.
* [positioning_design.md](positioning_design.md): the positioning proposal, not implemented yet.

## 1. Architecture

```
            ┌────────────── core (pure Python / numpy, no UI imports) ──────────────┐
RouteProvider ──► RawRoute ──► RoadPath ──► SpeedProfile ──► Longitudinal ──► GroundTruth ──► ImuStream
 (OSRM, synthetic)  (lat/lon     (smooth      (spatial plan,    (time domain,     (hidden      (observation,
                    polyline)    arc-length    seeded RNG)       jerk-limited)     state)       phone axes)
                                 spline)
            └── ScenarioConfig (route + parameters + seed) ──► run_scenario() ──► SimulationResult ┘
                                                                     │
                                                    app/ (NiceGUI) ◄─┘  rendering only
```

* **One pure entry point:** `run_scenario(ScenarioConfig) -> SimulationResult`. There is no hidden or
  global state, so identical config gives identical arrays (tested bit-for-bit).
* **The UI is a client of the core.** `app/` imports the core; nothing in the core imports `app/`.
  The playback clock (`app/playback.py`) and the figure builders (`app/plots.py`) are plain Python
  and unit-tested. `app/page.py` only orchestrates. Its components are the parameter panels
  (`controls.py`), the map (`map_view.py`), the A–D click selection (`route_picker.py`) and the HTML
  readouts (`readouts.py`, pure functions).
* **Ground truth is separate from observations.** `GroundTruth` is the simulator's hidden state. The
  `sensors/` package reads it and emits an observation stream, `ImuStream` (timestamps, accel[N,3],
  gyro[N,3], axis convention, source label). `ImuStream` carries **no** simulation truth, not even the
  true phone mounting (a test guards this). A recorded-phone loader will produce the same type, so
  positioning code written against `ImuStream` works on both. Positioning code will never import
  `GroundTruth`, and a test will enforce that import boundary once that package exists.
  *Resolved (P1):* the observation types live in the neutral module `throughtunnel/observations.py`.
  A subprocess test checks that importing positioning code loads no simulator module.

## 2. Technology decisions

| Decision | Choice | Alternatives considered and why not |
|---|---|---|
| UI | **NiceGUI 3** (FastAPI and Vue under the hood) with its built-in Leaflet map and Plotly | **Dash + dash-leaflet**: dash-leaflet's last release targets Dash 3, while Dash is now 4.x, so there is a compatibility risk on Python 3.14 and a heavy dependency tree. **Streamlit**: its rerun-the-script model is a poor fit for smooth 20 Hz playback. **Custom FastAPI + JS**: more code in two languages; NiceGUI already runs on FastAPI if REST endpoints are needed later. |
| Playback | The server owns the playback clock and drives readouts, slider and plot cursor (`Plotly.relayout` on the cursor shape only). **Map motion is rendered in the browser** (`app/static/track_player.js`) from a 10 Hz copy of the track, interpolated every animation frame and re-anchored to the server clock on play/pause/seek/speed changes | Server-pushed marker positions stuttered (see §2.1). Moving the whole clock client-side would duplicate the playback logic in JS. |
| Routing | **OSRM HTTP API** (public demo server, configurable URL) | **OSMnx + networkx** would give OSM tags and offline graphs, but pulls in geopandas/shapely/pyproj and depends on Overpass, which was overloaded (HTTP 504) during development. The fetched geometry is stored in scenario files, so scenarios never need the network again. |
| Geodesy | Own WGS84 geodetic↔ECEF↔ENU (~60 lines, exact, tested) | pyproj or pymap3d: unnecessary dependencies for one well-known transform. |
| Numerics | numpy, scipy (sparse solve, B-splines, FFT convolution) | |
| Config / persistence | pydantic v2 models → JSON | Validation of ranges and lossless JSON round-trip for free. |

### 2.1 Playback jitter investigation

After milestone 1, the marker visibly jittered during playback, especially at 5×. I measured the
cause before changing anything:

* **The simulated positions are continuous.** Step length = v·dt to 0.04 µm, the second difference of
  position equals the true acceleration, and sampling the truth at ideal 20 Hz ticks gives uniform
  displacements (CV 0.5% = the real speed variation).
* **Rendering was the cause.** NiceGUI timer ticks reached the browser at ~16 Hz (62 ms) while it draws
  at 60–75 fps. The marker held still for 4–5 frames and then jumped. The jump grows with playback
  speed × zoom (0–1 px at zoom 15 and 1×; 5–9 px at zoom 17 and 5×). At low on-screen speed,
  Leaflet's whole-pixel rounding turned this into irregular 0/1 px steps (58% of updates moved nothing).
  The orange trail was appended every 0.5 s of simulation time, so its end lagged the marker in a
  0–10 m sawtooth.
* **Fix (rendering only, physics unchanged).** The browser interpolates the marker, heading tick and
  trail from a decimated track every animation frame. The trail is now drawn up to the last sample plus
  a short link to the marker. Result at zoom 17 and 5×: the marker advances in 92% of frames by
  1.7 px on average (= on-screen speed / frame rate), instead of 5–9 px jumps 16 times a second. The
  periodic server re-sync is "soft": both clocks run in real time, so it only corrects genuine drift
  (> max(0.25 s, 0.1 s × rate)) and ignores ±40 ms timing noise.

## 3. Coordinate frames and conventions

| Item | Convention |
|---|---|
| Navigation frame | Local **ENU** tangent plane anchored at the first route vertex (x East, y North, z Up). |
| Body frame | **ISO 8855** vehicle axes: x forward, y left, z up. |
| Phone (sensor) frame | **Android `SensorEvent`** axes, device in portrait: x = right edge, y = top edge, z = out of the screen. |
| Mounting | `R_bs` (v_body = R_bs · v_phone) = Rz(yaw) · Ry(pitch) · Rx(roll), intrinsic Z-Y′-X″ angles of the phone frame relative to the vehicle frame. All zeros = aligned axes. |
| Yaw ψ | Angle from East to body-x, counter-clockwise positive, **unwrapped** (continuous). |
| Bearing | Compass heading = (90° − ψ) mod 360, clockwise from North (display only). |
| Signs | Curvature κ, yaw rate and lateral acceleration are **positive for a left turn**. |
| Units | SI everywhere internally (m, s, rad). km/h and degrees only in UI labels and config fields named `*_kmh`. |

The flat-earth (tangent-plane) approximation is accurate to well under a metre over the ≤ 10 km extent
of a scenario. The tangent plane drops below the Earth's surface by about 2 m at 5 km. Road height
(D36) is measured from the tangent plane, and the geodetic altitude adds that curvature.

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

**Why not just a Gaussian filter.** *One-off measurement* (only the default row is enforced by
a test, with looser ±12 % bounds) on an R = 300 m arc mapped like a hand-digitised way
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
`acc_enu = a·t̂ + κv²·n̂`, `acc_body = (a, κv², 0)` and `omega_body = (0, 0, κv)` on a flat road.

**5.4 Road elevation (`road_profile.py`, D36).** A road can have a height profile z(s) over the same
horizontal distance s.
* *Definition:* heights at points along the route (an even grid of ~200 m plus B and C). Between them
  the road follows a quintic Hermite curve:
  * slopes from a shape-preserving PCHIP fit, so the curve passes through every point and does not
    overshoot;
  * zero vertical curvature at the points, so grade and vertical curvature are continuous (C2) and
    the pitch rate never jumps.
* *Grade limit:* the grade is limited (default 6%) along the whole curve. The editor clamps dragged
  points to stay within it.
* *Kinematics:* s, v, a stay horizontal, so the map, B, C and the driver's speed profile are
  unchanged. With G = z′:
  * velocity v·(cos ψ, sin ψ, G);
  * vertical acceleration G·a + G′·v²;
  * pitch θ = −atan G (ISO, + = nose down);
  * attitude C_nb = Rz(ψ)·Ry(θ), body x along the 3-D velocity, no banking (roll = 0);
  * ω = (−sin θ·ψ̇, θ̇, cos θ·ψ̇), and α as its derivative.

  The IMU model needed no change: it already used the full attitude and the lever-arm terms.
* *Validation:* numerical differentiation of the phone pose on an underwater profile matches the
  IMU output to 0.005 m/s² and 3·10⁻⁷ rad/s.
* *Flat roads* (no points, or all heights equal) take exactly the old code path: bit-identical
  results.
* *Simplifications:* no banking; the driver's speed does not react to the grade; the profile is
  defined over map distance and applied over the driven path's distance (they differ by a few metres);
  the 2-D route map gives the estimators no height information.

**Driver presets** (comfort-oriented passenger-car values):

| | cruise | σ speed | a_lat,max | a_acc | a_dec | jerk |
|---|---|---|---|---|---|---|
| calm | 60 km/h | 2 km/h | 1.5 m/s² | 1.0 | 2.0 | 1.2 m/s³ |
| normal | 70 km/h | 4 km/h | 2.0 m/s² | 1.5 | 2.5 | 2.0 m/s³ |
| sporty | 85 km/h | 6 km/h | 3.0 m/s² | 2.5 | 3.5 | 3.5 m/s³ |

## 6. Smartphone IMU model (`sensors/`)

**Accelerometer.** It measures the specific force at the phone, expressed in phone axes:

```
f_s = R_bsᵀ · C_bn · ( a_phone,n − g_n )            g_n = (0, 0, −γ(lat))
a_phone = a_ref + α × r + ω × (ω × r)                (rigid-body transfer over the lever arm r)
```

* γ is the **WGS84 normal gravity** (Somigliana: 9.780 m/s² at the equator, 9.832 m/s² at the poles),
  evaluated at each sample's latitude. Normal gravity already includes the centrifugal part of Earth
  rotation. A constant 9.80665 is available as an option.
* A phone lying still, screen up, reads **+γ on z** (Android convention). Upright in portrait it reads +γ on
  y. Face down it reads −γ on z.
* **Lever arm r**: the phone's position relative to the vehicle reference point. That point is the one
  that follows the road without side-slip, i.e. the rear-axle centre in a kinematic bicycle model. A phone
  1.6 m ahead adds up to ~0.06 m/s² on the demo track: tangential α×r at curve entries and centripetal
  ω²r in curves.

**Gyroscope.** It measures the angular rate of the phone, ω_s = R_bsᵀ · ω_b. The phone is rigidly
mounted, so the lever arm does not matter.

**Earth rotation (option, off by default).** It adds Ω_ie (7.292e-5 rad/s ≈ 15 °/h) to the gyro and the
Coriolis term 2 Ω_ie × v to the accelerometer. Both are physically present but far below
consumer-sensor noise and bias: driving east at 90 km/h at 45° latitude, the Coriolis term is about
0.26 mg sideways, plus a similar Eötvös reduction of the vertical force. The transport rate of the
local frame (v / R ≈ 3e-6 rad/s) is neglected.

**Mounting presets.**

| preset | Euler (yaw, pitch, roll) | phone x / y / z point to |
|---|---|---|
| aligned | (0, 0, 0) | forward / left / up |
| flat_portrait | (−90°, 0, 0) | right / forward / up |
| dash_portrait | (−90°, 0, 90°) | right / up / backward (screen faces the driver) |
| dash_portrait_tilted | (−90°, 0, 75°) | right / 0.97 up + 0.26 forward / 0.97 backward + 0.26 up |
| dash_landscape | (0, −90°, 0) | up / left / backward. Pitch = −90° is the Euler gimbal lock, where yaw and roll rotate about the same axis. |

**Observation boundary.** `ImuStream` contains only what a phone reports. The mounting rotation, lever arm
and gravity model stay in the scenario config (simulator side). Estimating the phone-to-vehicle rotation
is part of the positioning problem, not an input to it. `SimulationResult.imu` is the measured stream
(the observation). `imu_ideal` (error-free) and `imu_errors` (the bias and σ actually applied) are
hidden simulator state, used only for display, debugging and evaluation.

### 6.1 Sample rate

The phone IMU runs on its own constant-rate clock, t_k = k / f_IMU (default 200 Hz, 10–2000 Hz),
independent of the vehicle simulation rate (default 100 Hz). The longitudinal model holds the jerk
constant over each simulation step, so s(t), v(t) and a(t) are exact cubic, quadratic and linear
polynomials between steps (`LongitudinalTrajectory.at`). The vehicle state, and from it the path
geometry, attitude, angular rate and specific force, is evaluated exactly at every IMU timestamp. A
400 Hz IMU on a 100 Hz simulation therefore gets genuinely new samples.

Measured: on the demo track, the second difference of the exact 400 Hz position matches the IMU to
2e-4 m/s². Repeating the 100 Hz values (sample-and-hold) would leave 2e-2 m/s² forward and 7e-3 m/s²
lateral, and the test tolerance rejects that. Sampling is instantaneous: there is no on-chip
anti-aliasing filter, which only matters once vibration is modelled.

### 6.2 Sensor errors (`sensors/errors.py`)

```
measured = ideal + b + n_k        n_k ~ N(0, σ² I) per axis, white;   σ = N_d · √f_s
```

* **White noise** is specified as a noise density N_d: µg/√Hz for the accelerometer, mdps/√Hz for the
  gyroscope (velocity / angle random walk). The per-sample σ grows with √(sample rate), while the
  1-second average (the Allan deviation at τ = 1 s) equals N_d at every rate. So changing the rate
  changes the noise per sample, not the information content per second.
* **Constant bias** (turn-on bias) is either an explicit vector in phone axes, or the configured
  magnitude in a direction drawn from the seed.
* There are four independent switches (accel/gyro × noise/bias), and magnitudes are set in
  datasheet units. The defaults are smartphone-class values: accelerometer 180 µg/√Hz and 10 mg,
  gyroscope 7 mdps/√Hz (0.007 °/s/√Hz) and 0.1 °/s. At 200 Hz that gives σ = 2.55 mg and 0.099 °/s
  per sample.
* **Randomness:** the named streams `imu.accel.noise`, `imu.accel.bias`, `imu.gyro.noise` and
  `imu.gyro.bias` draw their standard normals whether or not a source is enabled. Toggling or rescaling
  one source therefore never changes another, and changing a magnitude rescales the same noise
  pattern. `errors.seed` (default: the scenario seed) gives Monte-Carlo runs over sensor errors on an
  identical drive.
* Not modelled yet: bias instability and random walk, temperature drift, scale factor, cross-axis
  misalignment, quantisation, saturation, vibration, timestamp jitter, and separate accel/gyro clocks.

**UI.** Changing the mounting re-runs only `ideal_imu` (`with_imu_config`), so the vehicle motion is
bit-identical. Each IMU axis gets its own plot row, because gravity moves between axes with the mount.
Each row has a minimum y-span (1 m/s², 0.1 rad/s) so physically negligible variations are not blown up
by autoscaling, e.g. the ~1e-5 m/s² change of normal gravity along a 3 km route.

### 6.3 Phone GPS (`sensors/gnss.py`)

Android-`Location`-style fixes (D16), not raw GNSS. Defaults are in decision D25.
* **Timing and position:** 1 Hz fixes of the **phone** position (reference point + lever arm).
* **Errors:**
  * position: per-axis first-order Gauss-Markov (2.5 m, 30 s) + 0.5 m white;
  * speed: 0.2 m/s white noise; bearing noise = speed noise / speed;
  * consistent accuracy fields (68 % radius).
* **Availability:**
  * the loss starts at a seeded random point up to 30 m before B, so the loss time does not reveal
    the exact entrance (PD4);
  * no fixes in B–C;
  * fixes return 3 s + U(0, 2 s) after the true crossing of C.
* **Not modelled:** degradation ramp before the entrance, outliers, poor first fixes, latency (R4).
* **Validated:**
  * ideal fixes equal the phone position, and the course over ground is checked by differentiating
    the phone position (in turns it differs from the vehicle heading by the lever-arm term);
  * error σ, time correlation and 68 % coverage;
  * availability around B–C;
  * independence from IMU errors.

### 6.4 Route structure A–D (`scenario.py`)

* **Definition:** a scenario has a route A→D and a `TunnelConfig`: B and C as distances along the *map*
  route (the original OSRM polyline), plus one exit-announcement distance before C (D32).
* **What the estimator gets:** `route_map` contains this map knowledge.
* **Hidden truth:** `SectionTruth` projects the map points onto the smoothed true path (same ENU frame)
  and gives the true crossing times of B, C and the announcement point. It is used for GPS
  availability and evaluation only.
* **Checks:** scenario warnings cover the B–C length (0.5–5 km), an approach shorter than 30 s, a short
  recovery, and U-turns. `run_scenario` refuses turns tighter than 3 m radius (not drivable).

## 7. Reproducibility

* A `ScenarioConfig` contains the **route geometry as fetched** (not just the endpoints), every
  parameter, the sample rate and the seed. Saved JSON reproduces runs bit-for-bit, offline, and
  independently of later OSM edits.
* Randomness comes from **named streams**: `rng_stream(seed, "driver")` =
  `SeedSequence([seed, crc32(name)])`. Adding a random consumer later (e.g. accelerometer noise in
  M3) cannot change the realisation of existing ones, and toggling one sensor's noise will not change
  another's.
* Presets live inside the package (`throughtunnel/presets/*.json`), so the app and the tests run
  offline.

## 8. Validation (`uv run pytest`, 187 tests, no network)

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
| IMU: gravity | stationary phone reads exactly γ(lat) on the axis that points up, for every preset; face down → −γ; WGS84 normal gravity values at 0°/45°/90° |
| IMU: motion | aligned phone: accel = (a_long, a_lat, γ), gyro = (0, 0, yaw rate); flat portrait: x = −a_lat, y = a_long |
| IMU: mounting | 26 random and preset mounts are proper rotations; the Euler convention is pinned; changing the mount leaves the ground truth bit-identical, preserves the magnitudes of f and ω, and rotating back gives the same body vectors |
| IMU: end-to-end | Numerically differentiate the phone's actual pose (vehicle pose + lever arm, tilted mount) twice for position and once for orientation, and compare with the IMU: residual 5e-4 m/s² (tolerance 0.005, while the lever-arm terms alone reach 0.06) and 4e-7 rad/s |
| IMU: lever arm | steady turn: extra −ω²r on the forward axis |
| IMU: Earth rotation | at rest the gyro reads Ω(cosφ, 0, sinφ) when heading north; driving east, accel gets +2Ωv sinφ to the north and −2Ωv cosφ vertically (Eötvös) |
| IMU: observation type | shape and timestamp validation; `ImuStream` fields and metadata carry no truth (no mounting) |
| IMU rate | own constant clock at 50/200/416 Hz; 400 Hz on a 100 Hz simulation equals the exact continuous-time kinematics and is not sample-and-hold; differentiated 400 Hz position matches within 1e-3; 50 Hz hits the right simulation samples |
| IMU errors | all disabled → measured ≡ ideal; bias → constant offset with the configured norm (or the explicit vector); noise → zero mean, σ = N·√rate (±1%), white (lag-1 correlation < 0.01), independent axes and sensors; 1-s Allan deviation = N at 100 and 400 Hz |
| IMU randomness | sources independent (toggling accel noise leaves gyro and bias unchanged); doubling N doubles the same residual; same seed → identical; sensor seed changes errors but not drive or ideal; scenario seed drives errors by default |
| Persistence | v2 files migrate to an ideal IMU at the simulation rate; configs built in code are not migrated; rate and error settings round-trip |
| UI construction | the page builds in NiceGUI's in-process user simulation (this caught a control-ordering bug) |
| A–D structure | route map = original polyline; B/C located on the true path within 1 m of the map point at the true crossing time; ordered crossing times; warnings; U-turn rejection |
| GPS | see §6.3 |
| Observation boundary | importing positioning loads no simulator module (subprocess); observation types have no truth fields |
| Positioning | causality of every estimator (perturb the future, past unchanged); runner order and tie rule; zero-error dead reckoning < 1 m; forward-bias error = analytic vector integral (1 %); gyro-bias heading error linear (5 %); calibration removes > 95 % / > 80 % of bias errors; tilted mount recovered < 1°; gyro-bias calibration < 0.02 °/s on the hardest approach; GPS blending improves the hand-over state; route estimators stay on the route; on-time announcements with perfect data |
| Evaluation | along/cross sign conventions on shifted truth; recovery-time definition |
| Road elevation (D36) | curve passes through the points without overshoot; grade and vertical curvature continuous (C2); grade limit validated and enforced by the drag clamp (lands exactly on the limit); templates within the limit and gentle (< 0.3 m/s² at 90 km/h); truth height/grade/pitch follow the profile, body x along the 3-D velocity; flat profile bit-identical to no profile; the IMU end-to-end test also runs on an underwater profile; a grade change after calibration leaks gravity, a constant grade does not; editor: drag events parsed, only points draggable, simulated drag clamped and re-simulated |
| App logic | playback clock (play/pause/seek/end/restart), figure decimation and cursor, browser track payload, IMU figure ranges |

**Evidence note.** The table above is enforced by tests. These figures are *one-off measurements*
recorded during development and are not re-checked automatically:
* the smoother comparison table (§4);
* the jitter study figures (§2.1);
* the ~0.06 m/s² lever-arm magnitude (§6);
* the real-tunnel deviation 0.7–0.9 m and radius 700–900 m (§4; the tests use looser bounds,
  < 1.5 m and > 300 m);
* the browser checks below.

The browser checks below were made with ad-hoc Playwright scripts that are **not in the repository**
(roadmap F9).

The UI was additionally driven end-to-end in a headless browser: the preset loads, play/pause advance
correctly in wall-clock time, seek lands on the requested time, the plot cursor matches the playback
time, clicking two map points produces an OSRM route, regeneration with another driver style works,
and saving then loading a scenario reproduces it exactly. For milestone 2: the IMU tab shows gravity on
z for the aligned mount and on y for the dashboard-portrait mount (with the yaw rate moving to gyro y).
Changing the mount leaves the drive unchanged. A custom yaw switches the preset to "custom", and the
custom mount survives save/load. The cursor follows on whichever plot tab is visible, with no
console errors.

## 9. Assumptions

* The road is flat and level: z = 0, no grade, no banking, roll = pitch = 0. (The Eisenhower tunnel
  really has a ~1.6% grade, which is ignored.)
* Single lane: the vehicle drives on the smoothed OSM centreline (OSRM returns the carriageway
  geometry).
* No side-slip: the velocity is always along body-x. Kinematic constraint, no tyre model.
* No suspension, so no body roll or pitch under acceleration.
* The driver behaves reasonably (comfort limits above) and never stops.
* The GPS-denied section is the user-selected B–C of an A–D route (D11; implemented). Earlier the
  whole route was GPS-denied (D10, superseded).
* Gravity is WGS84 normal gravity on the ellipsoid surface. There is no height correction, no gravity
  anomalies and no deflection of the vertical.
* The phone is rigidly mounted. There is no holder vibration, no engine/road vibration and no
  phone movement relative to the car.
* The sensor error model is Gaussian white noise plus a constant bias per axis (§6.2). The phone IMU
  samples instantaneously, at a constant rate with perfect timestamps. Accelerometer and gyroscope
  share one clock.
* Earth rotation is off by default, and the transport rate is always neglected (see §6).

## 10. Known limitations and next steps

* **OSRM demo server:** rate-limited, no SLA, development use only. Routes from clicked points may snap
  to an unexpected carriageway. When extending the presets beyond the tunnel portals, endpoints snapped
  onto the opposite carriageway and produced detours, which is why the presets are portal-to-portal.
  A self-hosted OSRM, or via-points along the motorway, would allow approach sections with GPS before
  and after the tunnel.
* *Resolved:* the tunnel is the user-selected section B–C (D11/D12), the 0.5–5 km check applies to
  B–C, and phone-position truth is available (`GroundTruth.point_enu`, `truth_at`).
* **Lateral limit is soft** (≤ 5–6% overshoot at sharp corners). That is acceptable for "reasonable
  driver" realism, but it is not a hard guarantee.
* **Single vehicle, no traffic.** No stop-and-go or lane changes. The `DriverConfig` and scenario
  structure leave room for those.
* **Corner geometry at intersections** is synthetic: the fillet radius comes from the corner-cut
  bound, not from surveyed geometry.
* **Smoothing changes geometry slightly** (bounded and reported). It can be disabled
  (`smoothing_wavelength_m = 0`) to study the raw-polyline artefacts.
* **IMU error model is first-order.** White noise and constant bias only. Natural next steps are bias
  instability and random walk (Gauss-Markov), temperature drift, scale factor and misalignment,
  vibration, per-device profiles, timestamp jitter, and separate accel/gyro rates.
* **Road grade is modelled (D36), banking is not.** The presets are still flat: their real profiles
  are unknown offline. The driver ignores the grade, and the estimators get no height information.
