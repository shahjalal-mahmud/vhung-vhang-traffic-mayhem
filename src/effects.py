"""STUB - replaced in Phase 11. All effects are no-ops."""
from __future__ import annotations

import pygame


class EffectsSystem:
    """STUB - replaced in Phase 11."""

    def spawn_smoke(self, pos: tuple) -> None:
        """Would spawn smoke particles."""

    def spawn_sparks(self, pos: tuple) -> None:
        """Would spawn spark particles."""

    def floating_text(self, pos: tuple, text: str, color: tuple) -> None:
        """Would show rising text."""

    def shake(self, duration: float, magnitude: float) -> None:
        """Would start a screen shake."""

    def update(self, dt: float) -> None:
        """Would advance particles."""

    def draw(self, surface: pygame.Surface) -> None:
        """Would draw particles."""

    @property
    def shake_offset(self) -> tuple[int, int]:
        """Current (x, y) camera offset; (0, 0) for now."""
        return (0, 0)