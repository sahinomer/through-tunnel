"""Uncertainty-aware announcement (step 6.2): fires at d̂ + min(2σ, 300 m) ≥ target; precise if σ ≤ 30 m."""

import math
from types import SimpleNamespace

import pytest

from throughtunnel.positioning.base import StateEstimate
from throughtunnel.positioning.runner import UncertaintyAwareAnnouncer

TARGET_M = 1000.0


def _drive(std_m: float | None, step_m: float = 1.0) -> UncertaintyAwareAnnouncer:
    """Feed estimates advancing 1 m per second, with a constant σ, until the target is passed."""
    ann = UncertaintyAwareAnnouncer(SimpleNamespace(announcement_m=TARGET_M))
    d = 0.0
    while d <= TARGET_M + 10.0:
        est = StateEstimate(t=d, east=0.0, north=0.0, speed=1.0, heading=0.0, mode="dead_reckoning",
                            route_distance=d, position_std_m=std_m)  # fmt: skip
        ann.update(est, d)
        d += step_m
    return ann


def test_without_uncertainty_it_never_fires():
    ann = _drive(None)
    assert math.isnan(ann.fired_t) and ann.precise is None


def test_small_uncertainty_gives_a_precise_announcement_2_sigma_early():
    ann = _drive(10.0)
    assert ann.fired_t == pytest.approx(TARGET_M - 20.0)
    assert ann.precise is True


def test_large_uncertainty_gives_a_hedged_announcement_at_most_300_m_early():
    ann = _drive(50.0)
    assert ann.fired_t == pytest.approx(TARGET_M - 100.0) and ann.precise is False
    ann = _drive(1700.0)  # long stop-and-go outage: σ far too large, the lead is capped
    assert ann.fired_t == pytest.approx(TARGET_M - 300.0) and ann.precise is False


def test_it_fires_only_once():
    ann = UncertaintyAwareAnnouncer(SimpleNamespace(announcement_m=TARGET_M))
    for d, t in ((990.0, 1.0), (1500.0, 2.0)):
        est = StateEstimate(t=t, east=0.0, north=0.0, speed=1.0, heading=0.0, mode="gnss",
                            route_distance=d, position_std_m=5.0)  # fmt: skip
        ann.update(est, d)
    assert ann.fired_t == 1.0
