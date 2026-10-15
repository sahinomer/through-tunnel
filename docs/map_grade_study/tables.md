# Map-grade study: generated tables

Each run is evaluated with the map grade off and on (paired: identical drive, sensor data and GPS). Ideal = error-free sensors and GPS (one run); realistic = preset sensor and GPS errors, 20 runs (seeds 0–19). Cells with two values are **off / on**. § = the route estimator reached the route end D before C in that many runs (its error is then capped by the route length).

## Eisenhower Tunnel, I-70 (westbound)

### Free flow

Median dead-reckoning time from GPS loss to C: 125 s.

**Ideal sensors: error at C [m], map grade off → on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 0 → 0.3 | 0 → 0.0 | 0 → 0.3 | 1 → 1.3 | 336 → 335.6 |
| Steady climb 2 % (whole route) | 1555 → 1.0 | 0 → 0.0 | 0 → 0.3 | 1 → 1.3 | 336 → 335.6 |
| Climb in the tunnel +1 % | 744 → 0.4 | 729 → 0.9 | 738 → 0.6 | 731 → 1.4 | 336 → 335.6 |
| Climb in the tunnel +2 % | 1489 → 0.5 | 1457 → 1.9 | 1476 → 1.5 | 881 § → 1.8 | 336 → 335.6 |
| Climb in the tunnel +4 % | 2977 → 0.6 | 2913 → 4.3 | 2951 → 3.6 | 881 § → 3.6 | 336 → 335.6 |
| Descent in the tunnel −2 % | 1481 → 1.1 | 1453 → 1.3 | 1471 → 0.8 | 1471 → 1.6 | 336 → 335.6 |
| Underwater V 2 % | 683 → 0.6 | 651 → 2.9 | 670 → 2.6 | 670 → 3.0 | 336 → 335.6 |
| Underwater V 4 % | 1364 → 0.8 | 1301 → 7.6 | 1339 → 7.4 | 1339 → 7.6 | 336 → 335.6 |

