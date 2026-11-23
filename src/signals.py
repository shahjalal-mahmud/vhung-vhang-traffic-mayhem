"""Signal state machine + cartoon traffic lights (Phase 3).

CG concepts: translation/reflection (one light layout placed at 4 corners with
heading vectors), alpha blending (translucent glow halo), painter's algorithm
(shadow -> housing -> glow -> lamps), parametric circle (progress ring).
"""
from __future__ import annotations

import math

import pygame

from .constants import (ALL_RED_TIME, COLORS, CX, CY, MIN_GREEN, YELLOW_TIME)
from .road import APPROACHES, axis_of, heading

STATES = ("NS_GREEN", "NS_YELLOW", "EW_GREEN", "EW_YELLOW", "ALL_RED")
_DURATION = {"GREEN": MIN_GREEN, "YELLOW": YELLOW_TIME, "RED": ALL_RED_TIME}
_LAMPS = ("red", "yellow", "green")

# ---- drawing-only constants ----
_ALONG, _ACROSS = 110, 92      # light center: along the road / off the road axis
_HOUSE_W, _HOUSE_L = 20, 54    # housing size (cross, along)
_LAMP_R, _LAMP_GAP, _HALO_R = 6, 17, 20
_RING_R, _BASE_OFF, _DIM = 10, 14, 0.28
_POLE, _TRACK, _SHADOW = (150, 155, 168), (28, 28, 36), (70, 140, 66)


def _make_halo(color: tuple) -> pygame.Surface:
    """Soft glow: concentric translucent circles, outer = faint, inner = strong."""
    surf = pygame.Surface((_HALO_R * 2, _HALO_R * 2), pygame.SRCALPHA)
    for r in range(_HALO_R, _LAMP_R, -1):
        k = (_HALO_R - r) / (_HALO_R - _LAMP_R)
        pygame.draw.circle(surf, (*color, int(150 * k ** 1.6) + 12),
                           (_HALO_R, _HALO_R), r)
    return surf.convert_alpha() if pygame.display.get_surface() else surf


