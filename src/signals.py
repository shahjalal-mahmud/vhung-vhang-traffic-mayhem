"""STUB - replaced in Phase 3. Requests switch the light instantly."""
from __future__ import annotations

import pygame

from .constants import COLORS, CX, CY

_STATES = ("NS_GREEN", "NS_YELLOW", "EW_GREEN", "EW_YELLOW", "ALL_RED")


class SignalController:
    """STUB - replaced in Phase 3."""

    def __init__(self) -> None:
        self.state = "NS_GREEN"
        self.time_in_state = 0.0
        self._font: pygame.font.Font | None = None

    def reset(self) -> None:
        """Back to NS green."""
        self.state = "NS_GREEN"
        self.time_in_state = 0.0

    def request(self, axis: str) -> None:
        """Stub: switch immediately to the requested axis."""
        new = "NS_GREEN" if axis == "NS" else "EW_GREEN"
        if new != self.state:
            self.state = new
            self.time_in_state = 0.0

    def update(self, dt: float) -> None:
        """Advance the state timer."""
        self.time_in_state += dt

    def light_for(self, approach: str) -> str:
        """Return 'green' | 'yellow' | 'red' for an approach."""
        axis = "NS" if approach in ("N", "S") else "EW"
        if self.state == f"{axis}_GREEN":
            return "green"
        if self.state == f"{axis}_YELLOW":
            return "yellow"
        return "red"

    def draw(self, surface: pygame.Surface) -> None:
        """Draw one indicator dot per axis on the grass corners."""
        if self._font is None:
            self._font = pygame.font.Font(None, 20)
        spots = {"NS": (CX - 100, CY - 100), "EW": (CX + 100, CY + 100)}
        for axis, pos in spots.items():
            color = COLORS[self.light_for("N" if axis == "NS" else "E")]
            pygame.draw.circle(surface, COLORS["black"], pos, 14)
            pygame.draw.circle(surface, color, pos, 10)
            label = self._font.render(axis, True, COLORS["black"])
            surface.blit(label, label.get_rect(center=(pos[0], pos[1] + 24)))