**Realistic sensors: error at C [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 460 (773) / 460 (773) | 55 (76) / 55 (76) | 38 (60) / 38 (60) | 34 (55) / 34 (55) | 330 (362) / 330 (362) |
| Steady climb 2 % (whole route) | 1651 (2308) / 461 (772) | 55 (76) / 55 (76) | 38 (60) / 38 (60) | 34 (55) / 34 (55) | 330 (362) / 330 (362) |
| Climb in the tunnel +1 % | 844 (1504) / 459 (797) | 715 (786) / 54 (74) | 730 (780) / 37 (60) | 723 (771) / 33 (56) | 330 (362) / 330 (362) |
| Climb in the tunnel +2 % | 1584 (2243) / 459 (822) | 1438 (1514) / 53 (75) | 1468 (1518) / 36 (60) | 881 (881) §20 / 33 (57) | 330 (362) / 330 (362) |
| Climb in the tunnel +4 % | 3070 (3725) / 460 (872) | 2894 (2970) / 51 (79) | 2943 (2992) / 34 (60) | 881 (881) §20 / 33 (59) | 330 (362) / 330 (362) |
| Descent in the tunnel −2 % | 1398 (1825) / 460 (725) | 1457 (1502) / 55 (80) | 1477 (1514) / 39 (60) | 1478 (1514) / 35 (53) | 330 (362) / 330 (362) |
| Underwater V 2 % | 598 (1251) / 366 (647) | 657 (706) / 41 (54) | 678 (718) / 24 (43) | 679 (717) / 22 (38) | 330 (362) / 330 (362) |
| Underwater V 4 % | 1270 (1762) / 293 (503) | 1306 (1353) / 33 (40) | 1343 (1387) / 17 (37) | 1344 (1387) / 13 (27) | 330 (362) / 330 (362) |

**Realistic sensors: maximum error in the tunnel [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 460 (773) / 460 (773) | 55 (76) / 55 (76) | 38 (60) / 38 (60) | 34 (55) / 34 (55) | 330 (362) / 330 (362) |
| Steady climb 2 % (whole route) | 1650 (2307) / 461 (772) | 55 (76) / 55 (76) | 38 (60) / 38 (60) | 34 (55) / 34 (55) | 330 (362) / 330 (362) |
| Climb in the tunnel +1 % | 843 (1504) / 459 (797) | 715 (786) / 54 (73) | 730 (779) / 37 (60) | 723 (770) / 33 (56) | 330 (362) / 330 (362) |
| Climb in the tunnel +2 % | 1584 (2242) / 459 (822) | 1438 (1514) / 53 (75) | 1468 (1517) / 36 (60) | 1159 (1180) §20 / 33 (57) | 330 (362) / 330 (362) |
| Climb in the tunnel +4 % | 3070 (3724) / 460 (872) | 2894 (2969) / 51 (79) | 2942 (2992) / 34 (60) | 1584 (1596) §20 / 33 (59) | 330 (362) / 330 (362) |
| Descent in the tunnel −2 % | 1398 (1824) / 460 (725) | 1457 (1502) / 55 (80) | 1477 (1514) / 39 (60) | 1478 (1513) / 35 (53) | 330 (362) / 330 (362) |
| Underwater V 2 % | 605 (1251) / 366 (647) | 657 (706) / 41 (54) | 678 (718) / 23 (43) | 679 (717) / 22 (38) | 330 (362) / 330 (362) |
| Underwater V 4 % | 1275 (1762) / 293 (503) | 1307 (1353) / 34 (41) | 1343 (1387) / 18 (37) | 1344 (1387) / 17 (27) | 330 (362) / 330 (362) |

**Realistic sensors: paired change of the error at C from switching the grade on [m], median [min, max]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] |
| Steady climb 2 % (whole route) | -1490 [-1556, -186] | +0 [-0, +0] | +0 [-0, +0] | +0 [-0, +0] | +0 [+0, +0] |
| Climb in the tunnel +1 % | -690 [-741, +617] | -682 [-728, -573] | -715 [-737, -604] | -715 [-731, -602] | +0 [+0, +0] |
| Climb in the tunnel +2 % | -1415 [-1481, -122] | -1410 [-1455, -1295] | -1453 [-1474, -1342] | -848 [-878, -815] | +0 [+0, +0] |
| Climb in the tunnel +4 % | -2857 [-2961, -1611] | -2853 [-2909, -2737] | -2919 [-2946, -2816] | -848 [-876, -815] | +0 [+0, +0] |
| Descent in the tunnel −2 % | -1189 [-1408, +38] | -1428 [-1451, -1251] | -1452 [-1467, -1364] | -1457 [-1470, -1369] | +0 [+0, +0] |
| Underwater V 2 % | -469 [-886, +533] | -641 [-668, -485] | -659 [-690, -577] | -664 [-690, -580] | +0 [+0, +0] |
| Underwater V 4 % | -1153 [-1505, -57] | -1287 [-1331, -1144] | -1321 [-1372, -1256] | -1324 [-1374, -1265] | +0 [+0, +0] |

**Realistic sensors, map grade on: error at C minus the same run on the flat road without grade [m], median [p10, p90]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu |
|---|---|---|---|---|
| Steady climb 2 % (whole route) | -1 [-1, +1] | -0 [-0, +0] | -0 [-0, +0] | +0 [-0, +0] |
| Climb in the tunnel +1 % | +2 [-0, +24] | -0 [-1, +2] | -0 [-1, +1] | +0 [-1, +1] |
| Climb in the tunnel +2 % | +4 [-1, +49] | -1 [-2, +4] | -0 [-2, +3] | -0 [-2, +3] |
| Climb in the tunnel +4 % | +7 [-2, +99] | -1 [-5, +8] | -1 [-5, +6] | -1 [-6, +7] |
| Descent in the tunnel −2 % | -3 [-48, +0] | +0 [-3, +2] | +0 [-2, +2] | -0 [-2, +2] |
| Underwater V 2 % | -94 [-155, -12] | -13 [-22, -2] | -10 [-18, -0] | -10 [-20, -0] |
| Underwater V 4 % | -171 [-285, -22] | -22 [-38, -2] | -17 [-34, +1] | -19 [-37, +3] |

**Realistic sensors: exit-announcement timing, median |error| [s], off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 14.6 / 14.6 | 1.9 / 1.9 | 1.3 / 1.3 | 1.3 / 1.3 | 12.4 / 12.4 |
| Steady climb 2 % (whole route) | 31.3 / 14.6 | 1.9 / 1.9 | 1.3 / 1.3 | 1.3 / 1.3 | 12.4 / 12.4 |
| Climb in the tunnel +1 % | 20.0 / 14.6 | 17.9 / 1.9 | 18.3 / 1.2 | 18.3 / 1.3 | 12.4 / 12.4 |
| Climb in the tunnel +2 % | 30.2 / 14.6 | 28.5 / 1.8 | 29.1 / 1.2 | 29.0 / 1.2 | 12.4 / 12.4 |
| Climb in the tunnel +4 % | 42.5 / 14.6 | 41.3 / 1.7 | 41.8 / 1.1 | 41.8 / 1.2 | 12.4 / 12.4 |
| Descent in the tunnel −2 % | 18.0 / 14.7 | 18.0 / 1.9 | 18.0 / 1.3 | 22.9 / 1.3 | 12.4 / 12.4 |
| Underwater V 2 % | 17.4 / 12.1 | 17.9 / 1.2 | 17.9 / 0.9 | 18.7 / 0.9 | 12.4 / 12.4 |
| Underwater V 4 % | 17.9 / 8.6 | 17.9 / 0.6 | 18.0 / 0.4 | 21.7 / 0.4 | 12.4 / 12.4 |

### Stop-and-go traffic (T3)

Median dead-reckoning time from GPS loss to C: 456 s.

**Ideal sensors: error at C [m], map grade off → on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 2 → 1.7 | 7 → 7.1 | 7 → 7.0 | 7 → 6.8 | 881 § → 881.3 § |
| Climb in the tunnel +2 % | 21679 → 1.4 | 20876 → 42.2 | 20987 → 41.5 | 881 § → 41.3 | 881 § → 881.3 § |
| Descent in the tunnel −2 % | 1987 → 10.5 | 1955 → 2.9 | 1967 → 2.9 | 1967 → 3.1 | 881 § → 881.3 § |
| Underwater V 4 % | 4722 → 9.0 | 5085 → 2.4 | 5071 → 2.2 | 881 § → 2.6 | 881 § → 881.3 § |

**Realistic sensors: error at C [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 1682 (8438) / 1682 (8438) | 142 (596) / 142 (596) | 118 (532) / 118 (532) | 115 (530) §1 / 115 (530) §1 | 881 (881) §20 / 881 (881) §20 |
| Climb in the tunnel +2 % | 20787 (30384) / 2741 (16164) | 19021 (25983) / 170 (1310) | 19100 (26203) / 126 (1013) | 881 (881) §20 / 122 (881) §3 | 881 (881) §20 / 881 (881) §20 |
| Descent in the tunnel −2 % | 2083 (2299) / 1194 (2764) | 2087 (2232) / 126 (293) | 2099 (2242) / 103 (272) | 2100 (2242) / 89 (268) | 881 (881) §20 / 881 (881) §20 |
| Underwater V 4 % | 5477 (9734) / 694 (2114) | 5546 (7843) / 78 (276) | 5534 (7832) / 46 (123) | 881 (881) §20 / 22 (117) | 881 (881) §20 / 881 (881) §20 |

**Realistic sensors: maximum error in the tunnel [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 1682 (8437) / 1682 (8437) | 142 (596) / 142 (596) | 118 (532) / 118 (532) | 115 (530) §1 / 115 (530) §1 | 1622 (2017) §20 / 1622 (2017) §20 |
| Climb in the tunnel +2 % | 20787 (30383) / 2740 (16159) | 19019 (25981) / 170 (1309) | 19098 (26201) / 126 (1012) | 2599 (2745) §20 / 122 (908) §3 | 1622 (2017) §20 / 1622 (2017) §20 |
| Descent in the tunnel −2 % | 2083 (2299) / 1369 (3014) | 2086 (2232) / 131 (357) | 2099 (2242) / 113 (323) | 2100 (2242) / 105 (321) | 1622 (2017) §20 / 1622 (2017) §20 |
| Underwater V 4 % | 5477 (9734) / 694 (2112) | 5546 (7842) / 78 (276) | 5532 (7831) / 51 (123) | 1396 (1498) §20 / 39 (117) | 1622 (2017) §20 / 1622 (2017) §20 |

**Realistic sensors: paired change of the error at C from switching the grade on [m], median [min, max]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] |
| Climb in the tunnel +2 % | -15122 [-21283, -7479] | -18919 [-28684, -14458] | -19037 [-28833, -14599] | -759 [-868, +0] | +0 [+0, +0] |
| Descent in the tunnel −2 % | -1002 [-1640, +1763] | -1915 [-2233, -1381] | -1965 [-2247, -1425] | -1974 [-2253, -1426] | +0 [+0, +0] |
| Underwater V 4 % | -4732 [-11623, -2360] | -5104 [-10293, -2339] | -5427 [-10339, -2329] | -859 [-879, -263] | +0 [+0, +0] |

**Realistic sensors, map grade on: error at C minus the same run on the flat road without grade [m], median [p10, p90]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu |
|---|---|---|---|---|
| Climb in the tunnel +2 % | +1384 [+1, +7750] | +24 [-0, +695] | +23 [+1, +475] | +20 [+1, +210] |
| Descent in the tunnel −2 % | -939 [-6317, +1] | -18 [-268, +1] | -15 [-234, -1] | -17 [-234, -2] |
| Underwater V 4 % | -1152 [-7290, -255] | -61 [-378, +10] | -53 [-407, +5] | -65 [-362, +10] |

**Realistic sensors: exit-announcement timing, median |error| [s], off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 110.6 / 110.6 | 15.3 / 15.3 | 12.3 / 12.3 | 12.3 / 12.3 | 204.7 / 204.7 |
| Climb in the tunnel +2 % | 283.4 / 110.7 | 278.8 / 14.6 | 279.7 / 11.9 | 279.8 / 11.9 | 204.7 / 204.7 |
| Descent in the tunnel −2 % | 40.9 / 110.6 | 40.9 / 15.2 | 40.9 / 12.5 | 48.4 / 12.5 | 204.7 / 204.7 |
| Underwater V 4 % | 57.6 / 25.1 | 65.7 / 3.6 | 65.4 / 1.7 | 65.4 / 1.7 | 204.7 / 204.7 |

## Seattle SR 99 Tunnel (northbound)

### Free flow

Median dead-reckoning time from GPS loss to C: 151 s.

**Ideal sensors: error at C [m], map grade off → on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 0 → 0.1 | 0 → 0.4 | 0 → 0.4 | 1 → 0.5 | 1 → 0.9 |
| Steady climb 2 % (whole route) | 2188 → 0.5 | 0 → 0.4 | 0 → 0.4 | 1 → 0.5 | 1 → 0.9 |
| Climb in the tunnel +1 % | 1050 → 0.4 | 1029 → 0.4 | 1044 → 0.5 | 889 § → 0.4 | 1 → 0.9 |
| Climb in the tunnel +2 % | 2100 → 0.9 | 2058 → 0.8 | 2088 → 0.9 | 889 § → 0.6 | 1 → 0.9 |
| Climb in the tunnel +4 % | 4198 → 2.8 | 4115 → 2.1 | 4174 → 2.4 | 889 § → 2.1 | 1 → 0.9 |
| Descent in the tunnel −2 % | 1878 → 0.2 | 1861 → 0.5 | 1880 → 0.6 | 1878 → 0.5 | 1 → 0.9 |
| Underwater V 2 % | 969 → 0.3 | 928 → 0.7 | 957 → 0.7 | 960 → 0.4 | 1 → 0.9 |
| Underwater V 4 % | 1713 → 0.7 | 1675 → 1.1 | 1696 → 1.2 | 1678 → 0.6 | 1 → 0.9 |

**Realistic sensors: error at C [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 640 (1070) / 640 (1070) | 65 (116) / 65 (116) | 61 (93) / 61 (93) | 32 (72) / 32 (72) | 20 (56) / 20 (56) |
| Steady climb 2 % (whole route) | 2371 (3259) / 640 (1070) | 64 (116) / 64 (116) | 61 (93) / 61 (93) | 32 (72) / 32 (72) | 20 (56) / 20 (56) |
| Climb in the tunnel +1 % | 1226 (2116) / 646 (1122) | 1035 (1097) / 65 (115) | 1046 (1098) / 61 (93) | 889 (889) §20 / 32 (73) | 20 (56) / 20 (56) |
| Climb in the tunnel +2 % | 2276 (3166) / 653 (1174) | 2072 (2134) / 65 (114) | 2098 (2140) / 61 (93) | 889 (889) §20 / 32 (74) | 20 (56) / 20 (56) |
| Climb in the tunnel +4 % | 4380 (5264) / 666 (1281) | 4139 (4212) / 64 (111) | 4199 (4241) / 62 (93) | 889 (889) §20 / 32 (77) | 20 (56) / 20 (56) |
| Descent in the tunnel −2 % | 1816 (2166) / 630 (968) | 1869 (1906) / 64 (117) | 1884 (1910) / 61 (95) | 1883 (1909) / 31 (71) | 20 (56) / 20 (56) |
| Underwater V 2 % | 826 (1795) / 489 (865) | 949 (1020) / 50 (94) | 975 (1032) / 51 (87) | 972 (1025) / 20 (43) | 20 (56) / 20 (56) |
| Underwater V 4 % | 1650 (1972) / 350 (633) | 1690 (1723) / 42 (91) | 1708 (1734) / 46 (86) | 1684 (1714) / 13 (19) | 20 (56) / 20 (56) |

**Realistic sensors: maximum error in the tunnel [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 640 (1069) / 640 (1069) | 65 (116) / 65 (116) | 61 (93) / 61 (93) | 32 (72) / 32 (72) | 34 (65) / 34 (65) |
| Steady climb 2 % (whole route) | 2370 (3257) / 639 (1070) | 64 (116) / 64 (116) | 61 (93) / 61 (93) | 32 (72) / 32 (72) | 34 (65) / 34 (65) |
| Climb in the tunnel +1 % | 1226 (2115) / 646 (1121) | 1034 (1096) / 65 (115) | 1045 (1097) / 61 (93) | 987 (1017) §20 / 32 (73) | 34 (65) / 34 (65) |
| Climb in the tunnel +2 % | 2275 (3165) / 652 (1174) | 2071 (2133) / 65 (114) | 2097 (2139) / 61 (93) | 1428 (1444) §20 / 32 (74) | 34 (65) / 34 (65) |
| Climb in the tunnel +4 % | 4378 (5262) / 666 (1280) | 4137 (4210) / 64 (111) | 4197 (4239) / 62 (93) | 1847 (1853) §20 / 32 (77) | 34 (65) / 34 (65) |
| Descent in the tunnel −2 % | 1815 (2166) / 630 (967) | 1868 (1906) / 64 (117) | 1884 (1909) / 61 (94) | 1882 (1909) / 31 (71) | 34 (65) / 34 (65) |
| Underwater V 2 % | 840 (1795) / 489 (864) | 949 (1020) / 50 (94) | 975 (1032) / 51 (87) | 972 (1025) / 20 (43) | 34 (65) / 34 (65) |
| Underwater V 4 % | 1673 (1972) / 349 (633) | 1704 (1733) / 44 (91) | 1723 (1747) / 45 (86) | 1722 (1746) / 14 (22) | 34 (65) / 34 (65) |

**Realistic sensors: paired change of the error at C from switching the grade on [m], median [min, max]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] |
| Steady climb 2 % (whole route) | -2130 [-2214, -291] | +0 [-0, +0] | +0 [-0, +0] | +0 [-0, +0] | +0 [+0, +0] |
| Climb in the tunnel +1 % | -987 [-1045, +845] | -997 [-1039, -819] | -996 [-1051, -867] | -857 [-888, -789] | +0 [+0, +0] |
| Climb in the tunnel +2 % | -1990 [-2091, -204] | -2026 [-2079, -1845] | -2045 [-2102, -1912] | -857 [-888, -788] | +0 [+0, +0] |
| Climb in the tunnel +4 % | -3992 [-4196, -2299] | -4088 [-4156, -3899] | -4141 [-4202, -4001] | -857 [-888, -786] | +0 [+0, +0] |
| Descent in the tunnel −2 % | -1295 [-1692, -21] | -1809 [-1863, -1617] | -1828 [-1883, -1729] | -1858 [-1886, -1729] | +0 [+0, +0] |
| Underwater V 2 % | -648 [-1331, +665] | -892 [-992, -681] | -919 [-986, -793] | -962 [-998, -802] | +0 [+0, +0] |
| Underwater V 4 % | -1479 [-1681, -216] | -1638 [-1706, -1563] | -1657 [-1699, -1601] | -1675 [-1704, -1606] | +0 [+0, +0] |

**Realistic sensors, map grade on: error at C minus the same run on the flat road without grade [m], median [p10, p90]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu |
|---|---|---|---|---|
| Steady climb 2 % (whole route) | +0 [-0, +0] | -0 [-0, +0] | +0 [-0, +0] | +0 [-0, +0] |
| Climb in the tunnel +1 % | +3 [-0, +47] | +0 [-1, +1] | +0 [-1, +0] | -0 [-1, +1] |
| Climb in the tunnel +2 % | +6 [-1, +95] | +0 [-2, +1] | +0 [-1, +1] | -0 [-2, +1] |
| Climb in the tunnel +4 % | +13 [-2, +192] | +0 [-4, +4] | +0 [-3, +3] | +0 [-5, +4] |
| Descent in the tunnel −2 % | -5 [-93, +0] | -0 [-1, +1] | +0 [-1, +1] | -0 [-1, +2] |
| Underwater V 2 % | -166 [-289, -23] | -10 [-43, -0] | -6 [-28, -0] | -15 [-29, -1] |
| Underwater V 4 % | -295 [-482, -38] | -12 [-69, -1] | -8 [-50, +0] | -23 [-54, +0] |

**Realistic sensors: exit-announcement timing, median |error| [s], off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 18.5 / 18.5 | 1.5 / 1.5 | 1.4 / 1.4 | 1.2 / 1.2 | 0.8 / 0.8 |
| Steady climb 2 % (whole route) | 45.0 / 18.5 | 1.5 / 1.5 | 1.4 / 1.4 | 1.2 / 1.2 | 0.8 / 0.8 |
| Climb in the tunnel +1 % | 30.0 / 18.5 | 26.9 / 1.5 | 27.2 / 1.3 | 28.1 / 1.2 | 0.8 / 0.8 |
| Climb in the tunnel +2 % | 43.5 / 18.5 | 41.3 / 1.5 | 41.9 / 1.3 | 42.7 / 1.2 | 0.8 / 0.8 |
| Climb in the tunnel +4 % | 59.0 / 18.5 | 57.6 / 1.4 | 58.2 / 1.2 | 58.2 / 1.2 | 0.8 / 0.8 |
| Descent in the tunnel −2 % | 18.7 / 18.4 | 18.7 / 1.6 | 18.7 / 1.4 | 25.5 / 1.2 | 0.8 / 0.8 |
| Underwater V 2 % | 18.6 / 14.6 | 18.6 / 1.0 | 18.6 / 0.9 | 21.4 / 0.8 | 0.8 / 0.8 |
| Underwater V 4 % | 18.7 / 8.9 | 18.6 / 0.5 | 18.6 / 0.4 | 24.5 / 0.5 | 0.8 / 0.8 |

### Stop-and-go traffic (T3)

Median dead-reckoning time from GPS loss to C: 486 s.

**Ideal sensors: error at C [m], map grade off → on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 2 → 1.7 | 5 → 4.7 | 4 → 4.4 | 4 → 4.1 | 889 § → 888.9 § |
| Climb in the tunnel +2 % | 23722 → 6.7 | 23168 → 4.7 | 23279 → 4.7 | 889 § → 4.4 | 889 § → 888.9 § |
| Descent in the tunnel −2 % | 2158 → 0.3 | 2138 → 4.2 | 2149 → 3.8 | 2152 → 3.4 | 889 § → 888.9 § |
| Underwater V 4 % | 5110 → 7.4 | 5355 → 13.1 | 5341 → 11.6 | 889 § → 11.1 | 889 § → 888.9 § |

**Realistic sensors: error at C [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 2036 (9751) / 2036 (9751) | 228 (450) / 228 (450) | 199 (433) / 199 (433) | 86 (366) / 86 (366) | 889 (889) §20 / 889 (889) §20 |
| Climb in the tunnel +2 % | 22551 (35659) / 3590 (18902) | 21099 (29251) / 228 (641) | 21305 (29388) / 199 (618) | 889 (889) §20 / 93 (597) §1 | 889 (889) §20 / 889 (889) §20 |
| Descent in the tunnel −2 % | 2247 (2523) / 1349 (3057) | 2234 (2423) / 227 (286) | 2253 (2426) / 198 (279) | 2258 (2424) / 79 (234) | 889 (889) §20 / 889 (889) §20 |
| Underwater V 4 % | 6214 (11050) / 779 (1897) | 6137 (9330) / 181 (624) | 6121 (9318) / 155 (320) | 889 (889) §20 / 56 (251) | 889 (889) §20 / 889 (889) §20 |

**Realistic sensors: maximum error in the tunnel [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 2036 (9750) / 2036 (9750) | 228 (450) / 228 (450) | 199 (433) / 199 (433) | 86 (366) / 86 (366) | 1865 (2152) §20 / 1865 (2152) §20 |
| Climb in the tunnel +2 % | 22548 (35657) / 3589 (18900) | 21096 (29251) / 228 (640) | 21302 (29388) / 199 (618) | 2721 (2895) §20 / 93 (597) §1 | 1865 (2152) §20 / 1865 (2152) §20 |
| Descent in the tunnel −2 % | 2246 (2523) / 1539 (3280) | 2234 (2422) / 227 (359) | 2253 (2426) / 198 (350) | 2258 (2424) / 83 (300) | 1865 (2152) §20 / 1865 (2152) §20 |
| Underwater V 4 % | 6212 (11050) / 779 (1896) | 6135 (9327) / 181 (624) | 6119 (9316) / 155 (320) | 1443 (1575) §20 / 58 (250) | 1865 (2152) §20 / 1865 (2152) §20 |

**Realistic sensors: paired change of the error at C from switching the grade on [m], median [min, max]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] |
| Climb in the tunnel +2 % | -16886 [-23392, -8222] | -20860 [-32813, -16696] | -21081 [-32767, -16733] | -796 [-885, +0] | +0 [+0, +0] |
| Descent in the tunnel −2 % | -992 [-1763, +1815] | -2026 [-2369, -1665] | -2063 [-2348, -1683] | -2179 [-2413, -1685] | +0 [+0, +0] |
| Underwater V 4 % | -5347 [-13964, -2366] | -5938 [-11671, -2378] | -5923 [-11720, -2383] | -833 [-888, -465] | +0 [+0, +0] |

**Realistic sensors, map grade on: error at C minus the same run on the flat road without grade [m], median [p10, p90]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu |
|---|---|---|---|---|
| Climb in the tunnel +2 % | +1779 [-4, +9254] | +5 [-1, +197] | +4 [-0, +198] | +6 [+1, +195] |
| Descent in the tunnel −2 % | -1118 [-7215, +4] | -4 [-158, +0] | -5 [-168, +1] | -7 [-174, -2] |
| Underwater V 4 % | -1270 [-8453, -139] | -7 [-196, +127] | -7 [-214, +73] | -17 [-251, +80] |

**Realistic sensors: exit-announcement timing, median |error| [s], off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 126.4 / 126.4 | 11.2 / 11.2 | 9.8 / 9.8 | 9.4 / 9.4 | 216.8 / 216.8 |
| Climb in the tunnel +2 % | 306.1 / 126.1 | 302.8 / 10.3 | 305.0 / 9.5 | 301.3 / 8.8 | 216.8 / 216.8 |
| Descent in the tunnel −2 % | 38.6 / 126.9 | 38.6 / 11.2 | 38.6 / 10.1 | 46.5 / 9.7 | 216.8 / 216.8 |
| Underwater V 4 % | 64.2 / 23.3 | 68.3 / 4.5 | 67.9 / 3.2 | 67.1 / 3.9 | 216.8 / 216.8 |

## Synthetic demo route

### Free flow

Median dead-reckoning time from GPS loss to C: 104 s.

**Ideal sensors: error at C [m], map grade off → on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 0 → 0.0 | 0 → 0.1 | 0 → 0.0 | 0 → 0.3 | 17 → 17.3 |
| Steady climb 2 % (whole route) | 962 → 2.5 | 0 → 0.1 | 0 → 0.0 | 0 → 0.3 | 17 → 17.3 |
| Climb in the tunnel +1 % | 451 → 1.1 | 437 → 1.1 | 447 → 1.2 | 477 → 1.6 | 17 → 17.3 |
| Climb in the tunnel +2 % | 901 → 2.1 | 875 → 2.1 | 894 → 2.2 | 782 § → 2.7 | 17 → 17.3 |
| Climb in the tunnel +4 % | 1802 → 3.6 | 1749 → 3.8 | 1788 → 3.8 | 782 § → 4.6 | 17 → 17.3 |
| Descent in the tunnel −2 % | 901 → 2.7 | 874 → 2.6 | 894 → 2.6 | 869 → 2.5 | 17 → 17.3 |
| Underwater V 2 % | 455 → 1.0 | 429 → 1.0 | 448 → 1.0 | 483 → 0.7 | 17 → 17.3 |
| Underwater V 4 % | 909 → 1.5 | 857 → 1.5 | 895 → 1.5 | 858 → 0.8 | 17 → 17.3 |

**Realistic sensors: error at C [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 282 (463) / 282 (463) | 29 (56) / 29 (56) | 17 (37) / 17 (37) | 17 (40) / 17 (40) | 18 (45) / 18 (45) |
| Steady climb 2 % (whole route) | 1043 (1419) / 282 (461) | 29 (56) / 29 (56) | 17 (37) / 17 (37) | 17 (40) / 17 (40) | 18 (45) / 18 (45) |
| Climb in the tunnel +1 % | 525 (898) / 283 (468) | 433 (467) / 29 (57) | 445 (465) / 18 (36) | 475 (494) / 18 (39) | 18 (45) / 18 (45) |
| Climb in the tunnel +2 % | 976 (1348) / 285 (475) | 876 (907) / 29 (57) | 894 (912) / 19 (35) | 782 (782) §20 / 18 (38) | 18 (45) / 18 (45) |
| Climb in the tunnel +4 % | 1880 (2250) / 288 (499) | 1758 (1783) / 30 (58) | 1795 (1811) / 20 (37) | 782 (782) §20 / 18 (39) | 18 (45) / 18 (45) |
| Descent in the tunnel −2 % | 836 (1162) / 279 (437) | 893 (936) / 30 (55) | 906 (934) / 18 (38) | 879 (905) / 15 (40) | 18 (45) / 18 (45) |
| Underwater V 2 % | 393 (806) / 227 (391) | 444 (493) / 27 (47) | 459 (489) / 15 (28) | 495 (525) / 11 (29) | 18 (45) / 18 (45) |
| Underwater V 4 % | 849 (1258) / 193 (328) | 881 (922) / 21 (42) | 910 (943) / 14 (20) | 872 (901) / 8 (19) | 18 (45) / 18 (45) |

**Realistic sensors: maximum error in the tunnel [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 282 (463) / 282 (463) | 29 (56) / 29 (56) | 17 (37) / 17 (37) | 17 (40) / 17 (40) | 47 (56) / 47 (56) |
| Steady climb 2 % (whole route) | 1042 (1418) / 282 (461) | 29 (56) / 29 (56) | 17 (37) / 17 (37) | 17 (40) / 17 (40) | 47 (56) / 47 (56) |
| Climb in the tunnel +1 % | 524 (897) / 283 (468) | 433 (467) / 29 (57) | 445 (465) / 18 (36) | 475 (494) / 18 (39) | 47 (56) / 47 (56) |
| Climb in the tunnel +2 % | 975 (1347) / 284 (475) | 875 (907) / 29 (57) | 894 (912) / 19 (35) | 856 (865) §20 / 18 (38) | 47 (56) / 47 (56) |
| Climb in the tunnel +4 % | 1879 (2249) / 287 (499) | 1757 (1782) / 30 (58) | 1794 (1810) / 20 (37) | 1180 (1184) §20 / 18 (39) | 47 (56) / 47 (56) |
| Descent in the tunnel −2 % | 836 (1162) / 279 (437) | 892 (936) / 30 (55) | 905 (934) / 18 (38) | 879 (905) / 15 (40) | 47 (56) / 47 (56) |
| Underwater V 2 % | 397 (806) / 227 (391) | 444 (493) / 27 (47) | 459 (489) / 15 (28) | 495 (525) / 11 (29) | 47 (56) / 47 (56) |
| Underwater V 4 % | 849 (1258) / 193 (328) | 881 (922) / 23 (42) | 910 (943) / 14 (20) | 872 (901) / 9 (19) | 47 (56) / 47 (56) |

**Realistic sensors: paired change of the error at C from switching the grade on [m], median [min, max]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] |
| Steady climb 2 % (whole route) | -942 [-983, -26] | +0 [-0, +0] | +0 [-0, +0] | +0 [-0, +0] | +0 [+0, +0] |
| Climb in the tunnel +1 % | -429 [-453, +443] | -410 [-443, -306] | -429 [-453, -350] | -468 [-483, -377] | +0 [+0, +0] |
| Climb in the tunnel +2 % | -868 [-906, +32] | -852 [-887, -747] | -879 [-906, -797] | -764 [-781, -727] | +0 [+0, +0] |
| Climb in the tunnel +4 % | -1744 [-1812, -870] | -1737 [-1774, -1622] | -1781 [-1811, -1690] | -764 [-782, -726] | +0 [+0, +0] |
| Descent in the tunnel −2 % | -744 [-885, -11] | -863 [-888, -806] | -894 [-906, -827] | -867 [-879, -802] | +0 [+0, +0] |
| Underwater V 2 % | -314 [-586, +352] | -421 [-457, -366] | -448 [-467, -393] | -487 [-503, -424] | +0 [+0, +0] |
| Underwater V 4 % | -777 [-1072, -125] | -858 [-909, -798] | -899 [-932, -858] | -866 [-890, -823] | +0 [+0, +0] |

**Realistic sensors, map grade on: error at C minus the same run on the flat road without grade [m], median [p10, p90]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu |
|---|---|---|---|---|
| Steady climb 2 % (whole route) | -2 [-3, +3] | +0 [-0, +0] | +0 [-0, +0] | +0 [-0, +0] |
| Climb in the tunnel +1 % | +2 [-0, +11] | +0 [-1, +1] | +0 [-1, +2] | +1 [-1, +2] |
| Climb in the tunnel +2 % | +3 [-0, +22] | +1 [-2, +2] | +0 [-1, +3] | +1 [-2, +3] |
| Climb in the tunnel +4 % | +6 [+0, +45] | +1 [-4, +4] | +1 [-2, +5] | +2 [-4, +6] |
| Descent in the tunnel −2 % | -4 [-21, +0] | -1 [-3, +2] | -0 [-3, +2] | -0 [-4, +3] |
| Underwater V 2 % | -49 [-87, -9] | -5 [-19, -1] | -3 [-9, +1] | -4 [-10, +1] |
| Underwater V 4 % | -95 [-155, -15] | -8 [-33, -0] | -5 [-19, +1] | -7 [-21, +1] |

**Realistic sensors: exit-announcement timing, median |error| [s], off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 5.3 / 5.3 | 0.8 / 0.8 | 0.5 / 0.5 | 0.6 / 0.6 | 0.4 / 0.4 |
| Steady climb 2 % (whole route) | 21.7 / 5.3 | 0.8 / 0.8 | 0.5 / 0.5 | 0.6 / 0.6 | 0.4 / 0.4 |
| Climb in the tunnel +1 % | 11.7 / 5.3 | 9.6 / 0.8 | 9.9 / 0.5 | 12.8 / 0.6 | 0.4 / 0.4 |
| Climb in the tunnel +2 % | 19.5 / 5.3 | 16.9 / 0.8 | 17.6 / 0.5 | 20.7 / 0.6 | 0.4 / 0.4 |
| Climb in the tunnel +4 % | 33.3 / 5.3 | 31.3 / 0.8 | 32.3 / 0.6 | 30.2 / 0.6 | 0.4 / 0.4 |
| Descent in the tunnel −2 % | 19.4 / 5.3 | 19.4 / 0.8 | 19.4 / 0.4 | 22.3 / 0.6 | 0.4 / 0.4 |
| Underwater V 2 % | 16.5 / 4.0 | 18.9 / 0.6 | 19.3 / 0.4 | 19.3 / 0.4 | 0.4 / 0.4 |
| Underwater V 4 % | 19.3 / 2.9 | 19.4 / 0.4 | 19.4 / 0.3 | 21.3 / 0.3 | 0.4 / 0.4 |

### Stop-and-go traffic (T3)

Median dead-reckoning time from GPS loss to C: 364 s.

**Ideal sensors: error at C [m], map grade off → on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 1 → 1.3 | 4 → 4.1 | 4 → 3.8 | 4 → 3.9 | 782 § → 781.8 § |
| Climb in the tunnel +2 % | 13356 → 4.9 | 12930 → 4.4 | 13008 → 4.4 | 782 § → 5.2 | 782 § → 781.8 § |
| Descent in the tunnel −2 % | 1234 → 25.3 | 1216 → 26.6 | 1224 → 26.6 | 1203 → 28.8 | 782 § → 781.8 § |
| Underwater V 4 % | 3903 → 3.6 | 4141 → 3.6 | 4129 → 3.6 | 782 § → 4.5 | 782 § → 781.8 § |

**Realistic sensors: error at C [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 958 (4508) / 958 (4508) | 88 (277) / 88 (277) | 58 (242) / 58 (242) | 52 (267) / 52 (267) | 782 (782) §19 / 782 (782) §19 |
| Climb in the tunnel +2 % | 12540 (17652) / 1671 (9841) | 11016 (15717) / 75 (381) | 11159 (15729) / 55 (339) | 782 (782) §20 / 52 (361) | 782 (782) §19 / 782 (782) §19 |
| Descent in the tunnel −2 % | 1164 (1477) / 828 (1783) | 1214 (1366) / 82 (171) | 1225 (1377) / 55 (143) | 1194 (1346) / 41 (150) | 782 (782) §19 / 782 (782) §19 |
| Underwater V 4 % | 3455 (5288) / 295 (1274) | 3914 (5309) / 42 (84) | 3902 (5316) / 24 (51) | 782 (782) §20 / 13 (27) | 782 (782) §19 / 782 (782) §19 |

**Realistic sensors: maximum error in the tunnel [m], median (p90), off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 958 (4507) / 958 (4507) | 88 (277) / 88 (277) | 58 (242) / 58 (242) | 52 (267) / 52 (267) | 1321 (1516) §19 / 1321 (1516) §19 |
| Climb in the tunnel +2 % | 12539 (17648) / 1670 (9838) | 11013 (15717) / 75 (381) | 11156 (15728) / 55 (339) | 1803 (1917) §20 / 52 (361) | 1321 (1516) §19 / 1321 (1516) §19 |
| Descent in the tunnel −2 % | 1163 (1477) / 849 (1878) | 1214 (1366) / 85 (211) | 1225 (1377) / 56 (192) | 1193 (1345) / 48 (211) | 1321 (1516) §19 / 1321 (1516) §19 |
| Underwater V 4 % | 3454 (5285) / 309 (1273) | 3912 (5306) / 47 (86) | 3900 (5313) / 28 (54) | 1137 (1224) §20 / 16 (53) | 1321 (1516) §19 / 1321 (1516) §19 |

**Realistic sensors: paired change of the error at C from switching the grade on [m], median [min, max]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] | +0 [+0, +0] |
| Climb in the tunnel +2 % | -8740 [-12611, -4445] | -10962 [-16872, -7364] | -11125 [-17088, -7424] | -730 [-776, -63] | +0 [+0, +0] |
| Descent in the tunnel −2 % | -629 [-1045, +1509] | -1125 [-1395, -782] | -1166 [-1407, -803] | -1144 [-1380, -735] | +0 [+0, +0] |
| Underwater V 4 % | -3043 [-6256, -1506] | -3891 [-5870, -1435] | -3881 [-5914, -1410] | -769 [-781, -649] | +0 [+0, +0] |

**Realistic sensors, map grade on: error at C minus the same run on the flat road without grade [m], median [p10, p90]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu |
|---|---|---|---|---|
| Climb in the tunnel +2 % | +845 [+6, +4261] | +3 [-51, +94] | +5 [-43, +78] | +6 [-53, +79] |
| Descent in the tunnel −2 % | -505 [-3530, -7] | -6 [-111, +7] | -5 [-70, +9] | -9 [-94, +11] |
| Underwater V 4 % | -812 [-3964, -111] | -26 [-224, +1] | -29 [-198, +1] | -37 [-254, +1] |

**Realistic sensors: exit-announcement timing, median |error| [s], off / on:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 81.6 / 81.6 | 5.0 / 5.0 | 4.7 / 4.7 | 8.8 / 8.8 | 178.7 / 178.7 |
| Climb in the tunnel +2 % | 225.6 / 81.4 | 219.5 / 5.1 | 220.9 / 3.2 | 211.1 / 5.1 | 178.7 / 178.7 |
| Descent in the tunnel −2 % | 40.9 / 81.8 | 40.9 / 7.0 | 40.9 / 6.4 | 44.8 / 8.4 | 178.7 / 178.7 |
| Underwater V 4 % | 38.8 / 15.6 | 49.6 / 1.9 | 49.7 / 1.3 | 51.2 / 0.8 | 178.7 / 178.7 |
