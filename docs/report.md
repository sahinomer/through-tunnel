# Through the Tunnel: keeping a phone's position through a GPS outage

<!-- Summary: written last, once the results sections are agreed. -->

## 1. The problem and its interpretation

A driver is following turn-by-turn directions on a phone when the road enters a long tunnel. GPS fades
within seconds and stays gone for anything from half a minute to several minutes. The navigation app
is still expected to show the car in the right place, call out the exit at the right moment, and pick
up GPS again cleanly when the car comes out. This case study asks how far a phone can get on its own
sensors in that situation: what it can learn from GPS before the tunnel, how long its accelerometer and
gyroscope can carry the position through the outage, and where that stops being enough. To answer it,
a simulator was built and the estimators were developed step by step against a fixed benchmark. This
report summarises that work and what the experiments showed.

### What the app is assumed to know

The brief leaves most of the setting open; it was fixed as follows.

| Topic | Assumption | Why |
|---|---|---|
| Route | The app knows the planned route as a map polyline, and where the tunnel starts (B) and ends (C). The car follows the route. | A navigation app has both. Together they turn the problem into one dimension: how far along the route the car is. |
| Call-out | One announcement a set distance before the tunnel exit (default 300 m), triggered from the estimated position while GPS is still absent. | "Call out an exit inside the tunnel" is read as an instruction given inside the tunnel, for a manoeuvre at or after the exit. Any other point at a known distance along the route works the same way. |
| Phone | Fixed in a holder for the whole drive, at an unknown angle that is estimated from the approach. | People mount phones in all sorts of ways. A phone picked up inside the tunnel is out of scope. |
| GPS | The phone's location fixes at 1 Hz (position, speed, bearing, reported accuracy), not raw GNSS. Lost shortly before the entrance, back a few seconds after the exit. | This is what a navigation app receives. |
| Phone sensors used | GPS, accelerometer and gyroscope. | The magnetometer is disturbed by the tunnel's steel and electrical installations, and tunnel ventilation and traffic disturb the barometer. |
| Road grade | Optional: the road's slope along the route, taken from the map and assumed exact. | Without it, inertial methods fail on sloped roads (section 5). |
| Information from outside the phone | The car's own speed reading (OBD, CarPlay / Android Auto) and a perfect standstill signal are given only to separately labelled estimators, never to the phone-only ones. | They show what that extra information would be worth, without mixing it into the phone-only results. |
| Tunnel | Single lane: no lane changes, no junctions inside. | Given by the brief. |

### Why it is hard

No phone sensor measures speed or position inside a tunnel. Speed has to come from integrating the
forward accelerometer, so any constant error in it grows with the square of time in the position:

* **1 mg** of uncorrected forward offset, a tenth of the accelerometer bias simulated for a phone,
  becomes about **330 m** over a 5 km tunnel at 70 km/h (258 s without GPS);
