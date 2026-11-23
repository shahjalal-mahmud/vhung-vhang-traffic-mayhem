"""STUB - replaced in Phase 8. Simple linear curves so wiring can be tested."""
from __future__ import annotations

from .constants import (BASE_SPAWN_INTERVAL, MAX_LEVEL, MIN_SPAWN_INTERVAL,
                        SPEED_MULT_PER_LEVEL)
from .utils import clamp, lerp


def _t(level: int) -> float:
    """Level 1..MAX_LEVEL -> 0..1."""
    return clamp((level - 1) / (MAX_LEVEL - 1), 0.0, 1.0)


def spawn_interval(level: int) -> float:
    """Seconds between spawns (shrinks with level)."""
    return lerp(BASE_SPAWN_INTERVAL, MIN_SPAWN_INTERVAL, _t(level))


def speed_multiplier(level: int) -> float:
    """Vehicle speed factor (grows with level)."""
    return 1.0 + SPEED_MULT_PER_LEVEL * (level - 1)


def chaos_chance(level: int) -> float:
    """Chance per second-ish that a driver runs a red light."""
    return lerp(0.02, 0.15, _t(level))