# Positioning design (PROPOSED, awaiting review)

Status: **not implemented.** This is the proposed minimal architecture and first baseline for the
positioning phase. Decisions referenced as Dxx / PDx are in [decisions.md](decisions.md); task IDs in
[roadmap.md](roadmap.md).

## 1. Information flow

```
 simulator side (hidden)                       │  estimator side (what a phone app has)
───────────────────────────────────────────────┼──────────────────────────────────────────────
 ScenarioConfig (A,B,C,D, nav event, ...)      │
   └► run_scenario ─► GroundTruth, imu_ideal,  │
                       imu_errors, gnss_ideal  │
                     ─► ImuStream (measured) ──┼──►┐
                     ─► GnssStream (measured) ─┼──►├─ Observations ─► Runner ─► Estimator(s)
   RawRoute + A..D + nav event ─► RouteMap ────┼──►┘   (static map +     (chronological,  │
                                               │        time series)      incremental)    ▼
 Evaluation ◄── truth at estimate times ◄──────┼───────────────────────── EstimateTrack(s)
   (errors, announcement timing, recovery)     │                          + announcements
```

* `Observations` is the **only** input to estimators (D15). It contains the measured IMU stream, the
  measured GPS stream, and a `RouteMap`. It never contains `GroundTruth`, `imu_ideal`, `imu_errors`, the
  mounting, the smoothed truth path, or crossing times.
* `RouteMap` is built from the **original OSRM polyline** (D21), not from the smoothed `RoadPath`. It
  holds:
  * the polyline and cumulative distance;
  * B and C as points with their along-map distances;
  * the navigation event(s) (D14).
* Evaluation is the only place where truth and estimates meet.

## 2. Types (neutral module `throughtunnel/observations.py`, PD1)

```python
ImuStream      # moved here unchanged: t[N], accel[N,3] (m/s²), gyro[N,3] (rad/s), Android phone axes
GnssFix        # t, lat, lon, horizontal_accuracy_m (68 %), speed_mps, bearing_deg,
               # speed_accuracy_mps, bearing_accuracy_deg  (Android Location fields)
GnssStream     # time-ordered GnssFix records (arrays internally)
NavigationEvent  # id, kind ("exit"), map_distance_m (along RouteMap), announce_lead_m
RouteMap       # polyline lat/lon, cumulative distance, tunnel_entrance / tunnel_exit (point + distance),
               # events: list[NavigationEvent]
Observations   # imu: ImuStream, gnss: GnssStream, route: RouteMap
```

## 3. Estimator contract and runner

```python
class Estimator(ABC):                      # inheritance: the common contract (D18)
    name: str
    def __init__(self, route: RouteMap, config: EstimatorConfig): ...
    @abstractmethod
    def on_imu(self, t: float, accel: NDArray, gyro: NDArray) -> None: ...
    @abstractmethod
    def on_gnss(self, fix: GnssFix) -> None: ...
    @abstractmethod
    def state(self) -> StateEstimate: ...   # estimate at the time of the last processed event

StateEstimate  # t, east/north (route-local ENU) + lat/lon, speed, heading, mode ("gnss"/"dead_reckoning"),
               # optional: along-route distance, 2x2 position covariance, other internals (diagnostics)
```

* **Runner** (D17): merges all streams into one timestamp-ordered event sequence (ties: IMU before GPS
  at the same timestamp). It calls the handlers one event at a time and records `state()` at a fixed
  output rate (e.g. 20 Hz) into an `EstimateTrack`. Several estimators can run on the *same*
  `Observations` object (D19).
* **Causality is tested, not just intended.** For every estimator: perturb all observations after a time
  t*, re-run, and require identical estimates up to t*. Together with the import-boundary test (PD1),
  this guards D15/D17 mechanically.
* **Composition** (D18): reusable stages are plain objects that estimators own and call, for example:
  * `MountAligner`: levelling and yaw misalignment;
  * `CausalLowPass`;
  * `BiasCalibrator`;
  * `RouteProjector`: map matching;
  * `LocalFrame`, which reuses `geodesy.py`.

  Stateful probabilistic estimators (EKF, particle filter) are estimators in their own right, not
  pipeline stages.
