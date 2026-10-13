"""IMU bias drift and GPS degradation before the tunnel portal (D38): both off by default."""

import math

import numpy as np
import pytest

from throughtunnel.scenario import load_preset, run_scenario, truth_at, with_sensor_config
from throughtunnel.sensors.errors import DEG, MDPS, MG, ImuErrorConfig, gauss_markov_series
from throughtunnel.sensors.gnss import GnssConfig


@pytest.fixture(scope="module")
def demo():
    return run_scenario(load_preset("synthetic_demo_track"))


def with_drift(cfg_imu, accel_sigma=0.5 * MG, gyro_sigma=5.0 * MDPS, tau=300.0, on=True):
    e = cfg_imu.errors

    def upd(sensor, sigma):
        return sensor.model_copy(update={"drift_enabled": on, "drift_sigma": sigma, "drift_tau_s": tau})

    errors = e.model_copy(update={"accel": upd(e.accel, accel_sigma), "gyro": upd(e.gyro, gyro_sigma)})
    return cfg_imu.model_copy(update={"errors": errors})


# ------------------------------------------------------------------ bias drift
def test_gauss_markov_series_statistics():
    rng = np.random.default_rng(0)
    x = gauss_markov_series(rng.standard_normal((400_000, 1)), 0.1, 2.0, 30.0)[:, 0]
    assert x.std() == pytest.approx(2.0, rel=0.05)
    lag = 300  # samples = one correlation time
    assert np.corrcoef(x[:-lag], x[lag:])[0, 1] == pytest.approx(math.exp(-1.0), abs=0.05)


def test_drift_off_by_default_and_defaults_are_set():
    e = ImuErrorConfig()
    assert not e.accel.drift_enabled and not e.gyro.drift_enabled
    assert e.accel.drift_sigma == pytest.approx(0.5 * MG) and e.gyro.drift_sigma == pytest.approx(5 * MDPS)


def test_drift_is_added_on_top_and_leaves_other_sources_unchanged(demo):
    drifted = with_sensor_config(demo, imu=with_drift(demo.config.imu))
    real = drifted.imu_errors
    assert real.accel.drift is not None and real.accel.drift.shape == drifted.imu.accel.shape
    # measured = (measured without drift) + drift, exactly: noise and bias realisations are unchanged
    assert np.allclose(drifted.imu.accel - demo.imu.accel, real.accel.drift, atol=1e-12)
    assert np.allclose(drifted.imu.gyro - demo.imu.gyro, real.gyro.drift, atol=1e-12)
    assert np.array_equal(real.accel.bias, demo.imu_errors.accel.bias)
    # the drift wanders slowly: per-sample changes are tiny compared with its size
    d = real.gyro.drift
    assert np.abs(np.diff(d, axis=0)).max() < 0.05 * np.abs(d).max()
    assert d.std() == pytest.approx(5 * MDPS, rel=0.6)  # one realisation of a slow process


def test_drift_is_reproducible_and_seeded(demo):
    a = with_sensor_config(demo, imu=with_drift(demo.config.imu)).imu_errors.accel.drift
    b = with_sensor_config(demo, imu=with_drift(demo.config.imu)).imu_errors.accel.drift
    imu2 = with_drift(demo.config.imu)
    imu2 = imu2.model_copy(update={"errors": imu2.errors.model_copy(update={"seed": 99})})
    c = with_sensor_config(demo, imu=imu2).imu_errors.accel.drift
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_drift_moves_the_calibrated_estimate(demo):
    """With ideal GPS and no other IMU error, a drifting accelerometer bias is no longer fully absorbed
    by the approach calibration: the dead-reckoning error at C grows."""
    from throughtunnel.evaluation.experiment import compare_estimators

    ideal_errors = ImuErrorConfig.ideal()
    base_imu = demo.config.imu.model_copy(update={"errors": ideal_errors})
    gnss = GnssConfig.ideal()
    clean = with_sensor_config(demo, imu=base_imu, gnss=gnss)
    drifting = with_sensor_config(
        demo, imu=with_drift(base_imu, accel_sigma=2 * MG, gyro_sigma=0.0), gnss=gnss
    )

    def err(res):
        return compare_estimators(res, ["dr_calibrated"]).evaluations[0].summary["exit_total_m"]

    assert err(clean) < 2.0 and err(drifting) > 5.0


