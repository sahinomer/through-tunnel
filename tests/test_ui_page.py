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
