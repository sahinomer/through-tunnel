# Traffic in and around road tunnels: real-life variants (research for R2)

Research note of 2026-10-13. It collects how traffic actually behaves in tunnels and proposed which
variants to simulate. *Outcome:* T1, T2, T3, T5 and T6 were implemented (D37; T4 skipped by decision)
and studied in [traffic_study.md](traffic_study.md). Sources are listed at the end. Where the
evidence is weak (news reports, FAQ pages), it is marked as an example, not as data.

## 1. Why traffic matters for this case study

Inside the tunnel no sensor measures speed directly. The estimators so far fail in opposite ways
(factor and slope studies):
* **Speed hold** (`route_hold`) assumes the speed at the tunnel entrance stays the same. Its error is
  (entrance speed − actual mean speed) × time, whatever the sensors do. Examples:
  * a 15 km/h drop held for 150 s → about 600 m;
  * a single one-minute stop entered at 70 km/h → about 1.2 km ahead.
* **IMU integration** sees speed changes, but drifts with calibration residuals and grade.

The current simulated driver is kind to speed hold. Its speed varies smoothly by a few km/h around a
cruise speed and never drops below 10 km/h (`DriverConfig.min_speed_kmh`). Before choosing or building
a better estimator, the simulation must contain the speed changes real tunnels have.

## 2. Real-life variants

### V1. Portal effect: slowing down at the tunnel entrance

* **What happens.** Drivers slow down approaching a tunnel portal (change of light level, confined
  space). They speed up again after adapting inside, and slow down before the exit if a curve or
  interchange follows.
* **Magnitudes.** A field study on two expressway tunnels and one urban tunnel (> 500 vehicles per
  section) measured:
  * passenger cars: **−12 to −21 km/h**, with the strongest braking in the last 100 m before the
    portal, **0.47–0.70 m/s²**;
  * trucks: −2 to −10 km/h, braking 0.23–0.58 m/s²;
  * speed ranges at the portals: 75–110 km/h on expressways, 60–88 km/h in urban tunnels.

  [chd.edu.cn 2021]
* **Effect.** A systematic speed change exactly at B, i.e. right when GPS is lost. Speed hold then
  takes the *pre-drop* speed.

### V2. Lower speed limit in the tunnel

* **What happens.** Many motorway tunnels have their own limit, e.g. 80 or 100 km/h in parts of
  Europe, with enforcement cameras in some tunnels. Others keep the approach limit (Italy, unless
  signed). *(Example sources, not data.)*
* **Effect.** A step change in speed at or near B, as in V1 but planned and possibly larger.

### V3. Recurrent congestion at the tunnel bottleneck

* **Tunnels are bottlenecks.** In Japan about **50 % of expressway congestion** forms at sags and
  tunnel sections. At sags, S-curves and long tunnel entrances, capacity is about **60–70 %** of a
  basic expressway segment. [NILIM 2004; sag/tunnel studies]
* **Capacity drop.** Once a queue forms, its discharge rate is about **10 % lower** than the
  capacity before congestion, caused by slow acceleration out of the queue.
* **Urban peaks.** Example: the SR 99 tunnel carried about 5,300 vehicles/h in peak hours, with both
  ends "much more congested" than before. *(News reports.)*
* **Effect.** Slow traffic inside the tunnel for long periods, with speeds well below the approach
  speed.

### V4. Stop-and-go waves (oscillations in queues)

* **What happens.** Oscillations arise **only in queues** and have **periods of several minutes**.
  They travel *upstream* at a nearly constant speed of about **15–24 km/h**:
  * 22–24 km/h on the Queen Elizabeth Way (Mauch & Cassidy);
  * −15 ± 5 km/h for "wide moving jams" in German data (Kerner, Helbing);
  * about 18–21 km/h in the I-24 MOTION trajectories.
* **Inside a wide moving jam,** speed and flow are approximately **zero**: vehicles stand still. The
  outflow from a jam is 1500–2000 vehicles/h/lane.
* **Triggers.** On multi-lane roads they are mostly triggered by lane changes. In a single-lane
  tunnel (as the brief assumes), car-following instability alone can still produce them.
* **For a vehicle driving through,** this means alternating standing and moving phases. A moving
  vehicle meets the waves more often than a fixed observer sees them, so its stop/go cycle is shorter
  than the wave period. *Estimate, not measured:* stops of 10–60 s, moving phases of tens of seconds
  to minutes, at 20–40 km/h between the stops.
* **Effect.** The hardest case for speed hold: the entrance speed has nothing to do with the
  average. Also the case where a smartphone navigation app is most often used in congestion.

### V5. Incident: traffic stopped in the tunnel

