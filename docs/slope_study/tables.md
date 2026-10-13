# Road-slope study: generated tables

Preset drives; ideal = error-free sensors and GPS (one run); realistic = preset sensor and GPS errors, 20 runs (seeds 0–19), paired across profiles. § = the route estimator reached the route end D before C in that many runs (its error is then capped by the route length).

## Eisenhower Tunnel, I-70 (westbound)

Dead-reckoning time from GPS loss to C: 125 s.

**Ideal sensors: error at C [m]; dr_calibrated details; speed error measured vs predicted from gravity leakage:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold | dr_calibrated along / cross | dr_calibrated heading err. | speed err. measured / predicted |
|---|---|---|---|---|---|---|---|---|
| Flat | 0 | 0 | 0 | 1 | 336 | -0 / +0 | +0.001° | -0.00 / +0.00 m/s |
| Steady climb 2 % (whole route) | 1555 | 0 | 0 | 1 | 336 | -0 / +0 | +0.001° | -0.00 / +0.00 m/s |
| Climb in the tunnel +1 % | 744 | 729 | 738 | 731 | 336 | +722 / -94 | +0.001° | +11.64 / +11.59 m/s |
| Climb in the tunnel +2 % | 1489 | 1457 | 1476 | 881 § | 336 | +1445 / -187 | +0.001° | +23.28 / +23.18 m/s |
| Climb in the tunnel +4 % | 2977 | 2913 | 2951 | 881 § | 336 | +2889 / -374 | +0.003° | +46.53 / +46.34 m/s |
| Descent in the tunnel −2 % | 1481 | 1453 | 1471 | 1471 | 336 | -1441 / +187 | +0.001° | -22.20 / -23.18 m/s |
| Underwater V 2 % | 683 | 651 | 670 | 670 | 336 | -644 / +94 | +0.002° | +0.41 / +0.51 m/s |
| Underwater V 4 % | 1364 | 1301 | 1339 | 1339 | 336 | -1288 / +188 | +0.005° | +0.82 / +1.03 m/s |

**Realistic sensors: error at C [m], median (p90):**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 460 (773) | 55 (76) | 38 (60) | 34 (55) | 330 (362) |
| Steady climb 2 % (whole route) | 1651 (2308) | 55 (76) | 38 (60) | 34 (55) | 330 (362) |
| Climb in the tunnel +1 % | 844 (1504) | 715 (786) | 730 (780) | 723 (771) | 330 (362) |
| Climb in the tunnel +2 % | 1584 (2243) | 1438 (1514) | 1468 (1518) | 881 (881) §20 | 330 (362) |
| Climb in the tunnel +4 % | 3070 (3725) | 2894 (2970) | 2943 (2992) | 881 (881) §20 | 330 (362) |
| Descent in the tunnel −2 % | 1398 (1825) | 1457 (1502) | 1477 (1514) | 1478 (1514) | 330 (362) |
| Underwater V 2 % | 598 (1251) | 657 (706) | 678 (718) | 679 (717) | 330 (362) |
| Underwater V 4 % | 1270 (1762) | 1306 (1353) | 1343 (1387) | 1344 (1387) | 330 (362) |

**Realistic sensors: along-track shift at C caused by the profile (paired) [m], median [min, max]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Steady climb 2 % (whole route) | +1539 [+1508, +1553] | +0 [-0, +0] | +0 [-0, +0] | +0 [-0, +0] | +0 [+0, +0] |
| Climb in the tunnel +1 % | +738 [+726, +743] | +723 [+712, +724] | +732 [+725, +732] | +717 [+709, +717] | +0 [+0, +0] |
| Climb in the tunnel +2 % | +1475 [+1452, +1487] | +1445 [+1425, +1447] | +1464 [+1450, +1465] | +883 [+820, +940] | +0 [+0, +0] |
| Climb in the tunnel +4 % | +2949 [+2903, +2972] | +2889 [+2849, +2894] | +2926 [+2900, +2929] | +883 [+820, +940] | +0 [+0, +0] |
| Descent in the tunnel −2 % | -1457 [-1486, -1178] | -1439 [-1446, -1418] | -1457 [-1462, -1441] | -1459 [-1464, -1442] | +0 [+0, +0] |
| Underwater V 2 % | -675 [-681, -660] | -644 [-646, -625] | -663 [-664, -649] | -666 [-666, -651] | +0 [+0, +0] |
| Underwater V 4 % | -1338 [-1361, -1106] | -1288 [-1291, -1248] | -1325 [-1326, -1296] | -1330 [-1330, -1301] | +0 [+0, +0] |