class SignalController:
    """Traffic-light state machine. Only one axis is ever non-red."""

    def __init__(self) -> None:
        self.state = "NS_GREEN"
        self.time_in_state = 0.0
        self._target: str | None = None    # axis that turns green after ALL_RED
        self._pending: str | None = None   # ONE stored request
        self._halos: dict[str, pygame.Surface] = {}

    # ----------------------------------------------------------- properties
    @property
    def pending_request(self) -> str | None:
        """Axis ('NS'/'EW') waiting for MIN_GREEN to pass, or None."""
        return self._pending

    @property
    def destination(self) -> str:
        """Axis that is green now or will be green after the switch."""
        return self.state[:2] if self.state.endswith("_GREEN") else (self._target or "NS")

    @property
    def progress(self) -> float:
        """0..1 of the current state's duration (green: of MIN_GREEN)."""
        total = _DURATION[self.state.split("_")[1]]
        return min(1.0, self.time_in_state / total)

    # ---------------------------------------------------------------- logic
    def reset(self) -> None:
        """Back to NS green, no pending request."""
        self.state, self.time_in_state = "NS_GREEN", 0.0
        self._target = self._pending = None

    def request(self, axis: str) -> None:
        """Ask for green on 'NS' or 'EW'. Safe to spam."""
        if axis not in ("NS", "EW") or axis == self.destination \
                or axis == self._pending:
            return  # already green / being switched to / already pending
        if self.state.endswith("_GREEN") and self.time_in_state >= MIN_GREEN:
            self._begin_switch(axis)
            self.time_in_state = 0.0
        else:
            self._pending = axis  # too early (or mid-switch): remember it

    def _begin_switch(self, axis: str) -> None:
        """Current green axis -> YELLOW, remember who gets green next."""
        self.state = f"{self.state[:2]}_YELLOW"
        self._target, self._pending = axis, None

    def update(self, dt: float) -> None:
        """Advance the timer and run any due transitions."""
        self.time_in_state += dt
        for _ in range(4):  # bounded: a huge dt can never loop forever
            if not self._advance():
                break

    def _advance(self) -> bool:
        """Do at most one due transition. Leftover time carries over."""
        t = self.time_in_state
        if self.state.endswith("_GREEN"):
            if self._pending and t >= MIN_GREEN:
                self._begin_switch(self._pending)
                self.time_in_state = t - MIN_GREEN
                return True
        elif self.state.endswith("_YELLOW"):
            if t >= YELLOW_TIME:
                self.state, self.time_in_state = "ALL_RED", t - YELLOW_TIME
                return True
        elif t >= ALL_RED_TIME:
            self.state = f"{self._target or 'NS'}_GREEN"
            self.time_in_state, self._target = t - ALL_RED_TIME, None
            return True
        return False

    def light_for(self, approach: str) -> str:
        """'green' | 'yellow' | 'red' for an approach (N, S, E or W)."""
        axis = axis_of(approach)
        if self.state == f"{axis}_GREEN":
            return "green"
        return "yellow" if self.state == f"{axis}_YELLOW" else "red"

    # -------------------------------------------------------------- drawing
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the four lights (one per corner, beside each stop line)."""
        if not self._halos:
            self._halos = {n: _make_halo(COLORS[n]) for n in _LAMPS}
        for a in APPROACHES:
            self._draw_light(surface, a)

    def _draw_light(self, surf: pygame.Surface, a: str) -> None:
        """One light: stand + progress ring, housing, glow, three lamps."""
        hx, hy = heading(a)
        ox, oy = hy, -hx  # outward = driver's left, away from the road
        cx, cy = CX - hx * _ALONG + ox * _ACROSS, CY - hy * _ALONG + oy * _ACROSS
        w, h = (_HOUSE_W, _HOUSE_L) if hx == 0 else (_HOUSE_L, _HOUSE_W)
        body = pygame.Rect(0, 0, w, h)
        body.center = (cx, cy)
        state = self.light_for(a)
        reach = _HOUSE_W / 2 + _BASE_OFF
        base = (int(cx + ox * reach), int(cy + oy * reach))
        pygame.draw.rect(surf, _SHADOW, body.move(3, 4), border_radius=8)
        pygame.draw.line(surf, _POLE, (int(cx + ox * _HOUSE_W / 2),
                                       int(cy + oy * _HOUSE_W / 2)), base, 4)
        pygame.draw.circle(surf, _POLE, base, _RING_R - 3)
        pygame.draw.circle(surf, _TRACK, base, _RING_R, 3)
        frac = self.progress if (state != "red" or self.state == "ALL_RED") else 0.0
        if frac > 0.02:  # arc = points on a circle, angle from 12 o'clock
            pts = [(base[0] + (_RING_R - 1) * math.cos(-math.pi / 2 + 2 * math.pi * frac * i / 24),
                    base[1] + (_RING_R - 1) * math.sin(-math.pi / 2 + 2 * math.pi * frac * i / 24))
                   for i in range(25)]
            pygame.draw.lines(surf, COLORS[state], False, pts, 3)
        pygame.draw.rect(surf, (24, 24, 30), body, border_radius=8)
        pygame.draw.rect(surf, (96, 98, 112), body, 2, border_radius=8)
        for i, name in enumerate(_LAMPS):  # red = upstream end, green = downstream
            off = (i - 1) * _LAMP_GAP
            p = (cx + hx * off, cy + hy * off)
            on = name == state
            pygame.draw.circle(surf, (10, 10, 14), p, _LAMP_R + 2)
            if on:  # alpha-blended glow
                surf.blit(self._halos[name], self._halos[name].get_rect(center=p))
            col = COLORS[name]
            pygame.draw.circle(surf, col if on else tuple(int(c * _DIM) for c in col),
                               p, _LAMP_R)
            if on:
                pygame.draw.circle(surf, COLORS["white"], (p[0] - 2, p[1] - 2), 2)