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
