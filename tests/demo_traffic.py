"""Traffic demo: python tests/demo_traffic.py

1 / 2 = request NS / EW      A = auto signals (serve the longer queue)
F = stress (level 10 for 30 s)   UP / DOWN = base level
C = crash a random vehicle (obstacle test)   R = reset   ESC = quit
A 3-minute headless stress test with assertions runs at startup.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from src.constants import (COLORS, CRASH_CLEAR_TIME, FPS, HEIGHT, MAX_DT,  # noqa: E402
                           MAX_LEVEL, WIDTH)
from src.road import APPROACHES, Road, intersection_rect  # noqa: E402
from src.signals import SignalController  # noqa: E402
from src.traffic_manager import TrafficManager, progress  # noqa: E402


def lane_overlaps(vehicles: list) -> list[str]:
    """Warnings for same-lane vehicles that overlap (crashed pairs skipped)."""
    lanes: dict[str, list] = {}
    for v in vehicles:
        lanes.setdefault(v.approach, []).append(v)
    msgs = []
    for a, lane in lanes.items():
        lane.sort(key=progress)
        for back, front in zip(lane, lane[1:]):
            if back.state == "crashed" or front.state == "crashed":
                continue  # a vehicle crashed in front of a close follower
            gap = (progress(front) - front.length / 2
                   - progress(back) - back.length / 2)
            if gap < 0 or back.rect.colliderect(front.rect):
                msgs.append(f"{a}: {back.vtype} overlaps {front.vtype} "
                            f"(gap {gap:.1f}px)")
    return msgs


def run_headless(seconds: float = 180.0, seed: int = 11) -> None:
    """Random signal mashing, all levels, random dt. Asserts the traffic rules."""
    rng = random.Random(seed)
    sig, tm, square = SignalController(), TrafficManager(seed), intersection_rect()
    t, passed, peak = 0.0, 0, 0
    while t < seconds:
        dt = rng.choice((1 / 60, 1 / 60, 1 / 60, 1 / 30, MAX_DT))
        level = 1 + int(t // 15) % MAX_LEVEL
        if rng.random() < 0.04:
            sig.request(rng.choice(("NS", "EW")))
        sig.update(dt)
        passed += len(tm.update(dt, sig, level))
        peak = max(peak, len(tm.vehicles))
        bad = lane_overlaps(tm.vehicles)
        assert not bad, f"t={t:.1f}s level {level}: {bad[0]}"
        for v in tm.vehicles:
            assert not (v.state == "stopped" and v.rect.colliderect(square)), \
                f"t={t:.1f}s {v.vtype} from {v.approach} stopped INSIDE the intersection"
        t += dt
    assert passed > 0, "no vehicle ever exited"
    print(f"Headless stress test OK: {seconds:.0f}s simulated, {passed} vehicles "
          f"exited, peak {peak} on screen, 0 overlaps")


def auto_signal(sig: SignalController, tm: TrafficManager) -> None:
    """Tiny AI: request the axis that has more stopped vehicles waiting."""
    waiting = {"NS": 0, "EW": 0}
    for v in tm.vehicles:
        if v.state == "stopped":
            waiting[v.axis] += 1
    cur = sig.destination
    other = "EW" if cur == "NS" else "NS"
    if waiting[other] > waiting[cur]:
        sig.request(other)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Traffic demo - 1/2 signals, A auto, F stress, C crash")
    run_headless()
    road, sig, tm = Road(), SignalController(), TrafficManager()
    font, clock = pygame.font.Font(None, 24), pygame.time.Clock()
    screen_rect, rng = pygame.Rect(0, 0, WIDTH, HEIGHT), random.Random()
    base_level, stress_left, passed = 1, 0.0, 0
    overlap_frames, auto, running = 0, False, True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, MAX_DT)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                k = e.key
                if k == pygame.K_ESCAPE:
                    running = False
                elif k == pygame.K_1:
                    sig.request("NS")
                elif k == pygame.K_2:
                    sig.request("EW")
                elif k == pygame.K_a:
                    auto = not auto
                elif k == pygame.K_f:
                    stress_left = 30.0
                elif k == pygame.K_UP:
                    base_level = min(MAX_LEVEL, base_level + 1)
                elif k == pygame.K_DOWN:
                    base_level = max(1, base_level - 1)
                elif k == pygame.K_c:
                    pool = [v for v in tm.vehicles
                            if v.state != "crashed" and screen_rect.contains(v.rect)]
                    if pool:
                        rng.choice(pool).crash()
                elif k == pygame.K_r:
                    sig.reset()
                    tm.reset()
                    passed = overlap_frames = 0
        level = MAX_LEVEL if stress_left > 0 else base_level
        stress_left = max(0.0, stress_left - dt)
        if auto:
            auto_signal(sig, tm)
        sig.update(dt)
        passed += len(tm.update(dt, sig, level))
        for v in tm.vehicles:  # stand-in for CollisionSystem (Phase 7)
            if v.state == "crashed" and v.crash_timer > CRASH_CLEAR_TIME:
                v.alive = False
        warn = lane_overlaps(tm.vehicles)
        if warn:
            overlap_frames += 1
            if overlap_frames % 60 == 1:
                print("WARNING:", warn[0])

        road.draw(screen)
        sig.draw(screen)
        tm.draw(screen)
        counts = {a: sum(1 for v in tm.vehicles if v.approach == a) for a in APPROACHES}
        stopped = sum(1 for v in tm.vehicles if v.state == "stopped")
        lines = [f"level {level}" + (f" (STRESS {stress_left:4.1f}s)" if stress_left else "")
                 + f"   passed: {passed}   vehicles: {len(tm.vehicles)}"
                 f"   stopped: {stopped}   overlap frames: {overlap_frames}",
                 "per approach  " + "  ".join(f"{a}:{counts[a]}" for a in APPROACHES)
                 + f"   signal: {sig.state}   pending: {sig.pending_request}"
                 f"   auto: {'ON' if auto else 'off'}",
                 "1/2 signal   A auto   F stress   UP/DOWN level   C crash   R reset"]
        for i, text in enumerate(lines):
            screen.blit(font.render(text, True, COLORS["white"], COLORS["black"]),
                        (8, HEIGHT - 82 + i * 26))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()