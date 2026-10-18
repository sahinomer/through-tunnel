"""HTML text blocks of the simulator page: scenario summary and live readouts. Pure functions."""

from __future__ import annotations

import html
import math
from collections.abc import Iterable

import numpy as np

from throughtunnel.app.positioning_view import swatch_html
from throughtunnel.evaluation.metrics import TrackEvaluation
from throughtunnel.routing import RawRoute
from throughtunnel.scenario import (
    TUNNEL_MAX_LENGTH_M,
    TUNNEL_MIN_LENGTH_M,
    SimulationResult,
    scenario_warnings,
)


def fmt_km(m: float) -> str:
    return f"{m / 1000:.3f} km"


def route_info_html(result: SimulationResult, route: RawRoute) -> str:
    """Scenario summary: route and tunnel lengths, GPS outage, road processing, drive, warnings."""
    res, d = result, result.path.diagnostics
    tr = res.truth
    names = ", ".join(route.metadata.get("road_names", [])[:6])
    rm = res.route_map
    tunnel_m = rm.tunnel_exit_m - rm.tunnel_entrance_m
    in_range = TUNNEL_MIN_LENGTH_M <= tunnel_m <= TUNNEL_MAX_LENGTH_M
    length_style = "" if in_range else "color:#e65100;font-weight:bold"
    ev = res.gnss_events
    outage = f"{ev.reacquire_t - ev.loss_t:.0f} s without fixes" if math.isfinite(ev.loss_t) else "none"
    rows = [
        ("Scenario", html.escape(res.config.name)),
        ("Source", html.escape(route.source) + (f" · {html.escape(names)}" if names else "")),
        ("Route A–D", f"{fmt_km(rm.length_m)} (driven path {fmt_km(res.path.length_m)})"),
        (
            "Tunnel B–C",
            f"<span style='{length_style}'>{fmt_km(tunnel_m)}</span> · approach "
            f"{fmt_km(rm.tunnel_entrance_m)} · recovery {fmt_km(rm.length_m - rm.tunnel_exit_m)}",
        ),
        ("GPS", f"{len(res.gnss)} fixes · outage: {outage}"),
        ("Calibration error", html.escape(res.config.calibration.describe())),
        ("Map data", "route + road grade" if rm.has_grade else "route geometry only"),
        (
            "Vehicle speed",
            f"scale error {res.config.vehicle_speed.scale_error_pct:+g} % (reference estimator only)",
        ),
        ("Traffic", html.escape(traffic_summary(res))),
        ("Map polyline", f"{fmt_km(d.raw_length_m)} · {d.raw_vertices} vertices"),
        ("Smoothing deviation", f"max {d.max_deviation_m:.2f} m · rms {d.rms_deviation_m:.2f} m"),
        ("Min turn radius", f"{d.min_radius_m:,.0f} m" if math.isfinite(d.min_radius_m) else "∞"),
        ("Duration", f"{tr.duration_s:.1f} s · mean {np.mean(tr.speed) * 3.6:.1f} km/h"),
        (
            "Peaks",
            f"|a_lat| {np.abs(tr.accel_lat).max():.2f} m/s² · a_long "
            f"{tr.accel_long.min():.2f}…{tr.accel_long.max():.2f} m/s²",
        ),
    ]
    body = "".join(f"<tr><td class='pr-3 text-gray-500'>{k}</td><td>{v}</td></tr>" for k, v in rows)
    warnings = [*scenario_warnings(res), *d.warnings]
    warn = "".join(f"<div style='color:#e65100'>⚠ {html.escape(w)}</div>" for w in warnings)
    return f"<table>{body}</table>{warn}"


def traffic_summary(result: SimulationResult) -> str:
    """E.g. 'Stop-and-go (T3) · 3 stops, 82 s standing · tunnel crossed in 346 s'."""
    from throughtunnel.vehicle.traffic import SCENARIO_LABELS

    label = SCENARIO_LABELS.get(result.config.traffic.scenario, result.config.traffic.scenario)
    sec = result.sections
    if sec is None or result.config.traffic.scenario == "free":
        return label
    m = result.motion
    standing = float(np.sum(m.v == 0.0) * (m.t[1] - m.t[0]))
    parts = [label]
    if result.traffic.stops:
        parts.append(f"{len(result.traffic.stops)} stops, {standing:.0f} s standing")
    parts.append(f"tunnel crossed in {sec.exit_t - sec.entrance_t:.0f} s")
    return " · ".join(parts)


def state_readout_html(
    st: dict[str, float],
    measured: tuple[np.ndarray, np.ndarray],
    ideal: tuple[np.ndarray, np.ndarray],
) -> str:
    """Vehicle state at the playback time and the phone IMU readings (measured and ideal)."""
    kappa = st["curvature"]
    radius = "straight" if abs(kappa) < 1e-4 else f"{1 / abs(kappa):,.0f} m {'L' if kappa > 0 else 'R'}"
    items = [
        ("t", f"{st['t']:.2f} s"),
        ("distance", f"{st['s']:.1f} m"),
        ("speed", f"{st['speed'] * 3.6:.1f} km/h"),
        ("a long", f"{st['accel_long']:+.2f} m/s²"),
        ("a lat", f"{st['accel_lat']:+.2f} m/s²"),
        ("bearing", f"{st['bearing_deg']:.1f}°"),
        ("yaw rate", f"{math.degrees(st['yaw_rate']):+.2f} °/s"),
        ("turn radius", radius),
    ]
    cells = "".join(
        f"<div><div class='text-xs text-gray-500'>{k}</div><div class='font-mono'>{v}</div></div>"
        for k, v in items
    )

    def row(label: str, values: np.ndarray, fmt: str, unit: str) -> str:
        nums = " ".join(format(v, fmt) for v in values)
        return f"<div class='font-mono text-sm whitespace-pre'>{label} {nums} {unit}</div>"

    imu = (
        "<div class='mt-2 text-xs text-gray-500'>phone IMU, phone axes x / y / z (measured, ideal)</div>"
        + row("accel", measured[0], "+7.3f", "m/s²")
        + row("     ", ideal[0], "+7.3f", "ideal")
        + row("gyro ", measured[1], "+7.4f", "rad/s")
        + row("     ", ideal[1], "+7.4f", "ideal")
    )
    return f"<div class='grid grid-cols-4 gap-x-4 gap-y-1'>{cells}</div>{imu}"


def estimate_readout_html(evaluations: Iterable[TrackEvaluation], visible: set[str], t: float) -> str:
    """Each visible estimator's position error at time ``t`` (evaluation-only information)."""
    parts = []
    for ev in evaluations:
        if ev.name in visible and len(ev.t) and ev.t[0] <= t:
            err = float(np.interp(t, ev.t, ev.total))
            parts.append(f"{swatch_html(ev.name)} {err:,.1f} m")
    if not parts:
        return ""
    return (
        "<div class='mt-2 text-xs text-gray-500'>position error now (evaluation only)</div>"
        f"<div class='font-mono text-sm'>{' &nbsp; '.join(parts)}</div>"
    )
