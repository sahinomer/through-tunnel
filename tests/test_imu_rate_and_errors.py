"""Phone IMU sample rate and sensor imperfections (white noise, constant bias)."""

import json

import numpy as np
import pytest

from throughtunnel.randomness import rng_stream
from throughtunnel.scenario import (
    SCHEMA_VERSION,
    ScenarioConfig,
    load_preset,
    load_scenario,
    run_scenario,
    save_scenario,
    scenario_from_json,
    with_imu_config,
)
from throughtunnel.sensors.errors import (
    DEFAULT_ACCEL_BIAS,
    DEFAULT_ACCEL_NOISE_DENSITY,
    DEFAULT_GYRO_NOISE_DENSITY,
    MG,
    ImuErrorConfig,
    SensorErrorConfig,
    apply_sensor_errors,
)
from throughtunnel.sensors.imu import ImuConfig, normal_gravity
from throughtunnel.vehicle.truth import build_ground_truth


@pytest.fixture(scope="module")
def base():
    """Demo track, 100 Hz vehicle simulation, default (noisy, biased) 200 Hz phone IMU."""
    return run_scenario(load_preset("synthetic_demo_track"))


def errors(accel: dict | None = None, gyro: dict | None = None, **kw) -> ImuErrorConfig:
    ideal = ImuErrorConfig.ideal()
    return ImuErrorConfig(
        accel=ideal.accel.model_copy(update=accel or {}), gyro=ideal.gyro.model_copy(update=gyro or {}), **kw
    )


def rerun(result, **imu_update):
    return with_imu_config(result, result.config.imu.model_copy(update=imu_update))


# ------------------------------------------------------------------ sample rate
def test_defaults(base):
    assert base.config.sample_rate_hz == 100.0
    assert base.config.imu.rate_hz == 200.0
    assert base.config.imu.errors.accel.noise_enabled and base.config.imu.errors.accel.bias_enabled
    assert base.config.imu.errors.gyro.noise_enabled and base.config.imu.errors.gyro.bias_enabled


@pytest.mark.parametrize("rate", [50.0, 200.0, 416.0])
def test_imu_timestamps_are_its_own_constant_rate_clock(base, rate):
    res = rerun(base, rate_hz=rate)
    t = res.imu.t
    assert t[0] == 0.0
    assert np.allclose(t, np.arange(len(t)) / rate, rtol=0, atol=1e-12)
    assert np.allclose(np.diff(t), 1.0 / rate)  # constant during the run
    assert t[-1] <= base.truth.t[-1] + 1e-12 < t[-1] + 1.0 / rate
    assert res.imu.rate_hz == pytest.approx(rate)
    assert np.array_equal(res.imu.t, res.imu_ideal.t)


def test_faster_than_simulation_gives_new_exact_samples_not_duplicates(base):
    """400 Hz phone IMU on a 100 Hz vehicle simulation: in-between samples come from the exact
    continuous-time motion (constant jerk between steps), not from repeating the 100 Hz values."""
    res = with_imu_config(base, ImuConfig(rate_hz=400.0, errors=ImuErrorConfig.ideal()))
    imu, tr = res.imu, base.truth
    # Longitudinal acceleration is piecewise linear in time -> linear interpolation is exact.
    assert np.allclose(imu.accel[:, 0], np.interp(imu.t, tr.t, tr.accel_long), atol=1e-12)
    # Lateral acceleration and yaw rate from the exact state, evaluated independently here.
    exact = base.motion.at(imu.t)
    geo = base.path.evaluate(exact.s)
    assert np.allclose(imu.accel[:, 1], geo.curvature * exact.v**2, atol=1e-12)
    assert np.allclose(imu.gyro[:, 2], geo.curvature * exact.v, atol=1e-14)
    # Not sample-and-hold: off-grid samples differ from the preceding 100 Hz sample.
    off_grid = np.arange(len(imu.t)) % 4 != 0
    held = tr.accel_lat[np.searchsorted(tr.t, imu.t, side="right") - 1]
    assert np.mean(imu.accel[off_grid, 1] != held[off_grid]) > 0.99


def test_fast_imu_is_consistent_with_differentiated_position(base):
    """End-to-end at 400 Hz: second difference of the exact vehicle position = measured acceleration."""
    rate = 400.0
    res = with_imu_config(base, ImuConfig(rate_hz=rate, errors=ImuErrorConfig.ideal()))
    kin = build_ground_truth(base.motion.at(res.imu.t), base.path)
    dt = 1.0 / rate
    ax = (kin.x[2:] - 2 * kin.x[1:-1] + kin.x[:-2]) / dt**2
    ay = (kin.y[2:] - 2 * kin.y[1:-1] + kin.y[:-2]) / dt**2
    c, s = np.cos(kin.yaw[1:-1]), np.sin(kin.yaw[1:-1])
    # Exact sampling leaves ~2e-4 (finite-difference error); repeating the 100 Hz values would leave
    # 2e-2 forward and 7e-3 lateral, so this tolerance also rules out sample-and-hold.
    assert np.abs(c * ax + s * ay - res.imu.accel[1:-1, 0]).max() < 1e-3
    assert np.abs(-s * ax + c * ay - res.imu.accel[1:-1, 1]).max() < 1e-3