**Realistic sensors: |heading error| at C, median (p90):**

| profile | dr_raw | dr_calibrated | dr_filtered |
|---|---|---|---|
| Flat | 6.22° (9.51°) | 0.42° (0.89°) | 0.28° (0.65°) |
| Steady climb 2 % (whole route) | 6.22° (9.51°) | 0.42° (0.88°) | 0.28° (0.65°) |
| Climb in the tunnel +1 % | 6.22° (9.51°) | 0.42° (0.89°) | 0.28° (0.65°) |
| Climb in the tunnel +2 % | 6.22° (9.51°) | 0.42° (0.89°) | 0.28° (0.65°) |
| Climb in the tunnel +4 % | 6.22° (9.51°) | 0.42° (0.90°) | 0.28° (0.66°) |
| Descent in the tunnel −2 % | 6.22° (9.51°) | 0.42° (0.88°) | 0.28° (0.65°) |
| Underwater V 2 % | 6.22° (9.51°) | 0.41° (0.88°) | 0.28° (0.65°) |
| Underwater V 4 % | 6.22° (9.52°) | 0.41° (0.87°) | 0.27° (0.64°) |

**Realistic sensors: exit-announcement timing error [s], median |error| (signed mean):**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 14.6 (-1.1) | 1.9 (+0.3) | 1.3 (+0.3) | 1.3 (+0.3) | 12.4 (-12.5) |
| Steady climb 2 % (whole route) | 31.3 (-30.6) | 1.9 (+0.3) | 1.3 (+0.3) | 1.3 (+0.3) | 12.4 (-12.5) |
| Climb in the tunnel +1 % | 20.0 (-18.5) | 17.9 (-18.1) | 18.3 (-18.3) | 18.3 (-18.3) | 12.4 (-12.5) |
| Climb in the tunnel +2 % | 30.2 (-29.4) | 28.5 (-28.7) | 29.1 (-29.0) | 29.0 (-29.0) | 12.4 (-12.5) |
| Climb in the tunnel +4 % | 42.5 (-42.1) | 41.3 (-41.3) | 41.8 (-41.8) | 41.8 (-41.8) | 12.4 (-12.5) |
| Descent in the tunnel −2 % | 18.0 (+18.0) | 18.0 (+18.0) | 18.0 (+18.0) | 22.9 (+22.9) | 12.4 (-12.5) |
| Underwater V 2 % | 17.4 (+13.7) | 17.9 (+17.9) | 17.9 (+17.9) | 18.7 (+18.9) | 12.4 (-12.5) |
| Underwater V 4 % | 17.9 (+17.9) | 17.9 (+17.9) | 18.0 (+17.9) | 21.7 (+21.8) | 12.4 (-12.5) |

**Realistic sensors: median error vs time since GPS loss [m]:**

