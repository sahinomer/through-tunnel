"""Route-constrained Kalman filter (D51): phone-only, tracks the forward offset across re-solves of the
calibration, estimates a constant offset from the GPS speed, and reports a growing uncertainty."""

import numpy as np
import pytest

from throughtunnel.evaluation.error_sources import BY_KEY, run_config
from throughtunnel.geodesy import normal_gravity
from throughtunnel.positioning import MAIN_ESTIMATORS, align_imu, run_estimator
from throughtunnel.positioning.alignment import GpsImuAlignment
from throughtunnel.positioning.route_kalman import RouteKalman
from throughtunnel.positioning.runner import replay
from throughtunnel.scenario import run_scenario, with_calibration
from throughtunnel.sensors.errors import MG
from throughtunnel.sensors.mounting import CalibrationErrorConfig


@pytest.fixture(scope="module")
def realistic():
    return run_scenario(run_config(BY_KEY["realistic"], 1, "free"))


def test_registered_as_phone_only():
    assert "route_kf" in MAIN_ESTIMATORS
    assert not RouteKalman.uses_standstill and not RouteKalman.uses_vehicle_speed


def test_offset_shift_reports_how_a_re_solve_moves_the_forward_offset(realistic):
    """The stage's forward offset jumps by ~0.85 mg rms from fix to fix; the reported shift must match."""
    res = realistic
    obs = res.observations()
    up = res.config.imu.mount.rotation_body_from_phone().T @ np.eye(3)[:, 2]
    g = float(normal_gravity(res.truth.lat[0]))
    pairs = []

    class Logged(GpsImuAlignment):
        def _use(self, axes):
            before = self._pending_shift
            old = None if self._axes is None else float(self._axes.forward @ (g * up))
            super()._use(axes)
            if old is not None:
                pairs.append((float(self._axes.forward @ (g * up)) - old, self._pending_shift - before))

    align_imu(Logged(obs.route), obs)
    d = np.array(pairs) / MG
    assert len(d) > 30 and np.sqrt(np.mean(d[:, 0] ** 2)) > 0.3  # the jumps are real
    assert np.sqrt(np.mean((d[:, 1] - d[:, 0]) ** 2)) < 0.02  # and reported to within 0.02 mg rms


def test_yaw_shift_reports_how_a_re_solve_turns_the_forward_axis(realistic):
    """With realistic sensors the stage's yaw jumps by ~0.5° rms from fix to fix (step 4.1); the reported
    shift must match the change of the lateral leak factor F·L."""
    res = realistic
    obs = res.observations()
    left = res.config.imu.mount.rotation_body_from_phone().T @ np.eye(3)[:, 1]
    pairs = []

    class Logged(GpsImuAlignment):
        def _use(self, axes):
            before = self._pending_yaw
            old = None if self._axes is None else float(self._axes.forward @ left)
            super()._use(axes)
            if old is not None:
                pairs.append((float(self._axes.forward @ left) - old, self._pending_yaw - before))

    align_imu(Logged(obs.route), obs)
    d = np.degrees(np.array(pairs))
    assert len(d) > 30 and np.sqrt(np.mean(d[:, 0] ** 2)) > 0.2  # the jumps are real
    assert np.sqrt(np.mean((d[:, 1] - d[:, 0]) ** 2)) < 0.005  # and reported to within 0.005° rms


def test_a_calibration_yaw_error_is_estimated(realistic):
    """A 2° yaw residual leaks lateral acceleration into the forward channel on the approach curves; the
    yaw state must find it from the GPS speed (step 4.1), here on top of the calibration's natural
    residual (realistic sensors)."""
    yaw_only = CalibrationErrorConfig(enabled=True, pitch_deg=0.0, yaw_deg=2.0, roll_deg=0.0)
    res = with_calibration(realistic, yaw_only)
    obs = res.observations()
    stage = GpsImuAlignment(obs.route, res.config.calibration.rotation_error())
    stream = align_imu(stage, obs)
    kf = RouteKalman(obs.route)
    seen = {}
    orig = kf.on_imu

    def on_imu(t, imu):
        if t >= res.gnss_events.loss_t and "psi" not in seen:
            seen["psi"] = kf.yaw
        orig(t, imu)

    kf.on_imu = on_imu
    replay(kf, obs, stream)
    left = res.config.imu.mount.rotation_body_from_phone().T @ np.eye(3)[:, 1]
    actual = np.degrees(float(stage.alignment.forward @ left))  # residual of the axes in use at loss
    assert actual > 1.0  # the injected yaw dominates
    assert abs(np.degrees(seen["psi"]) - actual) < 0.6  # found within the natural residual's spread


def test_a_constant_calibration_offset_is_estimated(realistic):
    """A 0.1° pitch residual (and nothing else injected; the config's default yaw and roll errors are set
    to 0) adds ~1.7 mg to the forward offset; the offset state must find it from the GPS speed over the
    approach (realistic sensors)."""
    from throughtunnel.evaluation.error_sources import alignment_at_loss

    pitch_only = CalibrationErrorConfig(enabled=True, pitch_deg=0.1, yaw_deg=0.0, roll_deg=0.0)
    res = with_calibration(realistic, pitch_only)
    obs = res.observations()
    kf = RouteKalman(obs.route)
    seen = {}
    orig = kf.on_imu

    def on_imu(t, imu):
        if t >= res.gnss_events.loss_t and "b" not in seen:
            seen["b"] = kf.offset
        orig(t, imu)

    kf.on_imu = on_imu
    run_estimator(kf, obs, calibration_error=res.config.calibration.rotation_error())
    actual = alignment_at_loss(res)["forward_offset_mg"]
    assert actual < -1.0  # the injected pitch dominates the offset
    assert abs(seen["b"] / MG - actual) < 0.5 * abs(actual)  # most of it found (here ~2/3: yaw leak, noise)


def test_without_the_yaw_state_the_first_version_is_reproduced():
    """yaw_state = False with the first version's turn noise is D51 bit for bit (error at C of the
    milestone_step4 error-source run: realistic, free flow, seed 0)."""
    from throughtunnel.evaluation.metrics import evaluate_track
    from throughtunnel.evaluation.route_kf_check import FirstVersion

    res = run_scenario(run_config(BY_KEY["realistic"], 0, "free"))
    obs = res.observations()
    ev = evaluate_track(run_estimator(FirstVersion(obs.route), obs), res)
    assert ev.summary["exit_total_m"] == pytest.approx(45.100051, abs=1e-5)


def test_uncertainty_grows_in_the_tunnel(realistic):
    obs = realistic.observations()
    track = run_estimator(RouteKalman(obs.route), obs)
    sec = realistic.sections
    std = track.position_std_m
    assert np.all(np.isfinite(std)) and np.all(std >= 0.0)
    at_b = std[np.searchsorted(track.t, sec.entrance_t + 5.0)]
    at_c = std[np.searchsorted(track.t, sec.exit_t - 1.0)]
    assert at_c > 10.0 * at_b
