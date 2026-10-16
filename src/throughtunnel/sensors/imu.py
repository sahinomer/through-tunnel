"""Smartphone IMU (accelerometer + gyroscope) measurement model.

``ImuStream`` itself is defined in ``throughtunnel.observations`` (re-exported here).

``ImuStream`` is an *observation*: exactly what a phone reports, with no ground truth attached.
The simulator produces it here; a loader for recorded phone logs will produce the same type,
so downstream positioning code cannot tell (and must not care) where it came from.

Physics (ideal sensors, i.e. no noise/bias yet)
-----------------------------------------------
Accelerometer = specific force at the phone's location, in phone axes:

    f = a_phone - g                      (a: acceleration w.r.t. the Earth-fixed ENU frame)
    a_phone = a_ref + α × r + ω × (ω × r)  (rigid-body transfer over the lever arm r)

with g = (0, 0, -γ) in ENU and γ the WGS84 normal gravity at the vehicle's latitude (normal
gravity already contains the centrifugal effect of Earth rotation). A phone lying still, screen
up, therefore reads +γ on z, as Android devices do.

Gyroscope = angular rate of the phone w.r.t. inertial space, in phone axes. The phone is rigid
with the vehicle, so this is the vehicle's angular rate ω (the lever arm does not matter).

Optional Earth rotation (off by default): adds the Earth rate Ω_ie (7.29e-5 rad/s, ~15 °/h) to
the gyroscope and the Coriolis term 2 Ω_ie × v to the accelerometer. Both are far below
consumer-sensor noise and bias, but they are physically present. The transport rate of the
local frame (v / R_earth ~ 3e-6 rad/s) is neglected.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

from throughtunnel.geodesy import STANDARD_GRAVITY, normal_gravity
from throughtunnel.observations import ImuStream
from throughtunnel.sensors.errors import ImuErrorConfig
from throughtunnel.sensors.mounting import PhoneMount
from throughtunnel.vehicle.truth import GroundTruth

OMEGA_EARTH = 7.292115e-5  # WGS84 Earth rotation rate [rad/s]


class ImuConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    mount: PhoneMount = Field(default_factory=PhoneMount)
    gravity_model: Literal["wgs84", "standard"] = Field(
        "wgs84", description="'wgs84': normal gravity at the latitude; 'standard': 9.80665 m/s^2"
    )
    earth_rotation: bool = Field(False, description="Include Earth rate (gyro) and Coriolis (accel)")
    rate_hz: float = Field(
        200.0, ge=10.0, le=2000.0, description="Phone sensor sample rate, constant during a run"
    )
    errors: ImuErrorConfig = Field(default_factory=ImuErrorConfig)


def imu_timestamps(t_end: float, rate_hz: float) -> NDArray[np.float64]:
    """Sample times k / rate_hz covering [0, t_end] (a sensor clock started with the run)."""
    n = int(np.floor(t_end * rate_hz + 1e-9)) + 1
    return np.arange(n) / rate_hz


def ideal_imu(truth: GroundTruth, config: ImuConfig | None = None) -> ImuStream:
    """Error-free accelerometer and gyroscope readings of a phone rigidly mounted in the vehicle."""
    cfg = config or ImuConfig()
    r_bs = cfg.mount.rotation_body_from_phone()
    lever = np.asarray(cfg.mount.lever_arm_m, dtype=float)
    c_nb = truth.rotation_enu_from_body()  # (N, 3, 3): v_enu = C_nb v_body

    omega_b = truth.omega_body
    alpha_b = truth.alpha_body
    # Acceleration of the phone point, w.r.t. ENU, expressed in ENU.
    a_lever_b = np.cross(alpha_b, lever) + np.cross(omega_b, np.cross(omega_b, lever))
    a_n = truth.acc_enu + np.einsum("nij,nj->ni", c_nb, a_lever_b)

    n = len(truth)
    gamma = normal_gravity(truth.lat) if cfg.gravity_model == "wgs84" else np.full(n, STANDARD_GRAVITY)
    f_n = a_n.copy()
    f_n[:, 2] += gamma  # f = a - g with g = (0, 0, -gamma)
    gyro_b = omega_b.copy()

    if cfg.earth_rotation:
        lat = np.radians(truth.lat)
        w_ie_n = OMEGA_EARTH * np.column_stack([np.zeros(n), np.cos(lat), np.sin(lat)])
        v_phone_n = truth.vel_enu + np.einsum("nij,nj->ni", c_nb, np.cross(omega_b, lever))
        f_n += 2.0 * np.cross(w_ie_n, v_phone_n)
        gyro_b += np.einsum("nji,nj->ni", c_nb, w_ie_n)  # C_bn = C_nb^T

    f_b = np.einsum("nji,nj->ni", c_nb, f_n)
    # Row-vector form of v_s = R_bs^T v_b for every sample.
    accel_s = f_b @ r_bs
    gyro_s = gyro_b @ r_bs
    return ImuStream(
        t=truth.t.copy(),
        accel=accel_s,
        gyro=gyro_s,
        source="simulated:ideal",
    )
