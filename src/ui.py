"""STUB - replaced in Phase 12. Simple placeholder text screens."""
from __future__ import annotations

import pygame

from .constants import COLORS, HEIGHT, WIDTH
from .utils import draw_text, draw_text_shadow


class UI:
    """STUB - replaced in Phase 12."""

    def __init__(self) -> None:
        pygame.font.init()
        self.title_font = pygame.font.Font(None, 80)
        self.font = pygame.font.Font(None, 36)
        self.small = pygame.font.Font(None, 26)

    def _dim(self, surface: pygame.Surface, alpha: int = 150) -> None:
        """Translucent black overlay (alpha blending)."""
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, alpha))
        surface.blit(shade, (0, 0))

    def draw_menu(self, surface: pygame.Surface, mouse_pos: tuple) -> None:
        """Placeholder main menu."""
        surface.fill(COLORS["ui_bg"])
        cx = WIDTH // 2
        draw_text_shadow(surface, "VhungVhang", self.title_font,
                         COLORS["accent"], (cx, 200), center=True)
        draw_text_shadow(surface, "Traffic Mayhem", self.font,
                         COLORS["ui_text"], (cx, 260), center=True)
        for i, line in enumerate(("ENTER / SPACE = Play", "H = Help",
                                  "ESC = Quit")):
            draw_text(surface, line, self.font, COLORS["ui_text"],
                      (cx, 360 + i * 44), center=True)

    def draw_help(self, surface: pygame.Surface) -> None:
        """Placeholder help screen."""
        surface.fill(COLORS["ui_bg"])
        cx = WIDTH // 2
        draw_text_shadow(surface, "HELP", self.title_font, COLORS["accent"],
                         (cx, 120), center=True)
        lines = ("1 = North-South green", "2 = East-West green",
                 "P = Pause / resume", "R = Restart", "ESC = Quit",
                 "", "H / BACKSPACE = back")
        for i, line in enumerate(lines):
            draw_text(surface, line, self.font, COLORS["ui_text"],
                      (cx, 230 + i * 44), center=True)

    def draw_hud(self, surface: pygame.Surface, score_mgr, signals) -> None:
        """Placeholder HUD in the top-left corner."""
        info = (f"Score: {score_mgr.score}   Lives: {score_mgr.lives}   "
                f"Level: {score_mgr.level}   Best: {score_mgr.high_score}")
        draw_text_shadow(surface, info, self.font, COLORS["white"], (14, 10))
        draw_text_shadow(surface, f"Signal: {signals.state}", self.small,
                         COLORS["yellow"], (14, 46))
        draw_text_shadow(surface, "[debug] L = lose life, K = +50 score",
                         self.small, COLORS["white"], (14, HEIGHT - 30))

    def draw_pause(self, surface: pygame.Surface) -> None:
        """Placeholder pause overlay."""
        self._dim(surface)
        draw_text_shadow(surface, "PAUSED", self.title_font, COLORS["white"],
                         (WIDTH // 2, HEIGHT // 2 - 20), center=True)
        draw_text(surface, "P = resume   R = restart   ESC = quit", self.font,
                  COLORS["ui_text"], (WIDTH // 2, HEIGHT // 2 + 40), center=True)

    def draw_game_over(self, surface: pygame.Surface, score_mgr) -> None:
        """Placeholder game-over overlay."""
        self._dim(surface, 180)
        cx, cy = WIDTH // 2, HEIGHT // 2
        draw_text_shadow(surface, "GAME OVER", self.title_font, COLORS["red"],
                         (cx, cy - 80), center=True)
        draw_text(surface, f"Score: {score_mgr.score}   "
                  f"Best: {score_mgr.high_score}", self.font,
                  COLORS["ui_text"], (cx, cy), center=True)
        if score_mgr.new_high_score:
            draw_text_shadow(surface, "NEW HIGH SCORE!", self.font,
                             COLORS["yellow"], (cx, cy + 44), center=True)
        draw_text(surface, "R = restart   ENTER = menu", self.font,
                  COLORS["ui_text"], (cx, cy + 100), center=True)

    def handle_event(self, event: pygame.event.Event, state: str) -> str | None:
        """Return an action ('play','help','back','quit','restart','menu').

        STUB: no mouse buttons yet, so always None.
        """
        return None