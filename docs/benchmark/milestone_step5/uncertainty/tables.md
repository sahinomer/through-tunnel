# Uncertainty consistency: tables

Commit `0b4ee46`, 2026-10-17 16:19 UTC; 20 seeds per case. Coverage = share of runs whose along-track error lies within ±1σ / ±2σ of the filter's own uncertainty (honest: ~68 % / ~95 %). rms z = rms of error/σ (honest: ~1; > 1 = overconfident). |err| / σ: medians [m].

## route_kf

### At the announcement point (true time) and at C

| case | announce 1σ / 2σ | announce rms z | announce |err| / σ | C 1σ / 2σ | C rms z | C |err| / σ | outage samples 1σ / 2σ |
|---|---|---|---|---|---|---|---|
| floor/free | 100 % / 100 % | 0.0 | 0 / 134 | 100 % / 100 % | 0.0 | 1 / 153 | 100 % / 100 % |
| floor/stop_and_go | 100 % / 100 % | 0.0 | 3 / 1594 | 100 % / 100 % | 0.0 | 3 / 1800 | 100 % / 100 % |
| realistic/free | 70 % / 90 % | 1.0 | 66 / 157 | 70 % / 95 % | 1.0 | 80 / 178 | 74 % / 89 % |
| realistic/stop_and_go | 100 % / 100 % | 0.3 | 232 / 1698 | 100 % / 100 % | 0.2 | 241 / 1912 | 92 % / 98 % |
| gps_speed/free | 85 % / 100 % | 0.7 | 78 / 157 | 85 % / 100 % | 0.7 | 86 / 178 | 82 % / 96 % |
| gps_speed/stop_and_go | 100 % / 100 % | 0.2 | 159 / 1698 | 100 % / 100 % | 0.2 | 172 / 1912 | 96 % / 99 % |
| acc_drift/free | 90 % / 100 % | 0.7 | 85 / 134 | 90 % / 100 % | 0.7 | 92 / 153 | 90 % / 100 % |
| acc_drift/stop_and_go | 100 % / 100 % | 0.3 | 292 / 1594 | 100 % / 100 % | 0.2 | 306 / 1800 | 94 % / 100 % |
| cal_pitch_0.1/free | 100 % / 100 % | 0.0 | 0 / 134 | 100 % / 100 % | 0.0 | 0 / 153 | 100 % / 100 % |
| cal_pitch_0.1/stop_and_go | 100 % / 100 % | 0.0 | 3 / 1594 | 100 % / 100 % | 0.0 | 3 / 1800 | 100 % / 100 % |
| cal_yaw_2/free | 100 % / 100 % | 0.4 | 50 / 134 | 100 % / 100 % | 0.4 | 64 / 153 | 98 % / 100 % |
| cal_yaw_2/stop_and_go | 100 % / 100 % | 0.1 | 185 / 1594 | 100 % / 100 % | 0.1 | 203 / 1800 | 99 % / 100 % |
| ladder_2km/flat/free | 75 % / 85 % | 1.3 | 19 / 24 | 75 % / 85 % | 1.2 | 22 / 31 | 76 % / 90 % |
| ladder_2km/flat/stop_and_go | 95 % / 100 % | 0.5 | 56 / 310 | 95 % / 100 % | 0.4 | 65 / 389 | 91 % / 96 % |
| ladder_5km/climb3/free | 70 % / 95 % | 0.9 | 75 / 157 | 70 % / 95 % | 0.9 | 96 / 178 | 78 % / 93 % |
| ladder_5km/climb3/stop_and_go | 100 % / 100 % | 0.3 | 238 / 1698 | 100 % / 100 % | 0.2 | 319 / 1912 | 93 % / 100 % |
| ladder_5km/underwater/free | 100 % / 100 % | 0.3 | 27 / 157 | 100 % / 100 % | 0.3 | 40 / 178 | 81 % / 93 % |
| ladder_5km/underwater/stop_and_go | 100 % / 100 % | 0.3 | 308 / 1698 | 100 % / 100 % | 0.3 | 322 / 1912 | 89 % / 96 % |

### Growth: rms z by distance into the tunnel