def test_slower_than_simulation_samples_at_its_own_times(base):
    res = with_imu_config(base, ImuConfig(rate_hz=50.0, errors=ImuErrorConfig.ideal()))
    tr = base.truth
    assert np.allclose(res.imu.accel[:, 0], tr.accel_long[::2][: len(res.imu)], atol=1e-12)
    assert np.allclose(res.imu.accel[:, 2], normal_gravity(tr.lat[::2][: len(res.imu)]), atol=1e-12)


# ------------------------------------------------------------------ enable / disable, ideal kept
def test_disabled_errors_reproduce_ideal_exactly(base):
    res = rerun(base, errors=ImuErrorConfig.ideal())
    assert np.array_equal(res.imu.accel, res.imu_ideal.accel)
    assert np.array_equal(res.imu.gyro, res.imu_ideal.gyro)
    assert np.all(res.imu_errors.accel.bias == 0) and res.imu_errors.accel.noise_std == 0


def test_ideal_stream_is_kept_and_unaffected_by_errors(base):
    ideal_run = rerun(base, errors=ImuErrorConfig.ideal())
    assert np.array_equal(base.imu_ideal.accel, ideal_run.imu.accel)
    assert not np.allclose(base.imu.accel, base.imu_ideal.accel)
    assert base.imu_ideal.source == "simulated:ideal" and base.imu.source == "simulated:measured"


# ------------------------------------------------------------------ bias
def test_bias_only_is_a_constant_offset_with_the_configured_magnitude(base):
    res = rerun(base, errors=errors(accel={"bias_enabled": True}, gyro={"bias_enabled": True}))
    for meas, ideal, real, mag in (
        (
            res.imu.accel,
            res.imu_ideal.accel,
            res.imu_errors.accel,
            res.config.imu.errors.accel.bias_magnitude,
        ),
        (res.imu.gyro, res.imu_ideal.gyro, res.imu_errors.gyro, res.config.imu.errors.gyro.bias_magnitude),
    ):
        diff = meas - ideal
        assert np.allclose(diff, diff[0], atol=1e-12)  # constant over the run
        assert np.allclose(diff[0], real.bias, atol=1e-12)
        assert np.linalg.norm(real.bias) == pytest.approx(mag)


def test_explicit_bias_vector():
    rng_a, rng_b = rng_stream(0, "a"), rng_stream(0, "b")
    cfg = SensorErrorConfig(noise_enabled=False, bias_vector=(0.1, -0.2, 0.05), bias_magnitude=9.0)
    out, real = apply_sensor_errors(np.zeros((10, 3)), 100.0, cfg, rng_a, rng_b)
    assert np.allclose(out, [0.1, -0.2, 0.05]) and np.allclose(real.bias, [0.1, -0.2, 0.05])


def test_bias_shifts_a_stationary_reading_by_mg():
    cfg = SensorErrorConfig(noise_enabled=False, bias_vector=(0.0, 0.0, 20 * MG))
    out, _ = apply_sensor_errors(
        np.full((5, 3), [0.0, 0.0, 9.80665]), 100.0, cfg, rng_stream(1, "n"), rng_stream(1, "b")
    )
    assert np.allclose(out[:, 2], 9.80665 * 1.02)


# ------------------------------------------------------------------ white noise
def noise_only(nd: float, rate: float, n: int, seed: int = 0):
    cfg = SensorErrorConfig(noise_density=nd, bias_enabled=False)
    out, real = apply_sensor_errors(np.zeros((n, 3)), rate, cfg, rng_stream(seed, "n"), rng_stream(seed, "b"))
    return out, real


def test_noise_statistics():
    nd, rate = DEFAULT_ACCEL_NOISE_DENSITY, 200.0
    x, real = noise_only(nd, rate, 200_000)
    sigma = nd * np.sqrt(rate)
    assert real.noise_std == pytest.approx(sigma)
    assert np.abs(x.mean(axis=0)).max() < 5 * sigma / np.sqrt(len(x))  # zero mean
    assert x.std(axis=0) == pytest.approx([sigma] * 3, rel=0.01)
    lag1 = [np.corrcoef(x[:-1, k], x[1:, k])[0, 1] for k in range(3)]
    assert np.abs(lag1).max() < 0.01  # white: uncorrelated in time
    cross = np.corrcoef(x.T)[np.triu_indices(3, 1)]
    assert np.abs(cross).max() < 0.01  # independent axes


