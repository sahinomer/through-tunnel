"""Decimated ground-truth track sent once to the browser for smooth client-side playback."""

from __future__ import annotations

import numpy as np

from throughtunnel.vehicle.truth import GroundTruth

TRACK_RATE_HZ = 10.0  # linear interpolation between 10 Hz samples: < 1 cm chord error on R >= 60 m curves
HEADING_ARROW_M = 40.0


def playback_track(
    truth: GroundTruth, rate_hz: float = TRACK_RATE_HZ, arrow_m: float = HEADING_ARROW_M
) -> dict[str, list[float]]:
    """Time, position and heading-arrow tip, decimated to ``rate_hz`` (the last sample is always kept)."""
    step = max(1, round(truth.sample_rate_hz / rate_hz))
    idx = np.arange(0, len(truth), step)
    if idx[-1] != len(truth) - 1:
        idx = np.append(idx, len(truth) - 1)
    yaw = truth.yaw[idx]
    tip = np.column_stack(
        [truth.x[idx] + arrow_m * np.cos(yaw), truth.y[idx] + arrow_m * np.sin(yaw), np.zeros(len(idx))]
    )
    tip_lat, tip_lon, _ = truth.frame.to_geodetic(tip)
    return {
        "t": np.round(truth.t[idx], 4).tolist(),
        "lat": np.round(truth.lat[idx], 8).tolist(),  # 1e-8 deg ~ 1 mm
        "lon": np.round(truth.lon[idx], 8).tolist(),
        "hlat": np.round(tip_lat, 8).tolist(),
        "hlon": np.round(tip_lon, 8).tolist(),
    }
