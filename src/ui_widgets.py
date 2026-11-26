"""UI building blocks (Phase 8): cached fonts, outlined text, buttons, hearts.

CG concepts: alpha blending (SRCALPHA overlays), a heart built from primitives
(2 circles + 1 triangle), surface caching (pre-rendered buffers), easing
functions (smooth animation curves).
"""
from __future__ import annotations

import pygame

from .constants import COLORS

_FONT_NAMES = "comicsansms,arialrounded,verdana,arial"  # first one installed wins
INK = (24, 22, 34)  # dark outline colour used by all cartoon text
_fonts: dict[tuple[int, bool], pygame.font.Font] = {}
_texts: dict[tuple, pygame.Surface] = {}
_shades: dict[tuple, pygame.Surface] = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Cached system font with a safe fallback (no font files needed)."""
    key = (size, bold)
    font = _fonts.get(key)
    if font is None:
        pygame.font.init()
        try:
            font = pygame.font.SysFont(_FONT_NAMES, size, bold=bold)
        except Exception:  # broken font system: use pygame's built-in font
            font = pygame.font.Font(None, int(size * 1.2))
        _fonts[key] = font
    return font


def ease_out(t: float) -> float:
    """Cubic ease-out: fast start, soft landing (t in 0..1)."""
    return 1.0 - (1.0 - t) ** 3


def outlined(text: str, font: pygame.font.Font, color: tuple,
             outline: tuple = INK, width: int = 3) -> pygame.Surface:
    """Text with a thick outline, cached (the same text is never re-rendered)."""
    key = (text, id(font), color, outline, width)
    surf = _texts.get(key)
    if surf is None:
        base, edge = font.render(text, True, color), font.render(text, True, outline)
        w, h = base.get_size()
        surf = pygame.Surface((w + 2 * width, h + 2 * width), pygame.SRCALPHA)
        for dx in range(-width, width + 1):  # stamp the edge colour around a disc
            for dy in range(-width, width + 1):
                if dx * dx + dy * dy <= width * width + 1:
                    surf.blit(edge, (width + dx, width + dy))
        surf.blit(base, (width, width))
        if len(_texts) > 400:
            _texts.clear()
        _texts[key] = surf
    return surf


def label(surface: pygame.Surface, text: str, size: int, color: tuple,
          pos: tuple, anchor: str = "center", bold: bool = False,
          shadow: bool = True, alpha: int = 255) -> pygame.Rect:
    """Draw text anchored at pos ('center', 'midleft', 'midright', ...)."""
    if not text:
        return pygame.Rect(int(pos[0]), int(pos[1]), 0, 0)
    font = get_font(size, bold)
    img = font.render(text, True, color)
    img.set_alpha(alpha)
    rect = img.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
    if shadow:  # drop shadow = same text translated by (2, 2)
        sh = font.render(text, True, (0, 0, 0))
        sh.set_alpha(alpha // 2)
        surface.blit(sh, rect.move(2, 2))
    surface.blit(img, rect)
    return rect


def translucent(surface: pygame.Surface, rect, color: tuple, alpha: int,
                radius: int = 0, fade: int = 255) -> None:
    """Alpha-blended (rounded) rectangle. The surface is cached per size."""
    rect = pygame.Rect(rect)
    key = (rect.size, color, alpha, radius)
    shade = _shades.get(key)
    if shade is None:
        shade = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(shade, (*color, alpha), shade.get_rect(),
                         border_radius=radius)
        if len(_shades) > 60:
            _shades.clear()
        _shades[key] = shade
    shade.set_alpha(fade)
    surface.blit(shade, rect.topleft)


def button(surface: pygame.Surface, rect, text: str, selected: bool = False,
           size: int = 30, base: tuple = (58, 66, 104)) -> None:
    """Cartoon button: shadow, body, gloss strip, border and outlined label."""
    r = pygame.Rect(rect)
    if selected:
        r = r.inflate(12, 6)  # highlighted buttons grow a little
    pygame.draw.rect(surface, (8, 10, 20), r.move(0, 5), border_radius=16)
    pygame.draw.rect(surface, COLORS["accent"] if selected else base, r,
                     border_radius=16)
    translucent(surface, (r.x + 6, r.y + 4, r.w - 12, r.h // 2 - 4),
                (255, 255, 255), 46 if selected else 24, 12)
    pygame.draw.rect(surface, COLORS["white"] if selected else (140, 150, 200),
                     r, 3, border_radius=16)
    img = outlined(text, get_font(size, True), COLORS["white"], INK, 2)
    surface.blit(img, img.get_rect(center=r.center))


def heart(surface: pygame.Surface, cx: float, cy: float, size: float,
          full: bool = True) -> None:
    """Heart from two circles and a triangle (empty hearts are grey)."""
    fill = COLORS["red"] if full else (62, 66, 90)
    edge = (110, 24, 40) if full else (36, 38, 54)
    s, r = size, int(size * 0.28)
    for dx, dy, col in ((1, 2, edge), (0, 0, fill)):  # shadow first, then body
        for side in (-1, 1):
            pygame.draw.circle(surface, col, (int(cx + side * s * 0.25 + dx),
                                              int(cy - s * 0.1 + dy)), r)
        pygame.draw.polygon(surface, col, [
            (cx - s * 0.51 + dx, cy - s * 0.03 + dy),
            (cx + s * 0.51 + dx, cy - s * 0.03 + dy),
            (cx + dx, cy + s * 0.52 + dy)])
    if full:
        pygame.draw.circle(surface, COLORS["white"],
                           (int(cx - s * 0.3), int(cy - s * 0.2)),
                           max(2, int(s * 0.08)))


def mini_light(surface: pygame.Surface, x: int, y: int, state: str) -> None:
    """Tiny 3-lamp signal (red, yellow, green); only `state` is lit."""
    pygame.draw.rect(surface, INK, (x - 9, y - 9, 44, 18), border_radius=9)
    for i, name in enumerate(("red", "yellow", "green")):
        col = COLORS[name]
        if name != state:
            col = tuple(int(c * 0.25) for c in col)
        pygame.draw.circle(surface, col, (x + i * 13, y), 5)


def key_chip(surface: pygame.Surface, text: str, topleft: tuple,
             width: int = 64, height: int = 32) -> pygame.Rect:
    """A keyboard-key looking label (for the controls table)."""
    r = pygame.Rect(topleft, (width, height))
    pygame.draw.rect(surface, (20, 22, 36), r.move(0, 3), border_radius=8)
    pygame.draw.rect(surface, (244, 244, 252), r, border_radius=8)
    pygame.draw.rect(surface, INK, r, 2, border_radius=8)
    label(surface, text, 20, INK, r.center, bold=True, shadow=False)
    return r