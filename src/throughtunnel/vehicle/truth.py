"""Ground-truth vehicle state: the simulator's hidden reality.

Everything here is derived from one integrated longitudinal state (s, v, a, j)
plus the path geometry, so all quantities are mutually consistent:

    position  = r(s)                       yaw       = ψ(s)
    yaw_rate  = κ(s) v                     yaw_accel = κ'(s) v^2 + κ(s) a
    accel_lat = κ(s) v^2   (centripetal)   accel_long = a

Frames
------
* Navigation frame: local ENU tangent plane (x East, y North, z Up).
* Body frame: ISO 8855 vehicle axes (x forward, y left, z up).
* yaw ψ: angle from East to body-x, counter-clockwise positive (continuous,
  unwrapped). Compass bearing = 90° - ψ.

Flat-road assumptions: roll = pitch = 0, z = 0, no side-slip (velocity along
body-x). ``acc_body``/``omega_body`` are the kinematic inputs the sensor model
of the next milestone turns into specific force and angular rate.

This object must never be handed to a positioning algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

import numpy as np
from numpy.typing import NDArray

from throughtunnel.geodesy import LocalFrame
from throughtunnel.road import RoadPath
from throughtunnel.vehicle.longitudinal import LongitudinalTrajectory

# Scalar time series exposed for plotting/export: name -> (unit, description)
SCALAR_CHANNELS: dict[str, tuple[str, str]] = {
    "t": ("s", "simulation time"),
    "s": ("m", "distance travelled along the road"),
    "x": ("m", "ENU east"),
    "y": ("m", "ENU north"),
    "z": ("m", "ENU up"),
    "lat": ("deg", "WGS84 latitude"),
    "lon": ("deg", "WGS84 longitude"),
    "alt": ("m", "WGS84 ellipsoidal height"),
    "speed": ("m/s", "speed over ground"),
    "accel_long": ("m/s^2", "longitudinal acceleration (body x)"),
    "accel_lat": ("m/s^2", "lateral (centripetal) acceleration (body y, + = left)"),
    "jerk": ("m/s^3", "longitudinal jerk"),
    "yaw": ("rad", "ENU yaw, CCW from East, unwrapped"),
    "bearing_deg": ("deg", "compass heading, clockwise from North"),
    "yaw_rate": ("rad/s", "yaw rate (body z, + = left turn)"),
    "yaw_accel": ("rad/s^2", "yaw angular acceleration"),
    "curvature": ("1/m", "path curvature (+ = left)"),
    "roll": ("rad", "roll angle (0: flat road)"),
    "pitch": ("rad", "pitch angle (0: flat road)"),
}


@dataclass(frozen=True)
class GroundTruth:
    frame: LocalFrame
    t: NDArray[np.float64]
    s: NDArray[np.float64]
    x: NDArray[np.float64]
    y: NDArray[np.float64]
    z: NDArray[np.float64]
    lat: NDArray[np.float64]
    lon: NDArray[np.float64]
    alt: NDArray[np.float64]
    speed: NDArray[np.float64]
    accel_long: NDArray[np.float64]
    accel_lat: NDArray[np.float64]
    jerk: NDArray[np.float64]
    yaw: NDArray[np.float64]
    yaw_rate: NDArray[np.float64]
    yaw_accel: NDArray[np.float64]
    curvature: NDArray[np.float64]
    roll: NDArray[np.float64]
    pitch: NDArray[np.float64]
    acc_enu: NDArray[np.float64]  # (N, 3) kinematic acceleration in ENU [m/s^2]
    acc_body: NDArray[np.float64]  # (N, 3) kinematic acceleration in body axes [m/s^2]
    omega_body: NDArray[np.float64]  # (N, 3) angular velocity of body w.r.t. ENU, body axes [rad/s]

    def __len__(self) -> int:
        return len(self.t)

    @property
    def bearing_deg(self) -> NDArray[np.float64]:
        return np.mod(90.0 - np.degrees(self.yaw), 360.0)

    @property
    def duration_s(self) -> float:
        return float(self.t[-1])

    @property
    def sample_rate_hz(self) -> float:
        return 1.0 / float(self.t[1] - self.t[0])

    def rotation_enu_from_body(self) -> NDArray[np.float64]:
        """(N, 3, 3) rotation matrices C such that v_enu = C @ v_body (yaw-only on a flat road)."""
        c, s = np.cos(self.yaw), np.sin(self.yaw)
        rot = np.zeros((len(self), 3, 3))
        rot[:, 0, 0], rot[:, 0, 1] = c, -s
        rot[:, 1, 0], rot[:, 1, 1] = s, c
        rot[:, 2, 2] = 1.0
        return rot

    def scalar_columns(self) -> dict[str, NDArray[np.float64]]:
        out = {f.name: getattr(self, f.name) for f in fields(self) if f.name in SCALAR_CHANNELS}
        out["bearing_deg"] = self.bearing_deg
        return {k: out[k] for k in SCALAR_CHANNELS}

    def sample(self, t: float) -> dict[str, float]:
        """Linearly interpolated scalar state at time ``t`` (for playback/display)."""
        tc = min(max(t, float(self.t[0])), float(self.t[-1]))
        vals = {name: float(np.interp(tc, self.t, col)) for name, col in self.scalar_columns().items()}
        vals["bearing_deg"] = float(np.mod(90.0 - np.degrees(vals["yaw"]), 360.0))
        return vals


def build_ground_truth(motion: LongitudinalTrajectory, path: RoadPath) -> GroundTruth:
    geo = path.evaluate(motion.s)
    v, a = motion.v, motion.a
    kappa = geo.curvature
    yaw = geo.yaw
    yaw_rate = kappa * v
    yaw_accel = geo.curvature_rate * v**2 + kappa * a
    accel_lat = kappa * v**2

    n = len(motion.t)
    zeros = np.zeros(n)
    c, s = np.cos(yaw), np.sin(yaw)
    acc_enu = np.column_stack([a * c - accel_lat * s, a * s + accel_lat * c, zeros])
    acc_body = np.column_stack([a, accel_lat, zeros])
    omega_body = np.column_stack([zeros, zeros, yaw_rate])

    x, y = geo.xy[:, 0], geo.xy[:, 1]
    lat, lon, alt = path.frame.to_geodetic(np.column_stack([x, y, zeros]))
    return GroundTruth(
        frame=path.frame,
        t=motion.t,
        s=motion.s,
        x=x,
        y=y,
        z=zeros,
        lat=lat,
        lon=lon,
        alt=alt,
        speed=v,
        accel_long=a,
        accel_lat=accel_lat,
        jerk=motion.jerk,
        yaw=yaw,
        yaw_rate=yaw_rate,
        yaw_accel=yaw_accel,
        curvature=kappa,
        roll=zeros.copy(),
        pitch=zeros.copy(),
        acc_enu=acc_enu,
        acc_body=acc_body,
        omega_body=omega_body,
    )
