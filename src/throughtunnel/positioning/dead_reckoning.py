"""Baseline B0: GPS-initialised 2-D vehicle dead reckoning (positioning_design.md §4).

While GPS fixes arrive, the state is reset to each fix (position, speed, bearing). Between fixes, and
after GPS is lost, it is propagated with the IMU:

    a_fwd = forward · accel          (forward specific force; flat road -> no gravity if levelled)
    w_up  = up · gyro - gyro_bias    (yaw rate)
    v    += a_fwd dt,  psi += w_up dt,  (E, N) += v (cos psi, sin psi) dt

The vehicle is assumed not to move sideways (non-holonomic), so the lateral accelerometer channel is
not integrated. Two configurations:

* ``assume_aligned``: phone axes taken as vehicle axes, no calibration. The "raw physics" baseline;
  valid only for an aligned mount (an explicit assumption, not knowledge of the true mounting).
* ``estimate``: axes and gyro bias from ``MountAlignmentEstimator`` using approach-phase GPS. The
  levelling absorbs the horizontal accelerometer bias.

Optional GPS blending (``blend_speed_tau_s`` / ``blend_heading_tau_s``): once the IMU is calibrated,
speed and heading are not reset to each (noisy) fix but pulled towards it with a first-order,
causal complementary filter, x += (dt_fix / tau) * (x_gps - x). Between fixes the calibrated IMU
carries them. This averages GPS speed/bearing noise over ~tau seconds, so the state handed over to
pure dead reckoning at the tunnel entrance is better than a single fix. Position is still reset to
each fix: GPS position errors are time-correlated, so averaging them gains little.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from throughtunnel.observations import GnssFix, RouteMap
from throughtunnel.positioning.alignment import (
    ALIGNED,
    Alignment,
    MountAlignmentEstimator,
    with_orientation_error,
)
from throughtunnel.positioning.base import Estimator, StateEstimate


@dataclass(frozen=True)
class DeadReckoningConfig:
    alignment: Literal["assume_aligned", "estimate"] = "estimate"
    calibrate_gyro_bias: bool = True
    gnss_timeout_s: float = 1.5  # no fix for this long -> dead-reckoning mode
    blend_speed_tau_s: float | None = None  # None: reset speed to every fix
    blend_heading_tau_s: float | None = None  # None: reset heading to every fix
    min_speed_for_bearing: float = 5.0  # GPS bearing is ignored below this speed when blending


class VehicleDeadReckoning(Estimator):
    name = "dr"
    label = "Dead reckoning"

    def __init__(
        self,
        route: RouteMap,
        config: DeadReckoningConfig | None = None,
        calibration_error: NDArray[np.float64] | None = None,
    ) -> None:
        super().__init__(route, calibration_error)
        self.config = config or DeadReckoningConfig()
        self._aligner = MountAlignmentEstimator() if self.config.alignment == "estimate" else None
        declared = with_orientation_error(ALIGNED, calibration_error)
        self._axes: Alignment | None = declared if self._aligner is None else None
        self._t: float | None = None
        self._last_fix_t = -math.inf
        self._e = self._n = self._v = self._psi = 0.0
        self._initialised = False

    # ------------------------------------------------------------------ observations
    def on_gnss(self, fix: GnssFix) -> None:
        cfg = self.config
        blending = (
            self._initialised and self._axes is not None and fix.t - self._last_fix_t <= cfg.gnss_timeout_s
        )
        self._e, self._n = self.fix_enu(fix)
        yaw_gps = self.bearing_to_yaw(fix.bearing_deg)
        if blending and cfg.blend_speed_tau_s:
            self._v += min(1.0, (fix.t - self._last_fix_t) / cfg.blend_speed_tau_s) * (
                fix.speed_mps - self._v
            )
        else:
            self._v = fix.speed_mps
        if blending and cfg.blend_heading_tau_s:
            if fix.speed_mps >= cfg.min_speed_for_bearing:
                gain = min(1.0, (fix.t - self._last_fix_t) / cfg.blend_heading_tau_s)
                self._psi += gain * math.remainder(yaw_gps - self._psi, 2.0 * math.pi)
        else:
            self._psi = yaw_gps
        self._last_fix_t = fix.t
        self._t = fix.t
        self._initialised = True
        if self._aligner is not None:
            self._aligner.add_fix(fix)
            solved = self._aligner.solve()
            if solved is not None and solved.ready:
                self._axes = with_orientation_error(solved, self.calibration_error)

    def on_imu(self, t: float, accel: Sequence[float], gyro: Sequence[float]) -> None:
        if self._aligner is not None and t - self._last_fix_t <= self.config.gnss_timeout_s:
            self._aligner.add_imu(accel, gyro)  # calibration data only while GPS is available
        if not self._initialised:
            return
        dt = t - self._t if self._t is not None else 0.0
        self._t = t
        if dt <= 0.0:
            return
        axes = self._axes
        if axes is None:  # alignment not ready yet: coast with the last GPS velocity
            self._e += self._v * math.cos(self._psi) * dt
            self._n += self._v * math.sin(self._psi) * dt
            return
        f, u = axes.forward, axes.up
        a_fwd = f[0] * accel[0] + f[1] * accel[1] + f[2] * accel[2]
        w_up = u[0] * gyro[0] + u[1] * gyro[1] + u[2] * gyro[2]
        if self.config.calibrate_gyro_bias:
            w_up -= axes.gyro_bias_up
        v_new = max(self._v + a_fwd * dt, 0.0)
        psi_new = self._psi + w_up * dt
        v_mid, psi_mid = 0.5 * (self._v + v_new), 0.5 * (self._psi + psi_new)  # midpoint integration
        self._e += v_mid * math.cos(psi_mid) * dt
        self._n += v_mid * math.sin(psi_mid) * dt
        self._v, self._psi = v_new, psi_new

    def state(self) -> StateEstimate | None:
        if not self._initialised or self._t is None:
            return None
        gnss = self._t - self._last_fix_t <= self.config.gnss_timeout_s
        return StateEstimate(
            t=self._t,
            east=self._e,
            north=self._n,
            speed=self._v,
            heading=self._psi,
            mode="gnss" if gnss else "dead_reckoning",
        )

    @property
    def alignment(self) -> Alignment | None:
        """Axes in use, including an injected calibration error (diagnostics)."""
        return self._axes


class RawDeadReckoning(VehicleDeadReckoning):
    name = "dr_raw"
    label = "DR raw IMU (assumed aligned mount)"

    def __init__(self, route: RouteMap, calibration_error: NDArray[np.float64] | None = None) -> None:
        super().__init__(
            route,
            DeadReckoningConfig(alignment="assume_aligned", calibrate_gyro_bias=False),
            calibration_error,
        )


class CalibratedDeadReckoning(VehicleDeadReckoning):
    name = "dr_calibrated"
    label = "DR GPS-calibrated IMU"

    def __init__(self, route: RouteMap, calibration_error: NDArray[np.float64] | None = None) -> None:
        super().__init__(
            route, DeadReckoningConfig(alignment="estimate", calibrate_gyro_bias=True), calibration_error
        )


class FilteredDeadReckoning(VehicleDeadReckoning):
    name = "dr_filtered"
    label = "DR calibrated + GPS-blended speed/heading"

    def __init__(self, route: RouteMap, calibration_error: NDArray[np.float64] | None = None) -> None:
        super().__init__(
            route,
            DeadReckoningConfig(
                alignment="estimate",
                calibrate_gyro_bias=True,
                blend_speed_tau_s=5.0,
                blend_heading_tau_s=10.0,
            ),
            calibration_error,
        )
