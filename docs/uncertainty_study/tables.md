# Uncertainty consistency: tables

Commit `2f2de42+dirty`, 2026-10-17 12:51 UTC; 20 seeds per case. Coverage = share of runs whose along-track error lies within ±1σ / ±2σ of the filter's own uncertainty (honest: ~68 % / ~95 %). rms z = rms of error/σ (honest: ~1; > 1 = overconfident). |err| / σ: medians [m].

## route_kf

### At the announcement point (true time) and at C

| case | announce 1σ / 2σ | announce rms z | announce |err| / σ | C 1σ / 2σ | C rms z | C |err| / σ | outage samples 1σ / 2σ |
|---|---|---|---|---|---|---|---|
| floor/free | 100 % / 100 % | 0.0 | 0 / 134 | 100 % / 100 % | 0.0 | 1 / 153 | 100 % / 100 % |
| floor/stop_and_go | 100 % / 100 % | 0.0 | 3 / 1594 | 100 % / 100 % | 0.0 | 3 / 1800 | 100 % / 100 % |
| realistic/free | 70 % / 95 % | 1.0 | 73 / 156 | 75 % / 95 % | 0.9 | 85 / 177 | 72 % / 90 % |
| realistic/stop_and_go | 100 % / 100 % | 0.3 | 190 / 1695 | 100 % / 100 % | 0.2 | 188 / 1909 | 92 % / 98 % |
| gps_speed/free | 80 % / 100 % | 0.7 | 78 / 156 | 85 % / 100 % | 0.7 | 85 / 177 | 72 % / 99 % |
| gps_speed/stop_and_go | 100 % / 100 % | 0.2 | 169 / 1695 | 100 % / 100 % | 0.2 | 182 / 1908 | 95 % / 100 % |
| acc_drift/free | 90 % / 100 % | 0.7 | 85 / 134 | 90 % / 100 % | 0.7 | 92 / 153 | 90 % / 100 % |
| acc_drift/stop_and_go | 100 % / 100 % | 0.3 | 292 / 1594 | 100 % / 100 % | 0.2 | 306 / 1800 | 94 % / 100 % |
| cal_pitch_0.1/free | 100 % / 100 % | 0.0 | 3 / 134 | 100 % / 100 % | 0.0 | 3 / 153 | 100 % / 100 % |
| cal_pitch_0.1/stop_and_go | 100 % / 100 % | 0.0 | 4 / 1594 | 100 % / 100 % | 0.0 | 5 / 1800 | 100 % / 100 % |
| cal_yaw_2/free | 100 % / 100 % | 0.4 | 51 / 134 | 100 % / 100 % | 0.4 | 65 / 153 | 98 % / 100 % |
| cal_yaw_2/stop_and_go | 100 % / 100 % | 0.1 | 186 / 1594 | 100 % / 100 % | 0.1 | 204 / 1800 | 99 % / 100 % |
| ladder_2km/flat/free | 65 % / 85 % | 1.2 | 18 / 24 | 70 % / 85 % | 1.2 | 20 / 31 | 74 % / 91 % |
| ladder_2km/flat/stop_and_go | 95 % / 100 % | 0.5 | 50 / 309 | 95 % / 100 % | 0.4 | 51 / 388 | 92 % / 97 % |
| ladder_5km/climb3/free | 70 % / 95 % | 0.9 | 91 / 156 | 75 % / 95 % | 0.9 | 103 / 177 | 75 % / 94 % |
| ladder_5km/climb3/stop_and_go | 100 % / 100 % | 0.3 | 204 / 1695 | 100 % / 100 % | 0.2 | 228 / 1909 | 93 % / 100 % |
| ladder_5km/underwater/free | 100 % / 100 % | 0.3 | 27 / 156 | 100 % / 100 % | 0.3 | 40 / 177 | 82 % / 93 % |
| ladder_5km/underwater/stop_and_go | 100 % / 100 % | 0.3 | 267 / 1695 | 100 % / 100 % | 0.3 | 312 / 1909 | 89 % / 96 % |

### Growth: rms z by distance into the tunnel

| case | 0.5 km | 1 km | 2 km | 3 km | 4 km | C |
|---|---|---|---|---|---|---|
| floor/free | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| floor/stop_and_go | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| realistic/free | 0.9 | 1.1 | 1.1 | 1.1 | 1.0 | 0.9 |
| realistic/stop_and_go | 1.0 | 0.7 | 0.5 | 0.4 | 0.4 | 0.2 |
| gps_speed/free | 1.0 | 1.0 | 0.9 | 0.9 | 0.8 | 0.7 |
| gps_speed/stop_and_go | 0.9 | 0.6 | 0.3 | 0.3 | 0.2 | 0.2 |
| acc_drift/free | 0.5 | 0.6 | 0.7 | 0.7 | 0.7 | 0.7 |
| acc_drift/stop_and_go | 0.7 | 0.6 | 0.5 | 0.5 | 0.5 | 0.2 |
| cal_pitch_0.1/free | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cal_pitch_0.1/stop_and_go | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cal_yaw_2/free | 0.5 | 0.8 | 0.6 | 0.2 | 0.2 | 0.4 |
| cal_yaw_2/stop_and_go | 0.8 | 0.6 | 0.3 | 0.2 | 0.2 | 0.1 |
| ladder_2km/flat/free | 0.9 | 1.1 | – | – | – | 1.2 |
| ladder_2km/flat/stop_and_go | 0.7 | 0.6 | – | – | – | 0.4 |
| ladder_5km/climb3/free | 0.7 | 0.9 | 1.0 | 1.0 | 0.9 | 0.9 |
| ladder_5km/climb3/stop_and_go | 0.7 | 0.6 | 0.5 | 0.4 | 0.4 | 0.2 |
| ladder_5km/underwater/free | 1.0 | 1.4 | 1.3 | 0.6 | 0.2 | 0.3 |
| ladder_5km/underwater/stop_and_go | 1.8 | 1.2 | 0.3 | 0.2 | 0.4 | 0.3 |

