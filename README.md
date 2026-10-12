# ThroughTunnel

A vehicle and smartphone-sensor simulator for **GPS-denied positioning research**. A car drives a real
road (OpenStreetMap) treated as a tunnel; the simulator produces physically consistent ground truth and,
in later milestones, what a phone in the car would measure.

**Status: milestone 1, vehicle simulation.** Smartphone sensors (M2), sensor imperfections and data
export (M3), and positioning algorithms come later.

![Simulator UI](docs/img/ui.jpg)

## Quick start

Requires [uv](https://docs.astral.sh/uv/) (Python 3.14 is pinned by the project).

```bash
uv sync                      # create the environment
uv run throughtunnel         # start the UI at http://127.0.0.1:8080 (opens a browser)
uv run pytest                # validation test suite (~5 s, no network needed)
```

Options: `uv run throughtunnel --port 8090 --host 0.0.0.0 --no-browser`.

## Using the simulator

1. **Pick a scenario.** Either choose a preset (*Seattle SR 99 Tunnel*, *Eisenhower Tunnel*, *Synthetic demo
   track*), or click a start point and a destination on the map. The route is computed with OSRM on
   OpenStreetMap data and snapped to the road network, and the scenario is generated immediately.
   The map shows the raw OSM polyline (grey, dashed) and the smoothed drivable path (blue). The panel
   shows the route length (highlighted when outside the 0.5–5 km tunnel range), how far the path
   deviates from the map polyline, the minimum turn radius, and any warnings.
2. **Play it back.** Use play/pause, restart, playback speed (0.5×–20×), and seek with the slider or by
   clicking a plot. The vehicle (yellow) moves along the road with a heading tick, the travelled trail
   is drawn in orange, and the readouts and plot cursor follow the simulation time.
3. **Change the scenario.** Under *Scenario parameters* you can set the driver style (calm / normal /
   sporty), cruise speed, speed variability, the lateral/longitudinal acceleration and jerk limits, the
   road smoothing settings, the random seed and the sample rate. Then press **Generate**.
4. **Reproduce it.** *Save scenario* downloads a JSON file with the route geometry *as fetched*, every
   parameter and the seed. *Load scenario* replays it bit-for-bit, offline.

### Programmatic use

The simulation core has no UI dependency:

```python
from throughtunnel.scenario import load_preset, run_scenario

result = run_scenario(load_preset("seattle_sr99_tunnel"))
truth = result.truth                 # GroundTruth: columnar numpy arrays at 100 Hz
truth.t, truth.speed, truth.yaw_rate, truth.acc_body, truth.omega_body
result.path.diagnostics              # road-geometry processing report
```

To simulate your own road, build a `ScenarioConfig(route=RawRoute(...))` or use
`OsrmRouteProvider().route(start, end)`.

## Project layout

```
src/throughtunnel/
  geodesy.py            WGS84 geodetic <-> ECEF <-> local ENU
  routing/              RawRoute model, OSRM provider, synthetic test roads
  road.py               map polyline -> smooth arc-length path (+ diagnostics)
  vehicle/              driver config, speed planning, longitudinal dynamics, ground truth
  scenario.py           ScenarioConfig, run_scenario, seeds, JSON persistence, presets
  presets/              bundled scenarios (route geometry cached -> work offline)
  app/                  NiceGUI front-end (depends on the core, never the reverse)
tests/                  physics and reproducibility validation
docs/design.md          design decisions, frames, models, assumptions, limitations
```

## Ground truth (per sample, default 100 Hz)

`t, s, x, y, z, lat, lon, alt, speed, accel_long, accel_lat, jerk, yaw, bearing_deg, yaw_rate, yaw_accel,
curvature, roll, pitch`, plus the vectors `acc_enu`, `acc_body` and `omega_body` (N×3). The navigation
frame is local ENU and the body frame is ISO 8855 (x forward, y left, z up). Positive yaw rate and
positive lateral acceleration mean a left turn. See [docs/design.md](docs/design.md#coordinate-frames-and-conventions).

The ground truth is the simulator's hidden reality. Positioning algorithms (later milestones) will only
receive sensor observations and explicitly allowed side information.

## Main assumptions (details and limitations in the design doc)

Flat, level road (no grade, roll or pitch); single lane on the OSM centreline; no side-slip; no
suspension dynamics; the driver never stops; the whole selected route is treated as GPS-denied. The
road is smoothed so the path has continuous curvature. The deviation from the map polyline is bounded
and reported.

## Roadmap

- **M2: smartphone sensors.** Accelerometer (specific force, gravity) and gyroscope from the ground
  truth, configurable phone mounting rotation, Android sensor axes, ideal-measurement plots.
- **M3: imperfections and scenarios.** Noise and bias toggles and sliders, independent seeded RNG
  streams per sensor, export, and a recorded-data loader that produces the same sensor-stream type.

## Data and services

Map tiles and road geometry © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors
(ODbL). Routing uses the public [OSRM](https://project-osrm.org/) demo server, which is meant for light
development use; set `OsrmRouteProvider(base_url=...)` to use a self-hosted instance.
