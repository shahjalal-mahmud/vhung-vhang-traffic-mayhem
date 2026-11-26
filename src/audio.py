"""Procedural audio (Phase 9): every sound is synthesised at startup.

No numpy and no asset files: samples are computed with `math`, stored in an
`array.array('h')` (signed 16-bit) and wrapped in pygame.mixer.Sound.
CG/DSP concepts: sampling (22050 samples/s), waveform synthesis (sine, soft
square, triangle), amplitude envelope (attack/decay/release), additive mixing,
one-pole low-pass filter (smooth noise), clipping.
"""
from __future__ import annotations

import array
import math
import random
import time

import pygame

RATE = 22050
TAU = 2.0 * math.pi
SOUND_NAMES = ("horn", "crash", "pass", "click", "gameover", "start")
HORN_GAP = 0.25  # minimum seconds between two horn sounds
_VOLUME = {"horn": 0.45, "crash": 0.85, "pass": 0.5, "click": 0.45,
           "start": 0.5, "gameover": 0.55}
_AMBIENCE_VOLUME = 0.16


# ---------------------------------------------------------------- synthesis
def _tone(freq: float, dur: float, shape: str = "sine", vol: float = 1.0,
          attack: float = 0.006, decay: float = 0.0,
          release: float = 0.02) -> list[float]:
    """One note. Envelope = attack ramp * exp(-decay*t) * release ramp."""
    out = []
    for i in range(int(dur * RATE)):
        t = i / RATE
        ph = TAU * freq * t
        if shape == "square":
            s = math.tanh(3.0 * math.sin(ph))      # soft (rounded) square
        elif shape == "tri":
            s = 0.6366 * math.asin(math.sin(ph))   # triangle
        else:
            s = math.sin(ph)
        env = min(1.0, t / attack, (dur - t) / release) * math.exp(-decay * t)
        out.append(s * env * vol)
    return out


def _noise(dur: float, alpha: float, decay: float, vol: float,
           rng: random.Random) -> list[float]:
    """White noise through a one-pole low-pass (alpha 1 = bright, 0.05 = dull)."""
    y, out = 0.0, []
    for i in range(int(dur * RATE)):
        y += alpha * (rng.uniform(-1.0, 1.0) - y)
        out.append(y * vol * math.exp(-decay * i / RATE))
    return out


def _thud(dur: float) -> list[float]:
    """Low 'boom': a sine whose pitch sweeps down from ~120 Hz to 40 Hz."""
    ph, out = 0.0, []
    for i in range(int(dur * RATE)):
        t = i / RATE
        ph += TAU * (40.0 + 80.0 * math.exp(-7.0 * t)) / RATE
        out.append(math.sin(ph) * math.exp(-5.0 * t) * 0.9)
    return out


def _mix(parts: list[tuple[float, list[float]]]) -> list[float]:
    """Add several sample lists, each starting at its own time (seconds)."""
    n = max(int(st * RATE) + len(s) for st, s in parts)
    out = [0.0] * n
    for st, s in parts:
        o = int(st * RATE)
        for i, v in enumerate(s):
            out[o + i] += v
    return out


def _normalize(s: list[float], peak: float = 0.9) -> list[float]:
    """Scale so the loudest sample equals `peak` (no clipping)."""
    m = max((abs(v) for v in s), default=1.0) or 1.0
    k = peak / m
    return [v * k for v in s]


def _horn() -> list[float]:
    """Two-tone 'pom-pom': 400 Hz then 500 Hz, soft square, quick envelope."""
    return _normalize(_mix([(0.0, _tone(400, 0.17, "square", 0.5, decay=1.5)),
                            (0.2, _tone(500, 0.26, "square", 0.5, decay=2.0))]))


def _crash(rng: random.Random) -> list[float]:
    """Crack (bright noise) + crunch (dull noise, decays) + low thud."""
    return _normalize(_mix([(0.0, _noise(0.7, 0.5, 6.0, 1.4, rng)),
                            (0.0, _noise(0.08, 1.0, 45.0, 0.7, rng)),
                            (0.0, _thud(0.6))]))


def _ding() -> list[float]:
    """Pleasant two-note ding (880 Hz then 1318 Hz, exponential decay)."""
    return _normalize(_mix([(0.0, _tone(880, 0.28, "sine", 0.55, decay=9.0)),
                            (0.07, _tone(1318, 0.35, "sine", 0.5, decay=8.0))]))


def _click() -> list[float]:
    return _normalize(_tone(700, 0.05, "square", 0.4, 0.002, 20.0), 0.7)


def _start() -> list[float]:
    """Rising arpeggio C5 E5 G5 C6."""
    notes = (523.25, 659.25, 783.99, 1046.5)
    return _normalize(_mix([(i * 0.09, _tone(f, 0.12 if i < 3 else 0.3, "tri",
                                              0.6, decay=3.0))
                            for i, f in enumerate(notes)]))