# ------------------------------------------------------------------ GPS degradation before the portal
def degraded(demo, **kw):
    return with_sensor_config(
        demo, gnss=demo.config.gnss.model_copy(update={"portal_degradation": True, **kw})
    )


def fix_errors(res):
    g = res.gnss
    tr = truth_at(res, g.t)
    phone = tr.point_enu(res.config.imu.mount.lever_arm_m)[:, :2]
    enu = res.path.frame.to_enu(g.lat, g.lon)[:, :2]
    return g.t, tr.s, np.linalg.norm(enu - phone, axis=1)


def test_degradation_off_by_default(demo):
    assert not GnssConfig().portal_degradation
    assert demo.gnss_events.entrance_s == pytest.approx(demo.sections.entrance_s)


def test_degradation_is_confined_to_the_approach_of_the_portal(demo):
    res = degraded(demo, degradation_length_m=200.0, degradation_sigma_m=10.0, outlier_probability=0.0)
    _, s, err_deg = fix_errors(res)
    _, _, err_base = fix_errors(demo)
    b = demo.sections.entrance_s
    far = (s < b - 200.0) | (s > b)  # before the zone, and after C (reacquisition)
    near = (s > b - 100.0) & (s <= b)
    assert np.array_equal(err_deg[far], err_base[far])  # untouched outside the zone
    assert near.sum() >= 3 and np.sqrt(np.mean(err_deg[near] ** 2)) > 2.0 * np.sqrt(
        np.mean(err_base[near] ** 2)
    )
    # the phone reports the larger correlated error in its accuracy estimate
    acc_near = res.gnss.horizontal_accuracy_m[near]
    assert acc_near.min() > demo.gnss.horizontal_accuracy_m.max()


def test_outliers_appear_only_near_the_portal(demo):
    res = degraded(demo, degradation_length_m=300.0, degradation_sigma_m=0.0, outlier_probability=1.0,
                   outlier_sigma_m=30.0, degradation_speed_sigma_mps=0.0)  # fmt: skip
    _, s, err = fix_errors(res)
    _, _, base = fix_errors(demo)
    b = demo.sections.entrance_s
    jumpy = np.abs(err - base) > 1e-9
    assert jumpy.any() and np.all((s[jumpy] > b - 300.0) & (s[jumpy] <= b))


def test_degradation_is_reproducible(demo):
    a, b = degraded(demo), degraded(demo)
    assert np.array_equal(a.gnss.lat, b.gnss.lat)
    assert not np.array_equal(a.gnss.lat, demo.gnss.lat)


def test_units_used_in_the_ui():
    assert DEG / 1000 == pytest.approx(MDPS)


def test_loaded_presets_get_default_drift_sizes_so_enabling_drift_has_an_effect(demo):
    """Regression: preset files predate the drift fields; they must get the per-sensor default size
    (not 0), otherwise switching drift on silently does nothing."""
    e = demo.config.imu.errors
    assert not e.accel.drift_enabled
    assert e.accel.drift_sigma == pytest.approx(0.5 * MG) and e.gyro.drift_sigma == pytest.approx(5 * MDPS)
    on = e.model_copy(update={"accel": e.accel.model_copy(update={"drift_enabled": True})})
    res = with_sensor_config(demo, imu=demo.config.imu.model_copy(update={"errors": on}))
    assert res.imu_errors.accel.drift is not None and not np.array_equal(res.imu.accel, demo.imu.accel)