* **Announcer** (PD8): one shared component. It projects an estimator's position onto the route map
  (or uses its along-route state) and fires each navigation event when estimated distance-to-event ≤
  `announce_lead_m`.

## 4. First baseline: GPS-initialised 2-D vehicle dead reckoning ("B0")

The simplest physically meaningful estimator, chosen to make error accumulation visible and explainable
before adding any correction (D22).

**Observations used:** measured IMU (all samples), GPS fixes while available. The map is used only for
the local frame origin and display. B0 does **not** use the map as a constraint; that is a later
estimator.

**Mounting (PD5).** The phone frame must be related to the vehicle frame:
* *Levelling:* the up axis in phone coordinates is the normalised mean specific force over the approach
  (gravity dominates; the mean vehicle acceleration over tens of seconds is small).
* *Forward axis:* one angle in the horizontal plane. Either declared (aligned-mount scenarios only,
  labelled as an assumption) or estimated by least squares. The estimate matches the phone's horizontal
  specific force to the GPS-derived vehicle accelerations a_long ≈ Δv_GPS/Δt and a_lat ≈ v_GPS · ω_up.
  Here ω_up = up · gyro does not depend on the unknown angle. This angle is observable only if the
  approach contains speed changes or turns. Otherwise B0 must fall back and report it.

**State:** position (E, N) in a local ENU frame at the route start, speed v, heading ψ (ENU yaw).

**While GPS fixes arrive (A–B, and after reacquisition):** reset to each fix: position = fix,
v = fix speed, ψ = fix bearing (converted to ENU yaw). Between fixes, propagate as below. B0 does no
filtering or averaging; later estimators improve on this.

**Without GPS (B–C, and the delay after C):** for each IMU sample (dt = 1/f_IMU),

```
a_fwd = forward_axisᵀ · accel          (forward specific force; flat road ⇒ no gravity term if levelled)
ω_up  = up_axisᵀ · gyro                 (yaw rate)
v    += a_fwd · dt                      (v clamped at ≥ 0)
ψ    += ω_up · dt
E,N  += v · (cos ψ, sin ψ) · dt          (no side-slip: velocity along the heading)
```

This is a non-holonomic, vehicle-frame dead reckoning. The lateral accelerometer channel is not
integrated, because the car cannot move sideways. A full unconstrained strapdown is a possible
comparison variant, not the first baseline.

**Outputs:** position, speed, heading, mode; no covariance in B0. A simple analytic uncertainty (from
the error budget below) could be added later for the calibration metrics.

**Expected error budget** (default smartphone errors, 20 m/s; tunnel durations 25–250 s for 0.5–5 km):

| Error source | Growth | 60 s | 120 s |
|---|---|---|---|
| Forward accel bias 10 mg (worst case all on the forward axis) | ½·b·t² along-track | 177 m | 706 m |
| Levelling error 1° (acts as forward bias 17 mg) | ½·g·sin ε·t² | 308 m | 1.2 km |
| Gyro bias 0.1 °/s about the up axis | ≈ ½·v·b·t² cross-track | 63 m | 251 m |
| Initial heading error 1° (GPS bearing) | v·δψ·t | 21 m | 42 m |
| Initial speed error 0.3 m/s (GPS speed) | δv·t | 18 m | 36 m |
| Accel white noise 180 µg/√Hz | N·t^1.5/√3 | 0.5 m | 1.3 m |
| Gyro white noise 7 mdps/√Hz | heading σ = N·√t | 0.05° | 0.08° |

Raw inertial dead reckoning is dominated by **constant forward-axis errors**: bias and levelling.
White noise is negligible. This is the expected, honest starting point, and it motivates the next steps:
* calibrate the forward bias and levelling against GPS during the approach;
* constrain to the route (removes cross-track error and heading drift);
* model or constrain speed.

**Validation of B0 itself** (separate from its accuracy):
* *Ideal sensors + ideal GPS + aligned mount* → error after 150 s of dead reckoning below ~1 m. This
  checks frames, signs and integration.
* *Single error source* (e.g. only an explicit forward accel bias, or only a gyro bias on the up axis) →
  measured error growth matches the analytic curve above within a few percent.