| profile | estimator | 15 s | 30 s | 60 s | 90 s | 120 s |
|---|---|---|---|---|---|---|
| Flat | dr_raw | 9 | 32 | 113 | 242 | 419 |
| Flat | dr_calibrated | 6 | 10 | 21 | 35 | 51 |
| Flat | dr_filtered | 4 | 6 | 13 | 22 | 35 |
| Flat | route_imu | 2 | 5 | 13 | 22 | 31 |
| Flat | route_hold | 9 | 46 | 151 | 249 | 317 |
| Steady climb 2 % (whole route) | dr_raw | 28 | 94 | 376 | 845 | 1503 |
| Steady climb 2 % (whole route) | dr_calibrated | 6 | 10 | 21 | 35 | 52 |
| Steady climb 2 % (whole route) | dr_filtered | 4 | 6 | 13 | 22 | 35 |
| Steady climb 2 % (whole route) | route_imu | 2 | 5 | 13 | 22 | 31 |
| Steady climb 2 % (whole route) | route_hold | 9 | 46 | 151 | 249 | 317 |
| Climb in the tunnel +1 % | dr_raw | 13 | 42 | 183 | 424 | 767 |
| Climb in the tunnel +1 % | dr_calibrated | 9 | 37 | 160 | 367 | 659 |
| Climb in the tunnel +1 % | dr_filtered | 8 | 37 | 163 | 376 | 672 |
| Climb in the tunnel +1 % | route_imu | 8 | 37 | 162 | 375 | 662 |
| Climb in the tunnel +1 % | route_hold | 9 | 46 | 151 | 249 | 317 |
| Climb in the tunnel +2 % | dr_raw | 21 | 79 | 345 | 799 | 1440 |
| Climb in the tunnel +2 % | dr_calibrated | 16 | 74 | 320 | 736 | 1324 |
| Climb in the tunnel +2 % | dr_filtered | 17 | 76 | 326 | 752 | 1350 |
| Climb in the tunnel +2 % | route_imu | 17 | 76 | 325 | 751 | 998 |
| Climb in the tunnel +2 % | route_hold | 9 | 46 | 151 | 249 | 317 |
| Climb in the tunnel +4 % | dr_raw | 38 | 155 | 670 | 1549 | 2796 |
| Climb in the tunnel +4 % | dr_calibrated | 32 | 146 | 638 | 1475 | 2655 |
| Climb in the tunnel +4 % | dr_filtered | 36 | 155 | 652 | 1499 | 2695 |
| Climb in the tunnel +4 % | route_imu | 36 | 155 | 651 | 1473 | 998 |
| Climb in the tunnel +4 % | route_hold | 9 | 46 | 151 | 249 | 317 |
| Descent in the tunnel −2 % | dr_raw | 15 | 71 | 305 | 707 | 1273 |
| Descent in the tunnel −2 % | dr_calibrated | 18 | 76 | 324 | 746 | 1343 |
| Descent in the tunnel −2 % | dr_filtered | 20 | 80 | 333 | 760 | 1362 |
| Descent in the tunnel −2 % | route_imu | 20 | 81 | 334 | 761 | 1363 |
| Descent in the tunnel −2 % | route_hold | 9 | 46 | 151 | 249 | 317 |
| Underwater V 2 % | dr_raw | 15 | 71 | 293 | 527 | 603 |
| Underwater V 2 % | dr_calibrated | 18 | 76 | 310 | 559 | 657 |
| Underwater V 2 % | dr_filtered | 20 | 80 | 319 | 574 | 677 |
| Underwater V 2 % | route_imu | 20 | 81 | 320 | 575 | 678 |
| Underwater V 2 % | route_hold | 9 | 46 | 151 | 249 | 317 |
| Underwater V 4 % | dr_raw | 33 | 145 | 605 | 1096 | 1275 |
| Underwater V 4 % | dr_calibrated | 33 | 150 | 617 | 1115 | 1307 |
| Underwater V 4 % | dr_filtered | 39 | 159 | 636 | 1143 | 1342 |
| Underwater V 4 % | route_imu | 39 | 160 | 637 | 1144 | 1343 |
| Underwater V 4 % | route_hold | 9 | 46 | 151 | 249 | 317 |

## Seattle SR 99 Tunnel (northbound)

Dead-reckoning time from GPS loss to C: 151 s.

**Ideal sensors: error at C [m]; dr_calibrated details; speed error measured vs predicted from gravity leakage:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold | dr_calibrated along / cross | dr_calibrated heading err. | speed err. measured / predicted |
|---|---|---|---|---|---|---|---|---|
| Flat | 0 | 0 | 0 | 1 | 1 | +0 / -0 | -0.016° | -0.00 / +0.00 m/s |
| Steady climb 2 % (whole route) | 2188 | 0 | 0 | 1 | 1 | +0 / -0 | -0.016° | -0.00 / +0.00 m/s |
| Climb in the tunnel +1 % | 1050 | 1029 | 1044 | 889 § | 1 | +968 / +350 | -0.016° | +13.99 / +13.99 m/s |
| Climb in the tunnel +2 % | 2100 | 2058 | 2088 | 889 § | 1 | +1935 / +701 | -0.015° | +27.98 / +27.97 m/s |
| Climb in the tunnel +4 % | 4198 | 4115 | 4174 | 889 § | 1 | +3869 / +1401 | -0.010° | +55.93 / +55.91 m/s |
| Descent in the tunnel −2 % | 1878 | 1861 | 1880 | 1878 | 1 | -1738 / -665 | -0.014° | -20.41 / -27.97 m/s |
| Underwater V 2 % | 969 | 928 | 957 | 960 | 1 | -834 / -407 | -0.013° | +0.69 / +0.69 m/s |
| Underwater V 4 % | 1713 | 1675 | 1696 | 1678 | 1 | -1502 / -743 | -0.004° | +3.36 / +1.38 m/s |