## route_kf_yaw

### At the announcement point (true time) and at C

| case | announce 1σ / 2σ | announce rms z | announce |err| / σ | C 1σ / 2σ | C rms z | C |err| / σ | outage samples 1σ / 2σ |
|---|---|---|---|---|---|---|---|
| floor/free | 100 % / 100 % | 0.0 | 0 / 130 | 100 % / 100 % | 0.0 | 0 / 150 | 100 % / 100 % |
| floor/stop_and_go | 100 % / 100 % | 0.0 | 2 / 1577 | 100 % / 100 % | 0.0 | 3 / 1781 | 100 % / 100 % |
| realistic/free | 85 % / 100 % | 0.8 | 81 / 167 | 85 % / 100 % | 0.8 | 89 / 189 | 75 % / 95 % |
| realistic/stop_and_go | 100 % / 100 % | 0.3 | 350 / 1724 | 100 % / 100 % | 0.2 | 401 / 1939 | 91 % / 98 % |
| gps_speed/free | 85 % / 100 % | 0.7 | 88 / 167 | 85 % / 100 % | 0.7 | 97 / 188 | 81 % / 97 % |
| gps_speed/stop_and_go | 100 % / 100 % | 0.2 | 163 / 1724 | 100 % / 100 % | 0.2 | 178 / 1939 | 94 % / 99 % |
| acc_drift/free | 90 % / 100 % | 0.7 | 84 / 130 | 90 % / 100 % | 0.7 | 92 / 150 | 90 % / 100 % |
| acc_drift/stop_and_go | 100 % / 100 % | 0.3 | 291 / 1577 | 100 % / 100 % | 0.2 | 308 / 1781 | 94 % / 100 % |
| cal_pitch_0.1/free | 100 % / 100 % | 0.0 | 0 / 130 | 100 % / 100 % | 0.0 | 0 / 150 | 100 % / 100 % |
| cal_pitch_0.1/stop_and_go | 100 % / 100 % | 0.0 | 2 / 1577 | 100 % / 100 % | 0.0 | 2 / 1781 | 100 % / 100 % |
| cal_yaw_2/free | 100 % / 100 % | 0.0 | 0 / 130 | 100 % / 100 % | 0.0 | 0 / 150 | 100 % / 100 % |
| cal_yaw_2/stop_and_go | 100 % / 100 % | 0.0 | 2 / 1577 | 100 % / 100 % | 0.0 | 2 / 1781 | 100 % / 100 % |
| ladder_2km/flat/free | 60 % / 90 % | 1.1 | 20 / 26 | 65 % / 90 % | 1.0 | 24 / 34 | 70 % / 94 % |
| ladder_2km/flat/stop_and_go | 95 % / 100 % | 0.5 | 52 / 320 | 95 % / 100 % | 0.4 | 71 / 400 | 89 % / 98 % |
| ladder_5km/climb3/free | 85 % / 100 % | 0.8 | 91 / 167 | 85 % / 100 % | 0.8 | 104 / 188 | 80 % / 100 % |
| ladder_5km/climb3/stop_and_go | 100 % / 100 % | 0.3 | 344 / 1724 | 100 % / 100 % | 0.3 | 467 / 1939 | 94 % / 100 % |
| ladder_5km/underwater/free | 100 % / 100 % | 0.3 | 27 / 166 | 100 % / 100 % | 0.3 | 38 / 188 | 82 % / 95 % |
| ladder_5km/underwater/stop_and_go | 100 % / 100 % | 0.4 | 489 / 1724 | 100 % / 100 % | 0.3 | 525 / 1939 | 89 % / 97 % |

### Growth: rms z by distance into the tunnel

| case | 0.5 km | 1 km | 2 km | 3 km | 4 km | C |
|---|---|---|---|---|---|---|
| floor/free | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| floor/stop_and_go | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| realistic/free | 0.8 | 1.0 | 1.0 | 0.9 | 0.9 | 0.8 |
| realistic/stop_and_go | 1.0 | 0.7 | 0.5 | 0.4 | 0.4 | 0.2 |
| gps_speed/free | 1.0 | 0.9 | 0.9 | 0.8 | 0.8 | 0.7 |
| gps_speed/stop_and_go | 0.9 | 0.6 | 0.4 | 0.3 | 0.3 | 0.2 |
| acc_drift/free | 0.5 | 0.7 | 0.7 | 0.7 | 0.7 | 0.7 |
| acc_drift/stop_and_go | 0.7 | 0.6 | 0.5 | 0.5 | 0.5 | 0.2 |
| cal_pitch_0.1/free | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cal_pitch_0.1/stop_and_go | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cal_yaw_2/free | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cal_yaw_2/stop_and_go | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ladder_2km/flat/free | 0.8 | 1.0 | – | – | – | 1.0 |
| ladder_2km/flat/stop_and_go | 0.7 | 0.6 | – | – | – | 0.4 |
| ladder_5km/climb3/free | 0.7 | 0.8 | 0.9 | 0.9 | 0.8 | 0.8 |
| ladder_5km/climb3/stop_and_go | 0.7 | 0.6 | 0.5 | 0.4 | 0.4 | 0.3 |
| ladder_5km/underwater/free | 1.0 | 1.3 | 1.2 | 0.5 | 0.2 | 0.3 |
| ladder_5km/underwater/stop_and_go | 1.7 | 1.1 | 0.3 | 0.2 | 0.4 | 0.3 |