* **What happens.** Breakdowns, crashes, fires and oversized vehicles close tunnels or lanes. News
  reports describe stationary queues inside and in front of tunnels (Dartford, Queensway, Limerick,
  Hindhead, Mumbai). *(Examples, not statistics.)*
* **Design values.** Tunnel safety design treats congested traffic in a tunnel explicitly:
  * PIARC uses a congested density of **130 vehicles/km/lane** (about 7.5 m spacing);
  * a Korean guideline checks ventilation at 10–80 km/h for congested and free traffic;
  * some operators actively prevent queues inside the tunnel, because queues raise the incident risk
    (PIARC).
* **Effect.** A long standstill (minutes). The GPS outage then lasts much longer than the
  free-flow crossing time.

### V6. Queue spilling back from the exit

* **What happens.** In urban tunnels the exit often leads to traffic signals or an interchange. Peak
  queues there can spill back into the tunnel. The general mechanism is well known in signal control
  research; the "congested tunnel ends" of SR 99 are an example.
* **Effect.** A slowdown or stop **in the last few hundred metres before C**. That is the worst place
  for positioning:
  * the dead-reckoning drift is at its maximum;
  * it is where the exit announcement (300 m before C) has to fire;
  * GPS is not yet back.

### V7. Heavy vehicles slowing on climbs

* **What happens.** Trucks lose speed on long upgrades; following traffic in a single-lane tunnel
  cannot pass, so the platoon slows too.
* **Effect.** It couples with the slope study: a climb in the tunnel means a gravity-leakage *and* a
  real slowdown at the same time. *(Highway grade literature; not tunnel-specific.)*

### V8. Normal driver variability in free flow (already modelled)

A smooth random speed variation of a few km/h around a cruise speed, plus curve limits.

## 3. Motion parameters for modelling

| quantity | value | source |
|---|---|---|
| Braking before a portal (cars) | 0.47–0.70 m/s² within 100 m | tunnel field study |
| Car-following, maximum acceleration | ~1.0–1.4 m/s² | IDM calibrations (Treiber & Kesting; calibrated tables) |
| Car-following, comfortable deceleration | ~1.5–2.0 m/s² | same |
| Accelerations in congested oscillations | mostly within ±1 m/s² | naturalistic study (Shanghai expressways) |
| Wave speed (upstream) | 15–24 km/h | Mauch & Cassidy; Kerner/Helbing; I-24 MOTION |
| Speed inside a wide moving jam | ≈ 0 | Kerner/Helbing |
| Jam outflow | 1500–2000 vehicles/h/lane | same |
| Congested density in tunnels | 130 vehicles/km/lane | PIARC |

The current driver limits (max accel 1.5 m/s², max decel 2.5 m/s², jerk 2 m/s³) already cover these
ranges.

## 4. Proposed traffic scenarios (for review)

Each variant becomes a seeded, reproducible traffic option, anchored to B and C like the road
profiles. The approach and recovery stay in free flow unless the variant says otherwise.

| ID | scenario | parameters (defaults from §2–3) | failure it exposes |
|---|---|---|---|
| T0 | Free flow (today) | — | baseline |
| T1 | Portal slowdown | −15 km/h, braking about 0.6 m/s² over the 100–200 m before B; recovery inside after N m, or none | speed hold takes the pre-drop speed |
| T2 | Tunnel speed limit | the tunnel speed differs from the approach speed (e.g. 100 → 80 km/h) | as T1, planned |
| T3 | Stop-and-go | k stop cycles in B–C; stops 10–60 s; moving phases at 20–40 km/h; acceleration ~1 m/s², braking ~1.5 m/s² | speed hold fails completely; IMU sees the transients |
| T4 | Incident stop | one standstill of 1–5 min mid-tunnel | long standstill, long outage |
| T5 | Exit queue | slowdown or stop in the last 200–500 m before C | worst-case location for the announcement |
| T6 | Slow congested flow | 20–40 km/h with slow variation through the tunnel | a sustained offset from the entrance speed |

T7 (truck-led slowdown on climbs) could follow by combining T6 with a slope profile.

**Modelling requirement found while reviewing the code.** The driver plans speed as a function of
*distance*, and its speed never drops below 10 km/h. A standstill cannot be expressed as a speed at a
distance: the vehicle stays at one distance for a while. Stops (T3–T5) therefore need a time-based
component, for example "stop at distance s for t seconds", followed by the existing jerk-limited
tracking. The minimum-speed floor must become optional. Everything downstream (truth, IMU, GPS
timing, evaluation) already works in time, so the change is contained in the vehicle model. A stop
also lengthens the GPS outage, which is realistic.

## 5. Decisions needed