* *Causality* test and *import-boundary* test (section 3).

## 5. Evaluation definitions (PD2, PD3)

* Reference: the true **phone** position, evaluated exactly at each estimate timestamp (via
  `LongitudinalTrajectory.at` + path + lever arm).
* Error vector e = estimate − truth (horizontal, ENU).
  * Along-track = e · t̂_true (+ = estimate ahead).
  * Cross-track = e · n̂_true (+ = estimate to the left).
  * Total = |e|.
* Error vs time, and vs true distance travelled since B.
* Error at the tunnel exit: at the true time of crossing C.
* Announcement timing error = t_announce − t_true(event − lead) (+ = late), plus the equivalent
  distance error.
* GPS recovery time: from C (or from the first fix after C) until the error stays below a threshold
  (e.g. 10 m) for a set time.
* Monte Carlo: same drive, varying sensor/GPS seeds. Report mean, RMS and percentiles per estimator.
* Calibration (when covariance exists): NEES and coverage of the 68 % / 95 % ellipses.

## 6. GPS simulation proposal

Essential for the first positioning step (D16):
* Fixes at 1 Hz (configurable) on the simulation clock, phone position (PD2).
* Position error per axis = first-order Gauss-Markov (σ ≈ 2–3 m, correlation time ≈ 20–60 s) +
  small white part.
* Speed noise ≈ 0.1–0.3 m/s. Bearing noise ≈ speed noise / speed.
* Reported accuracy fields consistent with the model.
* Availability by section: fixes on A–B, none on B–C, back after C + configurable delay.
* Recommended from the start (PD4): a randomised loss point / short degradation zone before B, so the
  loss time is not an exact entrance marker.
* Seeded named streams (`gnss.*`); ideal GPS kept as hidden diagnostics.

Later (still required, D16):
* realistic entrance degradation (growing errors, dropouts, multipath outliers);
* exit reacquisition transients (poor first fixes, jumps);
* latency.

## 7. Scenario definition A–D (D11, D13, D14)

* UI: four sequential map clicks (A, B, C, D; the hint says which is next).
* OSRM computes one route through the four points as waypoints (multi-waypoint request, legs
  A–B, B–C, C–D).
* The snapped B and C locations are placed on:
  * the map polyline (for `RouteMap`);
  * the smoothed truth path, by projection (for GPS availability and evaluation).
* The navigation event is a distance after B (slider, constrained to B–C), with an announcement lead
  distance.
* Validation warnings:
  * B–C outside 0.5–5 km (replaces today's whole-route check);
  * approach A–B too short to initialise (e.g. < 30 s at cruise speed);
  * route doubling back at a waypoint (U-turn) or legs much longer than the straight-line distance.
* Display: tunnel B–C as a thick, semi-transparent grey line under the route, A–D markers, the event
  marker, and phase colouring.
* Presets: rebuilt with approach and recovery sections. Earlier attempts to extend past tunnel portals
  snapped to the opposite carriageway; OSRM's `bearings` parameter or careful point placement should
  avoid this, to be verified. The synthetic track gets B/C by distance.
* Schema v4; v3 files load as legacy scenarios (PD7).

## 8. Risks specific to this design

1. **Mount observability:** a straight, constant-speed approach leaves the yaw misalignment unobservable.
   Levelling errors masquerade as accelerometer bias.
2. **GPS timing cue:** a sharp loss at B leaks the entrance time (PD4).
3. **Same-map optimism:** even the original polyline is close to truth (≤ ~1–4 m). Route-constrained
   estimators will look good until map errors are added (D21, R3).
4. **Initial-state quality:** GPS bearing and speed errors feed dead reckoning directly. Correlated GPS
   errors do not average out like white noise.
5. **Matched tuning:** if estimator parameters equal the simulator's settings, results are optimistic
   (PD6).
6. **Runtime:** Python per-event processing at 200 Hz is fine for a few estimators. Monte Carlo × many
   estimators may need decimated inputs or vectorised internals (without breaking causality).
7. **UI complexity:** `app/page.py` is ~720 lines. Multiple estimate overlays need the single-track
   browser player generalised to N tracks. Split the page into components before adding overlays.
