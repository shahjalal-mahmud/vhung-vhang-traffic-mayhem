"""STUB - replaced in Phase 9. Plain ints plus a working high-score file."""
from __future__ import annotations

import os

from .constants import (HIGHSCORE_FILE, LEVEL_SCORE_STEP, MAX_LEVEL,
                        START_LIVES, VEHICLE_SPECS)
from .utils import load_json, save_json

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PATH = os.path.join(_ROOT, HIGHSCORE_FILE)


class ScoreManager:
    """STUB - replaced in Phase 9."""

    def __init__(self) -> None:
        data = load_json(_PATH, {"high_score": 0})
        hs = data.get("high_score", 0) if isinstance(data, dict) else 0
        self.high_score = hs if isinstance(hs, int) else 0
        self.score = 0
        self.lives = START_LIVES
        self.new_high_score = False

    @property
    def level(self) -> int:
        """Level 1..MAX_LEVEL based on score."""
        return min(MAX_LEVEL, 1 + self.score // LEVEL_SCORE_STEP)

    @property
    def is_game_over(self) -> bool:
        """True when no lives remain."""
        return self.lives <= 0

    def add_vehicle(self, vehicle) -> None:
        """Award points for a vehicle that passed safely."""
        self.score += VEHICLE_SPECS[vehicle.vtype]["points"]

    def lose_life(self) -> None:
        """Remove one life (never below 0)."""
        self.lives = max(0, self.lives - 1)

    def save_high_score(self) -> None:
        """Persist the high score if beaten."""
        if self.score > self.high_score:
            self.high_score = self.score
            self.new_high_score = True
            save_json(_PATH, {"high_score": self.high_score})

    def reset(self) -> None:
        """Start a fresh run (high score is kept)."""
        self.score = 0
        self.lives = START_LIVES
        self.new_high_score = False