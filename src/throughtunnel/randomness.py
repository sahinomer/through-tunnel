"""Reproducible, independent random streams.

Every random consumer (driver behaviour, each sensor error source, ...) draws from its own named
stream derived from a seed: ``SeedSequence([seed, crc32(name)])``. Adding a consumer, or changing
how much one consumer draws (e.g. a different sample rate for one sensor), never changes the
realisation of the others.
"""

from __future__ import annotations

import zlib

import numpy as np


def rng_stream(seed: int, name: str) -> np.random.Generator:
    """Independent, reproducible random stream for one named consumer."""
    return np.random.default_rng(np.random.SeedSequence([seed, zlib.crc32(name.encode())]))
