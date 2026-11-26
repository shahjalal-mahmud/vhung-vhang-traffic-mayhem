"""Full cartoon UI (Phase 8): menu, help, HUD, pause, game over, level banner.

CG concepts: alpha blending (translucent HUD/overlays), easing (slide / fade /
shake animations), sprite reuse (decorative traffic = the real Vehicle class),
painter's algorithm (road -> vehicles -> dim layer -> widgets), parametric
motion (sine wave bounce of the title letters).
"""
from __future__ import annotations

import math
import random

import pygame

from .constants import (COLORS, CX, HEIGHT, LEVEL_SCORE_STEP, START_LIVES,
                        STATE_GAME_OVER, STATE_HELP, STATE_MENU, WIDTH)
from .road import Road
from .scoring import COMBO_BONUS, COMBO_EVERY
from .ui_widgets import (INK, button, ease_out, get_font, heart, key_chip,
                         label, mini_light, outlined, translucent)
from .vehicle_art import VEHICLE_TYPES, get_sprite, spec_value
from .vehicles import Vehicle

MENU_ITEMS = (("PLAY", "play"), ("HOW TO PLAY", "help"), ("QUIT", "quit"))
CREDIT = "Md Shahajalal Mahmud | 11230321539 | NUBTK"
BANNER_TIME = 2.0  # must match Game's level banner time
_TOP_H = 56
_DIM = (170, 178, 210)
_DECO_SPEED, _DECO_GAP, _LOOP = 110.0, 380, WIDTH + 160
_NAMES = {"cng": "CNG"}
_CONTROLS = (("1", "North-South gets green"), ("2", "East-West gets green"),
             ("P", "Pause / resume"), ("R", "Restart the game"),
             ("M", "Mute / unmute sound"), ("ESC", "Quit"))
_RULES = ("Let vehicles pass safely to score.",
          "Impatient drivers may run red lights!",
          f"A crash costs 1 life ({START_LIVES} lives in total).",
          f"Every {LEVEL_SCORE_STEP} points = next level, faster.",
          f"{COMBO_EVERY} safe in a row = +{COMBO_BONUS} bonus.")


def _now() -> float:
    """Wall-clock seconds (only used for cosmetic animations)."""
    return pygame.time.get_ticks() / 1000.0


