"""Traffic manager (Phase 5): spawning, car-following and signal obedience.

CG / simulation concepts: time-based movement (dt), projecting a position onto
the heading vector (dot product) to order a lane, AABB tests for crossing
obstacles, painter's algorithm (z-sorted draw order).
"""
from __future__ import annotations

import math
import random

import pygame

from .constants import BRAKE, SAFE_GAP
from .difficulty import spawn_interval, speed_multiplier
from .road import APPROACHES, heading, intersection_rect, spawn_pos
from .signals import SignalController
from .vehicle_art import VEHICLE_TYPES, spec_value
from .vehicles import Vehicle

_INF = float("inf")
_PLAN_DECEL = 0.7 * BRAKE   # comfortable braking used for planning (< BRAKE)
_STOP_BUFFER = 0.5          # a front stops this far before the stop line
_CROSSED = 6.0              # front this far past the line = already crossed
_COMMIT_SLACK = 1.5         # yellow: commit only if clearly unable to stop
_COMMIT_MIN_SPEED = 8.0     # slower vehicles can always stop
_WRECK_MARGIN = 8.0         # stop this far before a crashed vehicle
_SPAWN_CLEAR = 20           # extra free space around the spawn point
_QUEUE_LIMIT, _QUEUE_SPEED = 80, 10.0  # queue "reached the spawn" rule
_FIRST_SPAWN, _RETRY = 0.4, 0.3


def progress(v: Vehicle) -> float:
    """Position projected on the heading (dot product): bigger = further ahead."""
    dx, dy = v.heading
    return v.x * dx + v.y * dy


def stop_distance(speed: float) -> float:
    """Distance needed to stop with full BRAKE: v^2 / (2 * BRAKE)."""
    return speed * speed / (2.0 * BRAKE)


def safe_speed(free: float, lead_speed: float = 0.0) -> float:
    """Highest speed from which we can still stop within `free` px.

    The leader keeps rolling while it brakes, so its own stopping distance is
    added to the free space. Planning uses _PLAN_DECEL, so we brake smoothly.
    """
    reach = free + lead_speed * lead_speed / (2.0 * BRAKE)
    return math.sqrt(2.0 * _PLAN_DECEL * reach) if reach > 0.0 else 0.0


def _wreck_gap(v: Vehicle, w: Vehicle) -> float | None:
    """Free distance from v's front to crashed w if w blocks v's lane, else None."""
    r, vr = w.rect, v.rect
    fx, fy = v.front_pos()
    dx, dy = v.heading
    if v.axis == "NS":
        if vr.right <= r.left or vr.left >= r.right:  # AABB overlap on x
            return None
        gap = (r.top - fy) if dy > 0 else (fy - r.bottom)
    else:
        if vr.bottom <= r.top or vr.top >= r.bottom:  # AABB overlap on y
            return None
        gap = (r.left - fx) if dx > 0 else (fx - r.right)
    return gap if gap > -2.0 else None  # ignore wrecks behind us


