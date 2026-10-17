# Route Kalman filters on fresh seeds: route_kf (first) vs. route_kf_yaw (yaw)

Commit `d6f657d+dirty`, 2026-10-17 11:26 UTC; seeds 20–79. Error at C, median (p90) [m], ✗ = gross errors (> 200 m). Paired: runs where the yaw state is worse / better / within 1 m (capped runs end at the same point).

| case | runs | first | yaw | paired worse / better / same | sign test p | median paired change [m] |
|---|---|---|---|---|---|---|
| realistic/free | 60 | 142 (285) ✗19 | 139 (302) ✗16 | 33 / 27 / 0 | 0.52 | +9 |
| realistic/stop_and_go | 60 | 355 (782) ✗41 | 503 (782) ✗45 | 29 / 18 / 13 | 0.14 | +0 |
