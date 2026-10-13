"""The page builds in NiceGUI's in-process user simulation (catches UI wiring/ordering errors)."""

import pytest
from nicegui.testing.user_simulation import user_simulation

from throughtunnel.app.page import SimulatorPage


@pytest.mark.anyio
async def test_page_builds():
    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        await user.should_see("Preset scenario")
        await user.should_see("IMU sample rate & errors")
        await user.should_see("Phone mounting (IMU)")


@pytest.mark.anyio
async def test_single_exit_announcement_control():
    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        await user.should_see("Tunnel exit announcement")
        await user.should_see("Announce before exit C")
        await user.should_not_see("First announcement")
        await user.should_not_see("Exit position after B")


@pytest.mark.anyio
async def test_panels_feed_the_simulation():
    """Wiring: a loaded preset fills the panels, and a panel change reaches the next simulation."""
    import gc

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = next(o for o in gc.get_objects() if isinstance(o, SimulatorPage))
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
    import gc

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = next(o for o in gc.get_objects() if isinstance(o, SimulatorPage))
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
async def test_profile_drag_is_clamped_and_reaches_the_simulation():
    import gc

    import numpy as np

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = next(o for o in gc.get_objects() if isinstance(o, SimulatorPage))
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
    import gc

    from throughtunnel.scenario import load_preset

    async with user_simulation(root=SimulatorPage) as user:
        await user.open("/")
        page = next(o for o in gc.get_objects() if isinstance(o, SimulatorPage))
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
