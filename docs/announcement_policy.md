# Uncertainty-aware announcement (step 6.2)

Step 6.2 of [estimator_plan.md](estimator_plan.md), decision D53 (2026-10-17). A simple policy that shows how the
system uses the filters' uncertainty, with minimal effort (user: "a part of the system but not the improving
performance of estimator"). **No estimator was changed.** The plain announcement is unchanged; the new one is
recorded next to it on the same runs.

Data: [announcement_policy/](announcement_policy/): the benchmark dev subset (`benchmark_dev/`) and all flat-road
scenarios: tunnel lengths 0.5–5 km and the three presets (`benchmark_flat/`), 20 seeds; `compare.md`
reports no change in any estimator. Code: `UncertaintyAwareAnnouncer` in `positioning/runner.py`.

## The policy

* **Who:** estimators that report their 1σ along-route uncertainty, i.e. the two Kalman filters (user decision).
  The others keep only the plain announcement.
* **When:** once the estimate plus a safety lead reaches the announcement point (300 m before C):
  d̂ + min(2σ, 300 m) ≥ target.
  * 2σ because a late announcement is worse than an early one (user decision): "not late" in ~95 % if σ is
    honest.
  * The 300 m cap because σ is 5–10× too large in long stop-and-go outages ([uncertainty_study.md](uncertainty_study.md)).
* **What:** **precise** ("exit in 300 m") if σ ≤ 30 m when it fires, else **hedged** ("after the tunnel, keep
  right"). At 70 km/h, ±2·30 m is about ±3 s, the window of a good announcement. The wording is the product's
  decision; here "hedged" is a type.
* Nominal values chosen by reasoning, not tuned to the results. Shared component like the plain announcer (PD8).
* **UI:** a column "uncertainty-aware" in the summary table (time error and type).

## Results (`route_kf`, flat roads, 20 runs each)

Time error of the announcement: + = late; late > 3 s / late > 15 s / early > 15 s = share of runs; median [s].
Plain → uncertainty-aware.

### Free flow

| tunnel | type | late > 3 s | late > 15 s | early > 15 s | median |
|---|---|---|---|---|---|
| 0.5 km | precise 100 % | 0 → 0 % | 0 → 0 % | 0 → 0 % | +0.2 → −1.1 |
| 1 km | precise 100 % | 0 → 0 % | 0 → 0 % | 0 → 0 % | +0.2 → −1.1 |
| 2 km | precise 100 % | 10 → 0 % | 0 → 0 % | 0 → 0 % | +0.3 → −2.2 |
| demo track (2 km) | precise 100 % | 5 → 0 % | 0 → 0 % | 0 → 0 % | +0.5 → −2.0 |
| 3 km | hedged 100 % | 25 → 0 % | 0 → 0 % | 0 → 0 % | +0.6 → −4.1 |
| Seattle SR99 (3 km) | hedged 100 % | 5 → 0 % | 0 → 0 % | 0 → 0 % | +0.7 → −3.4 |
| Eisenhower (2.7 km) | hedged 100 % | 30 → **20 %** | 0 → 0 % | 0 → 0 % | +1.0 → −2.7 |
| 5 km | hedged 100 % | 50 → 0 % | 5 → 0 % | 5 → 35 % | +1.8 → −13.5 |

### Stop-and-go

| tunnel | type | late > 3 s | late > 15 s | early > 15 s | median |
|---|---|---|---|---|---|
| 0.5 km | precise 100 % | 0 → 0 % | 0 → 0 % | 0 → 5 % | −0.1 → −5.0 |
| 1 km | hedged 100 % | 10 → 0 % | 5 → 0 % | 5 → 40 % | −0.4 → −14 |
| 2 km | hedged 100 % | 20 → 0 % | 0 → 0 % | 20 → 100 % | −0.7 → −88 |
| 3 km | hedged 100 % | 35 → 0 % | 10 → 0 % | 25 → 100 % | −2.3 → −63 |
| 5 km | hedged 100 % | 35 → 10 % | 25 → 5 % | 40 → 85 % | −3.5 → −30 |
| Eisenhower | hedged 100 % | 50 → 10 % | 25 → 5 % | 35 → 85 % | +2.4 → −81 |
| Seattle SR99 | hedged 100 % | 40 → 0 % | 5 → 0 % | 45 → 100 % | −5.9 → −71 |

`route_kf_yaw` behaves the same except on Eisenhower (below). Sloped roads (dev subset, map grade on): the
same pattern ([benchmark_dev/tables.md](announcement_policy/benchmark_dev/tables.md)).

## Findings

1. **Late announcements nearly disappear.** Free flow: late by more than 3 s from up to 50 % to 0 % in
   every tunnel except Eisenhower (30 → 20 %, never more than 15 s). Stop-and-go: late by more than 15 s
   from up to 25 % to at most 5 %.
2. **The driver gets a precise announcement in short tunnels and a hedged one in long ones.** Precise in
   every run up to 2 km in free flow; hedged from 2.7–3 km on, and in stop-and-go from 1 km on. That is the
   product behaviour we wanted: precise when the phone knows where it is, hedged when it does not.
3. **The price is earliness, and in stop-and-go it is large.** Free flow: 1–4 s early up to 3 km, 13.5 s
   at 5 km. Stop-and-go: hedged announcements come 1–1.5 minutes early. The inflated σ always hits the
   300 m cap, and 300 m takes that long in a jam. With an honest σ (200–400 m there) it would come
   somewhat later; a time-based cap would bound it directly. Kept simple on purpose (D53).
4. **Precise announcements in slow traffic look "early" in seconds** (0.5 km stop-and-go: −5 s median),
   because the 2σ lead is a distance: 20–30 m at walking pace is several seconds. In metres they are on time.
5. **Eisenhower, free flow: still 20 % late by more than 3 s.** There the filter's σ is too small (as on the
   2 km ladder in 6.1), so 2σ does not cover the error.

## Flag: `route_kf_yaw` fails on Eisenhower (found here, not caused by the policy)

The flat-road run includes the presets, which the dev subsets do not. On Eisenhower the yaw filter is much
worse than `route_kf` (error at C, median (p90) ✗ gross errors):

| Eisenhower, flat | `route_kf` | `route_kf_yaw` |
|---|---|---|
| free flow | 75 (196) ✗2 | **250 (928) ✗12** |
| stop-and-go | 276 (796) ✗11 | **617 (1322) ✗16** |

* In the worst runs (seeds 3, 10, 17) the yaw filter learns ψ = −7° to −14° on the approach, where the true
  yaw residual is about 0°, with a σ of only 0.75°. Its offset b is then 8–14 mg off, and it ends 0.9–1.5 km
  behind. These runs also produce the late "precise" announcements: the estimate reaches the announcement
  point only after GPS returns, when σ is small again.
* **`route_kf` is affected too, less:** its b is 0.7–3 mg off on the Eisenhower approach (ladder: ~0.3 mg).
  Something on that approach misleads the offset learning, and the yaw state amplifies it.
* Ruled out: road grade (the flat variant is truly flat) and vehicle sideslip (not modelled).
* This corrects step 4.1 ([route_kalman_yaw.md](route_kalman_yaw.md)): `route_kf_yaw` is not merely neutral under
  realistic conditions; on this real geometry it fails. A diagnostic of the Eisenhower approach is proposed
  as the next step.

## Limits

* Policy values by reasoning (2σ, 300 m cap, 30 m precise threshold), not optimised.
* σ is too large in long stop-and-go (6.1); the cap only bounds the consequence.
* 20 seeds per scenario; flat roads and the dev subset only (the sloped presets are not in this run).
