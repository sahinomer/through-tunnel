# Modelling scope and known limitations

What the simulator and the experiments deliberately leave out, and what each omission probably does to
the results. It is kept for the write-up's limitations section and as a list of future work. Status
values:
* **modelled**: always simulated;
* **optional**: available, off by default (UI and config);
* **not modelled**: not simulated; the expected effect is stated instead.

"Direction" says whether including the effect would most likely make the results **better** (the
current numbers are pessimistic) or **worse** (the current numbers are optimistic), and for which
methods.

## Vehicle and road

| Effect | Status | Direction if included | Notes |
|---|---|---|---|
| Road grade (elevation profile) | optional (D36) | worse for IMU methods | Studied in [slope_study.md](slope_study.md). |
| Traffic: slowdowns, speed limits, stop-and-go, exit queues, congestion | optional (D37) | worse for speed hold; somewhat worse for IMU (longer outages) | Studied in [traffic_study.md](traffic_study.md). |
| Long incident stop (minutes) | not modelled | as stop-and-go, with one long outage | Skipped by decision; stop-and-go and exit queues already cover stopping. |
| Body pitch and roll on the suspension (braking, accelerating, load) | not modelled | worse for IMU methods | Acts like a few-% accelerometer scale error during speed changes and disturbs the approach calibration; mostly cancels over a stop/start cycle. |
| Road banking (roll in curves) | not modelled | slightly worse for unconstrained dead reckoning | Tilts the yaw axis like a cos(roll) factor; negligible for the route-constrained estimators. |
| Interacting vehicles (emergent traffic waves) | not modelled | unknown | Traffic is imposed on one vehicle as speed zones and stops, with plausible but uncalibrated parameters. |
| Driver reacting to grade (slowing on climbs) | not modelled | worse for speed hold | Would couple slope and traffic effects. |
| Real elevation profiles of the presets | not modelled | — | Presets stay flat; slope experiments use templates. |
| Tunnel lengths outside 2–3 km | covered by the editor, not by the studies | worse for long tunnels, better for short ones | The brief allows 0.5–5 km; errors grow with t² or faster. |
| Lane changes, multi-lane tunnels | not modelled | — | The brief assumes single-lane tunnels. |

## Phone sensors

| Effect | Status | Direction if included | Notes |
|---|---|---|---|
| White noise, constant bias | modelled | — | Studied in [factor_study.md](factor_study.md). |
| In-run bias drift (instability, temperature) | optional (D38) | worse for IMU methods, growing with outage length | Gauss-Markov per axis. See the realism check. |
| Calibration (orientation) residual | optional (D34) | worse for IMU methods | Studied in [calibration_error.md](calibration_error.md). |
| Vehicle and engine vibration | not modelled | neutral for today's estimators; needed for standstill detection | Without it, a stopped car and a car at constant speed look the same to the IMU; a standstill detector would be unrealistically easy or impossible. Not simulated by decision (user, 2026-10-16): a vibration model could not be validated here. Standstill is studied as an explicitly labelled oracle observation instead, kept out of the phone-only baseline. Vibration and engine audio for standstill and possibly speed are future research (roadmap R12). |
| Scale factor and cross-axis errors | not modelled | slightly worse | Small next to the dominant effects. |
| Timestamp jitter, separate accelerometer/gyro clocks | not modelled | slightly worse | |
| Phone moved or handled during the tunnel | not modelled | much worse (any method using the IMU orientation) | Scenario-specific; breaks the calibration. |
| Magnetometer | not modelled | — | Unreliable in tunnels (steel, electrical installations). |
| Gravity: altitude and local anomalies | not modelled | slightly worse for the map-grade correction | The simulator uses WGS84 normal gravity at the latitude, and since D48 so do the estimators, so their gravity is exact here. Real gravity also falls with altitude (−0.03 % per km, Eisenhower at 3.4 km: −0.1 %) and has local anomalies (~0.01 %). That scales the grade correction: 0.02 mg per 0.1 % of g on a 2 % grade change, ≈ 20 m after an 8 min stop-and-go outage at Eisenhower's altitude. GPS altitude would remove the altitude part (free-air gradient), but the simulated fixes carry no altitude. |
| Barometer | not modelled | could make IMU methods better (grade) | Tunnel ventilation and the pressure wave pushed by traffic disturb pressure by tens of pascals (1 Pa ≈ 8 cm); needs research. |

