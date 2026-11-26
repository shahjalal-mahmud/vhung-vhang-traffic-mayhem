"""Visual effects (Phase 9): smoke, sparks, floating text, bubbles, shake.

CG concepts: particle system (position += velocity * dt), alpha blending
(fading sprites), easing (ease-out rise), offscreen buffer (Game renders the
world to a Surface and blits it translated by shake_offset = a 2D translation),
sprite caching (pre-rendered smoke discs and bubbles), capped particle count.
"""
from __future__ import annotations

import math
import random

import pygame

from .constants import COLORS, HEIGHT, WIDTH
from .ui_widgets import INK, ease_out, get_font, outlined

MAX_PARTICLES = 300           # smoke + sparks together (performance cap)
MAX_TEXTS, MAX_BUBBLES = 24, 10
BUBBLE_WORDS = ("Pom pom!", "Pee pee!", "Horn!", "Boom!", "Shorun!", "Jaldi!",
                "Hat!", "Aro jore!")
_TOP_SAFE = 64                # keep bubbles below the HUD bar
_smoke_cache: dict[int, pygame.Surface] = {}
_bubble_cache: dict[str, pygame.Surface] = {}


def _smoke_sprite(radius: float) -> pygame.Surface:
    """Cached grey puff (two discs), radius quantised to even numbers 4..44."""
    r = int(max(4, min(44, radius))) // 2 * 2
    spr = _smoke_cache.get(r)
    if spr is None:
        spr = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
        pygame.draw.circle(spr, (120, 122, 134), (r, r), r)
        pygame.draw.circle(spr, (176, 178, 190), (r - r // 6, r - r // 6),
                           int(r * 0.7))
        _smoke_cache[r] = spr
    return spr


def _bubble_sprite(text: str) -> pygame.Surface:
    """Cached comic speech bubble: rounded white box, ink border, little tail."""
    spr = _bubble_cache.get(text)
    if spr is None:
        img = get_font(16, True).render(text, True, INK)
        w, h = img.get_width() + 18, img.get_height() + 10
        spr = pygame.Surface((w, h + 9), pygame.SRCALPHA)
        body = pygame.Rect(0, 0, w, h)
        tail = [(int(w * 0.2), h - 2), (int(w * 0.2) + 11, h - 2),
                (int(w * 0.2) - 2, h + 8)]
        pygame.draw.rect(spr, COLORS["white"], body, border_radius=12)
        pygame.draw.polygon(spr, COLORS["white"], tail)
        pygame.draw.rect(spr, INK, body, 2, border_radius=12)
        pygame.draw.line(spr, INK, tail[0], tail[2], 2)
        pygame.draw.line(spr, INK, tail[1], tail[2], 2)
        pygame.draw.line(spr, COLORS["white"], (tail[0][0] + 2, h - 1),
                         (tail[1][0] - 2, h - 1), 3)  # hide the border under the tail
        spr.blit(img, (9, 5))
        _bubble_cache[text] = spr
    return spr


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "age", "life", "r0", "r1", "smoke")

    def __init__(self, x, y, vx, vy, life, r0=0.0, r1=0.0, smoke=False) -> None:
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.age, self.life, self.r0, self.r1, self.smoke = 0.0, life, r0, r1, smoke


class _Item:
    """Floating text or honk bubble."""
    __slots__ = ("x", "y", "text", "color", "age", "life")

    def __init__(self, x, y, text, color, life) -> None:
        self.x, self.y, self.text, self.color = x, y, text, color
        self.age, self.life = 0.0, life