@pytest.mark.parametrize("rate", [100.0, 400.0])
def test_noise_density_is_rate_independent(rate):
    """Per-sample std grows with sqrt(rate), but the 1-s average (Allan deviation at tau = 1 s)
    equals the noise density for any rate: the physically meaningful quantity is preserved."""
    nd = DEFAULT_GYRO_NOISE_DENSITY
    x, real = noise_only(nd, rate, int(rate) * 4000)
    assert real.noise_std == pytest.approx(nd * np.sqrt(rate))
    one_second_means = x[:, 0].reshape(-1, int(rate)).mean(axis=1)
    assert one_second_means.std() == pytest.approx(nd, rel=0.05)


def test_noise_on_the_simulated_stream(base):
    res = rerun(base, errors=errors(accel={"noise_enabled": True}, gyro={"noise_enabled": True}))
    for meas, ideal, nd in (
        (res.imu.accel, res.imu_ideal.accel, res.config.imu.errors.accel.noise_density),
        (res.imu.gyro, res.imu_ideal.gyro, res.config.imu.errors.gyro.noise_density),
    ):
        resid = meas - ideal
        assert resid.std(axis=0) == pytest.approx([nd * np.sqrt(200.0)] * 3, rel=0.03)
    corr = np.corrcoef(
        res.imu.accel[:, 0] - res.imu_ideal.accel[:, 0], res.imu.gyro[:, 0] - res.imu_ideal.gyro[:, 0]
    )
    assert abs(corr[0, 1]) < 0.03  # accelerometer and gyroscope noise are independent


# ------------------------------------------------------------------ independence and determinism
def test_sources_are_independent(base):
    cfg = base.config.imu.errors
    no_accel_noise = rerun(
        base, errors=cfg.model_copy(update={"accel": cfg.accel.model_copy(update={"noise_enabled": False})})
    )
    assert np.array_equal(no_accel_noise.imu.gyro, base.imu.gyro)  # gyro untouched
    assert np.array_equal(no_accel_noise.imu_errors.accel.bias, base.imu_errors.accel.bias)  # bias untouched
    no_gyro_bias = rerun(
        base, errors=cfg.model_copy(update={"gyro": cfg.gyro.model_copy(update={"bias_enabled": False})})
    )
    assert np.array_equal(no_gyro_bias.imu.accel, base.imu.accel)


def test_magnitude_rescales_the_same_noise_realisation(base):
    one = rerun(base, errors=errors(accel={"noise_enabled": True}))
    two = rerun(
        base, errors=errors(accel={"noise_enabled": True, "noise_density": 2 * DEFAULT_ACCEL_NOISE_DENSITY})
    )
    r1 = one.imu.accel - one.imu_ideal.accel
    r2 = two.imu.accel - two.imu_ideal.accel
    assert np.allclose(r2, 2 * r1, atol=1e-12)


def test_deterministic_with_seed(base):
    again = run_scenario(base.config)
    assert np.array_equal(again.imu.accel, base.imu.accel) and np.array_equal(again.imu.gyro, base.imu.gyro)
    other_noise = rerun(base, errors=base.config.imu.errors.model_copy(update={"seed": 1234}))
    assert not np.allclose(other_noise.imu.accel, base.imu.accel)
    # A separate sensor seed changes only the sensor errors: same drive, same ideal readings.
    assert np.array_equal(other_noise.imu_ideal.accel, base.imu_ideal.accel)
    assert other_noise.truth is base.truth
    assert np.linalg.norm(other_noise.imu_errors.accel.bias) == pytest.approx(DEFAULT_ACCEL_BIAS)


def test_scenario_seed_drives_sensor_errors_by_default(base):
    other = run_scenario(base.config.model_copy(update={"seed": base.config.seed + 1}))
    assert not np.allclose(other.imu_errors.accel.bias, base.imu_errors.accel.bias)


# ------------------------------------------------------------------ persistence
def test_v2_scenarios_migrate_to_ideal_imu_at_simulation_rate():
    v3 = load_preset("synthetic_demo_track").model_dump(mode="json")
    v2 = {
        **v3,
        "schema_version": 2,
        "imu": {k: v3["imu"][k] for k in ("mount", "gravity_model", "earth_rotation")},
    }
    del v2["tunnel"]  # v2 files had no tunnel section
    cfg = scenario_from_json(json.dumps(v2))
    assert cfg.schema_version == SCHEMA_VERSION
    assert cfg.tunnel is not None and cfg.tunnel.entrance_m == 0.0  # legacy: whole route GPS-denied
    assert cfg.imu.rate_hz == cfg.sample_rate_hz
    assert cfg.imu.errors == ImuErrorConfig.ideal()


def test_new_configs_are_not_migrated():
    cfg = ScenarioConfig(route=load_preset("synthetic_demo_track").route)
    assert cfg.imu.rate_hz == 200.0 and cfg.imu.errors.accel.noise_enabled


def test_error_config_round_trips(tmp_path, base):
    cfg = base.config.model_copy(
        update={
            "imu": base.config.imu.model_copy(
                update={"rate_hz": 416.0, "errors": errors(gyro={"bias_enabled": True}, seed=7)}
            )
        }
    )
    save_scenario(cfg, tmp_path / "s.json")
    assert load_scenario(tmp_path / "s.json") == cfg