**Realistic sensors: error at C [m], median (p90):**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 640 (1070) | 65 (116) | 61 (93) | 32 (72) | 20 (56) |
| Steady climb 2 % (whole route) | 2371 (3259) | 64 (116) | 61 (93) | 32 (72) | 20 (56) |
| Climb in the tunnel +1 % | 1226 (2116) | 1035 (1097) | 1046 (1098) | 889 (889) §20 | 20 (56) |
| Climb in the tunnel +2 % | 2276 (3166) | 2072 (2134) | 2098 (2140) | 889 (889) §20 | 20 (56) |
| Climb in the tunnel +4 % | 4380 (5264) | 4139 (4212) | 4199 (4241) | 889 (889) §20 | 20 (56) |
| Descent in the tunnel −2 % | 1816 (2166) | 1869 (1906) | 1884 (1910) | 1883 (1909) | 20 (56) |
| Underwater V 2 % | 826 (1795) | 949 (1020) | 975 (1032) | 972 (1025) | 20 (56) |
| Underwater V 4 % | 1650 (1972) | 1690 (1723) | 1708 (1734) | 1684 (1714) | 20 (56) |

**Realistic sensors: along-track shift at C caused by the profile (paired) [m], median [min, max]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Steady climb 2 % (whole route) | +2080 [+1913, +2158] | -0 [-0, +0] | +0 [-0, +0] | +0 [-0, +0] | +0 [+0, +0] |
| Climb in the tunnel +1 % | +994 [+917, +1029] | +978 [+962, +985] | +988 [+975, +1000] | +893 [+790, +978] | +0 [+0, +0] |
| Climb in the tunnel +2 % | +1988 [+1835, +2059] | +1956 [+1925, +1970] | +1976 [+1949, +2000] | +893 [+790, +978] | +0 [+0, +0] |
| Climb in the tunnel +4 % | +3974 [+3669, +4116] | +3910 [+3849, +3939] | +3951 [+3897, +4000] | +893 [+790, +978] | +0 [+0, +0] |
| Descent in the tunnel −2 % | -1838 [-2032, -1147] | -1750 [-1794, -1692] | -1765 [-1804, -1704] | -1726 [-1778, -1672] | +0 [+0, +0] |
| Underwater V 2 % | -885 [-929, -811] | -848 [-863, -829] | -873 [-890, -855] | -942 [-956, -922] | +0 [+0, +0] |
| Underwater V 4 % | -1617 [-1822, -913] | -1512 [-1570, -1460] | -1533 [-1574, -1472] | -1551 [-1606, -1491] | +0 [+0, +0] |

**Realistic sensors: |heading error| at C, median (p90):**

| profile | dr_raw | dr_calibrated | dr_filtered |
|---|---|---|---|
| Flat | 7.43° (11.82°) | 1.24° (2.55°) | 1.49° (2.90°) |
| Steady climb 2 % (whole route) | 7.43° (11.82°) | 1.24° (2.55°) | 1.49° (2.90°) |
| Climb in the tunnel +1 % | 7.43° (11.82°) | 1.24° (2.56°) | 1.49° (2.90°) |
| Climb in the tunnel +2 % | 7.43° (11.82°) | 1.24° (2.56°) | 1.49° (2.89°) |
| Climb in the tunnel +4 % | 7.43° (11.81°) | 1.24° (2.56°) | 1.49° (2.89°) |
| Descent in the tunnel −2 % | 7.43° (11.82°) | 1.24° (2.54°) | 1.49° (2.90°) |
| Underwater V 2 % | 7.43° (11.81°) | 1.25° (2.54°) | 1.49° (2.90°) |
| Underwater V 4 % | 7.43° (11.81°) | 1.26° (2.52°) | 1.49° (2.90°) |

