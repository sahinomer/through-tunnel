"""Time-domain longitudinal motion along the path.

State: arc length s, speed v, acceleration a. The driver/powertrain is modelled
as a jerk-limited tracker of the planned reference speed:

    a_cmd = clip(a_ref(s_p) + K_v (v_ref(s_p) - v), -a_dec, +a_acc)
    j     = clip(K_a (a_cmd - a), -j_max, +j_max)

with a preview point s_p = s + v * T_p that compensates the lag introduced by
the jerk limit. The jerk is held constant over each step and the state is
integrated *exactly* (cubic in time), so a = dv/dt and v = ds/dt hold to
machine precision at every sample: the ground truth is self-consistent by
construction rather than by numerical differentiation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from throughtunnel.vehicle.config import DriverConfig
from throughtunnel.vehicle.speed_profile import SpeedProfile

MAX_DURATION_S = 3 * 3600.0


@dataclass(frozen=True)
class LongitudinalTrajectory:
    t: NDArray[np.float64]
    s: NDArray[np.float64]
    v: NDArray[np.float64]
    a: NDArray[np.float64]
    jerk: NDArray[np.float64]  # jerk applied on [t_k, t_k + dt)


def simulate_longitudinal(
    profile: SpeedProfile, length_m: float, driver: DriverConfig, dt: float
) -> LongitudinalTrajectory:
    v_ref = profile.v_ref.tolist()
    a_ref = profile.a_ref.tolist()
    h = profile.step
    n_grid = len(v_ref)

    def lookup(table: list[float], s: float) -> float:
        x = s / h
        i = int(x)
        if i >= n_grid - 1:
            return table[-1]
        f = x - i
        return table[i] * (1.0 - f) + table[i + 1] * f

    k_v, k_a = driver.speed_tracking_gain, driver.accel_response_rate
    a_lo, a_hi, j_max = -driver.max_decel, driver.max_accel, driver.max_jerk
    t_p = driver.preview_time_s

    s, v, a, t = 0.0, v_ref[0], 0.0, 0.0
    ts, ss, vs, accs, js = [], [], [], [], []
    dt2, dt3 = dt * dt / 2.0, dt**3 / 6.0
    while s <= length_m:
        s_p = s + v * t_p
        a_cmd = lookup(a_ref, s_p) + k_v * (lookup(v_ref, s_p) - v)
        a_cmd = min(max(a_cmd, a_lo), a_hi)
        j = min(max(k_a * (a_cmd - a), -j_max), j_max)

        ts.append(t)
        ss.append(s)
        vs.append(v)
        accs.append(a)
        js.append(j)

        s += v * dt + a * dt2 + j * dt3
        v += a * dt + j * dt2
        a += j * dt
        t += dt
        if v <= 0.0:
            raise RuntimeError(f"vehicle stopped at s={s:.1f} m; the speed profile is inconsistent")
        if t > MAX_DURATION_S:
            raise RuntimeError("simulation exceeded the maximum duration")

    return LongitudinalTrajectory(
        t=np.arange(len(ts)) * dt,  # avoids accumulated floating-point drift in t
        s=np.asarray(ss),
        v=np.asarray(vs),
        a=np.asarray(accs),
        jerk=np.asarray(js),
    )
