"""Red-light runners (Phase 6): impatient drivers ignore the signal.

CG / simulation concepts: frame-rate independent probability
(p = 1 - e^(-rate * dt)), AABB test against the intersection square to know
when a runner has cleared the junction.
"""
from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from .difficulty import chaos_chance
from .road import intersection_rect

if TYPE_CHECKING:
    from .vehicles import Vehicle

# Small vehicles are more reckless, big ones less (multiplies the chance).
RECKLESS = {"motorcycle": 1.5, "rickshaw": 1.5, "bus": 0.5, "truck": 0.5}
FALLBACK_BASE, FALLBACK_PER_LEVEL = 0.04, 0.03  # used if chaos_chance() <= 0
_LINE_ZONE = 6.0    # front within 6 px before the stop line = head of the queue
_LINE_SLACK = 2.0   # tolerated overshoot past the line (px)


def reckless_factor(vtype: str) -> float:
    """Chance multiplier for a vehicle type (1.0 for cars and CNGs)."""
    return RECKLESS.get(vtype, 1.0)


def base_rate(level: int) -> float:
    """Chance per second that a waiting driver loses patience."""
    rate = chaos_chance(level)
    return rate if rate > 0.0 else FALLBACK_BASE + FALLBACK_PER_LEVEL * level


class ChaosSystem:
    """Turns patient drivers into red-light runners (sets ignores_signal)."""

    def __init__(self, seed: int | None = None, rate_scale: float = 1.0) -> None:
        self._rng = random.Random(seed)
        self.rate_scale = rate_scale        # demo/test knob: 1.0 = normal game
        self._square = intersection_rect()
        self._inside: set[Vehicle] = set()  # runners that entered the square

    def update(self, dt: float, vehicles: list, level: int) -> None:
        """Roll for impatient drivers; clear the flag of finished runners."""
        self._inside &= set(vehicles)       # forget removed vehicles
        rate = base_rate(level) * self.rate_scale
        for v in vehicles:
            if v.state == "crashed":
                v.ignores_signal = False    # a wreck obeys nothing
                self._inside.discard(v)
            elif v.ignores_signal:
                self._track_runner(v)
            elif self._waiting_at_red(v):
                lam = rate * reckless_factor(v.vtype)
                if self._rng.random() < 1.0 - math.exp(-lam * dt):
                    v.ignores_signal = True  # floor it through the red light
                    v.honk = True            # Game reads + clears (audio later)

    @staticmethod
    def _waiting_at_red(v: Vehicle) -> bool:
        """Stopped at the head of the queue (front on the stop line) and out of
        patience. (The light colour is implied: only red keeps a front stopped.)"""
        return (v.state == "stopped" and v.wait_time > v.patience
                and -_LINE_SLACK <= v.distance_to_stop_line() <= _LINE_ZONE)

    def _track_runner(self, v: Vehicle) -> None:
        """Clear ignores_signal once the runner has left the intersection square."""
        if v.rect.colliderect(self._square):  # AABB: body touches the square
            self._inside.add(v)
        elif v in self._inside:
            v.ignores_signal = False
            self._inside.discard(v)