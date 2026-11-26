"""Vehicle class (Phase 4): movement, state, geometry and drawing.

CG concepts: translation (position += velocity * dt), AABB (rect property),
rotation transform (sprite rotated to heading), frame-based animation.
"""
from __future__ import annotations

import math

import pygame

from .constants import ACCEL, BRAKE, HEIGHT, WIDTH
from .road import axis_of, heading, lane_center, spawn_pos, stop_line
from .vehicle_art import N_FRAMES, get_sprite, spec_value

_INITIAL_SPEED = 40.0  # px/s when spawned (small, so they roll in gently)
_ANIM_PX = 7.0         # pixels travelled per animation frame
_DESPAWN = 80          # px beyond the opposite screen edge


class Vehicle:
    """One vehicle driving straight along its lane."""

    def __init__(self, vtype: str, approach: str, speed_mult: float = 1.0) -> None:
        self.vtype = vtype
        self.approach = approach
        self.axis = axis_of(approach)
        self.heading = heading(approach)
        self.x, self.y = (float(v) for v in spawn_pos(approach))
        lane = float(lane_center(approach))  # lock onto the lane center line
        if self.axis == "NS":
            self.x = lane
        else:
            self.y = lane
        self.length = spec_value(vtype, "length")
        self.width = spec_value(vtype, "width")
        self.max_speed = float(spec_value(vtype, "max_speed"))
        self.speed_mult = speed_mult
        self.target_speed = self.max_speed * speed_mult
        self.speed = min(_INITIAL_SPEED, self.target_speed)
        self.color = spec_value(vtype, "color")
        self.patience = float(spec_value(vtype, "patience"))
        self.state = "moving"  # "moving" | "stopped" | "crashed"
        self.wait_time = 0.0
        self.ignores_signal = False
        self.honk = False  # set True by ChaosSystem; Game reads and clears it
        self.scored = False
        self.alive = True
        self.crash_timer = 0.0
        self._anim = 0.0  # animation phase in frames

    # ------------------------------------------------------------ properties
    @property
    def cruise_speed(self) -> float:
        """Normal driving speed (max_speed * speed_mult)."""
        return self.max_speed * self.speed_mult

    @property
    def rect(self) -> pygame.Rect:
        """Axis-aligned box of the body: length/width swap for vertical travel."""
        w, h = ((self.width, self.length) if self.axis == "NS"
                else (self.length, self.width))
        r = pygame.Rect(0, 0, int(w), int(h))
        r.center = (int(self.x), int(self.y))
        return r

    @property
    def braking(self) -> bool:
        """True while slowing down or standing still (brake lights on)."""
        return self.state == "stopped" or self.speed > self.target_speed + 0.5

    @property
    def frame(self) -> int:
        """Animation frame; frozen at 0 when standing still."""
        return 0 if self.speed < 1.0 else int(self._anim) % N_FRAMES

    # -------------------------------------------------------------- geometry
    def front_pos(self) -> tuple[float, float]:
        """Center of the front edge."""
        dx, dy = self.heading
        return (self.x + dx * self.length / 2, self.y + dy * self.length / 2)

    def distance_to_stop_line(self) -> float:
        """Positive = front has not reached the stop line, negative = crossed."""
        fx, fy = self.front_pos()
        dx, dy = self.heading
        line = stop_line(self.approach)
        return (line - fy) * dy if self.axis == "NS" else (line - fx) * dx

    # ---------------------------------------------------------------- update
    def update(self, dt: float) -> None:
        """Accelerate / brake toward target_speed, then translate."""
        if self.state == "crashed":
            self.speed = 0.0
            self.crash_timer += dt
            return
        if self.speed < self.target_speed:
            self.speed = min(self.target_speed, self.speed + ACCEL * dt)
        elif self.speed > self.target_speed:
            self.speed = max(self.target_speed, self.speed - BRAKE * dt)
        dx, dy = self.heading
        self.x += dx * self.speed * dt  # translation: p += v * dt
        self.y += dy * self.speed * dt
        self._anim += self.speed * dt / _ANIM_PX
        if self.target_speed <= 0.0 and self.speed < 1.0:
            self.speed = 0.0
            self.state = "stopped"
            self.wait_time += dt
        else:
            self.state = "moving"
            self.wait_time = 0.0
        if self._past_exit():
            self.alive = False

    def _past_exit(self) -> bool:
        """True once the center is _DESPAWN px beyond the far screen edge."""
        dx, dy = self.heading
        if dx > 0:
            return self.x > WIDTH + _DESPAWN
        if dx < 0:
            return self.x < -_DESPAWN
        return self.y > HEIGHT + _DESPAWN if dy > 0 else self.y < -_DESPAWN

    def crash(self) -> None:
        """Become a wreck: stop, start the crash timer."""
        self.state = "crashed"
        self.speed = 0.0
        self.target_speed = 0.0
        self.crash_timer = 0.0

    # --------------------------------------------------------------- drawing
    def _tilt(self) -> float:
        """Crash wobble angle in degrees: settles from a shake to a slight tilt."""
        decay = max(0.0, 1.0 - self.crash_timer / 1.5)
        return 7.0 + 12.0 * math.sin(self.crash_timer * 16.0) * decay

    def draw(self, surface: pygame.Surface) -> None:
        """Blit the cached sprite centered on (x, y)."""
        sprite = get_sprite(self.vtype, self.heading, self.frame, self.braking)
        if self.state == "crashed":
            sprite = pygame.transform.rotate(sprite, self._tilt())
        surface.blit(sprite, sprite.get_rect(center=(int(self.x), int(self.y))))
        if self.state == "crashed" and int(self.crash_timer * 4) % 2 == 0:
            r = self.rect  # blinking hazard lights at the four corners
            for p in (r.topleft, r.topright, r.bottomleft, r.bottomright):
                pygame.draw.circle(surface, (255, 150, 30),
                                   (p[0] + (3 if p[0] == r.left else -3),
                                    p[1] + (3 if p[1] == r.top else -3)), 3)