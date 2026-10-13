> **Historical document (2026-10-12).** Superseded by [roadmap.md](roadmap.md) and
> [decisions.md](decisions.md) after review 4. It is kept unchanged below so no earlier reasoning is
> lost. Where each item went:
>
> | Item below | Disposition |
> |---|---|
> | §1.1 tunnel extents from OSM `tunnel=yes` | **superseded** by D11/D12 (four map points A–D) → P2 |
> | §1.1 find a tunnel with an internal exit | **superseded** by D14 (configurable navigation event) → P2, A9; D14 itself superseded by D32 (one announcement before C) |
> | §1.1 approach/exit sections, OSRM carriageway snapping | kept → P2 (OSRM `bearings` or point placement) |
> | §1.2 GPS (Android Location-level fixes) | **confirmed** by D16 → P5 (essential subset), R4 (details), A10 (recovery) |
> | §1.3 observation interface, causal runner | **confirmed** by D15/D17/D18 → P1, P6, P7 |
> | §1.4 evaluation harness, reference point | **confirmed** by D23 → P8, A9, A11; reference point → PD2/PD3 |
> | §1.5 map information policy, map errors | **decided**: D15, D21 → R3 |
> | §2 flat road, no stops, sensor errors, vibration | **backlog** (D05, D24) → R1, R2, R5 |
> | §3 OBD / Android Auto speed | **excluded from the main solution** (D20) → optional R6 |
> | §3 curvature matching, barometer/magnetometer | A7; barometer/magnetometer not planned |
> | §4 export, real-phone loader, timing, OSRM | F6, F7, R5, P2 |

# Readiness review before positioning

Status: the vehicle simulation and the smartphone IMU (rate, mounting, white noise, constant bias) are
implemented and validated (96 tests). This note lists what is still missing, or risky, before
positioning algorithms can be developed and evaluated fairly. Nothing here is implemented yet. Items
marked **decision** need input.

## 1. Essential infrastructure

### 1.1 Route sections: approach → tunnel → exit
* The presets currently run portal to portal: the whole route is GPS-denied. Experiments need GNSS
  before the tunnel (initialisation, and estimating the phone mounting and sensor biases), the outage,
  and recovery after the exit.
* Needed: a `RouteSections` model on the arc-length axis, e.g. `[(0, s_in, "open"), (s_in, s_out,
  "tunnel"), (s_out, L, "open")]`, with configurable approach and exit lengths.
* Tunnel extents can come from the OSM `tunnel=yes` ways, projected onto the route. The tunnel way
  geometry was already fetched for the presets.
* Known obstacle: extending routes past the portals snapped onto the opposite carriageway (detours).
  OSRM's `bearings` / `approaches` request options, or via-points along the same carriageway, should
  fix this (to be verified).
* **Maneuver points inside the tunnel.** The case study asks to "call out an exit inside the tunnel at the
  right moment". The current tunnels (SR 99, Eisenhower) have no exits inside, so we need at least
  one tunnel with an internal exit or junction, plus the exit's position on the route.
  **Decision:** which tunnels.

### 1.2 GNSS simulation (Android `Location`-level fixes)
* Fixes at ~1 Hz on the IMU clock: position, horizontal accuracy estimate, speed and bearing (Doppler).
* Errors should be **time-correlated** (e.g. Gauss-Markov, a few metres, correlation time tens of
  seconds), not white. Speed/bearing noise is much smaller than position noise.
* Per-section behaviour:
  * open sky: nominal;
  * approach: degradation near the portal (multipath, attenuation);
  * tunnel: no fixes (optionally rare, spurious fixes);
  * exit: reacquisition delay (a few seconds), initially poor accuracy, possible jumps.
* Same design rules as the IMU: a named random stream, separate enable switches, seeded, and both
  ideal and measured kept. **Decision:** level of fidelity (Location fixes vs. raw GNSS measurements). I
  recommend Location fixes; that is what a navigation app sees.

### 1.3 Observation interface for positioning
* An `Observations` bundle containing only what a phone app has: `imu: ImuStream`,
  `gnss: GnssStream`, `map: MapInfo`, rates, and the clock. No `GroundTruth`, no `imu_ideal`, no true
  mounting or bias.
