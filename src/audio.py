"""STUB - replaced in Phase 10. Silent; no mixer is initialised yet."""
from __future__ import annotations

SOUND_NAMES = ("horn", "crash", "pass", "click", "gameover", "start")


class AudioManager:
    """STUB - replaced in Phase 10."""

    def __init__(self) -> None:
        self.muted = False

    def play(self, name: str) -> None:
        """Would play a generated sound; does nothing for now."""
        return None

    def set_muted(self, muted: bool) -> None:
        """Set mute state."""
        self.muted = bool(muted)

    def toggle_mute(self) -> None:
        """Flip mute state."""
        self.muted = not self.muted