* a **0.1° tilt error** in the phone's estimated orientation leaks 1.7 mg of gravity into the forward
  axis, which costs about **550 m** at the end of the same tunnel, as the
  [error-source benchmark](benchmark/README.md#what-the-error-source-benchmark-says) shows;
* a **1 % change in road grade** that the estimator does not know about leaks 10 mg, and costs
  0.4–1 km at the exit of the 2–3 km preset tunnels ([slope study](slope_study.md));
* in **stop-and-go traffic** the same 5 km takes 738 s instead of 258 s, so the same offset costs
  roughly eight times as much.

The gyroscope's heading matters far less. Once the estimate is held on the route, the map bounds the
cross-track error, and what remains is the error along the route. That is the number the rest of this
report is about: **how far along the route the car is**, and therefore how well its speed is known.

## 2. The simulator

The simulator produces what a phone in a car would record on a drive through a tunnel, together with
the true motion of the car. The true motion is kept hidden from the estimators and used only to score
them. The simulator is written in Python; the same core runs behind an interactive browser app and
behind the batch benchmarks.

### A drive through a tunnel

A scenario is a route through four points: the start A, the tunnel entrance B, the tunnel exit C and
the end D. The approach A–B has GPS, the tunnel B–C has none, and C–D shows the recovery. The route can
be a real road from OpenStreetMap or a synthetic one. The tunnel itself is simulated: GPS is switched
off between B and C, so any stretch of road can serve as one. Three scenarios are bundled: the Seattle
SR 99 tunnel (3.0 km) and the Eisenhower tunnel (2.7 km) on their real road geometry, and a synthetic
demo route (2.0 km). The benchmark adds synthetic tunnels of 0.5–5 km.

The map's polyline is smoothed into a drivable path whose curvature changes continuously, at most
about 1 m from the map. The car drives the smoothed path, while the estimators receive the original
polyline, so the map is close to the truth but not identical to it.

A driver model moves the car along the route: a speed that varies smoothly around a cruise speed,
braking for curves, and limits on acceleration and jerk. The motion is integrated exactly, so position,
speed and acceleration agree with each other at every sample. Two optional features make the drive
harder:
* **Road grade:** an editable elevation profile, with templates for a steady climb, a climb inside
  the tunnel and an underwater tunnel; the car then moves in 3-D;
* **Traffic:** a slowdown at the portal, a speed limit in the tunnel, stop-and-go with real stops, a
  queue at the exit, or congested flow.

### What the phone records

| Source | Model | Default ("Realistic" level) |
|---|---|---|
| Accelerometer and gyroscope | Specific force (including gravity and the lever arm) and turn rate in the phone's own axes, with the phone mounted at any angle. White noise, constant bias and an optional slowly drifting bias. | 200 Hz; noise 180 µg/√Hz and 7 mdps/√Hz; bias 10 mg and 0.1 °/s; drift 0.5 mg and 5 mdps with a 5 min correlation time |
| GPS | Location fixes of the phone: position, speed, bearing and reported accuracy. Time-correlated position error and speed noise. Lost up to 30 m before B, back 3–5 s after C. Optionally degraded just before the entrance, with larger errors and multipath jumps. | 1 Hz; 2.5 m correlated + 0.5 m white; 0.2 m/s; degradation over the last 150 m, up to 8 m extra error and 5 % jumps |
| Route map | The polyline with B, C and the announcement point; optionally the road grade. | grade exact when enabled |
| Car speed reading (reference estimator only) | The car's own speed with a fixed scale error. | 10 Hz, +2 % |
| Standstill signal (oracle estimators only) | The exact moments the car stops and starts again. | perfect |

One control in the app sets all sensor errors together, at four levels:
* **Error-free:** no errors at all; shows the limit of the algorithms themselves;
* **Good:** sensor noise and bias, clean GPS up to the entrance;
* **Realistic:** Good plus bias drift and GPS degradation before the entrance; the benchmark setting;
* **Hard:** Realistic plus an error in the phone orientation the estimators work with (yaw 2°,
  pitch 0.5°, roll 0.5°). It is applied after the estimators' own orientation estimate, because a
  fixed rotation in the sensor data would simply be estimated and removed.

### Keeping the comparison fair

* **The truth stays hidden.** Estimators receive only the sensor streams and the map. A test checks
  that loading the positioning code loads no part of the simulator.
* **No look-ahead.** Observations are fed in time order, and a test checks that changing future data
  never changes earlier estimates.
* **Paired runs.** Every random error has its own seeded stream. Switching one error source on or off
  leaves all others unchanged, and every estimator sees exactly the same data. A saved scenario file
  replays a run bit for bit, offline.
* **Checked physics.** 348 automated tests cover the simulator and the estimators. For example, the
  simulated IMU agrees with the numerically differentiated motion of a tilted phone on a lever arm to
  0.0005 m/s².

### The app

<!-- Screenshot to be refreshed: docs/img/ui.jpg predates the current estimators and controls. -->

In the browser app a scenario is picked from the bundled ones or by clicking four points on a map. The
drive is played back with the true car and every estimator moving along the route, and settings can be
changed live: phone mounting, sensor errors, road grade, traffic, announcement distance. Error plots
and a summary table (error at the exit, announcement timing) follow every change. The
[README](../README.md) describes how to run it.

Some effects are deliberately left out, notably engine and road vibration, map errors, and a phone
moved during the drive. Section 6 discusses what they mean for the results; the
[full list](limitations.md) gives the expected effect of each.

## 3. Approach

The method was built up in layers. Each layer was added only after the benchmark (section 4) had shown
the problem it addresses, and was kept only if it measurably helped.

### The pipeline

```
GPS fixes ─┐
IMU ───────┼─► calibration ──────────► estimator ─────────► position on the route ± σ
route map ─┘   phone orientation,      distance along           → map display
               sensor biases           the route, speed, …      → exit announcement
```

**Calibration.** On the approach, the phone's orientation in the car is learned from GPS: the up
direction from gravity, the forward direction by matching the phone's horizontal acceleration to the
speed changes and turns seen by GPS, and the gyroscope bias from the GPS bearing. It is re-solved with
every fix while GPS lasts. A tilted mount and constant sensor biases are removed almost completely this
way. The main thing left is a small residual tilt, which looks exactly like a forward acceleration: the
error of section 1.

**Estimator.** All main estimators work along the route. Holding the estimate on the route removes the
heading drift and the cross-track error, so only the distance along the route has to be estimated. The
simplest version advances that distance with the last GPS speed; the next integrates the calibrated
forward acceleration. Two-dimensional dead reckoning without the route was also built as a first step,
and was dropped once the route-constrained versions proved better.

**Road grade.** On a slope, gravity leaks into the forward axis. When the map provides the grade, every
estimator that uses the IMU subtracts the leak of the grade change since the calibration. Without it, a
sloped tunnel costs 0.8–25 km at the exit; with it, sloped tunnels in free flow are about as accurate as flat ones
([map grade study](map_grade_study.md)).

### From problems to solutions

The benchmarks pointed to one problem at a time. The table lists each, the change it led to, and the
clearest evidence for the change. The overall effect is in section 5.

| Problem found | Change | Evidence |
|---|---|---|
| **The error is decided before the tunnel.** In free flow, the speed and forward offset handed over at GPS loss predict the error 5 km later almost exactly, and the last fixes before the entrance, the ones most disturbed by multipath, set both ([analysis of the state at GPS loss](gps_loss_state.md)). | **Portal freeze:** GPS stops feeding the calibration and the speed 200 m before the entrance; the IMU carries the last trusted state into the tunnel. | GPS degradation before the entrance alone: 184 → 4 m after 5 km ([portal freeze](portal_freeze.md)). |
| **Small biases in the calibration itself:** a slightly wrong gravity constant, a half-sample timing lag in the averages, and road grade on the approach disturbing the forward direction ([residual study](residual_study.md)). | **Calibration fixes:** gravity for the route's latitude, exact interval timing, map grade in the fit. | With error-free sensors, the largest residual dropped from 42 m to 1.4 m, and every case ends within 7 m ([calibration fixes](calibration_fixes.md)). |
| **The residual tilt cannot be seen after the calibration**, and learning it from the last few fixes is noisy. | **Kalman filter** with distance, speed and forward offset as states. The offset is learned from all approach fixes, weighted by the speed accuracy the phone reports, and follows each re-solve of the calibration. The filter also reports its uncertainty σ. | A 0.1° tilt error: about 600 m → 3 m after 5 km ([Kalman filter](route_kalman.md)). |
| **A wrong forward direction** leaks the car's sideways acceleration in curves into the forward axis. | **Kalman filter with a yaw state**, learned on approach curves. | A 2° yaw error in stop-and-go: 204 → 2 m. Under realistic conditions no gain, so it stays a robustness variant and is not carried further ([yaw filter](route_kalman_yaw.md)). |
| **No information inside the tunnel:** after GPS loss, every error can only grow. | **Curves on the map as position fixes:** every 25 m driven, the heading integrated by the gyroscope is compared with the map's heading. On straights this calibrates the gyro drift; in curves (radius below 2 km) it fixes the position along the curve. | Realistic 5 km tunnel: 80 → 12 m in free flow, 241 → 30 m in stop-and-go ([map curves](route_kalman_map.md)). Works only where the tunnel curves and the map is accurate. |
| **Stops are handled one-sidedly.** The speed cannot fall below zero, so at a stop negative speed errors vanish but positive ones keep the estimate creeping forward. | **A standstill signal**, given as an oracle (not phone-only): speed and distance are held while the car stands, and the forward offset is measured at each stop. | Realistic 5 km stop-and-go: 385 → 103 m. Used this simply, the restart must be detected in well under 0.5 s, or the gain is lost ([standstill oracle](standstill_oracle.md)). |
| **A late announcement is worse than an early one**, and a precise one is only possible when the position is good. | **Uncertainty-aware announcement:** fire when the estimate plus min(2σ, 300 m) reaches the announcement point; "exit in 300 m" if σ ≤ 30 m, otherwise a hedged instruction. | Free flow, announcements more than 3 s late: up to 50 % → 0 % of runs ([announcement policy](announcement_policy.md)). |

### The estimators carried into the results

Development produced eleven estimators; six of them carry the story through the results:

| Estimator | What it uses | Role |
|---|---|---|
| Route + last GPS speed | GPS speed held constant along the route | naive baseline |
| Route + IMU | calibrated IMU speed along the route | the starting point of the improvements |
| Kalman filter | the filter with distance, speed and forward offset | phone-only, independent of the tunnel's shape |
| Kalman filter + map curves | the same, plus heading fixes against the map | best phone-only, in curved tunnels |
| Route + car speed (reference) | the car's speed reading instead of the IMU | what car data would give |
| Route + IMU + standstill (oracle) | a perfect stop signal | what a standstill detector would give |

## 4. How the approach was evaluated

### What is measured

Every estimate is compared with the true position of the phone at the same moment, split into the
error along the route and across it. Per run, the evaluation records:
* the **error at the tunnel exit C**, at the end of the outage;
* the **largest error inside the tunnel**;
* the **announcement timing**: how many seconds early or late the call-out came compared with the
  moment the car truly passed the announcement point.

Two outcomes count as failures, because the driver would notice them:
* a **gross error:** the estimate was more than 200 m off at some moment in the tunnel, ahead or
  behind;
* an **announcement off:** the call-out came more than 15 s early or late.

An announcement within ±3 s counts as good. For the Kalman filters, the reported uncertainty σ is also
checked against the actual errors.

### Two benchmarks

* **The scenario benchmark** covers the range of the brief: synthetic tunnels of 0.5, 1, 2, 3 and 5 km
  (each with two S-shaped curves) and the three bundled scenarios, each on a flat road, a +3 % climb
  and an underwater tunnel (−4 % down, +4 % up), in free flow and in stop-and-go traffic (three stops of
  10–60 s, 30 km/h between them). That makes 48 scenarios, each run 20 times with the "Realistic"
  sensor errors; the sloped ones are evaluated both with and without map grade. Each run is a new drive
  with new sensor errors, and all estimators see the same data
  ([benchmark overview](benchmark/README.md)).
* **The error-source benchmark** takes the 5 km flat tunnel, in free flow and in stop-and-go, and adds
  one error source at a time to an error-free setup: each IMU error, a tilted mount, orientation errors
  in pitch, yaw and roll, GPS position and speed errors, and GPS degradation before the entrance.
  Together with "Realistic" and "Hard" that makes 18 conditions, each run 20 times on the same drives.
  Besides the error inside the tunnel, it records the state handed over at GPS loss, which made it the
  main diagnostic tool of the project.

### How changes were judged

Each change was first tested on a development subset of both benchmarks (the shortest and longest flat
tunnels, the sloped 5 km tunnels and the nearly straight Eisenhower tunnel; about 6 minutes each instead of more than half an hour).
The same runs were compared before and after the change, and any scenario that got worse by more than
10 % and 5 m was flagged. Both benchmarks were rerun in full at milestones, and each new change was
compared with the latest milestone rather than the original baseline, so that every step shows only its
own effect. Every run is stored with its raw per-run results and its full configuration, so any number
in this report can be regenerated.

With 20 runs per scenario the medians are solid, but a 90th percentile is roughly the second-worst run
and is read as an indication only.
