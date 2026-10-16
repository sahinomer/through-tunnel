"""Calibration fixes F1–F3 (D48, residual_study.md): gravity, interval timing, grade in the yaw fit."""

import math

import numpy as np
import pytest

from throughtunnel.geodesy import STANDARD_GRAVITY, normal_gravity
from throughtunnel.observations import GnssFix
from throughtunnel.positioning import portal
from throughtunnel.positioning.map_grade import GradeCompensation
from throughtunnel.positioning.mount_estimation import MountAlignmentEstimator


# ------------------------------------------------------------------ F1: gravity
def test_one_gravity_definition_for_simulator_and_estimators():
    """Simulator and estimators share geodesy.normal_gravity (known values in test_sensors.py)."""
    import throughtunnel.positioning.map_grade as mg
    import throughtunnel.sensors.imu as imu

    assert imu.normal_gravity is normal_gravity and mg.normal_gravity is normal_gravity
    assert not hasattr(mg, "GRAVITY")


def test_grade_compensation_uses_normal_gravity_at_the_route(monkeypatch):
    from throughtunnel.scenario import MapDataConfig, load_preset, run_scenario, with_map_data

    res = with_map_data(run_scenario(load_preset("eisenhower_tunnel")), MapDataConfig(road_grade=True))
    comp = GradeCompensation(res.route_map)
    assert comp.gravity == float(normal_gravity(float(res.route_map.lat[0])))
    assert comp.gravity < STANDARD_GRAVITY - 4e-3  # 39.7° N: ~0.05 % below standard gravity
    monkeypatch.setattr(GradeCompensation, "use_normal_gravity", False)
    assert GradeCompensation(res.route_map).gravity == STANDARD_GRAVITY


# ------------------------------------------------------------------ F2: interval timing
def _fix(t: float, speed: float = 10.0) -> GnssFix:
    return GnssFix(t=t, lat=0.0, lon=0.0, horizontal_accuracy_m=3.0, speed_mps=speed, bearing_deg=90.0,
                   speed_accuracy_mps=0.2, bearing_accuracy_deg=1.0)  # fmt: skip


@pytest.mark.parametrize("offset", [0.0, 0.0013, 0.0037])
def test_interval_means_are_time_averages(offset):
    """A ramp a(t) = c·t: each GPS interval's mean must be c × the interval midpoint, whether or not the
    IMU clock is aligned with the fixes (before F2 it lagged by half a sample)."""
    c, h = 0.7, 1.0 / 200.0
    est = MountAlignmentEstimator()
    samples = np.arange(offset, 10.1, h)
    fix_times = np.arange(1.0, 10.0 + 1e-9, 1.0)
    j = 0
    for t in samples:  # fixes strictly before the sample first, as the runner orders them
        while j < len(fix_times) and fix_times[j] < t - 1e-12:
            est.add_fix(_fix(fix_times[j]))
            j += 1
        est.add_imu([c * t, 0.0, 9.8], [0.0, 0.0, 0.0], float(t))
        while j < len(fix_times) and fix_times[j] <= t + 1e-12:
            est.add_fix(_fix(fix_times[j]))
            j += 1
    rows = est._rows
    assert len(rows) == len(fix_times) - 1
    for r in rows:
        t_end, dt = r[7], r[2]
        assert r[0][0] == pytest.approx(c * (t_end - 0.5 * dt), abs=1e-9)


def test_interval_after_a_start_or_gap_covers_the_whole_interval():
    """The stage adds IMU samples only once fixes arrive, so the first interval has no sample at its
    start. Its coverage must still begin at the fix (a 1.5-sample hole biased the levelling by up to
    0.003 mg in the first F2 version)."""
    c, h = 0.7, 1.0 / 200.0
    est = MountAlignmentEstimator()
    est.add_fix(_fix(1.0))  # first fix; the sample at 1.0 came before it and was not added
    for k in range(1, 401):  # samples from 1.005 to 3.0, fixes at 2.0 and 3.0 after their samples
        t = 1.0 + k * h
        est.add_imu([c * t, 0.0, 9.8], [0.0, 0.0, 0.0], t)
        if k % 200 == 0:
            est.add_fix(_fix(t))
    for r in est._rows:
        # the first sample stands in for the time back to the fix: O(h²), ≤ 2 % of the old lag c·h/2
        assert r[0][0] == pytest.approx(c * (r[7] - 0.5 * r[2]), abs=0.02 * 0.5 * c * h)


# ------------------------------------------------------------------ F3: grade in the yaw fit
def test_grade_ramp_in_the_calibration_window_leaves_no_yaw_error(monkeypatch):
    """Eisenhower +2 % climb, ideal sensors, freeze off: the ramp starts inside the calibration window.
    Before F3 the yaw estimate was 0.34° off with perfect sensors."""
    from throughtunnel.evaluation.residual_study import simulate, stage_at_loss

    monkeypatch.setattr(portal, "FREEZE_BEFORE_ENTRANCE_M", None)
    res = simulate("eisenhower_tunnel", "up2", "free")
    a = stage_at_loss(res).alignment
    r_bs = res.config.imu.mount.rotation_body_from_phone()
    fwd, left = (r_bs.T @ np.eye(3)[:, k] for k in range(2))
    yaw = math.degrees(math.atan2(float(a.forward @ left), float(a.forward @ fwd)))
    assert abs(yaw) < 0.02
