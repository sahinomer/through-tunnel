"""Ground-truth vehicle state: the simulator's hidden reality.

Everything here is derived from one integrated longitudinal state (s, v, a, j)
plus the path geometry and the road's height profile z(s), so all quantities are mutually consistent.
s, v, a are the horizontal distance along the road and its derivatives (the map and the driver's
speed profile are horizontal); G = z'(s) is the grade.

    position  = (r(s), z(s))               yaw       = ψ(s)
    yaw_rate  = κ(s) v                     yaw_accel = κ'(s) v^2 + κ(s) a
    velocity  = v (cos ψ, sin ψ, G)        acceleration (ENU) = a T + κ v^2 N + (G a + G' v^2) e_z
    pitch θ   = -atan(G)                   (ISO 8855: rotation about body y = left, + = nose down)

Frames
------
* Navigation frame: local ENU tangent plane (x East, y North, z Up).
* Body frame: ISO 8855 vehicle axes (x forward, y left, z up).
* yaw ψ: angle from East to body-x, counter-clockwise positive (continuous,
  unwrapped). Compass bearing = 90° - ψ.

Body attitude: C_nb = Rz(ψ) Ry(θ). Body x points along the 3-D velocity (no side-slip, the vehicle
pitches with the road), body y stays horizontal: no road banking, so roll = 0. Angular velocity in
body axes: ω = (-sin θ ψ', θ', cos θ ψ'). ``acc_body``/``omega_body``/``alpha_body`` are the
kinematic inputs the sensor models turn into specific force and angular rate. With a flat road
(no profile) every quantity is computed exactly as before slope was modelled.

This object must never be handed to a positioning algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

import numpy as np
from numpy.typing import ArrayLike, NDArray

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
    "speed": ("m/s", "horizontal speed over ground"),
    "accel_long": ("m/s^2", "longitudinal acceleration (body x)"),
    "accel_lat": ("m/s^2", "lateral (centripetal) acceleration (body y, + = left)"),
    "jerk": ("m/s^3", "longitudinal jerk"),
    "yaw": ("rad", "ENU yaw, CCW from East, unwrapped"),
    "bearing_deg": ("deg", "compass heading, clockwise from North"),
    "yaw_rate": ("rad/s", "yaw rate (body z, + = left turn)"),
    "yaw_accel": ("rad/s^2", "yaw angular acceleration"),
    "curvature": ("1/m", "path curvature (+ = left)"),
    "roll": ("rad", "roll angle (0: no road banking)"),
    "pitch": ("rad", "pitch angle, ISO 8855 (+ = nose down; -atan(grade))"),
    "grade": ("-", "road grade dz/ds (+ = uphill)"),
    "pitch_rate": ("rad/s", "pitch rate (body y)"),
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
    grade: NDArray[np.float64]
    pitch_rate: NDArray[np.float64]
    pitch_accel: NDArray[np.float64]
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

    @property
    def vel_enu(self) -> NDArray[np.float64]:
        """(N, 3) velocity of the reference point in ENU [m/s] (no side-slip: along the heading)."""
        v = self.speed
        return np.column_stack([v * np.cos(self.yaw), v * np.sin(self.yaw), v * self.grade])

    @property
    def alpha_body(self) -> NDArray[np.float64]:
        """(N, 3) angular acceleration of the body w.r.t. ENU, body axes [rad/s^2] (d/dt of omega_body)."""
        if not np.any(self.pitch):
            return np.column_stack([self.roll * 0.0, self.pitch * 0.0, self.yaw_accel])
        c, s = np.cos(self.pitch), np.sin(self.pitch)
        q, r, dr = self.pitch_rate, self.yaw_rate, self.yaw_accel
        return np.column_stack([-c * q * r - s * dr, self.pitch_accel, -s * q * r + c * dr])

    def point_enu(self, lever_body: ArrayLike) -> NDArray[np.float64]:
        """(N, 3) ENU position of a body-fixed point (e.g. the phone) at ``lever_body`` from the reference."""
        ref = np.column_stack([self.x, self.y, self.z])
        return ref + np.einsum(
            "nij,j->ni", self.rotation_enu_from_body(), np.asarray(lever_body, dtype=float)
        )

    def rotation_enu_from_body(self) -> NDArray[np.float64]:
        """(N, 3, 3) rotation matrices C = Rz(yaw) Ry(pitch) such that v_enu = C @ v_body."""
        c, s = np.cos(self.yaw), np.sin(self.yaw)
        rot = np.zeros((len(self), 3, 3))
        rot[:, 0, 0], rot[:, 0, 1] = c, -s
        rot[:, 1, 0], rot[:, 1, 1] = s, c
        rot[:, 2, 2] = 1.0
        if not np.any(self.pitch):
            return rot
        cp, sp = np.cos(self.pitch), np.sin(self.pitch)
        ry = np.zeros((len(self), 3, 3))
        ry[:, 0, 0], ry[:, 0, 2] = cp, sp
        ry[:, 1, 1] = 1.0
        ry[:, 2, 0], ry[:, 2, 2] = -sp, cp
        return rot @ ry

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
    if path.elevation is None:  # flat road: exactly the original arithmetic
        z, grade, pitch, pitch_rate, pitch_accel = (
            zeros,
            zeros.copy(),
            zeros.copy(),
            zeros.copy(),
            zeros.copy(),
        )
        acc_enu = np.column_stack([a * c - accel_lat * s, a * s + accel_lat * c, zeros])
        acc_body = np.column_stack([a, accel_lat, zeros])
        omega_body = np.column_stack([zeros, zeros, yaw_rate])
        accel_long = a
    else:
        z, grade, g1, g2 = path.elevation.evaluate(motion.s)  # height, grade, dG/ds, d2G/ds2
        a_up = grade * a + g1 * v**2  # vertical acceleration
        acc_enu = np.column_stack([a * c - accel_lat * s, a * s + accel_lat * c, a_up])
        k = 1.0 + grade**2
        pitch = -np.arctan(grade)
        pitch_rate = -g1 * v / k
        pitch_accel = -(g2 * v**2 + g1 * a) / k + 2.0 * grade * (g1 * v) ** 2 / k**2
        cp, sp = np.cos(pitch), np.sin(pitch)
        # Body x = cos(-θ) T + sin(-θ) e_z (along the road), body z = sin θ T + cos θ e_z: project.
        acc_body = np.column_stack([cp * a - sp * a_up, accel_lat, sp * a + cp * a_up])
        omega_body = np.column_stack([-sp * yaw_rate, pitch_rate, cp * yaw_rate])
        accel_long = acc_body[:, 0]

    x, y = geo.xy[:, 0], geo.xy[:, 1]
    lat, lon, alt = path.frame.to_geodetic(np.column_stack([x, y, z]))
    return GroundTruth(
        frame=path.frame,
        t=motion.t,
        s=motion.s,
        x=x,
        y=y,
        z=z,
        lat=lat,
        lon=lon,
        alt=alt,
        speed=v,
        accel_long=accel_long,
        accel_lat=accel_lat,
        jerk=motion.jerk,
        yaw=yaw,
        yaw_rate=yaw_rate,
        yaw_accel=yaw_accel,
        curvature=kappa,
        roll=zeros.copy(),
        pitch=pitch,
        grade=grade,
        pitch_rate=pitch_rate,
        pitch_accel=pitch_accel,
        acc_enu=acc_enu,
        acc_body=acc_body,
        omega_body=omega_body,
    )