**Realistic sensors: exit-announcement timing error [s], median |error| (signed mean):**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 18.5 (-3.0) | 1.5 (-0.1) | 1.4 (-0.2) | 1.2 (+0.1) | 0.8 (-0.8) |
| Steady climb 2 % (whole route) | 45.0 (-43.6) | 1.5 (-0.1) | 1.4 (-0.2) | 1.2 (+0.1) | 0.8 (-0.8) |
| Climb in the tunnel +1 % | 30.0 (-26.8) | 26.9 (-26.9) | 27.2 (-27.2) | 28.1 (-28.1) | 0.8 (-0.8) |
| Climb in the tunnel +2 % | 43.5 (-41.9) | 41.3 (-41.4) | 41.9 (-41.9) | 42.7 (-42.7) | 0.8 (-0.8) |
| Climb in the tunnel +4 % | 59.0 (-58.4) | 57.6 (-57.7) | 58.2 (-58.3) | 58.2 (-58.2) | 0.8 (-0.8) |
| Descent in the tunnel −2 % | 18.7 (+19.1) | 18.7 (+19.1) | 18.7 (+19.1) | 25.5 (+26.0) | 0.8 (-0.8) |
| Underwater V 2 % | 18.6 (+15.4) | 18.6 (+19.0) | 18.6 (+19.0) | 21.4 (+21.1) | 0.8 (-0.8) |
| Underwater V 4 % | 18.7 (+19.1) | 18.6 (+19.1) | 18.6 (+19.1) | 24.5 (+24.5) | 0.8 (-0.8) |

**Realistic sensors: median error vs time since GPS loss [m]:**

| profile | estimator | 15 s | 30 s | 60 s | 90 s | 120 s |
|---|---|---|---|---|---|---|
| Flat | dr_raw | 9 | 31 | 108 | 231 | 406 |
| Flat | dr_calibrated | 6 | 10 | 18 | 30 | 45 |
| Flat | dr_filtered | 3 | 7 | 15 | 26 | 40 |
| Flat | route_imu | 2 | 4 | 8 | 15 | 21 |
| Flat | route_hold | 3 | 5 | 11 | 28 | 18 |
| Steady climb 2 % (whole route) | dr_raw | 27 | 99 | 380 | 846 | 1513 |
| Steady climb 2 % (whole route) | dr_calibrated | 6 | 10 | 18 | 30 | 45 |
| Steady climb 2 % (whole route) | dr_filtered | 3 | 7 | 15 | 26 | 40 |
| Steady climb 2 % (whole route) | route_imu | 2 | 4 | 8 | 15 | 21 |
| Steady climb 2 % (whole route) | route_hold | 3 | 5 | 11 | 28 | 18 |
| Climb in the tunnel +1 % | dr_raw | 12 | 47 | 184 | 425 | 774 |
| Climb in the tunnel +1 % | dr_calibrated | 9 | 37 | 159 | 362 | 656 |
| Climb in the tunnel +1 % | dr_filtered | 10 | 40 | 163 | 370 | 666 |
| Climb in the tunnel +1 % | route_imu | 10 | 40 | 164 | 373 | 667 |
| Climb in the tunnel +1 % | route_hold | 3 | 5 | 11 | 28 | 18 |
| Climb in the tunnel +2 % | dr_raw | 20 | 82 | 343 | 791 | 1438 |
| Climb in the tunnel +2 % | dr_calibrated | 16 | 72 | 315 | 722 | 1309 |
| Climb in the tunnel +2 % | dr_filtered | 20 | 79 | 325 | 738 | 1331 |
| Climb in the tunnel +2 % | route_imu | 19 | 79 | 326 | 743 | 1325 |
| Climb in the tunnel +2 % | route_hold | 3 | 5 | 11 | 28 | 18 |
| Climb in the tunnel +4 % | dr_raw | 35 | 156 | 662 | 1525 | 2770 |
| Climb in the tunnel +4 % | dr_calibrated | 31 | 144 | 626 | 1443 | 2617 |
| Climb in the tunnel +4 % | dr_filtered | 37 | 157 | 648 | 1474 | 2658 |
| Climb in the tunnel +4 % | route_imu | 37 | 156 | 652 | 1444 | 1512 |
| Climb in the tunnel +4 % | route_hold | 3 | 5 | 11 | 28 | 18 |
| Descent in the tunnel −2 % | dr_raw | 15 | 69 | 297 | 681 | 1212 |
| Descent in the tunnel −2 % | dr_calibrated | 15 | 71 | 310 | 717 | 1259 |
| Descent in the tunnel −2 % | dr_filtered | 17 | 76 | 322 | 736 | 1279 |
| Descent in the tunnel −2 % | route_imu | 17 | 76 | 324 | 746 | 1287 |
| Descent in the tunnel −2 % | route_hold | 3 | 5 | 11 | 28 | 18 |
| Underwater V 2 % | dr_raw | 15 | 69 | 296 | 595 | 802 |
| Underwater V 2 % | dr_calibrated | 15 | 71 | 310 | 634 | 879 |
| Underwater V 2 % | dr_filtered | 17 | 76 | 321 | 649 | 901 |
| Underwater V 2 % | route_imu | 17 | 76 | 323 | 660 | 906 |
| Underwater V 2 % | route_hold | 3 | 5 | 11 | 28 | 18 |
| Underwater V 4 % | dr_raw | 30 | 142 | 610 | 1191 | 1600 |
| Underwater V 4 % | dr_calibrated | 30 | 143 | 615 | 1197 | 1621 |
| Underwater V 4 % | dr_filtered | 35 | 152 | 635 | 1218 | 1639 |
| Underwater V 4 % | route_imu | 35 | 153 | 637 | 1222 | 1648 |
| Underwater V 4 % | route_hold | 3 | 5 | 11 | 28 | 18 |

