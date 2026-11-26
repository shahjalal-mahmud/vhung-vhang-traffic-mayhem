"""Game class: window, state machine and main loop (double buffered)."""
from __future__ import annotations

import pygame

from .audio import AudioManager
from .chaos import ChaosSystem
from .collision import CollisionSystem
from .constants import (COLORS, FPS, HEIGHT, MAX_DT, STATE_GAME_OVER,
                        STATE_HELP, STATE_MENU, STATE_PAUSED, STATE_PLAYING,
                        WIDTH)
from .effects import EffectsSystem
from .road import Road
from .scoring import ScoreManager
from .signals import SignalController
from .traffic_manager import TrafficManager
from .ui import UI
from .utils import draw_text_shadow

_ENTER_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class Game:
    """Owns every subsystem and runs: events -> update(dt) -> draw -> flip."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("VhungVhang: Traffic Mayhem")
        self.clock = pygame.time.Clock()
        self.running = True
        self.show_fps = False
        self.state = STATE_MENU
        self.road = Road()
        self.signals = SignalController()
        self.traffic = TrafficManager()
        self.chaos = ChaosSystem()
        self.collisions = CollisionSystem()
        self.score = ScoreManager()
        self.ui = UI()
        self.audio = AudioManager()
        self.effects = EffectsSystem()
        self._fps_font = pygame.font.Font(None, 24)

    # ------------------------------------------------------------ main loop
    def run(self) -> None:
        """Main loop. display.flip() swaps back/front buffers (double buffering)."""
        while self.running:
            # tick() caps at FPS and returns ms since last frame -> dt seconds
            dt = min(self.clock.tick(FPS) / 1000.0, MAX_DT)
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()

    # --------------------------------------------------------------- events
    def handle_events(self) -> None:
        """Process the OS event queue."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            action = self.ui.handle_event(event, self.state)
            if action:
                self._apply_action(action)
            if event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    def _apply_action(self, action: str) -> None:
        """Run a UI action string."""
        if action == "play" or action == "restart":
            self.start_game()
        elif action == "help":
            self.state = STATE_HELP
        elif action in ("back", "menu"):
            self.state = STATE_MENU
        elif action == "quit":
            self.running = False

    def _on_key(self, key: int) -> None:
        """Keyboard handling for every state."""
        if key == pygame.K_ESCAPE:
            self.running = False
            return
        if key == pygame.K_F3:
            self.show_fps = not self.show_fps
            return
        if self.state == STATE_MENU:
            if key in _ENTER_KEYS:
                self.start_game()
            elif key == pygame.K_h:
                self.state = STATE_HELP
        elif self.state == STATE_HELP:
            if key in (pygame.K_h, pygame.K_BACKSPACE, pygame.K_RETURN):
                self.state = STATE_MENU
        elif self.state == STATE_PLAYING:
            self._on_key_playing(key)
        elif self.state == STATE_PAUSED:
            if key == pygame.K_p:
                self.state = STATE_PLAYING
            elif key == pygame.K_r:
                self.start_game()
        elif self.state == STATE_GAME_OVER:
            if key == pygame.K_r:
                self.start_game()
            elif key in _ENTER_KEYS:
                self.state = STATE_MENU

    def _on_key_playing(self, key: int) -> None:
        """Keys that work while playing."""
        if key == pygame.K_1:
            self.signals.request("NS")  # key 1: North-South wants green
        elif key == pygame.K_2:
            self.signals.request("EW")  # key 2: East-West wants green
        elif key == pygame.K_p:
            self.state = STATE_PAUSED
        elif key == pygame.K_r:
            self.start_game()
        elif key == pygame.K_l:  # temporary debug key (Phase 1 only)
            self.score.lose_life()
        elif key == pygame.K_k:  # temporary debug key (Phase 1 only)
            self.score.score += 50

    # ---------------------------------------------------------- state logic
    def start_game(self) -> None:
        """Reset all subsystems and enter PLAYING."""
        self.signals.reset()
        self.traffic.reset()
        self.score.reset()
        self.effects = EffectsSystem()
        self.state = STATE_PLAYING
        self.audio.play("start")

    def _end_game(self) -> None:
        """Enter GAME_OVER and save the high score."""
        self.score.save_high_score()
        self.state = STATE_GAME_OVER
        self.audio.play("gameover")

    def update(self, dt: float) -> None:
        """Advance the simulation (dt in seconds). Only runs while PLAYING."""
        if self.state != STATE_PLAYING:
            return
        level = self.score.level
        self.signals.update(dt)
        self.chaos.update(dt, self.traffic.vehicles, level)
        for v in self.traffic.vehicles:  # honk warning from impatient drivers
            if getattr(v, "honk", False):
                v.honk = False
                self.audio.play("horn")
        for v in self.traffic.update(dt, self.signals, level):
            self.score.add_vehicle(v)
            self.audio.play("pass")
        for a, b in self.collisions.update(dt, self.traffic.vehicles):
            self.score.lose_life()
            self.audio.play("crash")
            self.effects.spawn_sparks(self.collisions.get_crash_point(a, b))
            print(f"CRASH: {a.vtype} from {a.approach} x {b.vtype} from {b.approach}")
        self.effects.update(dt)
        if self.score.is_game_over:
            self._end_game()

    # -------------------------------------------------------------- drawing
    def _draw_scene(self) -> None:
        """Draw the world back-to-front (painter's algorithm)."""
        self.road.draw(self.screen)
        self.signals.draw(self.screen)
        self.traffic.draw(self.screen)
        self.effects.draw(self.screen)
        self.ui.draw_hud(self.screen, self.score, self.signals)

    def draw(self) -> None:
        """Render the current state into the back buffer."""
        if self.state == STATE_MENU:
            self.ui.draw_menu(self.screen, pygame.mouse.get_pos())
        elif self.state == STATE_HELP:
            self.ui.draw_help(self.screen)
        else:
            self._draw_scene()
            if self.state == STATE_PAUSED:
                self.ui.draw_pause(self.screen)
            elif self.state == STATE_GAME_OVER:
                self.ui.draw_game_over(self.screen, self.score)
        if self.show_fps:
            draw_text_shadow(self.screen, f"FPS: {self.clock.get_fps():.0f}",
                             self._fps_font, COLORS["yellow"],
                             (WIDTH - 90, 10))