def _gameover() -> list[float]:
    """Descending sad tones G4 F4 Eb4 C4 (triangle wave)."""
    notes = (392.0, 349.2, 311.1, 261.6)
    return _normalize(_mix([(i * 0.24, _tone(f, 0.3 if i < 3 else 0.7, "tri",
                                              0.6, decay=2.5))
                            for i, f in enumerate(notes)]))


def _ambience(rng: random.Random) -> list[float]:
    """2 s loop: low-passed noise + 55 Hz engine hum (whole cycles = seamless)."""
    n, y, out = int(2.0 * RATE), 0.0, []
    for i in range(n):
        t = i / RATE
        y += 0.05 * (rng.uniform(-1.0, 1.0) - y)
        hum = (0.5 * math.sin(TAU * 55 * t) + 0.25 * math.sin(TAU * 110 * t)
               + 0.12 * math.sin(TAU * 165 * t))
        out.append(y * 3.0 + hum * 0.35 * (1.0 + 0.25 * math.sin(TAU * t)))
    fade = int(0.03 * RATE)
    for i in range(fade):  # tiny fades at both ends hide any loop click
        k = i / fade
        out[i] *= k
        out[n - 1 - i] *= k
    return _normalize(out)


# ------------------------------------------------------------------ manager
class AudioManager:
    """Generates all sounds once; stays silent (but alive) without a device."""

    def __init__(self) -> None:
        self.muted = False
        self.enabled = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._amb: pygame.mixer.Sound | None = None
        self._amb_channel: pygame.mixer.Channel | None = None
        self._want_amb = False
        self._last_horn = -1.0
        self._channels = 1
        if self._init_mixer():
            try:
                self._build()
                self.enabled = True
            except Exception as exc:  # never let audio kill the game
                print(f"[audio] could not build sounds ({exc}); running silent")

    def _init_mixer(self) -> bool:
        """22050 Hz, 16-bit, mono. pygame.init() may have opened another format."""
        try:
            cur = pygame.mixer.get_init()
            if cur is None or cur[0] != RATE or cur[1] != -16 or cur[2] != 1:
                pygame.mixer.quit()
                pygame.mixer.init(frequency=RATE, size=-16, channels=1,
                                  buffer=512, allowedchanges=0)
            freq, fmt, ch = pygame.mixer.get_init()
            if freq != RATE or fmt != -16:
                raise pygame.error(f"unsupported mixer format {freq}/{fmt}")
            self._channels = ch
            return True
        except pygame.error as exc:
            print(f"[audio] no audio device ({exc}); running silent")
            return False

    def _to_sound(self, samples: list[float], volume: float) -> pygame.mixer.Sound:
        """float samples (-1..1) -> signed 16-bit bytes -> Sound."""
        data = array.array("h", [int(max(-1.0, min(1.0, s)) * 32767)
                                 for s in samples])
        if self._channels > 1:  # device refused mono: duplicate every sample
            wide = array.array("h")
            for v in data:
                wide.extend((v,) * self._channels)
            data = wide
        snd = pygame.mixer.Sound(buffer=data.tobytes())
        snd.set_volume(volume)
        return snd

    def _build(self) -> None:
        """Synthesise everything (takes about a tenth of a second)."""
        rng = random.Random(1234)  # same noise every run
        makers = {"horn": _horn, "crash": lambda: _crash(rng), "pass": _ding,
                  "click": _click, "start": _start, "gameover": _gameover}
        for name in SOUND_NAMES:
            self._sounds[name] = self._to_sound(makers[name](), _VOLUME[name])
        self._amb = self._to_sound(_ambience(rng), _AMBIENCE_VOLUME)

    # ------------------------------------------------------------- playback
    def play(self, name: str) -> None:
        """Play a one-shot sound (ignored when muted or silent)."""
        snd = self._sounds.get(name)
        if snd is None or self.muted:
            return
        if name == "horn":  # rate limit: many honks must not become noise
            now = time.monotonic()
            if now - self._last_horn < HORN_GAP:
                return
            self._last_horn = now
        try:
            snd.play()
        except pygame.error:
            pass

    def set_ambience(self, on: bool) -> None:
        """Wanted state of the city hum (Game calls this every frame)."""
        self._want_amb = bool(on)
        self._sync_ambience()

    def _sync_ambience(self) -> None:
        """Start/stop the looping hum so it matches (wanted and not muted)."""
        if self._amb is None:
            return
        want = self._want_amb and not self.muted
        playing = self._amb_channel is not None and self._amb_channel.get_busy()
        try:
            if want and not playing:
                self._amb_channel = self._amb.play(loops=-1)
            elif not want and playing:
                self._amb.stop()
                self._amb_channel = None
        except pygame.error:
            pass

    def set_muted(self, muted: bool) -> None:
        """Mute / unmute everything (ambience stops immediately)."""
        self.muted = bool(muted)
        if self.muted and self._sounds:
            try:
                pygame.mixer.stop()
            except pygame.error:
                pass
            self._amb_channel = None
        self._sync_ambience()

    def toggle_mute(self) -> None:
        """Flip the mute state (key M)."""
        self.set_muted(not self.muted)