## Synthetic demo route

Dead-reckoning time from GPS loss to C: 103 s.

**Ideal sensors: error at C [m]; dr_calibrated details; speed error measured vs predicted from gravity leakage:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold | dr_calibrated along / cross | dr_calibrated heading err. | speed err. measured / predicted |
|---|---|---|---|---|---|---|---|---|
| Flat | 0 | 0 | 0 | 0 | 17 | -0 / +0 | +0.003° | -0.00 / +0.00 m/s |
| Steady climb 2 % (whole route) | 962 | 0 | 0 | 0 | 17 | -0 / +0 | +0.003° | -0.00 / +0.00 m/s |
| Climb in the tunnel +1 % | 451 | 437 | 447 | 477 | 17 | +404 / +167 | +0.005° | +9.30 / +9.32 m/s |
| Climb in the tunnel +2 % | 901 | 875 | 894 | 782 § | 17 | +808 / +334 | +0.009° | +18.60 / +18.64 m/s |
| Climb in the tunnel +4 % | 1802 | 1749 | 1788 | 782 § | 17 | +1616 / +669 | +0.027° | +37.18 / +37.26 m/s |
| Descent in the tunnel −2 % | 901 | 874 | 894 | 869 | 17 | -808 / -334 | +0.009° | -18.60 / -18.64 m/s |
| Underwater V 2 % | 455 | 429 | 448 | 483 | 17 | -361 / -231 | +0.016° | -0.36 / -0.36 m/s |
| Underwater V 4 % | 909 | 857 | 895 | 858 | 17 | -721 / -462 | +0.057° | -0.72 / -0.72 m/s |

**Realistic sensors: error at C [m], median (p90):**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 282 (463) | 29 (56) | 17 (37) | 17 (40) | 18 (45) |
| Steady climb 2 % (whole route) | 1043 (1419) | 29 (56) | 17 (37) | 17 (40) | 18 (45) |
| Climb in the tunnel +1 % | 525 (898) | 433 (467) | 445 (465) | 475 (494) | 18 (45) |
| Climb in the tunnel +2 % | 976 (1348) | 876 (907) | 894 (912) | 782 (782) §20 | 18 (45) |
| Climb in the tunnel +4 % | 1880 (2250) | 1758 (1783) | 1795 (1811) | 782 (782) §20 | 18 (45) |
| Descent in the tunnel −2 % | 836 (1162) | 893 (936) | 906 (934) | 879 (905) | 18 (45) |
| Underwater V 2 % | 393 (806) | 444 (493) | 459 (489) | 495 (525) | 18 (45) |
| Underwater V 4 % | 849 (1258) | 881 (922) | 910 (943) | 872 (901) | 18 (45) |

