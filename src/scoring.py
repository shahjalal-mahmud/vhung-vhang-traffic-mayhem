"""Score, lives, combo, level and persistent high score (Phase 7)."""
from __future__ import annotations

import os

from .constants import (HIGHSCORE_FILE, LEVEL_SCORE_STEP, MAX_LEVEL,
                        START_LIVES)
from .utils import load_json, save_json
from .vehicle_art import spec_value

COMBO_EVERY = 5    # every 5 consecutive safe vehicles ...
COMBO_BONUS = 10   # ... give this many bonus points

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PATH = os.path.join(_ROOT, HIGHSCORE_FILE)  # stored next to main.py


class ScoreManager:
    """Tracks score, lives, combo and the saved high score."""

    def __init__(self, path: str | None = None) -> None:
        self._path = path or _PATH
        data = load_json(self._path, {"high_score": 0})
        hs = data.get("high_score", 0) if isinstance(data, dict) else 0
        ok = isinstance(hs, int) and not isinstance(hs, bool) and hs > 0
        self.high_score: int = hs if ok else 0
        self.score = 0
        self.lives = START_LIVES
        self.combo = 0            # consecutive safe vehicles since last crash
        self.last_event = ""      # short text for the HUD ("+10", "CRASH!"...)
        self.event_id = 0         # +1 on every new last_event (HUD change flag)
        self.new_high_score = False

    # ------------------------------------------------------------ properties
    @property
    def level(self) -> int:
        """Level 1..MAX_LEVEL: one level per LEVEL_SCORE_STEP points."""
        return min(MAX_LEVEL, 1 + self.score // LEVEL_SCORE_STEP)

    @property
    def is_game_over(self) -> bool:
        """True when no lives remain."""
        return self.lives <= 0

    # --------------------------------------------------------------- events
    def _event(self, text: str) -> None:
        self.last_event = text
        self.event_id += 1

    def add_vehicle(self, vehicle) -> None:
        """Award points for a vehicle that passed safely (+ combo bonus)."""
        points = int(spec_value(vehicle.vtype, "points"))
        self.score += points
        self.combo += 1
        if self.combo % COMBO_EVERY == 0:
            self.score += COMBO_BONUS
            self._event(f"COMBO x{self.combo}! +{points + COMBO_BONUS}")
        else:
            self._event(f"+{points}")

    def lose_life(self) -> None:
        """A crash: lose one life (never below 0) and reset the combo."""
        self.lives = max(0, self.lives - 1)
        self.combo = 0
        self._event("CRASH! -1 life")

    # ---------------------------------------------------------- persistence
    def save_high_score(self) -> None:
        """Save only if this run beat the stored high score."""
        if self.score > self.high_score:
            self.high_score = self.score
            self.new_high_score = True
            save_json(self._path, {"high_score": self.high_score})

    def reset(self) -> None:
        """Fresh run (the high score is kept)."""
        self.score = 0
        self.lives = START_LIVES
        self.combo = 0
        self.last_event = ""
        self.event_id = 0
        self.new_high_score = False