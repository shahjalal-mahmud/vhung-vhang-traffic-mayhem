"""Difficulty curves (Phase 7): spawn rate, speed and chaos per level.

Level runs 1..MAX_LEVEL. All curves use t = (level - 1) / (MAX_LEVEL - 1),
so t = 0 at level 1 and t = 1 at MAX_LEVEL (linear interpolation = lerp).

Formulas
  spawn base  = lerp(BASE_SPAWN_INTERVAL, MIN_SPAWN_INTERVAL, 1 - (1 - t)^1.25)
                (ease-out: traffic gets denser a bit faster in early levels)
  spawn_interval = spawn base * uniform(0.85, 1.15)         (+-15 % jitter)
  speed_multiplier = 1 + SPEED_MULT_PER_LEVEL * (level - 1)
  chaos_chance = 0.03 + 0.15 * t        (0.03/s at level 1 -> 0.18/s at level 10)
"""
from __future__ import annotations

import random

from .constants import (BASE_SPAWN_INTERVAL, MAX_LEVEL, MIN_SPAWN_INTERVAL,
                        SPEED_MULT_PER_LEVEL)
from .utils import clamp, lerp

JITTER = 0.15          # +-15 % random variation of the spawn interval
_EASE = 1.25           # >1 = steeper at the start, flatter near MAX_LEVEL
CHAOS_MIN, CHAOS_MAX = 0.03, 0.18  # chance per second at level 1 / MAX_LEVEL
_rng = random.Random()


def seed(value: int | None) -> None:
    """Seed the jitter generator (used by tests for reproducible runs)."""
    _rng.seed(value)


def _t(level: float) -> float:
    """Level 1..MAX_LEVEL -> 0..1 (clamped)."""
    return clamp((level - 1) / (MAX_LEVEL - 1), 0.0, 1.0)


def spawn_base(level: int) -> float:
    """Average seconds between spawns, without jitter."""
    eased = 1.0 - (1.0 - _t(level)) ** _EASE
    return lerp(BASE_SPAWN_INTERVAL, MIN_SPAWN_INTERVAL, eased)


def spawn_interval(level: int) -> float:
    """Seconds until the next spawn: base interval with +-15 % jitter."""
    return spawn_base(level) * _rng.uniform(1.0 - JITTER, 1.0 + JITTER)


def speed_multiplier(level: int) -> float:
    """Vehicle speed factor: +SPEED_MULT_PER_LEVEL per level above 1."""
    return 1.0 + SPEED_MULT_PER_LEVEL * (clamp(level, 1, MAX_LEVEL) - 1)


def chaos_chance(level: int) -> float:
    """Chance per second that a waiting driver runs the red (linear in t)."""
    return lerp(CHAOS_MIN, CHAOS_MAX, _t(level))