**Realistic sensors: along-track shift at C caused by the profile (paired) [m], median [min, max]:**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Steady climb 2 % (whole route) | +895 [+845, +934] | +0 [-0, +0] | +0 [-0, +0] | +0 [-0, +0] | +0 [+0, +0] |
| Climb in the tunnel +1 % | +418 [+396, +433] | +406 [+400, +413] | +415 [+411, +418] | +476 [+467, +485] | +0 [+0, +0] |
| Climb in the tunnel +2 % | +837 [+791, +866] | +812 [+800, +826] | +830 [+823, +836] | +733 [+689, +782] | +0 [+0, +0] |
| Climb in the tunnel +4 % | +1674 [+1582, +1731] | +1623 [+1600, +1651] | +1659 [+1646, +1672] | +733 [+689, +782] | +0 [+0, +0] |
| Descent in the tunnel −2 % | -817 [-858, -691] | -811 [-825, -800] | -829 [-836, -822] | -783 [-808, -757] | +0 [+0, +0] |
| Underwater V 2 % | -389 [-411, -361] | -365 [-376, -356] | -382 [-389, -377] | -487 [-493, -480] | +0 [+0, +0] |
| Underwater V 4 % | -774 [-822, -714] | -729 [-752, -710] | -764 [-776, -753] | -780 [-806, -750] | +0 [+0, +0] |

**Realistic sensors: |heading error| at C, median (p90):**

| profile | dr_raw | dr_calibrated | dr_filtered |
|---|---|---|---|
| Flat | 4.62° (8.36°) | 0.44° (1.26°) | 0.29° (0.61°) |
| Steady climb 2 % (whole route) | 4.62° (8.35°) | 0.44° (1.26°) | 0.29° (0.61°) |
| Climb in the tunnel +1 % | 4.62° (8.36°) | 0.44° (1.26°) | 0.29° (0.61°) |
| Climb in the tunnel +2 % | 4.62° (8.35°) | 0.44° (1.26°) | 0.29° (0.61°) |
| Climb in the tunnel +4 % | 4.62° (8.34°) | 0.46° (1.28°) | 0.31° (0.59°) |
| Descent in the tunnel −2 % | 4.62° (8.35°) | 0.44° (1.26°) | 0.30° (0.61°) |
| Underwater V 2 % | 4.62° (8.35°) | 0.45° (1.26°) | 0.30° (0.59°) |
| Underwater V 4 % | 4.62° (8.32°) | 0.50° (1.28°) | 0.33° (0.62°) |

**Realistic sensors: exit-announcement timing error [s], median |error| (signed mean):**

| profile | dr_raw | dr_calibrated | dr_filtered | route_imu | route_hold |
|---|---|---|---|---|---|
| Flat | 5.3 (+1.1) | 0.8 (+0.5) | 0.5 (+0.3) | 0.6 (+0.3) | 0.4 (+0.2) |
| Steady climb 2 % (whole route) | 21.7 (-20.3) | 0.8 (+0.5) | 0.5 (+0.3) | 0.6 (+0.3) | 0.4 (+0.2) |
| Climb in the tunnel +1 % | 11.7 (-10.2) | 9.6 (-9.6) | 9.9 (-9.9) | 12.8 (-12.8) | 0.4 (+0.2) |
| Climb in the tunnel +2 % | 19.5 (-18.3) | 16.9 (-16.9) | 17.6 (-17.6) | 20.7 (-20.6) | 0.4 (+0.2) |
| Climb in the tunnel +4 % | 33.3 (-32.3) | 31.3 (-31.2) | 32.3 (-32.3) | 30.2 (-30.2) | 0.4 (+0.2) |
| Descent in the tunnel −2 % | 19.4 (+19.4) | 19.4 (+19.5) | 19.4 (+19.5) | 22.3 (+22.4) | 0.4 (+0.2) |
| Underwater V 2 % | 16.5 (+13.7) | 18.9 (+18.6) | 19.3 (+19.1) | 19.3 (+19.4) | 0.4 (+0.2) |
| Underwater V 4 % | 19.3 (+19.1) | 19.4 (+19.5) | 19.4 (+19.5) | 21.3 (+21.4) | 0.4 (+0.2) |