class TrafficManager:
    """Spawns vehicles and decides every vehicle's target speed each frame."""

    def __init__(self, seed: int | None = None) -> None:
        self.vehicles: list[Vehicle] = []
        self._rng = random.Random(seed)
        self._square = intersection_rect()
        self._weights = [spec_value(t, "weight") for t in VEHICLE_TYPES]
        self._committed: set[Vehicle] = set()  # ran the yellow: may not stop
        self._recent: list[str] = []           # last two spawn approaches
        self._timer = _FIRST_SPAWN

    def reset(self) -> None:
        """Remove all vehicles and restart the spawn timer."""
        self.vehicles.clear()
        self._committed.clear()
        self._recent.clear()
        self._timer = _FIRST_SPAWN

    # ------------------------------------------------------------- spawning
    def _spawn(self, dt: float, level: int) -> None:
        """Count down the timer; try to spawn when it expires."""
        self._timer -= dt
        if self._timer > 0.0:
            return
        if self._try_spawn(level):
            self._timer = spawn_interval(level) * self._rng.uniform(0.8, 1.25)
        else:
            self._timer = _RETRY  # blocked: try again soon

    def _try_spawn(self, level: int) -> bool:
        """Pick type + approach and spawn if the spawn area is free."""
        vtype = self._rng.choices(VEHICLE_TYPES, weights=self._weights)[0]
        cands = list(APPROACHES)
        if len(self._recent) == 2 and self._recent[0] == self._recent[1]:
            cands.remove(self._recent[0])  # never the same approach 3 times
        self._rng.shuffle(cands)
        for a in cands:
            if not self._spawn_blocked(a, vtype):
                self.vehicles.append(Vehicle(vtype, a, speed_multiplier(level)))
                self._recent = (self._recent + [a])[-2:]
                return True
        return False

    def _spawn_blocked(self, approach: str, vtype: str) -> bool:
        """True if the spawn area is occupied or the queue reached the spawn."""
        sx, sy = spawn_pos(approach)
        dx, dy = heading(approach)
        length = spec_value(vtype, "length")
        for v in self.vehicles:
            if v.approach != approach:
                continue
            along = abs((v.x - sx) * dx + (v.y - sy) * dy)
            need = max(length, (length + v.length) / 2) + SAFE_GAP + _SPAWN_CLEAR
            if along < need:
                return True
            if along < _QUEUE_LIMIT and v.speed < _QUEUE_SPEED:
                return True  # queue overflow: stop spawning on this approach
        return False

    # ---------------------------------------------------------- driving AI
    def _signal_limit(self, v: Vehicle, signals: SignalController) -> float:
        """Speed limit imposed by the traffic light (inf = no limit)."""
        light = signals.light_for(v.approach)
        if light == "green":
            self._committed.discard(v)
            return _INF
        d = v.distance_to_stop_line()  # > 0: front not yet at the line
        if d < -_CROSSED or v in self._committed:
            return _INF  # already crossed / committed: never stop in the middle
        if (light == "yellow" and v.speed > _COMMIT_MIN_SPEED
                and d < stop_distance(v.speed) - _COMMIT_SLACK):
            self._committed.add(v)  # cannot stop before the line: go on
            return _INF
        return safe_speed(d - _STOP_BUFFER)  # stop with the front on the line

    def _target(self, v: Vehicle, leader: Vehicle | None,
                signals: SignalController, wrecks: list[Vehicle]) -> float:
        """Target speed = the strictest of cruise, leader, signal and wrecks."""
        target = v.cruise_speed
        if leader is not None:  # gap between my front and the leader's rear
            free = (progress(leader) - leader.length / 2
                    - progress(v) - v.length / 2 - SAFE_GAP)
            target = min(target, safe_speed(free, leader.speed))
        if not v.ignores_signal:
            target = min(target, self._signal_limit(v, signals))
        if wrecks and not v.rect.colliderect(self._square):
            for w in wrecks:  # wrecks of other lanes that block my path
                if w.approach != v.approach:
                    gap = _wreck_gap(v, w)
                    if gap is not None:
                        target = min(target, safe_speed(gap - _WRECK_MARGIN))
        return target

    # ----------------------------------------------------------- main update
    def update(self, dt: float, signals: SignalController,
               level: int) -> list[Vehicle]:
        """Spawn, steer, move. Returns vehicles that exited safely this frame."""
        self._spawn(dt, level)
        wrecks = [v for v in self.vehicles if v.state == "crashed"]
        lanes: dict[str, list[Vehicle]] = {a: [] for a in APPROACHES}
        for v in self.vehicles:
            lanes[v.approach].append(v)
        for lane in lanes.values():
            lane.sort(key=progress)  # last element = front of the queue
            for i, v in enumerate(lane):
                if v.state != "crashed":
                    leader = lane[i + 1] if i + 1 < len(lane) else None
                    v.target_speed = self._target(v, leader, signals, wrecks)
        for v in self.vehicles:
            v.update(dt)
        exited: list[Vehicle] = []
        for v in self.vehicles:
            if not v.alive and v.state != "crashed" and not v.scored:
                v.scored = True
                exited.append(v)
        self.vehicles = [v for v in self.vehicles if v.alive]
        self._committed.intersection_update(self.vehicles)
        return exited

    def draw(self, surface: pygame.Surface) -> None:
        """Painter's algorithm: wrecks first, then small -> big vehicles."""
        for v in sorted(self.vehicles,
                        key=lambda v: (v.state != "crashed", v.length)):
            v.draw(surface)