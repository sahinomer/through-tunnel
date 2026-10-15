"""The page builds in NiceGUI's in-process user simulation (catches UI wiring/ordering errors)."""

import pytest
from nicegui.testing.user_simulation import user_simulation

from throughtunnel.app.page import SimulatorPage


def current_page(user) -> SimulatorPage:
    """The page of this test's client (pages of earlier tests may still be alive)."""
    import gc

    return next(o for o in gc.get_objects() if isinstance(o, SimulatorPage) and o.plot.client is user.client)


@pytest.mark.anyio
async def test_page_builds():
    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        await user.should_see("Preset scenario")
        await user.should_see("Phone IMU: mounting, errors, calibration")
        await user.should_see("Phone GPS")
        await user.should_see("Drive and simulation")


@pytest.mark.anyio
async def test_single_exit_announcement_control():
    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        await user.should_see("Tunnel: exit announcement and traffic")
        await user.should_see("Announce before exit C")
        await user.should_not_see("First announcement")
        await user.should_not_see("Exit position after B")


@pytest.mark.anyio
async def test_panels_feed_the_simulation():
    """Wiring: a loaded preset fills the panels, and a panel change reaches the next simulation."""

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = current_page(user)
        cfg = load_preset("synthetic_demo_track")
        with user.client:
            await page._load_scenario(cfg)
            assert page.result.config.tunnel == cfg.tunnel and page.result.config.imu == cfg.imu
            assert "announcement (300 m before C)" in page.positioning_summary.content
            page.mount_panel.s_yaw.value = 90
            await page.mount_panel._on_control()
        imu = page.result.config.imu
        assert imu.mount.yaw_deg == 90 and imu.mount.label == "custom"
        assert imu.errors == cfg.imu.errors  # other sensor settings unchanged


@pytest.mark.anyio
async def test_calibration_panel_reaches_the_estimators_only():

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = current_page(user)
        with user.client:
            await page._load_scenario(load_preset("synthetic_demo_track"))
            before = page.result
            page.calibration_panel.enabled.value = True
            page.calibration_panel.s_pitch.value = 0.25
            await page.calibration_panel._changed()
        cal = page.result.config.calibration
        assert cal.enabled and cal.pitch_deg == 0.25
        assert page.result.imu is before.imu and page.result.gnss is before.gnss  # nothing re-simulated
        assert "Calibration error" in page.route_info.content


@pytest.mark.anyio
async def test_map_grade_switch_reaches_the_estimators_only():

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = current_page(user)
        with user.client:
            await page._load_scenario(load_preset("synthetic_demo_track"))
            before = page.result
            assert not before.route_map.has_grade and not page.map_data_panel.grade_on.value
            page.map_data_panel.grade_on.value = True
            await page.map_data_panel._changed()
        assert page.result.config.map_data.road_grade and page.result.route_map.has_grade
        assert page.result.imu is before.imu and page.result.gnss is before.gnss  # nothing re-simulated
        assert "route + road grade" in page.route_info.content


@pytest.mark.anyio
async def test_profile_drag_is_clamped_and_reaches_the_simulation():

    import numpy as np

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = current_page(user)
        editor = page.profile_editor
        with user.client:
            await page._load_scenario(load_preset("synthetic_demo_track"))
            assert page.result.config.road_profile.is_flat and len(editor.distances) > 10
            i = len(editor.distances) // 2
            await editor._on_relayout(type("E", (), {"args": {f"shapes[{i}].yanchor": 500.0}})())
        assert 0.0 < editor.heights[i] < 500.0  # clamped to the 6 % limit
        cfg = page.result.config.road_profile
        assert not cfg.is_flat and np.ptp(page.result.truth.z) > 1.0  # the drive now goes over a hill
        with user.client:
            await editor._apply_template("underwater")
        assert page.result.truth.z.min() < -20.0


@pytest.mark.anyio
async def test_traffic_panel_reaches_the_simulation():

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = current_page(user)
        panel = page.traffic_panel
        with user.client:
            await page._load_scenario(load_preset("synthetic_demo_track"))
            assert page.result.config.traffic.scenario == "free"
            panel.select.value = "stop_and_go"
            panel.s_count.value = 2
            await panel._changed()
        assert page.result.config.traffic.scenario == "stop_and_go" and len(page.result.traffic.stops) == 2
        assert (page.result.motion.v == 0.0).any()
        assert "standing" in page.route_info.content