| case | 0.5 km | 1 km | 2 km | 3 km | 4 km | C |
|---|---|---|---|---|---|---|
| floor/free | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| floor/stop_and_go | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| realistic/free | 0.9 | 1.1 | 1.2 | 1.2 | 1.1 | 1.0 |
| realistic/stop_and_go | 1.1 | 0.8 | 0.5 | 0.5 | 0.4 | 0.2 |
| gps_speed/free | 1.1 | 1.0 | 0.9 | 0.9 | 0.8 | 0.7 |
| gps_speed/stop_and_go | 1.0 | 0.5 | 0.4 | 0.3 | 0.2 | 0.2 |
| acc_drift/free | 0.5 | 0.6 | 0.7 | 0.7 | 0.7 | 0.7 |
| acc_drift/stop_and_go | 0.7 | 0.6 | 0.5 | 0.5 | 0.5 | 0.2 |
| cal_pitch_0.1/free | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cal_pitch_0.1/stop_and_go | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cal_yaw_2/free | 0.5 | 0.8 | 0.6 | 0.2 | 0.2 | 0.4 |
| cal_yaw_2/stop_and_go | 0.8 | 0.6 | 0.3 | 0.2 | 0.1 | 0.1 |
| ladder_2km/flat/free | 0.9 | 1.2 | – | – | – | 1.2 |
| ladder_2km/flat/stop_and_go | 0.8 | 0.6 | – | – | – | 0.4 |
| ladder_5km/climb3/free | 0.7 | 0.9 | 1.0 | 1.1 | 1.0 | 0.9 |
| ladder_5km/climb3/stop_and_go | 0.7 | 0.6 | 0.5 | 0.4 | 0.4 | 0.2 |
| ladder_5km/underwater/free | 1.1 | 1.4 | 1.4 | 0.6 | 0.2 | 0.3 |
| ladder_5km/underwater/stop_and_go | 1.8 | 1.2 | 0.3 | 0.2 | 0.4 | 0.3 |

## route_kf_yaw

### At the announcement point (true time) and at C

| case | announce 1σ / 2σ | announce rms z | announce |err| / σ | C 1σ / 2σ | C rms z | C |err| / σ | outage samples 1σ / 2σ |
|---|---|---|---|---|---|---|---|
| floor/free | 100 % / 100 % | 0.0 | 0 / 130 | 100 % / 100 % | 0.0 | 0 / 150 | 100 % / 100 % |
| floor/stop_and_go | 100 % / 100 % | 0.0 | 2 / 1577 | 100 % / 100 % | 0.0 | 3 / 1781 | 100 % / 100 % |
| realistic/free | 80 % / 95 % | 0.9 | 73 / 168 | 80 % / 95 % | 0.8 | 84 / 190 | 66 % / 94 % |
| realistic/stop_and_go | 100 % / 100 % | 0.3 | 274 / 1731 | 100 % / 100 % | 0.2 | 299 / 1947 | 91 % / 98 % |
| gps_speed/free | 80 % / 100 % | 0.7 | 87 / 169 | 85 % / 100 % | 0.7 | 97 / 191 | 71 % / 99 % |
| gps_speed/stop_and_go | 100 % / 100 % | 0.2 | 161 / 1731 | 100 % / 100 % | 0.2 | 175 / 1947 | 92 % / 100 % |
| acc_drift/free | 90 % / 100 % | 0.7 | 84 / 130 | 90 % / 100 % | 0.7 | 92 / 150 | 90 % / 100 % |
| acc_drift/stop_and_go | 100 % / 100 % | 0.3 | 291 / 1577 | 100 % / 100 % | 0.2 | 308 / 1781 | 94 % / 100 % |
| cal_pitch_0.1/free | 100 % / 100 % | 0.0 | 0 / 130 | 100 % / 100 % | 0.0 | 0 / 150 | 100 % / 100 % |
| cal_pitch_0.1/stop_and_go | 100 % / 100 % | 0.0 | 2 / 1577 | 100 % / 100 % | 0.0 | 3 / 1781 | 100 % / 100 % |
| cal_yaw_2/free | 100 % / 100 % | 0.0 | 0 / 130 | 100 % / 100 % | 0.0 | 0 / 150 | 100 % / 100 % |
| cal_yaw_2/stop_and_go | 100 % / 100 % | 0.0 | 1 / 1577 | 100 % / 100 % | 0.0 | 2 / 1781 | 100 % / 100 % |
| ladder_2km/flat/free | 60 % / 90 % | 1.1 | 18 / 27 | 60 % / 90 % | 1.1 | 18 / 34 | 66 % / 93 % |
| ladder_2km/flat/stop_and_go | 95 % / 100 % | 0.5 | 40 / 323 | 95 % / 100 % | 0.4 | 58 / 403 | 89 % / 97 % |
| ladder_5km/climb3/free | 80 % / 95 % | 0.8 | 86 / 168 | 80 % / 95 % | 0.8 | 108 / 190 | 72 % / 97 % |
| ladder_5km/climb3/stop_and_go | 100 % / 100 % | 0.3 | 275 / 1731 | 100 % / 100 % | 0.2 | 373 / 1947 | 93 % / 100 % |
| ladder_5km/underwater/free | 100 % / 100 % | 0.3 | 27 / 168 | 100 % / 100 % | 0.3 | 40 / 191 | 80 % / 95 % |
| ladder_5km/underwater/stop_and_go | 100 % / 100 % | 0.3 | 411 / 1731 | 100 % / 100 % | 0.3 | 490 / 1947 | 88 % / 97 % |