class UI:
    """Draws every screen and turns mouse/keyboard input into action strings."""

    def __init__(self, road: Road | None = None) -> None:
        pygame.font.init()
        self.road = road if road is not None else Road()  # reuse Game's road
        self.muted = False  # Game sets this when M is pressed
        self.sel = 0        # selected menu button
        self._last_mouse = (-1, -1)
        self._last_t = _now()
        self._rng = random.Random(7)
        self._menu_rects = [pygame.Rect(0, 0, 280, 56) for _ in MENU_ITEMS]
        for i, r in enumerate(self._menu_rects):
            r.center = (CX, 292 + i * 72)
        self._panel = pygame.Rect(CX - 170, 232, 340, 262)
        self._back_rect = pygame.Rect(0, 0, 220, 52)
        self._back_rect.center = (CX, 644)
        self._over_rects = {"restart": pygame.Rect(290, 484, 200, 56),
                            "menu": pygame.Rect(510, 484, 200, 56)}
        self._go_t0: float | None = None
        self._seen_event, self._event_t0 = 0, 0.0
        self._banner_text, self._banner_t0 = "", 0.0
        self._deco = [self._new_deco(a, -60 + k * _DECO_GAP if a == "W"
                                     else WIDTH + 60 - k * _DECO_GAP)
                      for a in ("W", "E") for k in range(3)]

    # ------------------------------------------------------------- input
    def handle_event(self, event: pygame.event.Event, state: str) -> str | None:
        """Return 'play','help','back','quit','restart','menu' or None."""
        if state == STATE_MENU:
            return self._menu_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == STATE_HELP and self._back_rect.collidepoint(event.pos):
                return "back"
            if state == STATE_GAME_OVER:
                for action, rect in self._over_rects.items():
                    if rect.collidepoint(event.pos):
                        return action
        return None

    def _menu_event(self, event: pygame.event.Event) -> str | None:
        """UP/DOWN + ENTER or mouse hover/click on the three menu buttons."""
        n = len(MENU_ITEMS)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % n
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % n
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return MENU_ITEMS[self.sel][1]
        elif event.type == pygame.MOUSEMOTION:
            self._hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._menu_rects):
                if rect.collidepoint(event.pos):
                    self.sel = i
                    return MENU_ITEMS[i][1]
        return None

    def _hover(self, pos: tuple) -> None:
        """Mouse over a button selects it (keyboard and mouse share `sel`)."""
        if pos != self._last_mouse:
            self._last_mouse = pos
            for i, rect in enumerate(self._menu_rects):
                if rect.collidepoint(pos):
                    self.sel = i

    def start_game_over(self) -> None:
        """Restart the game-over shake-in animation (Game calls this)."""
        self._go_t0 = _now()

    # -------------------------------------------------------------- menu
    def _new_deco(self, approach: str, x: float) -> Vehicle:
        """Decorative vehicle on the horizontal road, constant speed."""
        v = Vehicle(self._rng.choice(VEHICLE_TYPES), approach)
        v.x = float(x)
        v.speed = v.target_speed = _DECO_SPEED
        return v

    def _update_deco(self) -> None:
        """Move the menu traffic (real-time dt) and wrap it around."""
        now = _now()
        dt = min(0.05, max(0.0, now - self._last_t))
        self._last_t = now
        for i, v in enumerate(self._deco):
            v.update(dt)
            if not v.alive:  # left the screen: re-enter on the other side
                x = v.x - _LOOP if v.heading[0] > 0 else v.x + _LOOP
                self._deco[i] = self._new_deco(v.approach, x)

    def draw_menu(self, surface: pygame.Surface, mouse_pos: tuple,
                  high_score: int = 0) -> None:
        """Animated menu: road + traffic, bouncing title, 3 buttons, credit."""
        t = _now()
        self._hover(tuple(mouse_pos))
        self.road.draw(surface)
        self._update_deco()
        for v in self._deco:
            v.draw(surface)
        translucent(surface, (0, 0, WIDTH, HEIGHT), (20, 24, 48), 110)
        self._title(surface, t)
        translucent(surface, self._panel, (20, 24, 44), 175, 24)
        pygame.draw.rect(surface, COLORS["accent"], self._panel, 3, border_radius=24)
        for i, (text, _) in enumerate(MENU_ITEMS):
            button(surface, self._menu_rects[i], text, i == self.sel)
        label(surface, f"BEST SCORE: {high_score}", 30, COLORS["yellow"],
              (CX, 528), bold=True)
        label(surface, "UP / DOWN + ENTER, or click   |   M = mute", 18, _DIM,
              (CX, 566))
        label(surface, CREDIT, 18, COLORS["ui_text"], (CX, 676))
        if self.muted:
            label(surface, "SOUND OFF", 20, COLORS["red"], (WIDTH - 14, 20),
                  "midright", True)

    def _title(self, surface: pygame.Surface, t: float) -> None:
        """Title letters bounce on a travelling sine wave."""
        font, text = get_font(92, True), "VhungVhang"
        widths = [font.size(c)[0] for c in text]
        x = CX - sum(widths) // 2
        for i, ch in enumerate(text):
            col = COLORS["accent"] if i % 2 == 0 else COLORS["yellow"]
            img = outlined(ch, font, col, INK, 5)
            y = 100 + math.sin(t * 3.2 + i * 0.6) * 9
            surface.blit(img, img.get_rect(center=(x + widths[i] // 2, int(y))))
            x += widths[i]
        sub = outlined("Traffic Mayhem", get_font(40, True), COLORS["white"], INK, 3)
        surface.blit(sub, sub.get_rect(center=(CX, 176 + int(math.sin(t * 2) * 3))))

    # -------------------------------------------------------------- help
    def draw_help(self, surface: pygame.Surface) -> None:
        """Controls table, rules, scoring table with vehicle icons, BACK."""
        surface.fill(COLORS["ui_bg"])
        label(surface, "HOW TO PLAY", 50, COLORS["accent"], (CX, 46), bold=True)
        for box in (pygame.Rect(30, 92, 470, 508), pygame.Rect(520, 92, 450, 508)):
            translucent(surface, box, (255, 255, 255), 18, 20)
            pygame.draw.rect(surface, (90, 100, 150), box, 2, border_radius=20)
        yellow, text_c = COLORS["yellow"], COLORS["ui_text"]
        label(surface, "CONTROLS", 26, yellow, (52, 120), "midleft", True)
        for i, (key, text) in enumerate(_CONTROLS):
            y = 150 + i * 42
            key_chip(surface, key, (52, y))
            label(surface, text, 22, text_c, (132, y + 16), "midleft")
        label(surface, "RULES", 26, yellow, (52, 424), "midleft", True)
        for i, line in enumerate(_RULES):
            label(surface, line, 20, text_c, (52, 458 + i * 28), "midleft")
        label(surface, "SCORING", 26, yellow, (542, 120), "midleft", True)
        for i, vt in enumerate(VEHICLE_TYPES):
            cy = 172 + i * 54
            if i:
                pygame.draw.line(surface, (70, 78, 120), (540, cy - 27), (950, cy - 27))
            spr = get_sprite(vt, (1, 0), 0, False)  # same art as in the game
            surface.blit(spr, spr.get_rect(center=(600, cy)))
            label(surface, _NAMES.get(vt, vt.capitalize()), 24, COLORS["white"],
                  (668, cy), "midleft")
            label(surface, f"+{spec_value(vt, 'points')}", 28, yellow,
                  (945, cy), "midright", True)
        translucent(surface, (540, 478, 410, 100), (255, 143, 56), 40, 16)
        label(surface, "COMBO BONUS", 24, COLORS["accent"], (745, 505), bold=True)
        label(surface, f"{COMBO_EVERY} safe vehicles in a row = +{COMBO_BONUS}",
              20, text_c, (745, 536))
        label(surface, "A crash resets the combo!", 20, COLORS["red"], (745, 562))
        hover = self._back_rect.collidepoint(pygame.mouse.get_pos())
        button(surface, self._back_rect, "BACK", hover, size=28)
        label(surface, "H / BACKSPACE", 18, _DIM,
              (self._back_rect.right + 16, self._back_rect.centery), "midleft")

    # --------------------------------------------------------------- HUD
    def _stat(self, surface, name: str, value: str, x: int,
              color: tuple = COLORS["white"]) -> None:
        label(surface, name, 15, _DIM, (x, 15), "midleft", shadow=False)
        label(surface, value, 28, color, (x, 37), "midleft", True)

    def draw_hud(self, surface: pygame.Surface, score_mgr, signals) -> None:
        """Translucent top bar + bottom hint; the road stays visible."""
        t = _now()
        translucent(surface, (0, 0, WIDTH, _TOP_H), (14, 18, 36), 175)
        pygame.draw.line(surface, COLORS["accent"], (0, _TOP_H), (WIDTH, _TOP_H), 2)
        self._stat(surface, "SCORE", str(score_mgr.score), 16)
        self._stat(surface, "BEST", str(max(score_mgr.high_score, score_mgr.score)),
                   150, COLORS["yellow"])
        self._stat(surface, "LEVEL", str(score_mgr.level), 280, COLORS["green"])
        label(surface, "LIVES", 15, _DIM, (372, 15), "midleft", shadow=False)
        for i in range(max(START_LIVES, score_mgr.lives)):
            size = 24 + (3 * math.sin(t * 8) if score_mgr.lives == 1 and i == 0 else 0)
            heart(surface, 386 + i * 32, 38, size, i < score_mgr.lives)
        label(surface, f"COMBO x{score_mgr.combo}", 15, _DIM, (498, 15),
              "midleft", shadow=False)
        for i in range(COMBO_EVERY):  # pips fill up to the next bonus
            on = i < score_mgr.combo % COMBO_EVERY
            pygame.draw.circle(surface, COLORS["accent"] if on else (60, 66, 96),
                               (504 + i * 15, 40), 5)
        for row, (name, app) in enumerate((("N-S", "N"), ("E-W", "E"))):
            y = 17 + row * 23
            label(surface, name, 16, COLORS["white"], (628, y), "midleft",
                  True, shadow=False)
            mini_light(surface, 680, y, signals.light_for(app))
        pend = signals.pending_request
        if pend:  # a request is waiting for MIN_GREEN to pass
            a = 160 + int(95 * abs(math.sin(t * 6)))
            label(surface, f"NEXT: {'N-S' if pend == 'NS' else 'E-W'}", 22,
                  COLORS["yellow"], (750, 28), "midleft", True, alpha=a)
        if self.muted:
            label(surface, "MUTED", 16, COLORS["red"], (WIDTH - 14, 28),
                  "midright", True)
        self._event_text(surface, score_mgr)
        translucent(surface, (0, HEIGHT - 34, WIDTH, 34), (14, 18, 36), 150)
        label(surface, "1 = North-South  |  2 = East-West  |  P = Pause", 20,
              COLORS["white"], (CX, HEIGHT - 17))

    def _event_text(self, surface: pygame.Surface, score_mgr) -> None:
        """'+10' / 'COMBO x5!' / 'CRASH!' floats up under the bar for 2 s."""
        now = _now()
        if score_mgr.event_id != self._seen_event:
            self._seen_event, self._event_t0 = score_mgr.event_id, now
        age, text = now - self._event_t0, score_mgr.last_event
        if not text or age > 2.0:
            return
        color = COLORS["red"] if text.startswith("CRASH") else COLORS["yellow"]
        img = outlined(text, get_font(30, True), color, INK, 3)
        img.set_alpha(int(255 * min(1.0, (2.0 - age) / 0.5)))
        y = 88 + int(18 * (1 - ease_out(min(1.0, age / 0.25))))
        surface.blit(img, img.get_rect(center=(CX, y)))

    # ------------------------------------------------- pause / game over
    def draw_pause(self, surface: pygame.Surface) -> None:
        """Dark translucent layer with a pulsing PAUSED panel."""
        translucent(surface, (0, 0, WIDTH, HEIGHT), (8, 10, 24), 160)
        panel = pygame.Rect(CX - 250, 230, 500, 240)
        translucent(surface, panel, (24, 28, 52), 235, 26)
        pygame.draw.rect(surface, COLORS["accent"], panel, 4, border_radius=26)
        img = outlined("PAUSED", get_font(84, True), COLORS["white"], INK, 5)
        y = 305 + int(math.sin(_now() * 3) * 5)
        surface.blit(img, img.get_rect(center=(CX, y)))
        label(surface, "P = Resume     R = Restart", 28, COLORS["ui_text"], (CX, 385))
        label(surface, "M = Mute     ESC = Quit", 24, _DIM, (CX, 425))

    def draw_game_over(self, surface: pygame.Surface, score_mgr) -> None:
        """Title drops in with a decaying shake; high score blinks."""
        age = 99.0 if self._go_t0 is None else _now() - self._go_t0
        k = min(1.0, age / 0.7)
        translucent(surface, (0, 0, WIDTH, HEIGHT), (6, 8, 20), 185)
        panel = pygame.Rect(240, 160, 520, 420)
        translucent(surface, panel, (24, 28, 52), 240, 28)
        pygame.draw.rect(surface, COLORS["red"], panel, 4, border_radius=28)
        shake = math.sin(age * 45) * 24 * (1 - k)  # decaying horizontal shake
        ty = 235 - 280 * (1 - ease_out(k))          # falls in from above
        img = outlined("GAME OVER", get_font(76, True), COLORS["red"], INK, 5)
        surface.blit(img, img.get_rect(center=(int(CX + shake), int(ty))))
        a = int(255 * min(1.0, max(0.0, (age - 0.5) / 0.4)))  # fade in the rest
        label(surface, f"SCORE: {score_mgr.score}", 44, COLORS["white"],
              (CX, 318), bold=True, alpha=a)
        label(surface, f"BEST: {score_mgr.high_score}", 30, COLORS["yellow"],
              (CX, 368), bold=True, alpha=a)
        label(surface, f"Level reached: {score_mgr.level}", 22, _DIM,
              (CX, 404), alpha=a)
        if score_mgr.new_high_score and age > 0.7 and int(age * 2.5) % 2 == 0:
            label(surface, "NEW HIGH SCORE!", 38, COLORS["yellow"], (CX, 446),
                  bold=True)
        mouse = pygame.mouse.get_pos()
        for name, text in (("restart", "RESTART (R)"), ("menu", "MENU (ENTER)")):
            rect = self._over_rects[name]
            button(surface, rect, text, rect.collidepoint(mouse), size=22)

    # ------------------------------------------------------------ banner
    def draw_banner(self, surface: pygame.Surface, text: str,
                    remaining: float | None = None) -> None:
        """Level-up banner: slides down, holds, fades. `remaining` = seconds left
        (Game passes level_banner); without it the UI times itself."""
        if remaining is None:
            if text != self._banner_text:
                self._banner_text, self._banner_t0 = text, _now()
            age = _now() - self._banner_t0
        else:
            age = BANNER_TIME - remaining
        if not 0.0 <= age <= BANNER_TIME:
            return
        fade = int(255 * min(1.0, (BANNER_TIME - age) / 0.5))
        cy = int(-50 + 210 * ease_out(min(1.0, age / 0.4)))  # slide-in
        img = outlined(text, get_font(76, True), COLORS["yellow"], INK, 5)
        ribbon = pygame.Rect(0, 0, img.get_width() + 90, 110)
        ribbon.center = (CX, cy)
        translucent(surface, ribbon, (20, 24, 48), 190, 30, fade)
        img.set_alpha(fade)
        surface.blit(img, img.get_rect(center=(CX, cy)))