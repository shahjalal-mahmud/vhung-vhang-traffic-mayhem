"""UI demo: python tests/demo_ui.py

1 menu   2 help   3 HUD   4 pause   5 game over        ESC = quit
HUD / game-over keys: L lose life   C +combo   B level banner   R reset lives
                      N / E request NS / EW signal   H toggle high score 0
                      V toggle NEW HIGH SCORE   M toggle MUTED label
Menu: mouse or UP/DOWN + ENTER.  Help / game over: mouse buttons work too.
An automatic self-check runs first.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from src.constants import (FPS, HEIGHT, LEVEL_SCORE_STEP, MAX_DT, MAX_LEVEL,  # noqa: E402
                           START_LIVES, STATE_GAME_OVER, STATE_HELP,
                           STATE_MENU, STATE_PAUSED, STATE_PLAYING, WIDTH)
from src.road import Road  # noqa: E402
from src.scoring import COMBO_BONUS, COMBO_EVERY  # noqa: E402
from src.signals import SignalController  # noqa: E402
from src.ui import UI  # noqa: E402


class FakeScore:
    """Stand-in for ScoreManager with freely editable values."""

    def __init__(self, score=340, lives=2, high=1200, combo=3) -> None:
        self.score, self.lives, self.high_score, self.combo = score, lives, high, combo
        self.last_event, self.event_id, self.new_high_score = "+10", 1, False

    @property
    def level(self) -> int:
        return min(MAX_LEVEL, 1 + self.score // LEVEL_SCORE_STEP)

    def bump(self, text: str) -> None:
        self.last_event = text
        self.event_id += 1


def self_check(ui: UI) -> None:
    """Event -> action mapping and a draw of every screen with edge values."""
    def key(k):
        return pygame.event.Event(pygame.KEYDOWN, key=k)

    def click(pos):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)

    ui.sel = 0
    assert ui.handle_event(key(pygame.K_DOWN), STATE_MENU) is None and ui.sel == 1
    assert ui.handle_event(key(pygame.K_RETURN), STATE_MENU) == "help"
    ui.handle_event(key(pygame.K_UP), STATE_MENU)
    assert ui.handle_event(key(pygame.K_SPACE), STATE_MENU) == "play"
    got = [ui.handle_event(click(r.center), STATE_MENU) for r in ui._menu_rects]
    assert got == ["play", "help", "quit"], got
    assert ui.handle_event(click((5, 5)), STATE_MENU) is None
    assert ui.handle_event(click(ui._back_rect.center), STATE_HELP) == "back"
    assert ui.handle_event(click((5, 5)), STATE_HELP) is None
    over = ui._over_rects
    assert ui.handle_event(click(over["restart"].center), STATE_GAME_OVER) == "restart"
    assert ui.handle_event(click(over["menu"].center), STATE_GAME_OVER) == "menu"
    assert ui.handle_event(click(ui._back_rect.center), STATE_PLAYING) is None
    surf, sig = pygame.Surface((WIDTH, HEIGHT)), SignalController()
    for s in (FakeScore(0, 0, 0, 0), FakeScore(99999, 5, 99999, 17)):
        s.last_event = ""
        ui.draw_menu(surf, (0, 0), s.high_score)
        ui.draw_help(surf)
        ui.draw_hud(surf, s, sig)
        ui.draw_pause(surf)
        ui.start_game_over()
        ui.draw_game_over(surf, s)
        ui.draw_banner(surf, "LEVEL 10!", 1.0)
        ui.draw_banner(surf, "LEVEL 10!")
    print("UI self-check OK (events, 5 screens, banner, zero/huge values)")


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("UI demo - keys 1-5 pick a screen")
    road, sig, score = Road(), SignalController(), FakeScore()
    ui = UI(road)
    self_check(ui)
    font, clock = pygame.font.Font(None, 22), pygame.time.Clock()
    screens = {pygame.K_1: STATE_MENU, pygame.K_2: STATE_HELP,
               pygame.K_3: STATE_PLAYING, pygame.K_4: STATE_PAUSED,
               pygame.K_5: STATE_GAME_OVER}
    to_state = {"play": STATE_PLAYING, "restart": STATE_PLAYING,
                "help": STATE_HELP, "back": STATE_MENU, "menu": STATE_MENU}
    state, banner, running = STATE_MENU, 0.0, True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, MAX_DT)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                continue
            action = ui.handle_event(e, state)
            if action:
                print("UI action:", action)
                running = action != "quit"
                state = to_state.get(action, state)
                if state == STATE_GAME_OVER:
                    ui.start_game_over()
                continue
            if e.type != pygame.KEYDOWN:
                continue
            k = e.key
            if k == pygame.K_ESCAPE:
                running = False
            elif k in screens:
                state = screens[k]
                if state == STATE_GAME_OVER:
                    ui.start_game_over()  # replay the shake-in animation
            elif k == pygame.K_l:
                score.lives, score.combo = max(0, score.lives - 1), 0
                score.bump("CRASH! -1 life")
            elif k == pygame.K_c:
                score.combo += 1
                score.score += 10
                if score.combo % COMBO_EVERY == 0:
                    score.score += COMBO_BONUS
                    score.bump(f"COMBO x{score.combo}! +{10 + COMBO_BONUS}")
                else:
                    score.bump("+10")
            elif k == pygame.K_r:
                score.lives = START_LIVES
            elif k == pygame.K_b:
                banner = 2.0
            elif k == pygame.K_n:
                sig.request("NS")
            elif k == pygame.K_e:
                sig.request("EW")
            elif k == pygame.K_h:
                score.high_score = 0 if score.high_score else 1200
            elif k == pygame.K_v:
                score.new_high_score = not score.new_high_score
            elif k == pygame.K_m:
                ui.muted = not ui.muted
        banner = max(0.0, banner - dt)
        if state == STATE_MENU:
            ui.draw_menu(screen, pygame.mouse.get_pos(), score.high_score)
        elif state == STATE_HELP:
            ui.draw_help(screen)
        else:
            if state == STATE_PLAYING:
                sig.update(dt)
            road.draw(screen)
            sig.draw(screen)
            ui.draw_hud(screen, score, sig)
            if banner > 0:
                ui.draw_banner(screen, "LEVEL 3!", banner)
            if state == STATE_PAUSED:
                ui.draw_pause(screen)
            elif state == STATE_GAME_OVER:
                ui.draw_game_over(screen, score)
            tip = font.render("demo: L life  C combo  B banner  N/E signal  "
                              "H best=0  V new-high  R lives  M mute  1-5 screens",
                              True, (255, 255, 255), (0, 0, 0))
            screen.blit(tip, (8, HEIGHT - 62))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()