class EffectsSystem:
    """All short-lived visuals. Everything is capped, nothing allocates per frame."""

    def __init__(self) -> None:
        self._rng = random.Random()
        self._p: list[_Particle] = []
        self._texts: list[_Item] = []
        self._bubbles: list[_Item] = []
        self._shake_t = self._shake_dur = self._shake_mag = 0.0
        self._offset = (0, 0)

    @property
    def particle_count(self) -> int:
        """Smoke + spark particles alive right now."""
        return len(self._p)

    # -------------------------------------------------------------- spawning
    def _room(self, n: int) -> None:
        """Make space for n new particles by dropping the oldest ones."""
        over = len(self._p) + n - MAX_PARTICLES
        if over > 0:
            del self._p[:over]

    def spawn_smoke(self, pos: tuple, count: int = 8) -> None:
        """Grey puffs that drift up, grow and fade."""
        count = min(count, MAX_PARTICLES)
        self._room(count)
        r = self._rng
        for _ in range(count):
            a, sp = r.uniform(0, math.tau), r.uniform(8, 42)
            self._p.append(_Particle(
                pos[0] + r.uniform(-8, 8), pos[1] + r.uniform(-8, 8),
                math.cos(a) * sp, math.sin(a) * sp - 24, r.uniform(0.9, 1.7),
                r.uniform(5, 9), r.uniform(22, 36), True))

    def spawn_sparks(self, pos: tuple, count: int = 22) -> None:
        """Fast orange/yellow sparks flying outward (no gravity)."""
        count = min(count, MAX_PARTICLES)
        self._room(count)
        r = self._rng
        for _ in range(count):
            a, sp = r.uniform(0, math.tau), r.uniform(120, 360)
            self._p.append(_Particle(pos[0], pos[1], math.cos(a) * sp,
                                     math.sin(a) * sp, r.uniform(0.25, 0.6)))

    def floating_text(self, pos: tuple, text: str, color: tuple) -> None:
        """Text that rises and fades ('+10', 'COMBO x5', 'CRASH!')."""
        if len(self._texts) >= MAX_TEXTS:
            del self._texts[0]
        self._texts.append(_Item(pos[0], pos[1], text, color, 1.2))

    def spawn_bubble(self, pos: tuple, text: str | None = None) -> None:
        """Comic honk bubble whose tail points at `pos`."""
        if len(self._bubbles) >= MAX_BUBBLES:
            del self._bubbles[0]
        word = text or self._rng.choice(BUBBLE_WORDS)
        self._bubbles.append(_Item(pos[0], pos[1], word, None, 1.1))

    def shake(self, duration: float, magnitude: float) -> None:
        """Screen shake: random offset that decays linearly to zero."""
        if duration <= 0 or magnitude <= 0:
            return
        now = self._shake_mag * max(0.0, self._shake_t) / (self._shake_dur or 1.0)
        if magnitude >= now:  # a weaker shake never cancels a stronger one
            self._shake_t = self._shake_dur = duration
            self._shake_mag = magnitude

    @property
    def shake_offset(self) -> tuple[int, int]:
        """Current (x, y) translation for the offscreen world buffer."""
        return self._offset

    # ---------------------------------------------------------------- update
    def update(self, dt: float) -> None:
        """Advance everything by dt seconds and drop expired items."""
        for p in self._p:
            p.age += dt
            p.x += p.vx * dt   # translation: p += v * dt
            p.y += p.vy * dt
            k = 0.5 ** (dt * (3.0 if p.smoke else 1.5))  # air drag
            p.vx *= k
            p.vy *= k
        self._p = [p for p in self._p if p.age < p.life]
        for lst in (self._texts, self._bubbles):
            for it in lst:
                it.age += dt
            lst[:] = [it for it in lst if it.age < it.life]
        if self._shake_t > 0.0:
            self._shake_t -= dt
            m = self._shake_mag * max(0.0, self._shake_t) / self._shake_dur
            self._offset = (round(self._rng.uniform(-m, m)),
                            round(self._rng.uniform(-m, m)))
        else:
            self._offset = (0, 0)

    # ------------------------------------------------------------------ draw
    def draw(self, surface: pygame.Surface) -> None:
        """Smoke first (back), then sparks, bubbles and text (painter's order)."""
        for p in self._p:
            if p.smoke:
                u = p.age / p.life
                spr = _smoke_sprite(p.r0 + (p.r1 - p.r0) * u)
                spr.set_alpha(int(150 * min(1.0, p.age / 0.1) * (1.0 - u)))
                surface.blit(spr, spr.get_rect(center=(int(p.x), int(p.y))))
        for p in self._p:
            if not p.smoke:
                t = 1.0 - p.age / p.life
                col = (255, int(110 + 140 * t), int(30 + 60 * t))
                tail = (p.x - p.vx * 0.04, p.y - p.vy * 0.04)
                pygame.draw.line(surface, col, (p.x, p.y), tail, 3 if t > 0.5 else 2)
        for b in self._bubbles:
            self._draw_bubble(surface, b)
        for it in self._texts:
            self._draw_text(surface, it)

    @staticmethod
    def _draw_bubble(surface: pygame.Surface, b: _Item) -> None:
        spr = _bubble_sprite(b.text)
        w, h = spr.get_size()
        x = min(max(b.x - w * 0.2, 4), WIDTH - w - 4)
        y = max(b.y - h - 14 * b.age, _TOP_SAFE)  # drifts up a little
        spr.set_alpha(int(255 * min(1.0, (b.life - b.age) / 0.25)))
        surface.blit(spr, (x, y))
        spr.set_alpha(255)

    @staticmethod
    def _draw_text(surface: pygame.Surface, it: _Item) -> None:
        img = outlined(it.text, get_font(26, True), it.color, INK, 3)
        y = it.y - 55 * ease_out(it.age / it.life)  # ease-out rise
        x = min(max(it.x, img.get_width() // 2 + 4), WIDTH - img.get_width() // 2 - 4)
        img.set_alpha(int(255 * min(1.0, (it.life - it.age) / 0.35)))
        surface.blit(img, img.get_rect(center=(int(x), int(max(y, _TOP_SAFE)))))
        img.set_alpha(255)  # the cached surface is shared: restore it