**Realistic sensors: median error vs time since GPS loss [m]:**

| profile | estimator | 15 s | 30 s | 60 s | 90 s | 120 s |
|---|---|---|---|---|---|---|
| Flat | dr_raw | 9 | 30 | 99 | 212 | – |
| Flat | dr_calibrated | 5 | 8 | 15 | 24 | – |
| Flat | dr_filtered | 3 | 4 | 8 | 14 | – |
| Flat | route_imu | 1 | 2 | 6 | 12 | – |
| Flat | route_hold | 8 | 29 | 32 | 9 | – |
| Steady climb 2 % (whole route) | dr_raw | 25 | 96 | 363 | 792 | – |
| Steady climb 2 % (whole route) | dr_calibrated | 5 | 8 | 15 | 24 | – |
| Steady climb 2 % (whole route) | dr_filtered | 3 | 4 | 8 | 14 | – |
| Steady climb 2 % (whole route) | route_imu | 1 | 2 | 6 | 12 | – |
| Steady climb 2 % (whole route) | route_hold | 8 | 29 | 32 | 9 | – |
| Climb in the tunnel +1 % | dr_raw | 12 | 41 | 174 | 395 | – |
| Climb in the tunnel +1 % | dr_calibrated | 8 | 34 | 141 | 322 | – |
| Climb in the tunnel +1 % | dr_filtered | 9 | 36 | 150 | 335 | – |
| Climb in the tunnel +1 % | route_imu | 8 | 37 | 158 | 363 | – |
| Climb in the tunnel +1 % | route_hold | 8 | 29 | 32 | 9 | – |
| Climb in the tunnel +2 % | dr_raw | 17 | 77 | 325 | 734 | – |
| Climb in the tunnel +2 % | dr_calibrated | 15 | 68 | 288 | 652 | – |
| Climb in the tunnel +2 % | dr_filtered | 17 | 74 | 301 | 673 | – |
| Climb in the tunnel +2 % | route_imu | 17 | 74 | 315 | 723 | – |
| Climb in the tunnel +2 % | route_hold | 8 | 29 | 32 | 9 | – |
| Climb in the tunnel +4 % | dr_raw | 32 | 149 | 627 | 1415 | – |
| Climb in the tunnel +4 % | dr_calibrated | 29 | 138 | 579 | 1315 | – |
| Climb in the tunnel +4 % | dr_filtered | 35 | 149 | 605 | 1352 | – |
| Climb in the tunnel +4 % | route_imu | 35 | 149 | 572 | 1040 | – |
| Climb in the tunnel +4 % | route_hold | 8 | 29 | 32 | 9 | – |
| Descent in the tunnel −2 % | dr_raw | 15 | 68 | 280 | 631 | – |
| Descent in the tunnel −2 % | dr_calibrated | 15 | 71 | 295 | 665 | – |
| Descent in the tunnel −2 % | dr_filtered | 18 | 76 | 305 | 680 | – |
| Descent in the tunnel −2 % | route_imu | 18 | 76 | 314 | 667 | – |
| Descent in the tunnel −2 % | route_hold | 8 | 29 | 32 | 9 | – |
| Underwater V 2 % | dr_raw | 15 | 68 | 256 | 388 | – |
| Underwater V 2 % | dr_calibrated | 15 | 71 | 272 | 428 | – |
| Underwater V 2 % | dr_filtered | 18 | 76 | 281 | 439 | – |
| Underwater V 2 % | route_imu | 18 | 76 | 291 | 429 | – |
| Underwater V 2 % | route_hold | 8 | 29 | 32 | 9 | – |
| Underwater V 4 % | dr_raw | 29 | 138 | 532 | 823 | – |
| Underwater V 4 % | dr_calibrated | 30 | 140 | 538 | 847 | – |
| Underwater V 4 % | dr_filtered | 35 | 151 | 559 | 873 | – |
| Underwater V 4 % | route_imu | 35 | 151 | 556 | 858 | – |
| Underwater V 4 % | route_hold | 8 | 29 | 32 | 9 | – |
