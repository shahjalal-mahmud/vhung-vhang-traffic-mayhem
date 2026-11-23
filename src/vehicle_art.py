"""Vehicle artwork (Phase 4): six cartoon top-down vehicles.

CG concepts: local model coordinates (every vehicle is drawn facing RIGHT),
rotation transform (pygame.transform.rotate to the heading), sprite cache
(pre-rendered buffers), frame-based animation (N_FRAMES), alpha blending
(brake-light glow).
"""
from __future__ import annotations

import math

import pygame

from .constants import COLORS, VEHICLE_SPECS

N_FRAMES = 8  # animation frames per cycle
_BLK = COLORS["black"]
_GLASS, _SKIN = (170, 225, 250), (232, 182, 140)
_ANGLE = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}  # ccw degrees
_WOBBLE_DEG = 2.5


def spec_value(vtype: str, key: str):
    """Read a VEHICLE_SPECS field (works for dict or SimpleNamespace specs)."""
    spec = VEHICLE_SPECS[vtype]
    return spec[key] if isinstance(spec, dict) else getattr(spec, key)


def _shade(color: tuple, k: float) -> tuple:
    return tuple(max(0, min(255, int(c * k))) for c in color)


def _bob(f: int, amp: float) -> int:
    """Integer up/down offset that follows a sine over the animation cycle."""
    return round(math.sin(2 * math.pi * f / N_FRAMES) * amp)


def _box(s, color, rect, r=4, w=2) -> None:
    """Filled rounded rect with a black cartoon outline."""
    pygame.draw.rect(s, color, rect, border_radius=r)
    if w:
        pygame.draw.rect(s, _BLK, rect, w, border_radius=r)


def _wheels(s, xs, W, wl, wt, f) -> None:
    """Black wheels peeking out of both sides; tread ticks roll with frame f."""
    for x in xs:
        for y in (0, W - wt):
            pygame.draw.rect(s, _BLK, (x, y, wl, wt), border_radius=2)
            for k in (0, wl // 2):
                tx = x + (f * wl // N_FRAMES + k) % wl
                pygame.draw.line(s, (130, 132, 145), (tx, y), (tx, y + wt - 1))


def _lights(s, L, ys, braking) -> None:
    """Headlights at the front (right edge), brake lights at the rear."""
    for y in ys:
        pygame.draw.circle(s, (255, 246, 180), (L - 3, y), 3)
        pygame.draw.circle(s, _BLK, (L - 3, y), 3, 1)
        if braking:
            glow = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 40, 40, 110), (7, 7), 7)
            s.blit(glow, (-5, y - 7))  # glow centered on the brake light
            pygame.draw.rect(s, (255, 60, 60), (0, y - 2, 4, 5))
        else:
            pygame.draw.rect(s, (120, 20, 28), (0, y - 2, 3, 5))


def _rickshaw(s, L, W, color, f, brk) -> None:
    m, bob = W // 2, _bob(f, 1.4)
    _wheels(s, (3,), W, 12, 4, f)
    pygame.draw.rect(s, _BLK, (L - 10, m - 2, 10, 4), border_radius=2)  # front wheel
    pygame.draw.line(s, (90, 92, 104), (14, m), (L - 10, m), 3)          # frame
    _box(s, color, (2, 3, 24, W - 6), 5)                                 # hood
    for i, c in enumerate(((255, 220, 90), (90, 170, 240), (255, 255, 255), (255, 220, 90))):
        pygame.draw.rect(s, c, (5 + i * 5, 6, 4, W - 12))                # stripes
    for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4)):                    # flower
        pygame.draw.circle(s, COLORS["white"], (14 + dx, m + dy), 3)
    pygame.draw.circle(s, (255, 120, 60), (14, m), 2)
    for sy in (-4, 4):                                                   # arms
        pygame.draw.line(s, _SKIN, (31, m + sy + bob), (L - 8, 5 if sy < 0 else W - 5), 2)
    pygame.draw.ellipse(s, (70, 110, 215), (26, m - 6 + bob, 8, 12))    # shoulders
    pygame.draw.ellipse(s, _BLK, (26, m - 6 + bob, 8, 12), 1)
    pygame.draw.circle(s, _SKIN, (30, m + bob), 4)                       # head
    pygame.draw.circle(s, (60, 40, 30), (29, m + bob), 3)                # hair
    pygame.draw.line(s, (60, 62, 72), (L - 8, 3), (L - 8, W - 3), 3)    # handlebar
    _lights(s, L, (m,), brk)


