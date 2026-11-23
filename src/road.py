"""STUB - replaced in Phase 2. Geometry helpers are final; drawing is basic."""
from __future__ import annotations

import pygame

from .constants import (COLORS, CX, CY, HEIGHT, ROAD_W, STOP_DIST, WIDTH)

_OFFSET = 35  # lane center offset from the road axis (LANE_W / 2)


def axis_of(approach: str) -> str:
    """'N'/'S' -> 'NS', 'E'/'W' -> 'EW'."""
    return "NS" if approach in ("N", "S") else "EW"


def heading(approach: str) -> tuple[int, int]:
    """Unit direction (dx, dy) a vehicle travels when coming FROM approach."""
    return {"N": (0, 1), "S": (0, -1), "W": (1, 0), "E": (-1, 0)}[approach]


def lane_center(approach: str) -> int:
    """Lane center line (left-hand traffic): x for N/S, y for W/E."""
    return {"N": CX + _OFFSET, "S": CX - _OFFSET,
            "W": CY - _OFFSET, "E": CY + _OFFSET}[approach]


def spawn_pos(approach: str) -> tuple[int, int]:
    """Spawn point 60px outside the screen, on the lane center line."""
    return {"N": (lane_center("N"), -60),
            "S": (lane_center("S"), HEIGHT + 60),
            "W": (-60, lane_center("W")),
            "E": (WIDTH + 60, lane_center("E"))}[approach]


def stop_line(approach: str) -> int:
    """Coordinate where a vehicle's FRONT must stop (y for N/S, x for W/E)."""
    return {"N": CY - STOP_DIST, "S": CY + STOP_DIST,
            "W": CX - STOP_DIST, "E": CX + STOP_DIST}[approach]


def intersection_rect() -> pygame.Rect:
    """The central square, CX±70 by CY±70."""
    half = ROAD_W // 2
    return pygame.Rect(CX - half, CY - half, ROAD_W, ROAD_W)


class Road:
    """STUB - replaced in Phase 2."""

    def __init__(self) -> None:
        self.rect = intersection_rect()

    def draw(self, surface: pygame.Surface) -> None:
        """Fill grass and draw two plain road bands."""
        surface.fill(COLORS["grass"])
        half = ROAD_W // 2
        pygame.draw.rect(surface, COLORS["road"], (CX - half, 0, ROAD_W, HEIGHT))
        pygame.draw.rect(surface, COLORS["road"], (0, CY - half, WIDTH, ROAD_W))