1. Which scenarios first? Proposal: **T1, T3, T4, T5**. They expose four different failure modes. T2
   behaves like T1, and T6 is a parameter setting of T3.
2. Should the vehicle really stand still (speed 0)? Proposal: yes. Standstill is the defining real
   case, and it tests speed hold and IMU integration hardest.
3. Event placement: fixed relative to B/C with seeded random variation (position, duration)?
4. UI: a *Traffic* selector with a few parameters, like the road profile templates?
5. Then, as with the earlier studies: a controlled experiment with the existing estimators (identical
   seeds, free flow vs each scenario), before any estimator improvement.

## Sources

* Driving speed characteristics at tunnel entrance and exit (expressway and urban tunnels):
  [transport.chd.edu.cn](https://transport.chd.edu.cn/en/article/doi/10.19818/j.cnki.1671-1637.2021.04.015)
* Speed reduction markings in highway tunnel entrance and exit zones:
  [traffic2.fpz.hr](https://traffic2.fpz.hr/index.php/PROMTT/article/download/639/216/6929)
* Mauch & Cassidy, *Freeway traffic oscillations: observations and predictions*:
  [its.berkeley.edu](https://its.berkeley.edu/publications/freeway-traffic-oscillations-observations-and-predictions),
  [econpapers](https://econpapers.repec.org/RePEc:cdl:uctcwp:qt9kb9x6n5)
* Scalable analysis of stop-and-go waves (I-24 MOTION): [arxiv.org/html/2409.00326v1](https://arxiv.org/html/2409.00326v1)
* Wide moving jams (−15 km/h, standstill, outflow): Helbing,
  [Traffic and related self-driven many-particle systems](https://arxiv.org/pdf/cond-mat/0012229);
  Schönhof & Helbing, [Empirical features of congested traffic states](https://arxiv.org/pdf/cond-mat/0408138)
* Sag/tunnel bottlenecks and capacity (Japan): [NILIM 2004](https://www.nilim.go.jp/lab/qcg/japanese/3paper/pdf/2004_10_itswc_is02_2.pdf);
  Kai et al., [Capacity drop at sag and tunnel bottlenecks](https://arxiv.org/abs/2511.16962);
  [ISTS 2018 paper 27](https://www.cee.ehime-u.ac.jp/~keikaku/ists18/pdf/ISTS_IWTDCS_2018_paper_27.pdf)
* PIARC road tunnels manual (traffic and ventilation design):
  [tunnelsmanual.piarc.org](https://tunnelsmanual.piarc.org/sites/tunnels-manual/files/public/wysiwyg/import/Chapters%20PIARC%20reports/2016%20R19%20EN%20Chap%206.pdf),
  [tunnels.piarc.org (2008 R17)](https://tunnels.piarc.org/sites/tunnels/files/public/wysiwyg/import/Chapters%20PIARC%20reports/2008%20R17%20Chap%203.pdf);
  Korean ventilation guideline: [koreascience.kr](https://koreascience.kr/article/JAKO201225038988554.do)
* Car-following parameters (IDM): [Bayesian calibration of the IDM](https://arxiv.org/pdf/2210.03571);
  [Twenty-five years of the IDM](https://arxiv.org/pdf/2506.05909)
* Naturalistic car-following on Shanghai expressways: [arxiv.org/pdf/1811.06395](https://arxiv.org/pdf/1811.06395)
* Tunnel speed limits (examples): [wandernundmehr.at](https://www.wandernundmehr.at/faq/warum-darf-man-im-tunnel-nur-80-fahren),
  [chronicle.lu](https://www.chronicle.lu/category/motoring-1/48078-90-km-h-speed-limit-back-in-force-in-a7-gousselerbierg-tunnel),
  [completecar.ie](https://www.completecar.ie/car-news/article/6797/New-Port-Tunnel-speed-cameras)
* SR 99 tunnel traffic (news): [komonews.com](https://komonews.com/news/local/hows-traffic-in-the-sr-99-tunnel-wsdot-releases-data),
  [mynorthwest.com](https://mynorthwest.com/chokepoints/traffic-changing-seattle-tunnel-sr-99/1383602)
* Tunnel incident examples (news): [kentonline.co.uk](https://www.kentonline.co.uk/dartford/news/tunnel-shut-due-to-incident-200212/),
  [birminghampost.co.uk](https://www.birminghampost.co.uk/news/local-news/huge-delays-queensway-tunnel-closed-3909162),
  [limerickleader.ie](https://www.limerickleader.ie/news/traffic-delays-as-oversized-truck-forces-closure-of-limerick-tunnel-8379598)
* Heavy vehicles on grades: [tac-atc.ca](https://tac-atc.ca/wp-content/uploads/mcguire.pdf)
