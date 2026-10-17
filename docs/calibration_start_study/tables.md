# Calibration start diagnostic: tables

Commit `618ed45`, 2026-10-17 13:47 UTC; 20 seeds per case, flat roads. Medians unless stated. *wide* = the filters' offset and yaw priors widened to 10 mg / 10° (counterfactual).

## 1. The calibration's start

| case | GPS before loss [s] | calibration ready before loss [s] | first solution: |offset| [mg] median (max) | first solution: |yaw| [°] median (max) | at loss: |yaw| [°] |
|---|---|---|---|---|---|
| eisenhower_tunnel/free | 67 | 42 | 3.9 (37.3) | 3.3 (26.5) | 0.22 |
| eisenhower_tunnel/stop_and_go | 69 | 44 | 3.9 (37.3) | 3.3 (26.5) | 0.22 |
| seattle_sr99_tunnel/free | 106 | 86 | 1.7 (5.7) | 0.7 (1.5) | 0.15 |
| seattle_sr99_tunnel/stop_and_go | 108 | 88 | 1.7 (5.7) | 0.7 (1.5) | 0.15 |
| synthetic_demo_track/free | 83 | 63 | 1.4 (3.3) | 2.3 (11.3) | 0.32 |
| synthetic_demo_track/stop_and_go | 84 | 64 | 1.4 (3.3) | 2.3 (11.3) | 0.32 |
| ladder_5km/free | 83 | 63 | 1.4 (3.3) | 2.3 (11.3) | 0.32 |
| ladder_5km/stop_and_go | 84 | 64 | 1.4 (3.3) | 2.3 (11.3) | 0.32 |

## 2. The filters: offset error at GPS loss and error at C, priors as they are → wide

| case | route_kf now: |b err| [mg] | route_kf now: error at C [m] | route_kf wide: |b err| [mg] | route_kf wide: error at C [m] | route_kf_yaw now: |b err| [mg] | route_kf_yaw now: error at C [m] | route_kf_yaw wide: |b err| [mg] | route_kf_yaw wide: error at C [m] |
|---|---|---|---|---|---|---|---|---|
| eisenhower_tunnel/free | 0.71 (3.0) | 75 (196) ✗2 | 0.39 (2.0) | 43 (127) | 1.92 (13.9) | 250 (928) ✗12 | 0.73 (2.6) | 86 (246) ✗5 |
| eisenhower_tunnel/stop_and_go | 0.77 (3.0) | 276 (796) ✗11 | 0.39 (2.0) | 133 (549) ✗7 | 1.86 (14.0) | 617 (1322) ✗16 | 0.73 (2.7) | 211 (881) ✗11 |
| seattle_sr99_tunnel/free | 0.18 (0.7) | 38 (63) | 0.18 (0.7) | 37 (63) | 0.21 (0.7) | 42 (113) | 0.24 (0.8) | 44 (102) |
| seattle_sr99_tunnel/stop_and_go | 0.18 (0.7) | 133 (567) ✗8 | 0.18 (0.7) | 132 (560) ✗8 | 0.20 (0.7) | 147 (726) ✗8 | 0.21 (0.8) | 127 (705) ✗8 |
| synthetic_demo_track/free | 0.18 (0.7) | 17 (58) | 0.18 (0.8) | 17 (69) | 0.24 (0.7) | 20 (52) | 0.28 (0.7) | 15 (53) |
| synthetic_demo_track/stop_and_go | 0.15 (0.8) | 45 (240) ✗3 | 0.18 (0.8) | 58 (227) ✗3 | 0.24 (0.7) | 67 (384) ✗3 | 0.25 (0.7) | 57 (304) ✗3 |
| ladder_5km/free | 0.18 (0.7) | 85 (283) ✗4 | 0.19 (0.8) | 80 (324) ✗4 | 0.24 (0.7) | 89 (244) ✗3 | 0.28 (0.7) | 84 (253) ✗4 |
| ladder_5km/stop_and_go | 0.16 (0.8) | 188 (782) ✗9 | 0.18 (0.8) | 241 (782) ✗13 | 0.24 (0.7) | 402 (782) ✗12 | 0.25 (0.7) | 299 (782) ✗12 |