### Growth: rms z by distance into the tunnel

| case | 0.5 km | 1 km | 2 km | 3 km | 4 km | C |
|---|---|---|---|---|---|---|
| floor/free | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| floor/stop_and_go | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| realistic/free | 0.9 | 1.1 | 1.1 | 1.0 | 0.9 | 0.8 |
| realistic/stop_and_go | 1.0 | 0.7 | 0.5 | 0.4 | 0.4 | 0.2 |
| gps_speed/free | 1.0 | 0.9 | 0.9 | 0.8 | 0.7 | 0.7 |
| gps_speed/stop_and_go | 0.9 | 0.6 | 0.4 | 0.4 | 0.3 | 0.2 |
| acc_drift/free | 0.5 | 0.7 | 0.7 | 0.7 | 0.7 | 0.7 |
| acc_drift/stop_and_go | 0.7 | 0.6 | 0.5 | 0.5 | 0.5 | 0.2 |
| cal_pitch_0.1/free | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cal_pitch_0.1/stop_and_go | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cal_yaw_2/free | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cal_yaw_2/stop_and_go | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ladder_2km/flat/free | 0.9 | 1.1 | – | – | – | 1.1 |
| ladder_2km/flat/stop_and_go | 0.7 | 0.6 | – | – | – | 0.4 |
| ladder_5km/climb3/free | 0.7 | 0.9 | 1.0 | 0.9 | 0.8 | 0.8 |
| ladder_5km/climb3/stop_and_go | 0.7 | 0.6 | 0.5 | 0.4 | 0.4 | 0.2 |
| ladder_5km/underwater/free | 1.0 | 1.3 | 1.2 | 0.5 | 0.2 | 0.3 |
| ladder_5km/underwater/stop_and_go | 1.7 | 1.1 | 0.3 | 0.2 | 0.4 | 0.3 |

## route_kf_map

### At the announcement point (true time) and at C