def _cng(s, L, W, color, f, brk) -> None:
    m = W // 2
    _wheels(s, (6,), W, 12, 4, f)
    pygame.draw.rect(s, _BLK, (L - 8, m - 3, 8, 6), border_radius=2)    # front wheel
    _box(s, color, (1, 2, L - 2, W - 4), 8)                              # body
    hood = [(34, 3), (L - 3, 8), (L - 3, W - 8), (34, W - 3)]
    pygame.draw.polygon(s, _shade(color, 1.18), hood)
    pygame.draw.polygon(s, _BLK, hood, 2)
    roof = pygame.Rect(5, 4 + f % 2, 30, W - 8)                          # engine jiggle
    _box(s, (50, 110, 205), roof, 5)
    for x in range(roof.left + 5, roof.right - 2, 5):                    # cage lines
        pygame.draw.line(s, (25, 60, 130), (x, roof.top + 2), (x, roof.bottom - 3))
    for k in (1, 2):
        y = roof.top + k * roof.height // 3
        pygame.draw.line(s, (25, 60, 130), (roof.left + 2, y), (roof.right - 3, y))
    pygame.draw.rect(s, _GLASS, (35, 6, 4, W - 12))                      # windshield
    _lights(s, L, (7, W - 7), brk)


def _motorcycle(s, L, W, color, f, brk) -> None:
    m, bob = W // 2, _bob(f, 1.2)
    for x in (1, L - 11):                                                # wheels
        pygame.draw.rect(s, _BLK, (x, m - 2, 10, 4), border_radius=2)
        tx = x + (f * 10 // N_FRAMES) % 10
        pygame.draw.line(s, (130, 132, 145), (tx, m - 2), (tx, m + 1))
    pygame.draw.line(s, (90, 92, 104), (8, m), (L - 8, m), 3)            # frame
    pygame.draw.ellipse(s, color, (15, m - 4, 12, 8))                    # tank
    pygame.draw.ellipse(s, _BLK, (15, m - 4, 12, 8), 1)
    pygame.draw.ellipse(s, (210, 70, 70), (8, 1, 8, W - 2))              # shoulders
    pygame.draw.ellipse(s, _BLK, (8, 1, 8, W - 2), 1)
    for y0, y1 in ((3, 2), (W - 3, W - 2)):                              # arms
        pygame.draw.line(s, (210, 70, 70), (13, y0), (L - 9, y1), 2)
    pygame.draw.line(s, _BLK, (L - 9, 1), (L - 9, W - 1), 2)             # handlebar
    pygame.draw.circle(s, (255, 210, 60), (18 + bob, m), 4)              # helmet
    pygame.draw.circle(s, _BLK, (18 + bob, m), 4, 1)
    pygame.draw.rect(s, _BLK, (20 + bob, m - 2, 2, 4))                   # visor
    _lights(s, L, (m,), brk)


def _car(s, L, W, color, f, brk) -> None:
    _wheels(s, (8, 40), W, 10, 4, f)
    _box(s, color, (1, 2, L - 2, W - 4), 8)                              # body
    _box(s, _shade(color, 1.15), (L - 19, 6, 14, W - 12), 4, 0)          # hood panel
    _box(s, _shade(color, 0.85), (4, 6, 10, W - 12), 3, 0)               # trunk
    pygame.draw.polygon(s, _GLASS, [(17, 7), (12, 10), (12, W - 10), (17, W - 7)])
    _box(s, _shade(color, 0.72), (17, 5, 22, W - 10), 6)                 # cabin
    _box(s, _shade(color, 1.12), (20, 8, 16, W - 16), 4, 0)              # roof
    gx = 21 + f * 13 // (N_FRAMES - 1)                                   # moving glint
    pygame.draw.line(s, COLORS["white"], (gx, 10), (gx, 13), 2)
    ws = [(39, 7), (45, 10), (45, W - 10), (39, W - 7)]
    pygame.draw.polygon(s, _GLASS, ws)
    pygame.draw.polygon(s, _BLK, ws, 1)
    for y in (0, W - 3):                                                 # mirrors
        _box(s, color, (36, y, 5, 3), 1, 1)
    _lights(s, L, (6, W - 6), brk)


def _bus(s, L, W, color, f, brk) -> None:
    m = W // 2
    _wheels(s, (12, 70), W, 12, 4, f)
    _box(s, color, (1, 2, L - 2, W - 4), 6)                              # body
    for x in range(8, L - 24, 9):                                        # window strips
        pygame.draw.rect(s, _GLASS, (x, 3, 6, 3))
        pygame.draw.rect(s, _GLASS, (x, W - 6, 6, 3))
    dent = _shade(color, 0.62)                                           # dents
    pygame.draw.polygon(s, dent, [(30, 2), (36, 5), (27, 5)])
    pygame.draw.polygon(s, dent, [(58, W - 2), (63, W - 6), (68, W - 2)])
    _box(s, _shade(color, 1.15), (6, 6, L - 26, W - 12), 5)              # roof panel
    pygame.draw.rect(s, COLORS["red"], (9, 9, L - 32, 3))                # stripes
    pygame.draw.rect(s, (40, 150, 90), (9, W - 12, L - 32, 3))
    for i in range(3):                                                   # roof hatches
        _box(s, (225, 228, 235), (14 + i * 22, m - 5, 12, 10), 2, 1)
    dc = COLORS["yellow"] if (f // 2) % 2 == 0 else COLORS["white"]      # twinkle
    for cx in (31, 53, 75):
        pts = [(cx - 4, m), (cx, m - 4), (cx + 4, m), (cx, m + 4)]
        pygame.draw.polygon(s, dc, pts)
        pygame.draw.polygon(s, _BLK, pts, 1)
    ws = [(L - 14, 5), (L - 6, 9), (L - 6, W - 9), (L - 14, W - 5)]
    pygame.draw.polygon(s, _GLASS, ws)
    pygame.draw.polygon(s, _BLK, ws, 1)
    _lights(s, L, (7, W - 7), brk)


def _truck(s, L, W, color, f, brk) -> None:
    m, bob = W // 2, _bob(f, 1.5)
    _wheels(s, (7, 22, 62), W, 10, 4, f)
    _box(s, (240, 228, 196), (1, 2, L - 35, W - 4), 4)                   # cargo box
    pal = ((231, 76, 60), (255, 200, 60), (46, 170, 140))
    for i in range(6):                                                   # checker pattern
        for j in range(3):
            h = min(8, (W - 12) - j * 8)
            pygame.draw.rect(s, pal[(i + j) % 3], (5 + i * 8, 6 + j * 8, 8, h))
    pygame.draw.rect(s, _BLK, (5, 6, 48, W - 12), 2)
    for x in (13, 29, 45):                                               # ropes
        pygame.draw.line(s, _BLK, (x, 4), (x, W - 5), 2)
    pygame.draw.rect(s, (80, 80, 90), (L - 34, m - 3, 8, 6))             # hitch
    _box(s, color, (L - 30, 3, 29, W - 6), 6)                            # cab
    _box(s, _shade(color, 1.2), (L - 26, 6, 12, W - 12), 4, 0)           # cab roof
    ws = [(L - 14, 6), (L - 8, 9), (L - 8, W - 9), (L - 14, W - 6)]
    pygame.draw.polygon(s, _GLASS, ws)
    pygame.draw.polygon(s, _BLK, ws, 1)
    pygame.draw.circle(s, (240, 70, 70), (L - 11, m + bob), 2)           # swinging charm
    for y in (0, W - 3):
        pygame.draw.rect(s, _BLK, (L - 16, y, 4, 3))                     # mirrors
    _lights(s, L, (6, W - 6), brk)


_DRAWERS = {"rickshaw": _rickshaw, "cng": _cng, "motorcycle": _motorcycle,
            "car": _car, "bus": _bus, "truck": _truck}
VEHICLE_TYPES = tuple(_DRAWERS)
_cache: dict[tuple, pygame.Surface] = {}


def get_sprite(vtype: str, hdg: tuple, frame: int, braking: bool) -> pygame.Surface:
    """Cached, rotated sprite. Local drawing faces RIGHT; rotate to heading."""
    key = (vtype, hdg, frame % N_FRAMES, bool(braking))
    spr = _cache.get(key)
    if spr is None:
        L, W = spec_value(vtype, "length"), spec_value(vtype, "width")
        base = pygame.Surface((L, W), pygame.SRCALPHA)
        _DRAWERS[vtype](base, L, W, spec_value(vtype, "color"), key[2], key[3])
        angle = float(_ANGLE[hdg])
        if vtype == "rickshaw":  # left-right wobble baked into the rotation
            angle += _WOBBLE_DEG * math.sin(2 * math.pi * key[2] / N_FRAMES)
        spr = pygame.transform.rotate(base, angle)
        if pygame.display.get_surface() is not None:
            spr = spr.convert_alpha()  # match display format -> faster blits
        _cache[key] = spr
    return spr