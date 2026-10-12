"""Phone mounting: the fixed rotation (and offset) between the vehicle body frame and the phone.

Frames
------
* Vehicle body frame ``b``: ISO 8855, x forward, y left, z up (see ``vehicle/truth.py``).
* Phone sensor frame ``s``: Android ``SensorEvent`` convention, with the device in its natural
  (portrait) orientation: x towards the right edge of the screen, y towards the top edge,
  z out of the screen. Right-handed.

The mounting is the rotation ``R_bs`` with ``v_b = R_bs @ v_s``: its columns are the phone axes
expressed in vehicle axes. It is parametrised by intrinsic Z-Y'-X'' Euler angles of the phone
frame relative to the vehicle frame, ``R_bs = Rz(yaw) @ Ry(pitch) @ Rx(roll)``. All zeros means
"aligned": the phone axes coincide with the vehicle axes (phone flat, screen up, its top edge
pointing to the vehicle's left).

As with any Euler parametrisation, pitch = ±90° is a gimbal lock: yaw and roll then rotate about
the same axis. The rotation itself stays well defined.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

AXIS_NAMES = {0: ("forward", "backward"), 1: ("left", "right"), 2: ("up", "down")}


def rot_x(a: float) -> NDArray[np.float64]:
    c, s = math.cos(a), math.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def rot_y(a: float) -> NDArray[np.float64]:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def rot_z(a: float) -> NDArray[np.float64]:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def euler_zyx(yaw: float, pitch: float, roll: float) -> NDArray[np.float64]:
    """Rotation matrix Rz(yaw) Ry(pitch) Rx(roll) for intrinsic Z-Y'-X'' angles in radians."""
    return rot_z(yaw) @ rot_y(pitch) @ rot_x(roll)


class PhoneMount(BaseModel):
    """Rigid, fixed placement of the phone in the vehicle."""

    model_config = ConfigDict(frozen=True)

    label: str = Field("aligned", description="Name of the preset this mount came from (informational)")
    yaw_deg: float = Field(0.0, ge=-180, le=180, description="Phone frame rotation about vehicle z")
    pitch_deg: float = Field(0.0, ge=-90, le=90, description="...then about the rotated y axis")
    roll_deg: float = Field(0.0, ge=-180, le=180, description="...then about the rotated x axis")
    lever_arm_m: tuple[float, float, float] = Field(
        (0.0, 0.0, 0.0),
        description="Phone position relative to the vehicle reference point (the point that follows the "
        "road centreline without side-slip, i.e. rear-axle centre), in vehicle axes [m]",
    )

    def rotation_body_from_phone(self) -> NDArray[np.float64]:
        """R_bs: v_body = R_bs @ v_phone (columns = phone axes in vehicle axes)."""
        return euler_zyx(
            math.radians(self.yaw_deg), math.radians(self.pitch_deg), math.radians(self.roll_deg)
        )


MOUNT_PRESETS: dict[str, PhoneMount] = {
    # Phone axes = vehicle axes: flat, screen up, top edge to the left.
    "aligned": PhoneMount(label="aligned"),
    # Flat on the centre console, screen up, top edge towards the front (portrait).
    "flat_portrait": PhoneMount(label="flat_portrait", yaw_deg=-90.0),
    # Upright in a dashboard holder, portrait, screen facing the driver.
    "dash_portrait": PhoneMount(label="dash_portrait", yaw_deg=-90.0, roll_deg=90.0),
    # Dashboard holder, portrait, screen tilted 15° up towards the driver's eyes.
    "dash_portrait_tilted": PhoneMount(label="dash_portrait_tilted", yaw_deg=-90.0, roll_deg=75.0),
    # Upright, landscape with the top edge to the left, screen facing the driver (pitch = -90°).
    "dash_landscape": PhoneMount(label="dash_landscape", pitch_deg=-90.0),
}


def describe_phone_axes(rotation_bs: NDArray[np.float64], threshold: float = 0.2) -> dict[str, str]:
    """Direction of each phone axis in the vehicle, e.g. {'x': 'right', 'y': '0.97 up + 0.26 forward'}."""
    out = {}
    for j, axis in enumerate("xyz"):
        col = rotation_bs[:, j]
        parts = []
        for i in np.argsort(-np.abs(col)):
            if abs(col[i]) < threshold:
                continue
            name = AXIS_NAMES[int(i)][0 if col[i] > 0 else 1]
            parts.append(name if abs(col[i]) > 0.999 else f"{abs(col[i]):.2f} {name}")
        out[axis] = " + ".join(parts)
    return out