@pytest.mark.anyio
async def test_bias_drift_and_gps_degradation_controls_reach_the_simulation():

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = current_page(user)
        panel, gps = page.imu_panel, page.gps_panel
        with user.client:
            await page._load_scenario(load_preset("synthetic_demo_track"))
            assert panel.s_acc_drift.value == pytest.approx(0.5)  # preset gets the default drift size (mg)
            panel.acc_drift_on.value = True
            panel.s_acc_drift.value = 2.0
            gps.deg_on.value = True
            gps.s_deg_sigma.value = 12.0
            await panel._changed()
        cfg = page.result.config
        assert cfg.imu.errors.accel.drift_enabled and cfg.imu.errors.accel.drift_sigma > 0
        assert cfg.gnss.portal_degradation and cfg.gnss.degradation_sigma_m == 12.0
        assert page.result.imu_errors.accel.drift is not None
        assert "Bias drift over the run" in panel.errors_label.content


@pytest.mark.anyio
async def test_values_set_from_code_trigger_no_handler():
    """F10: change handlers run as background tasks, so the loading guard must be checked when the
    event fires, not inside the task. Setting every panel from code must call no panel callback."""
    import asyncio

    from throughtunnel.scenario import load_preset
    from throughtunnel.sensors.mounting import CalibrationErrorConfig
    from throughtunnel.vehicle.traffic import TrafficConfig

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = current_page(user)
        calls = []

        def record(name):
            async def callback():
                calls.append(name)

            return callback

        panels = ("mount_panel", "calibration_panel", "map_data_panel", "imu_panel", "gps_panel")
        panels += ("traffic_panel",)
        for name in panels:
            getattr(page, name)._on_change = record(name)
        cfg = load_preset("seattle_sr99_tunnel")
        imu = cfg.imu.model_copy(update={"earth_rotation": not cfg.imu.earth_rotation})
        with user.client:
            page.mount_panel.set(imu)
            page.calibration_panel.set(CalibrationErrorConfig(enabled=True))
            page.map_data_panel.set(page.map_data_panel.config().model_copy(update={"road_grade": True}))
            page.imu_panel.set_imu(imu.model_copy(update={"errors": imu.errors.ideal()}))
            page.gps_panel.set_gnss(cfg.gnss.model_copy(update={"enabled": False}))
            page.traffic_panel.set(TrafficConfig(scenario="stop_and_go"))
            await asyncio.sleep(0.2)  # let any scheduled handler run
        assert calls == []


@pytest.mark.anyio
async def test_loaded_preset_label_with_modified_angles_keeps_the_angles():
    """F10: a file whose mount says "dash_portrait" but with other angles must load as written (the
    preset handler used to overwrite the angles after the load)."""
    import asyncio

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = current_page(user)
        cfg = load_preset("synthetic_demo_track")
        edited = {"label": "dash_portrait", "yaw_deg": -80.0, "roll_deg": 90.0}
        mount = cfg.imu.mount.model_copy(update=edited)
        cfg = cfg.model_copy(update={"imu": cfg.imu.model_copy(update={"mount": mount})})
        with user.client:
            aligned = cfg.imu.mount.model_copy(update={"label": "aligned", "yaw_deg": 0.0, "roll_deg": 0.0})
            page.mount_panel.set(cfg.imu.model_copy(update={"mount": aligned}))  # the load changes the label
            await asyncio.sleep(0.2)
            await page._load_scenario(cfg)
            await asyncio.sleep(0.2)
        assert page.mount_panel.s_yaw.value == -80.0
        assert page.result.config.imu.mount.yaw_deg == -80.0


@pytest.mark.anyio
async def test_imu_error_master_switch_turns_all_errors_off_and_back_on():

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = current_page(user)
        panel = page.imu_panel
        with user.client:
            await page._load_scenario(load_preset("synthetic_demo_track"))
            before = page.result.config.imu.errors
            assert panel.errors_on.value and before.accel.noise_enabled and before.gyro.bias_enabled
            panel.errors_on.value = False
            await panel._changed()
            off = page.result.config.imu.errors
            assert not any((off.accel.noise_enabled, off.accel.bias_enabled, off.gyro.noise_enabled,
                            off.gyro.bias_enabled))  # fmt: skip
            assert off.accel.noise_density == before.accel.noise_density  # magnitudes kept
            assert page.result.imu.accel.tolist() == page.result.imu_ideal.accel.tolist()
            panel.errors_on.value = True
            await panel._changed()
        assert page.result.config.imu.errors == before  # the individual choice is restored


@pytest.mark.anyio
async def test_defaults_map_selection_off_and_profile_panel_hidden():
    """Clicks while panning must not move route points; the profile panel opens on request."""
    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = current_page(user)
        assert page.picker.switch.value is False
        assert "Turn on the switch" in page.picker.hint.text
        assert not page.profile_overlay.shown and page.profile_overlay.show_button.visible
        with user.client:
            page.profile_overlay.set_shown(True)
        assert page.profile_overlay.shown and not page.profile_overlay.show_button.visible
