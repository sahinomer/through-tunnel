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
