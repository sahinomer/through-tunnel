"""The sensor-factor study isolates one factor per condition, with everything else identical."""

import numpy as np

from throughtunnel.evaluation.factor_study import CONDITIONS, condition_configs
from throughtunnel.scenario import load_preset, run_scenario, with_sensor_config

BY_KEY = {c.key: c for c in CONDITIONS}


def test_main_conditions_switch_exactly_the_named_factor():
    cfg = load_preset("synthetic_demo_track")
    flags = {}
    for key in ("ideal", "noise", "bias", "calibration", "combined"):
        imu, gnss, cal = condition_configs(cfg, BY_KEY[key], seed=7)
        e = imu.errors
        flags[key] = (
            e.accel.noise_enabled,
            e.gyro.noise_enabled,
            e.accel.bias_enabled,
            e.gyro.bias_enabled,
            cal.enabled,
        )
        assert e.seed == 7 and gnss.seed == 7
        assert gnss.position_sigma_m == gnss.white_sigma_m == gnss.speed_sigma_mps == 0.0  # GPS error-free
        assert gnss.loss_window_m == cfg.gnss.loss_window_m  # ... but the same availability model
        assert imu.mount == cfg.imu.mount and imu.rate_hz == cfg.imu.rate_hz
        # Magnitudes stay at the preset values whether a source is on or off.
        assert e.accel.bias_magnitude == cfg.imu.errors.accel.bias_magnitude
    assert flags == {
        "ideal": (False, False, False, False, False),
        "noise": (True, True, False, False, False),
        "bias": (False, False, True, True, False),
        "calibration": (False, False, False, False, True),
        "combined": (True, True, True, True, True),
    }
    imu, gnss, _ = condition_configs(cfg, BY_KEY["gps"], seed=7)
    assert gnss.position_sigma_m == cfg.gnss.position_sigma_m and not imu.errors.accel.noise_enabled


def test_same_run_same_outage_and_shared_noise_realisation():
    """Across conditions of one run, the GPS outage is identical, and a source that is on in two
    conditions has the identical realisation in both (independent random streams)."""
    cfg = load_preset("synthetic_demo_track")
    base = run_scenario(cfg)

    def sim(key):
        imu, gnss, _ = condition_configs(cfg, BY_KEY[key], seed=3)
        return with_sensor_config(base, imu=imu, gnss=gnss)

    ideal, noise, combined, gps = sim("ideal"), sim("noise"), sim("combined"), sim("gps")
    for res in (noise, combined, gps):
        assert res.gnss_events == ideal.gnss_events
    assert np.array_equal(gps.gnss.t, ideal.gnss.t)
    # combined = noise + bias, so (combined - noise) is the constant bias on every sample.
    diff = combined.imu.accel - noise.imu.accel
    assert np.allclose(diff, diff[0], atol=1e-12) and np.linalg.norm(diff[0]) > 0
