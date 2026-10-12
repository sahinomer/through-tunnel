"""The positioning side must not be able to reach the simulator's hidden state (D15, PD1).

Checked in a fresh interpreter: importing the observation types and every positioning module must not
load any simulator module (vehicle, road, scenario, sensors, routing, app).
"""

import json
import subprocess
import sys
from dataclasses import fields

from throughtunnel.observations import GnssStream, ImuStream, Observations, RouteMap

FORBIDDEN = (
    "throughtunnel.vehicle",
    "throughtunnel.road",
    "throughtunnel.scenario",
    "throughtunnel.sensors",
    "throughtunnel.routing",
    "throughtunnel.app",
    "throughtunnel.evaluation",
)

PROBE = """
import importlib, json, pkgutil, sys
import throughtunnel.observations
import throughtunnel.positioning as pos
for m in pkgutil.walk_packages(pos.__path__, prefix="throughtunnel.positioning."):
    importlib.import_module(m.name)
print(json.dumps(sorted(m for m in sys.modules if m.startswith("throughtunnel"))))
"""


def test_positioning_and_observations_do_not_load_simulator_modules():
    out = subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True, check=True)
    loaded = json.loads(out.stdout.strip().splitlines()[-1])
    leaked = [m for m in loaded if m.startswith(FORBIDDEN)]
    assert not leaked, f"positioning side imports simulator modules: {leaked}"
    assert "throughtunnel.positioning" in loaded


def test_observation_types_have_no_truth_fields():
    names = {f.name for cls in (ImuStream, GnssStream, RouteMap, Observations) for f in fields(cls)}
    for forbidden in ("truth", "mount", "bias", "ideal", "speed_true", "lever_arm"):
        assert not any(forbidden in n for n in names), forbidden
