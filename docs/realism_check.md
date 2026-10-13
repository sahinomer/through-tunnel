# Realism check: IMU bias drift and GPS degradation before the portal

Check of 2026-10-13 (D38). It asks whether the two realism effects added before freezing the simulator
change any earlier conclusion. Full tables and per-run data: [realism_check/](realism_check/).
Reproduce with:

```bash
uv run python -m throughtunnel.evaluation.realism_check --seeds 10
```

## Setup

* **Paired runs** on all three presets, 10 seeds, in free flow and in stop-and-go (long outage).
* **Baseline:** the realistic defaults (IMU noise and bias, GPS errors).
* **Conditions,** each with the default parameters and the identical seeds:
  * + IMU bias drift (0.5 mg / 5 mdps, τ = 300 s);
  * + GPS degradation before B (150 m zone, 8 m extra error, 5 % jumps at B);
  * both.
* **Metric: the size of the paired shift of the error vector at C.** How far the added effect moves
  each run's estimate. The change of the median error alone understates a random-sign effect: it can
  push an existing error up or down, and the median difference then sits near zero.

## Results (median / p90 shift at C [m])

| | free flow, drift | free flow, GPS degradation | stop-and-go, drift | stop-and-go, GPS degradation |
|---|---|---|---|---|
| IMU-based (`dr_calibrated`, `dr_filtered`, `route_imu`) | 8–29 / 18–47 | 24–87 / 47–137 | 41–103 / 334–603 | 60–276 / 233–1168 |
| `route_hold` | 0 | 22–48 / 53–79 | 0 | 0 (already at the route end) |

## What it means

1. **No conclusion changes; the magnitudes and tails of the IMU methods do.**
   * The ranking of root causes stays as it was: grade and calibration first, then the GPS hand-over,
     then driver behaviour (traffic).
   * In stop-and-go `route_imu` still beats the constant-speed baseline by far (88–213 m vs ≥ 782 m).
     In free flow the two remain comparable on lucky constant-speed drives.
2. **GPS degradation before the portal is the larger effect.** In free flow it moves the IMU estimates
   by 24–87 m, more than their whole baseline error on some presets.
   * This confirms the factor study: the state handed over at the tunnel entrance (speed, heading,
     calibration from the last fixes) is a dominant realistic error source.
   * `route_hold` is affected too: it takes its speed from the degraded last fix.
3. **Bias drift matters for long outages.** It is small in free flow (≈ 10–30 m), but in 5–8 minute
   stop-and-go outages its p90 reaches 0.3–0.6 km. A one-off calibration on the approach cannot track a
   bias that changes during the tunnel. Time-driven drift, already the IMU's weakness in traffic, gets
   larger tails.
4. **The two effects do not add simply.** "Both" is sometimes smaller than one effect alone, because
   random shifts of different origin partly cancel. The effects should be reported separately as well as
   combined.

## Limitations

The parameters are order-of-magnitude assumptions (D38). In particular, the drift size depends strongly
on the device and the temperature history. 10 runs per cell: the p90 values are indicative. Both
effects stay **off by default**; all earlier studies used them off.