| case | announce 1σ / 2σ | announce rms z | announce |err| / σ | C 1σ / 2σ | C rms z | C |err| / σ | outage samples 1σ / 2σ |
|---|---|---|---|---|---|---|---|
| floor/free | 100 % / 100 % | 0.2 | 2 / 13 | 100 % / 100 % | 0.1 | 2 / 18 | 100 % / 100 % |
| floor/stop_and_go | 100 % / 100 % | 0.1 | 6 / 54 | 100 % / 100 % | 0.1 | 8 / 82 | 100 % / 100 % |
| realistic/free | 75 % / 95 % | 1.0 | 8 / 14 | 80 % / 95 % | 0.9 | 12 / 19 | 82 % / 97 % |
| realistic/stop_and_go | 100 % / 100 % | 0.5 | 17 / 54 | 100 % / 100 % | 0.5 | 30 / 81 | 87 % / 96 % |
| gps_speed/free | 85 % / 100 % | 0.7 | 6 / 13 | 90 % / 100 % | 0.7 | 9 / 18 | 91 % / 99 % |
| gps_speed/stop_and_go | 100 % / 100 % | 0.1 | 5 / 54 | 100 % / 100 % | 0.1 | 6 / 81 | 95 % / 99 % |
| acc_drift/free | 95 % / 100 % | 0.6 | 6 / 13 | 95 % / 100 % | 0.6 | 9 / 18 | 91 % / 100 % |
| acc_drift/stop_and_go | 100 % / 100 % | 0.5 | 15 / 54 | 100 % / 100 % | 0.5 | 27 / 81 | 94 % / 99 % |
| cal_pitch_0.1/free | 100 % / 100 % | 0.2 | 2 / 13 | 100 % / 100 % | 0.1 | 2 / 18 | 100 % / 100 % |
| cal_pitch_0.1/stop_and_go | 100 % / 100 % | 0.1 | 6 / 54 | 100 % / 100 % | 0.1 | 8 / 82 | 100 % / 100 % |
| cal_yaw_2/free | 0 % / 0 % | 2.6 | 35 / 13 | 0 % / 0 % | 2.7 | 49 / 18 | 56 % / 75 % |
| cal_yaw_2/stop_and_go | 100 % / 100 % | 0.2 | 12 / 54 | 100 % / 100 % | 0.2 | 20 / 82 | 99 % / 100 % |
| ladder_2km/flat/free | 90 % / 100 % | 0.5 | 2 / 7 | 95 % / 100 % | 0.5 | 2 / 10 | 86 % / 99 % |
| ladder_2km/flat/stop_and_go | 100 % / 100 % | 0.4 | 3 / 19 | 100 % / 100 % | 0.4 | 9 / 34 | 93 % / 98 % |
| ladder_5km/climb3/free | 80 % / 95 % | 0.9 | 8 / 14 | 80 % / 95 % | 1.0 | 12 / 19 | 83 % / 98 % |
| ladder_5km/climb3/stop_and_go | 100 % / 100 % | 0.5 | 19 / 53 | 95 % / 100 % | 0.6 | 36 / 81 | 88 % / 97 % |
| ladder_5km/underwater/free | 70 % / 95 % | 1.0 | 8 / 14 | 65 % / 95 % | 1.0 | 11 / 19 | 80 % / 94 % |
| ladder_5km/underwater/stop_and_go | 70 % / 90 % | 1.1 | 43 / 54 | 50 % / 80 % | 29.3 | 78 / 70 | 77 % / 93 % |

### Growth: rms z by distance into the tunnel

| case | 0.5 km | 1 km | 2 km | 3 km | 4 km | C |
|---|---|---|---|---|---|---|
| floor/free | 0.0 | 0.0 | 0.5 | 0.5 | 0.5 | 0.1 |
| floor/stop_and_go | 0.0 | 0.0 | 0.3 | 0.1 | 0.3 | 0.1 |
| realistic/free | 0.9 | 1.1 | 0.7 | 0.7 | 0.8 | 0.9 |
| realistic/stop_and_go | 1.1 | 0.8 | 1.2 | 0.5 | 0.7 | 0.5 |
| gps_speed/free | 1.1 | 1.0 | 0.6 | 0.5 | 0.6 | 0.7 |
| gps_speed/stop_and_go | 1.0 | 0.5 | 0.4 | 0.1 | 0.3 | 0.1 |
| acc_drift/free | 0.5 | 0.6 | 0.5 | 0.8 | 0.6 | 0.6 |
| acc_drift/stop_and_go | 0.7 | 0.6 | 0.6 | 0.5 | 0.4 | 0.5 |
| cal_pitch_0.1/free | 0.0 | 0.0 | 0.5 | 0.5 | 0.5 | 0.1 |
| cal_pitch_0.1/stop_and_go | 0.0 | 0.0 | 0.3 | 0.1 | 0.3 | 0.1 |
| cal_yaw_2/free | 0.5 | 0.8 | 0.7 | 2.1 | 0.5 | 2.7 |
| cal_yaw_2/stop_and_go | 0.8 | 0.6 | 0.3 | 0.2 | 0.3 | 0.2 |
| ladder_2km/flat/free | 0.9 | 0.7 | – | – | – | 0.5 |
| ladder_2km/flat/stop_and_go | 0.8 | 0.5 | – | – | – | 0.4 |
| ladder_5km/climb3/free | 0.7 | 0.9 | 0.7 | 0.6 | 0.8 | 1.0 |
| ladder_5km/climb3/stop_and_go | 0.7 | 0.6 | 1.1 | 0.6 | 0.8 | 0.6 |
| ladder_5km/underwater/free | 1.1 | 1.4 | 0.6 | 0.6 | 0.8 | 1.0 |
| ladder_5km/underwater/stop_and_go | 1.8 | 1.2 | 1.3 | 0.4 | 0.8 | 29.3 |
