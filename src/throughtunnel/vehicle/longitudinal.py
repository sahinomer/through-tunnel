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

Traffic stops (D37). Before the next stop the reference is additionally capped by the braking curve
v = sqrt(2 b (s_stop - s)) with a_ref = -b. Close to rest the tracker hands over to a final
manoeuvre with the constant jerk j = a^2 / (2 v): speed and acceleration then reach zero together
after T = 2 v / |a|, so the vehicle comes to rest without an acceleration jump (v(tau) = j (T - tau)^2 / 2
never becomes negative). The state is snapped to exact rest at the end of the step that contains T;
the snap is below j*dt in acceleration and j*dt^2/2 in speed (< 0.02 m/s^2 and < 1e-4 m/s). The
vehicle then stands still for the stop's duration (time-based) and pulls away along the curve
v = sqrt(2 a_go (s - s_rest)) with a_ref = +a_go.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from throughtunnel.vehicle.config import DriverConfig
from throughtunnel.vehicle.speed_profile import SpeedProfile
from throughtunnel.vehicle.traffic import TrafficPlan

MAX_DURATION_S = 3 * 3600.0
FINAL_STOP_JERK_FRACTION = 0.5  # the final stop starts once j = a^2/(2v) reaches this fraction of j_max
FINAL_STOP_RANGE_M = 30.0  # ... and only this close to a stop
PULL_AWAY_RANGE_M = 1000.0  # the pull-away curve is ignored beyond this distance from the stop


@dataclass(frozen=True)
class LongitudinalTrajectory:
    t: NDArray[np.float64]
    s: NDArray[np.float64]
    v: NDArray[np.float64]
    a: NDArray[np.float64]
    jerk: NDArray[np.float64]  # jerk applied on [t_k, t_k + dt)

    def at(self, times: ArrayLike) -> LongitudinalTrajectory:
        """Exact state at arbitrary times within the run.

        The jerk is constant between samples, so s, v, a are exact cubic/quadratic/linear
        polynomials there. This gives physically consistent values at any timestamp (e.g. a phone
        IMU sampling faster than the simulation) instead of duplicated or interpolated samples.
        """
        t = np.asarray(times, dtype=float)
        if t.size and (t.min() < self.t[0] - 1e-12 or t.max() > self.t[-1] + 1e-9):
            raise ValueError("requested times are outside the simulated interval")
        k = np.clip(np.searchsorted(self.t, t, side="right") - 1, 0, len(self.t) - 1)
        tau = t - self.t[k]
        s0, v0, a0, j = self.s[k], self.v[k], self.a[k], self.jerk[k]
        return LongitudinalTrajectory(
            t=t,
            s=s0 + v0 * tau + a0 * tau**2 / 2.0 + j * tau**3 / 6.0,
            v=v0 + a0 * tau + j * tau**2 / 2.0,
            a=a0 + j * tau,
            jerk=j,
        )


def simulate_longitudinal(
    profile: SpeedProfile,
    length_m: float,
    driver: DriverConfig,
    dt: float,
    traffic: TrafficPlan | None = None,
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

    stops = sorted(traffic.stops, key=lambda st: st.at_m) if traffic is not None else []
    b_stop = traffic.stop_decel if traffic is not None else 0.0
    a_go = traffic.go_accel if traffic is not None else 0.0
    next_stop = 0  # index of the next stop to serve
    mode = "drive"  # "drive" | "final" (constant-jerk stop) | "stopped"
    final_j = 0.0
    standing_steps = 0
    rest_at: float | None = None  # where the vehicle last stood still (start of the pull-away curve)

    s, v, a, t = 0.0, v_ref[0], 0.0, 0.0
    ts, ss, vs, accs, js = [], [], [], [], []
    dt2, dt3 = dt * dt / 2.0, dt**3 / 6.0
    while s <= length_m:
        if mode == "stopped":
            j = 0.0
        elif mode == "final":
            j = final_j
        else:
            s_p = s + v * t_p
            v_t, a_t = lookup(v_ref, s_p), lookup(a_ref, s_p)
            approaching = False
            if next_stop < len(stops):
                v_env = math.sqrt(2.0 * b_stop * max(stops[next_stop].at_m - s_p, 0.0))
                if v_env < v_t:
                    v_t, a_t, approaching = v_env, -b_stop, True
            if rest_at is not None:
                if s_p - rest_at > PULL_AWAY_RANGE_M:
                    rest_at = None
                else:
                    v_go = math.sqrt(2.0 * a_go * max(s_p - rest_at, 0.0))
                    if v_go < v_t:
                        v_t, a_t = v_go, a_go
            a_cmd = a_t + k_v * (v_t - v)
            a_cmd = min(max(a_cmd, a_lo), a_hi)
            j = min(max(k_a * (a_cmd - a), -j_max), j_max)
            near = next_stop < len(stops) and stops[next_stop].at_m - s < FINAL_STOP_RANGE_M
            if approaching and near and a < 0.0 and a * a / (2.0 * v) >= FINAL_STOP_JERK_FRACTION * j_max:
                mode, final_j = "final", a * a / (2.0 * v)
                j = final_j

        ts.append(t)
        ss.append(s)
        vs.append(v)
        accs.append(a)
        js.append(j)

        s += v * dt + a * dt2 + j * dt3
        v += a * dt + j * dt2
        a += j * dt
        t += dt
        if mode == "final" and a >= 0.0:  # passed the instant of rest within this step: snap to rest
            v = a = 0.0
            mode = "stopped"
            standing_steps = max(1, round(stops[next_stop].duration_s / dt))
        elif mode == "stopped":
            standing_steps -= 1
            if standing_steps <= 0:
                mode, rest_at = "drive", s
                next_stop += 1
        elif v <= 0.0:
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
