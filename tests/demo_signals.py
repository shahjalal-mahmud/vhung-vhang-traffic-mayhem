"""Signal demo: python tests/demo_signals.py

1 / 2 = request NS / EW, T = 20 s random-mashing self-test, R = reset, ESC = quit.
A 60 s headless stress test also runs at startup.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from src.constants import (ALL_RED_TIME, COLORS, FPS, HEIGHT, MAX_DT,  # noqa: E402
                           MIN_GREEN, WIDTH, YELLOW_TIME)
from src.road import Road  # noqa: E402
from src.signals import STATES, SignalController  # noqa: E402


class Checker:
    """Validates the controller after every update()."""
    LEGAL = {"NS_GREEN": "NS_YELLOW", "EW_GREEN": "EW_YELLOW",
             "NS_YELLOW": "ALL_RED", "EW_YELLOW": "ALL_RED"}

    def __init__(self, sig: SignalController, verbose: bool = False) -> None:
        self.sig, self.verbose = sig, verbose
        self.prev, self.elapsed, self.last_yellow = sig.state, 0.0, None
        self.frames = self.switches = 0

    def step(self, dt: float) -> None:
        s = self.sig
        self.frames += 1
        self.elapsed += dt
        assert s.state in STATES, f"invalid state {s.state}"
        assert s.light_for("N") == s.light_for("S"), "N/S lights differ"
        assert s.light_for("E") == s.light_for("W"), "E/W lights differ"
        live = [a for a in "NE" if s.light_for(a) != "red"]
        assert len(live) <= 1, "both axes active at once!"
        assert s.state != "ALL_RED" or not live, "ALL_RED must show all red"
        assert s.time_in_state >= 0.0
        if s.state != self.prev:
            old, new = self.prev, s.state
            if old == "ALL_RED":
                want = "EW" if self.last_yellow == "NS" else "NS"
                assert new == f"{want}_GREEN", f"ALL_RED -> {new}?"
                self.switches += 1
            else:
                assert self.LEGAL[old] == new, f"illegal {old} -> {new}"
            lasted = self.elapsed - s.time_in_state  # exact time spent in `old`
            kind = old.split("_")[1]
            if kind == "GREEN":
                assert lasted >= MIN_GREEN - 1e-6, f"green only {lasted:.3f}s"
            elif kind == "YELLOW":
                assert abs(lasted - YELLOW_TIME) < 1e-6, f"yellow {lasted:.3f}s"
                self.last_yellow = old[:2]
            else:
                assert abs(lasted - ALL_RED_TIME) < 1e-6, f"all-red {lasted:.3f}s"
            if self.verbose:
                print(f"{old:<10} lasted {lasted:5.2f}s -> {new}")
            self.prev, self.elapsed = new, s.time_in_state


def run_headless(seconds: float = 60.0, seed: int = 7) -> None:
    """Random requests + random dt, no window."""
    rng = random.Random(seed)
    sig = SignalController()
    chk, t = Checker(sig), 0.0
    while t < seconds:
        dt = rng.uniform(0.004, MAX_DT)
        if rng.random() < 0.3:
            sig.request(rng.choice(("NS", "EW")))
        sig.update(dt)
        chk.step(dt)
        t += dt
    print(f"Headless stress test OK: {chk.frames} frames, {chk.switches} switches")


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Signal demo - 1/2 request, T self-test, R reset")
    run_headless()
    road, sig = Road(), SignalController()
    chk, rng = Checker(sig, verbose=True), random.Random()
    font = pygame.font.Font(None, 26)
    clock, test_left, running = pygame.time.Clock(), 0.0, True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, MAX_DT)
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_1:
                    sig.request("NS")
                elif e.key == pygame.K_2:
                    sig.request("EW")
                elif e.key in (pygame.K_r, pygame.K_t):
                    sig.reset()
                    chk = Checker(sig, verbose=True)
                    test_left = 20.0 if e.key == pygame.K_t else 0.0
        if test_left > 0:  # mash random requests (~18 per second)
            if rng.random() < 0.3:
                sig.request(rng.choice(("NS", "EW")))
            test_left -= dt
            if test_left <= 0:
                print(f"LIVE self-test PASSED ({chk.frames} frames, {chk.switches} switches)")
        sig.update(dt)
        chk.step(dt)
        road.draw(screen)
        sig.draw(screen)
        lines = [f"state: {sig.state}   time_in_state: {sig.time_in_state:4.2f}s",
                 f"progress: {sig.progress:4.2f}   pending: {sig.pending_request}"
                 f"   destination: {sig.destination}",
                 "SELF-TEST running: %.1fs left" % test_left if test_left > 0
                 else "1/2 = request   T = self-test   R = reset   ESC = quit"]
        for i, text in enumerate(lines):
            screen.blit(font.render(text, True, COLORS["white"], COLORS["black"]),
                        (10, 10 + i * 28))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()