* **A causal replay runner**: it merges streams in timestamp order and feeds events to an estimator
  (`on_imu`, `on_gnss`, `estimate(t)`), so an algorithm cannot look ahead. A navigation app works
  online, and I assume the evaluation should too. **Decision.**
* Estimator output: `EstimateStream(t, lat, lon, [along-route s], heading, covariance/accuracy)`.
* An import-boundary test: the positioning package must not import `vehicle.truth` or the scenario
  internals.
* The same interface for recorded data: phone-log loaders produce `ImuStream` / `GnssStream`.

### 1.4 Evaluation harness
* Align estimates with truth by interpolating the truth at estimate times. **Define the reference point**:
  truth refers to the vehicle reference point (rear axle), while the phone can sit up to ~2 m away via
  the lever arm.
* Metrics:
  * horizontal error, split into along-track and cross-track, over time and over distance into
    the tunnel;
  * error at the tunnel exit;
  * time to reconverge after the exit;
  * maneuver call-out timing error (estimated vs. true time of reaching the exit point).
* Monte-Carlo runner over sensor seeds (already possible: the drive stays fixed while the sensor seed
  varies), summary tables, and regression thresholds in CI.
* UI: estimated vs. true track and error plots. The browser track player would need to support several
  tracks.

### 1.5 What map information the estimator may use (**decision**)
* A navigation app knows the planned route and its geometry: tunnel length, curvature and exits.
  Map matching to a 1-D along-route position is probably the strongest constraint.
* Risk: the ground-truth path is derived from the *same* OSM polyline. An estimator given that map
  would be unrealistically well matched. At minimum, give the estimator the raw OSM polyline (≤ ~1 m
  from truth). Better, add a configurable map-error model: along-route scale error (~0.5–1 %),
  lateral offsets, and local distortions. Along-track scale error directly limits map-based dead
  reckoning.

## 2. Simulation gaps that bias results (recommended before evaluating)

| Gap | Why it matters for positioning |
|---|---|
| **Flat road** (no grade) | Gravity never leaks into the forward accelerometer axis. On a 3 % grade that leak is 0.29 m/s²; for comparison, a 10 mg bias alone integrates to ~12 m/s speed error after 120 s. Accelerometer-based speed estimation would look far better than reality. Needs an elevation profile (OSM `incline`, DEM or synthetic) and pitch in the truth. The frames and IMU model already support full 3-D attitude. |
| **Vehicle never stops** | Tunnel traffic jams are common. Stop-and-go breaks naive dead reckoning but also allows zero-velocity updates. Needs an optional stop/slow-traffic scenario. |
| **Only constant bias + white noise** | Fine for minutes-long tunnels to first order. Bias instability, scale factor and misalignment would make results less optimistic. |
| **No vibration** | Real accelerometers see ~0.1–0.5 m/s² rms road and engine vibration. It inflates the noise floor and needs an anti-aliasing model at low rates. |

## 3. Sensor and information choices (**decision**)

* **Speed is the key quantity in a tunnel.** Integrating the accelerometer drifts quickly (see the bias
  number above). Candidate sources:
  * GNSS speed before entry, plus a speed model;
  * yaw-rate vs. map-curvature matching (strong in curved tunnels like SR 99, useless in straight
    ones like Eisenhower);
  * vehicle speed via OBD-II / Android Auto, if "reasonably available";
  * pressure/elevation matching (needs a barometer and grade).
* Optional extra sensors: barometer (useful with grades; tunnel pressure effects make it noisy) and
  magnetometer (heavily disturbed in tunnels and vehicles; probably not worth it).

## 4. Smaller technical items

* Data export (CSV/NPZ of observations and truth) for notebooks, and a batch CLI.
* Real-phone log loader (Android sensor and GNSS logs): timestamp alignment, unknown mounting.
* Sensor timing: separate accel/gyro rates, timestamp jitter, and GNSS–IMU clock offset.
* The OSRM public demo server is development-only. Keep routes cached in scenario files (already
  done), or use a self-hosted instance for batch work.
