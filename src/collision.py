"""Collision detection (Phase 6): AABB tests, crash handling, wreck clearing.

CG concepts: collision detection with axis-aligned bounding boxes (AABB),
a shrunk "hit box" so near-misses do not count, rectangle intersection (clip)
to find the impact point.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from .constants import CRASH_CLEAR_TIME

if TYPE_CHECKING:
    from .vehicles import Vehicle

_SHRINK = 0.15  # hit box is 15 % smaller than the visible body


def hit_box(v: Vehicle) -> pygame.Rect:
    """The vehicle's AABB shrunk by ~15 % in each direction (about its centre)."""
    r = v.rect
    return r.inflate(-max(1, round(r.w * _SHRINK)), -max(1, round(r.h * _SHRINK)))


def get_crash_point(a: Vehicle, b: Vehicle) -> tuple[float, float]:
    """Midpoint of the overlap rectangle of the two bodies (for particles)."""
    clip = a.rect.clip(b.rect)  # empty (0 x 0) if the rects do not overlap
    if clip.w > 0 and clip.h > 0:
        return (float(clip.centerx), float(clip.centery))
    return ((a.x + b.x) / 2.0, (a.y + b.y) / 2.0)


class CollisionSystem:
    """Finds new collisions between moving vehicles of different axes."""

    get_crash_point = staticmethod(get_crash_point)

    def __init__(self) -> None:
        self._warned: set[tuple[int, int]] = set()

    def update(self, dt: float, vehicles: list) -> list[tuple[Vehicle, Vehicle]]:
        """Return NEW collisions (each pair once). dt is unused: wreck timing is
        driven by Vehicle.crash_timer."""
        live = [v for v in vehicles if v.alive and v.state != "crashed"]
        boxes = [hit_box(v) for v in live]
        found: list[tuple[Vehicle, Vehicle]] = []
        for i in range(len(live)):
            for j in range(i + 1, len(live)):
                if not boxes[i].colliderect(boxes[j]):
                    continue
                a, b = live[i], live[j]
                if a.axis == b.axis:
                    self._warn_same_lane(a, b)  # should never happen: ignore
                else:
                    found.append((a, b))
        for a, b in found:  # crash after the scan, so one frame = one snapshot
            a.crash()
            b.crash()
        for v in vehicles:  # wrecks are obstacles for CRASH_CLEAR_TIME seconds
            if v.state == "crashed" and v.crash_timer >= CRASH_CLEAR_TIME:
                v.alive = False
        return found

    def _warn_same_lane(self, a: Vehicle, b: Vehicle) -> None:
        """Print a debug warning once per overlapping same-axis pair."""
        key = tuple(sorted((id(a), id(b))))
        if key in self._warned:
            return
        if len(self._warned) > 200:
            self._warned.clear()
        self._warned.add(key)
        print(f"[collision] debug warning: same-lane overlap {a.vtype}/{b.vtype} "
              f"from {a.approach}/{b.approach} (ignored)")