## GPS

| Effect | Status | Direction if included | Notes |
|---|---|---|---|
| Correlated position errors, speed and bearing noise, loss before B, delayed reacquisition | modelled | — | |
| Degradation approaching the portal (multipath, jumps) | optional (D38) | worse for all methods (hand-over state) | Linear ramp over the last ~150 m before B. |
| Poor first fixes after reacquisition at C | not modelled | worse recovery | The "recovered after C" metric then means more than the reacquisition delay. |
| Time-correlated Doppler speed/bearing errors | not modelled | slightly worse (hand-over) | The model uses white noise. |
| The phone's own fused location (OS smoothing, map matching) | not modelled | unknown | Apps usually receive fused locations, not raw GNSS. |
| GNSS repeaters inside tunnels | not modelled | much better | Exists in some tunnels; an infrastructure answer. |

## Map

| Effect | Status | Direction if included | Notes |
|---|---|---|---|
| Map geometry and length scale errors | not modelled (map = OSM polyline) | worse for route-constrained methods | R3. |
| Map grade (road slope from the map provider) | optional (D39), assumed exact | — | Studied in [map_grade_study.md](map_grade_study.md). |
| Map grade errors: noise, offset, smoothing, profile shifted along the route | not modelled (user decision: map assumed correct) | worse for the IMU estimators with map grade | Each 0.1 % of grade error leaks 0.1 % of g into the speed (~70–100 m at C in the presets); a shifted profile acts like a position error at every grade change. A sensitivity sweep would quantify it. |
| Driver leaving the route (missed exit, detour) | not modelled | much worse for route-constrained methods | They assume the route is followed. |
| Exit or junction inside the tunnel | not modelled | — | Interpreted as an announcement before C (D32). |

## Information outside the phone (discussed, not simulated)

| Source | What it would give | Notes |
|---|---|---|
| Vehicle speed (OBD, Android Auto / CarPlay) | direct speed: immune to grade, traffic and stops; error ∝ distance | **Simulated** since D41 as a reference-only sensor (fixed scale error, default +2 %); only an estimator that declares it receives it (D20). Not modelled: the 1 km/h quantisation of the OBD value (up to ±0.14 m/s, i.e. ~20 m over 150 s at constant speed), noise, latency, dropouts. |
| Standstill (when the car stands still) | speed exactly 0 at stops, in both directions; a stop also measures the forward offset (zero-velocity update) | **Oracle since D49**, from the true motion, delivered only to the oracle estimators (`route_imu_stop`, `route_imu_zupt`, marked ‡); not a validated detector. A real source would be a phone detector (vibration, engine audio: roadmap R12) or the car. Perfect by default; the sensitivity study (D50) adds delay, missed stops and false standstills during real slow-downs: used naively, it needs release timing within ~0.5 s. |
| Bluetooth beacons in tunnels (e.g. the Waze Beacons programme) | absolute position fixes inside the tunnel | Installed in some cities' tunnels; an infrastructure answer. |
| Cellular / Wi-Fi positioning | coarse fixes | Coverage in tunnels varies; accuracy typically tens to hundreds of metres. |

## Experiments and validation

* **No real data.** Parameters come from datasheets and the literature, not from a real phone in a
  real tunnel. The simulator is checked for internal consistency (numerical differentiation, closed-form
  predictions), not against field recordings.
* **One drive per preset in most studies.** 10–20 sensor seeds; the percentiles are indicative.
* **Estimator tuning matches the simulated defaults** (PD6 tuning-mismatch experiments not run).
* **Calibration time is short, and longer is better (user note, 2026-10-17).** Every simulated drive starts
  only 67–106 s of GPS before the tunnel (Eisenhower 67 s, the ladder 83 s, Seattle 106 s), and the GPS + IMU
  calibration is first solved 42–86 s before GPS loss. The shortest approach (Eisenhower) gave the worst start
  and the worst offsets ([calibration_start_study.md](calibration_start_study.md)). A real drive usually has
  minutes of GPS before a tunnel, so for the calibrated estimators the results are **pessimistic** here.
  Caveat: a longer calibration only helps while the phone stays put in its holder (holder shift, R11, not
  simulated) and while the bias does not drift away from it.
