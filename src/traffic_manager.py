"""STUB - replaced in Phase 5. No spawning yet."""
from __future__ import annotations

import pygame

from .vehicles import Vehicle


class TrafficManager:
    """STUB - replaced in Phase 5."""

    def __init__(self) -> None:
        self.vehicles: list[Vehicle] = []

    def update(self, dt: float, signals, level: int) -> list[Vehicle]:
        """Update vehicles; return those that exited safely this frame."""
        exited: list[Vehicle] = []
        for v in self.vehicles:
            v.update(dt)
            if not v.alive and not v.scored and v.state != "crashed":
                exited.append(v)
        self.vehicles = [v for v in self.vehicles if v.alive]
        return exited

    def draw(self, surface: pygame.Surface) -> None:
        """Draw all vehicles."""
        for v in self.vehicles:
            v.draw(surface)

    def reset(self) -> None:
        """Remove all vehicles."""
        self.vehicles.clear()