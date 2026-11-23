"""Small helper functions shared by all modules."""
from __future__ import annotations

import json
import os
from typing import Any

import pygame


def clamp(value: float, lo: float, hi: float) -> float:
    """Limit value to the range [lo, hi]."""
    return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b (t=0 -> a, t=1 -> b)."""
    return a + (b - a) * t


def load_json(path: str, default: Any) -> Any:
    """Read JSON from path; return default if missing or corrupt."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path: str, data: Any) -> bool:
    """Write JSON safely (temp file + replace). Returns True on success."""
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, path)
        return True
    except (OSError, TypeError):
        return False


def draw_text(surface: pygame.Surface, text: str, font: pygame.font.Font,
              color: tuple, pos: tuple, center: bool = False) -> pygame.Rect:
    """Render text at pos (top-left, or centered). Returns its Rect."""
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (int(pos[0]), int(pos[1]))
    else:
        rect.topleft = (int(pos[0]), int(pos[1]))
    surface.blit(img, rect)  # blit = copy pixels onto the back buffer
    return rect


def draw_text_shadow(surface: pygame.Surface, text: str,
                     font: pygame.font.Font, color: tuple, pos: tuple,
                     center: bool = False, shadow_color: tuple = (0, 0, 0),
                     offset: tuple = (2, 2)) -> pygame.Rect:
    """Draw text with a drop shadow (translation of the same text by offset)."""
    sx, sy = pos[0] + offset[0], pos[1] + offset[1]
    draw_text(surface, text, font, shadow_color, (sx, sy), center)
    return draw_text(surface, text, font, color, pos, center)