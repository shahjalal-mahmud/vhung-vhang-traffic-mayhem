"""STUB - replaced in Phase 4. Real attributes, simple straight movement."""
from __future__ import annotations

import pygame

from .constants import COLORS, HEIGHT, VEHICLE_SPECS, WIDTH
from .road import axis_of, heading, spawn_pos, stop_line


class Vehicle:
    """STUB - replaced in Phase 4."""

    def __init__(self, vtype: str, approach: str, speed_mult: float = 1.0) -> None:
        spec = VEHICLE_SPECS[vtype]
        self.vtype = vtype
        self.approach = approach
        self.axis = axis_of(approach)
        self.heading = heading(approach)
        self.x, self.y = (float(v) for v in spawn_pos(approach))
        self.length = spec["length"]
        self.width = spec["width"]
        self.max_speed = spec["max_speed"] * speed_mult
        self.speed = self.max_speed
        self.target_speed = self.max_speed
        self.color = spec["color"]
        self.state = "moving"  # "moving" | "stopped" | "crashed"
        self.wait_time = 0.0
        self.patience = float(spec["patience"])
        self.ignores_signal = False
        self.scored = False
        self.alive = True
        self.crash_timer = 0.0

    @property
    def rect(self) -> pygame.Rect:
        """Axis-aligned bounding box of the (rotated) body, used for AABB."""
        w, h = ((self.width, self.length) if self.axis == "NS"
                else (self.length, self.width))
        r = pygame.Rect(0, 0, int(w), int(h))
        r.center = (int(self.x), int(self.y))
        return r

    def front_pos(self) -> tuple[float, float]:
        """Center of the front bumper."""
        dx, dy = self.heading
        return (self.x + dx * self.length / 2, self.y + dy * self.length / 2)

    def distance_to_stop_line(self) -> float:
        """Positive = front has not reached the stop line yet."""
        fx, fy = self.front_pos()
        dx, dy = self.heading
        line = stop_line(self.approach)
        return (line - fy) * dy if self.axis == "NS" else (line - fx) * dx

    def update(self, dt: float) -> None:
        """Move along heading (translation = position += velocity * dt)."""
        if self.state == "crashed":
            self.crash_timer += dt
            return
        dx, dy = self.heading
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt
        if (self.x < -80 or self.x > WIDTH + 80
                or self.y < -80 or self.y > HEIGHT + 80):
            if self.distance_to_stop_line() < 0:  # only after crossing
                self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw a plain rounded box."""
        pygame.draw.rect(surface, self.color, self.rect, border_radius=6)
        pygame.draw.rect(surface, COLORS["black"], self.rect, 2, border_radius=6)

    def crash(self) -> None:
        """Mark as crashed and stop."""
        self.state = "crashed"
        self.speed = 0.0
        self.crash_timer = 0.0