"""Collision demo: python tests/demo_collision.py [--no-window]

First runs deterministic tests (PASS/FAIL), then the interactive simulation.
1 / 2 = request NS / EW     X = chaos boost (x5 / x15 / x1)
UP / DOWN = level           B = hit boxes     R = reset     ESC = quit
Orange ring = vehicle currently ignoring its signal.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from src.chaos import ChaosSystem, reckless_factor  # noqa: E402
from src.collision import CollisionSystem, get_crash_point, hit_box  # noqa: E402
from src.constants import (COLORS, CRASH_CLEAR_TIME, FPS, HEIGHT, MAX_DT,  # noqa: E402
                           MAX_LEVEL, START_LIVES, WIDTH)
from src.road import Road, intersection_rect, lane_center, stop_line  # noqa: E402
from src.signals import SignalController  # noqa: E402
from src.traffic_manager import TrafficManager  # noqa: E402
from src.vehicles import Vehicle  # noqa: E402

BOOSTS = (5.0, 15.0, 1.0)  # chaos rate multipliers for the interactive demo


def make(vtype: str, approach: str, x=None, y=None) -> Vehicle:
    """Vehicle on its lane, optionally moved to x / y."""
    v = Vehicle(vtype, approach)
    if x is not None:
        v.x = float(x)
    if y is not None:
        v.y = float(y)
    return v


def run_test(name: str, fn) -> bool:
    """Run one test function; print PASS/FAIL."""
    try:
        info = fn()
    except AssertionError as e:
        print(f"FAIL  {name}: {e}")
        return False
    print(f"PASS  {name}" + (f"  ({info})" if info else ""))
    return True


# ------------------------------------------------------------------ tests
def scripted_scenario() -> str:
    """Rickshaw from N and motorcycle from W reach the crossing point together."""
    chaos, coll = ChaosSystem(seed=0), CollisionSystem()
    rick, moto = Vehicle("rickshaw", "N"), Vehicle("motorcycle", "W")
    meet_x, meet_y = lane_center("N"), lane_center("W")  # the two lanes cross here
    arrive = 1.5  # seconds until both centres reach the crossing point
    rick.y = meet_y - rick.cruise_speed * arrive
    moto.x = meet_x - moto.cruise_speed * arrive
    for v in (rick, moto):
        v.speed = v.target_speed = v.cruise_speed
    moto.ignores_signal = True  # W has red (NS_GREEN) but this driver runs it
    vehicles = [rick, moto]
    dt, t = 1 / 60, 0.0
    crashes, crash_t, removed_t, frozen, point = [], None, None, None, None
    while t < 10.0 and vehicles:
        chaos.update(dt, vehicles, 1)
        for v in vehicles:
            if v.state != "crashed":
                v.target_speed = v.cruise_speed  # drivers keep going
            v.update(dt)
        new = coll.update(dt, vehicles)
        if new:
            crashes += new
            if crash_t is None:
                crash_t, point = t, get_crash_point(*new[0])
                frozen = (rick.x, rick.y, moto.x, moto.y)
                assert rick.state == "crashed" and moto.state == "crashed", \
                    "both vehicles must be crashed"
        if removed_t is None and not (rick.alive and moto.alive):
            removed_t = t
            assert (rick.x, rick.y, moto.x, moto.y) == frozen, "wrecks moved"
        vehicles = [v for v in vehicles if v.alive]
        t += dt
    assert len(crashes) == 1, f"expected exactly 1 collision, got {len(crashes)}"
    assert set(crashes[0]) == {rick, moto}, "wrong vehicles in the collision"
    assert 1.0 <= crash_t <= 2.0, f"crash at unexpected time {crash_t:.2f}s"
    assert intersection_rect().collidepoint(point), f"crash point {point} outside"
    assert removed_t is not None, "wrecks were never removed"
    assert abs(removed_t - crash_t - CRASH_CLEAR_TIME) < 0.1, "wrong clear time"
    assert not vehicles and not rick.alive and not moto.alive
    assert not moto.ignores_signal, "runner flag must reset after the crash"
    return (f"crash at t={crash_t:.2f}s, point=({point[0]:.0f}, {point[1]:.0f}), "
            f"removed {removed_t - crash_t:.2f}s later")


def near_miss_test() -> str:
    """15 % shrink: grazing bodies do not crash; real overlaps do; same lane never."""
    coll, mx, my = CollisionSystem(), lane_center("N"), lane_center("W")
    a, b = make("car", "N", y=my + 42), make("car", "W", x=mx + 42)
    assert a.rect.colliderect(b.rect), "test setup: raw rects must touch"
    assert coll.update(0.016, [a, b]) == [], "a graze must not count"
    assert a.state != "crashed" and b.state != "crashed"
    a.y, b.x = my + 20, mx + 20  # now a real overlap
    hits = coll.update(0.016, [a, b])
    assert len(hits) == 1 and a.state == b.state == "crashed", "real hit missed"
    assert coll.update(0.016, [a, b]) == [], "a pair must be reported only once"
    c1, c2 = make("car", "N", y=300), make("car", "N", y=320)  # same lane
    assert coll.update(0.016, [c1, c2]) == [], "same-lane pair must be ignored"
    assert c1.state != "crashed" and c2.state != "crashed"
    return "graze ignored, hit detected once, same lane ignored"


def at_line(vtype: str, approach: str, behind: float = 0.5, delta=None) -> Vehicle:
    """Stopped vehicle whose front is `behind` px before its stop line."""
    v = Vehicle(vtype, approach)
    h = v.heading[1] if v.axis == "NS" else v.heading[0]
    c = stop_line(approach) - h * (behind + v.length / 2)
    if v.axis == "NS":
        v.y = c
    else:
        v.x = c
    v.state, v.speed, v.target_speed = "stopped", 0.0, 0.0
    v.wait_time = 0.0 if delta is None else v.patience + delta
    return v


def chaos_test() -> str:
    """Who may become a runner, type factors, and the flag reset."""
    assert reckless_factor("motorcycle") == reckless_factor("rickshaw") == 1.5
    assert reckless_factor("bus") == reckless_factor("truck") == 0.5
    assert reckless_factor("car") == reckless_factor("cng") == 1.0
    chaos = ChaosSystem(seed=1, rate_scale=1e6)  # ~100 % chance per frame
    ready = at_line("car", "E", delta=+1)          # head of queue, out of patience
    early = at_line("truck", "N", delta=-1)        # still patient
    second = at_line("bus", "S", behind=80, delta=+1)  # not at the line
    wreck = at_line("rickshaw", "W", delta=+1)
    wreck.crash()
    moving = Vehicle("car", "W")
    moving.wait_time = 99.0
    chaos.update(1 / 60, [ready, early, second, wreck, moving], 1)
    assert ready.ignores_signal and getattr(ready, "honk", False), "no runner"
    assert not any(v.ignores_signal for v in (early, second, wreck, moving)), \
        "a non-eligible vehicle became a runner"
    idle = ChaosSystem(seed=1, rate_scale=0.0)
    calm = at_line("car", "E", delta=+1)
    for _ in range(600):
        idle.update(1 / 60, [calm], 1)
    assert not calm.ignores_signal, "rate 0 must never create runners"
    square, chaos = intersection_rect(), ChaosSystem(seed=1, rate_scale=0.0)
    runner = at_line("motorcycle", "W", delta=+1)
    runner.ignores_signal, inside = True, False
    for _ in range(600):  # drive straight through the junction
        chaos.update(1 / 60, [runner], 1)
        runner.target_speed = runner.cruise_speed
        runner.update(1 / 60)
        if runner.rect.colliderect(square):
            inside = True
            assert runner.ignores_signal, "flag cleared while still inside"
    assert inside and not runner.ignores_signal, "flag must reset after exit"
    return "eligibility, type factors and flag reset OK"


def integration_test(seconds: float = 180.0, seed: int = 5) -> str:
    """Full headless simulation with a lazy signal operator and boosted chaos."""
    sig, tm = SignalController(), TrafficManager(seed)
    chaos, coll = ChaosSystem(seed, rate_scale=8.0), CollisionSystem()
    dt, t, next_switch, axis = 1 / 60, 0.0, 0.0, "EW"
    runners = crashes = passed = 0
    while t < seconds:
        level = 1 + int(t // 18) % MAX_LEVEL
        if t >= next_switch:  # long red waits -> impatient drivers
            sig.request(axis)
            axis, next_switch = ("NS" if axis == "EW" else "EW"), t + 14.0
        sig.update(dt)
        chaos.update(dt, tm.vehicles, level)
        for v in tm.vehicles:
            if getattr(v, "honk", False):
                v.honk = False
                runners += 1
        passed += len(tm.update(dt, sig, level))
        for a, b in coll.update(dt, tm.vehicles):
            assert a.axis != b.axis, "same-axis pair reported as a collision"
            crashes += 1
        for v in tm.vehicles:
            assert not (v.state == "crashed" and v.alive
                        and v.crash_timer > CRASH_CLEAR_TIME + 0.2), "wreck stayed"
        t += dt
    assert runners > 0, "no red-light runner appeared in 180 s"
    return f"{seconds:.0f}s: {runners} runners, {crashes} crashes, {passed} exited"


# ------------------------------------------------------------ interactive
def interactive() -> None:
    """Full simulation: signals, traffic, chaos, collisions."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Collision demo - 1/2 signals, X chaos, B boxes")
    road, sig, tm, coll = Road(), SignalController(), TrafficManager(), CollisionSystem()
    chaos = ChaosSystem(rate_scale=BOOSTS[0])
    font, clock = pygame.font.Font(None, 24), pygame.time.Clock()
    boost_i, level, boxes, running = 0, 1, False, True
    runners = crashes = passed = 0
    bursts: list[list[float]] = []  # [x, y, age] impact rings
    honks: list[list[float]] = []   # [x, y, age] "HONK!" labels
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
                elif k == pygame.K_x:
                    boost_i = (boost_i + 1) % len(BOOSTS)
                    chaos.rate_scale = BOOSTS[boost_i]
                elif k == pygame.K_UP:
                    level = min(MAX_LEVEL, level + 1)
                elif k == pygame.K_DOWN:
                    level = max(1, level - 1)
                elif k == pygame.K_b:
                    boxes = not boxes
                elif k == pygame.K_r:
                    sig.reset()
                    tm.reset()
                    runners = crashes = passed = 0
                    bursts.clear()
                    honks.clear()
        sig.update(dt)
        chaos.update(dt, tm.vehicles, level)
        for v in tm.vehicles:  # same pattern the Game uses
            if getattr(v, "honk", False):
                v.honk = False
                runners += 1
                honks.append([v.x, v.y - 24, 0.0])
        passed += len(tm.update(dt, sig, level))
        for a, b in coll.update(dt, tm.vehicles):
            crashes += 1
            p = get_crash_point(a, b)
            bursts.append([p[0], p[1], 0.0])
            print(f"CRASH: {a.vtype} from {a.approach} x {b.vtype} from {b.approach}")
        for fx in bursts + honks:
            fx[2] += dt
        bursts[:] = [f for f in bursts if f[2] < 0.7]
        honks[:] = [f for f in honks if f[2] < 1.0]

        road.draw(screen)
        sig.draw(screen)
        tm.draw(screen)
        for v in tm.vehicles:
            if v.ignores_signal:
                pygame.draw.circle(screen, (255, 120, 0), (int(v.x), int(v.y)),
                                   max(v.length, v.width) // 2 + 6, 2)
            if boxes:
                pygame.draw.rect(screen, (255, 0, 255), hit_box(v), 1)
        for x, y, age in bursts:
            pygame.draw.circle(screen, COLORS["red"], (int(x), int(y)),
                               int(10 + age * 70), 3)
        for x, y, age in honks:
            img = font.render("HONK!", True, COLORS["yellow"], COLORS["black"])
            screen.blit(img, img.get_rect(center=(int(x), int(y - age * 30))))
        lives = max(0, START_LIVES - crashes)
        running_now = sum(1 for v in tm.vehicles if v.ignores_signal)
        lines = [f"level {level}  chaos x{BOOSTS[boost_i]:g}  runners: {runners}"
                 f" (now {running_now})  crashes: {crashes}  lives (sim): {lives}"
                 f"  passed: {passed}",
                 f"signal: {sig.state}  pending: {sig.pending_request}  "
                 f"vehicles: {len(tm.vehicles)}",
                 "1/2 signal   X chaos boost   UP/DOWN level   B boxes   R reset"]
        for i, text in enumerate(lines):
            screen.blit(font.render(text, True, COLORS["white"], COLORS["black"]),
                        (8, HEIGHT - 82 + i * 26))
        pygame.display.flip()
    pygame.quit()


def main() -> None:
    print("--- Phase 6 tests ---")
    results = [
        run_test("scripted crossing (rickshaw N x motorcycle W)", scripted_scenario),
        run_test("near miss / shrink / same lane", near_miss_test),
        run_test("chaos rules", chaos_test),
        run_test("integration (180 s full sim)", integration_test),
    ]
    ok = all(results)
    print("ALL TESTS PASS" if ok else "SOME TESTS FAILED")
    if "--no-window" in sys.argv:
        sys.exit(0 if ok else 1)
    interactive()


if __name__ == "__main__":
    main()