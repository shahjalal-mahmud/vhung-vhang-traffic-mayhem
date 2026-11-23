"""Vehicle demo: python tests/demo_vehicles.py

1-6 spawn rickshaw/cng/motorcycle/car/bus/truck, A = cycle approach (N,S,E,W),
S = cycle speed multiplier, C = crash newest, B = bounding boxes, D = road debug,
SPACE = brake/go all, L = stop-at-stop-line mode, R = clear, ESC = quit.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from src.constants import (BRAKE, COLORS, CRASH_CLEAR_TIME, FPS, HEIGHT,  # noqa: E402
                           MAX_DT, WIDTH)
from src.road import APPROACHES, Road, lane_center, stop_line  # noqa: E402
from src.vehicle_art import VEHICLE_TYPES, get_sprite  # noqa: E402
from src.vehicles import Vehicle  # noqa: E402

SPEEDS = (0.5, 1.0, 1.5, 2.0)


def self_check() -> None:
    """Lane centers, rect sizes, front/stop-line maths and sprite sizes."""
    for a in APPROACHES:
        for t in VEHICLE_TYPES:
            v = Vehicle(t, a)
            L, W = v.length, v.width
            lane = lane_center(a)
            assert (v.x if v.axis == "NS" else v.y) == lane, f"{t}/{a} off lane"
            assert v.rect.size == ((W, L) if v.axis == "NS" else (L, W))
            assert get_sprite(t, v.heading, 0, False).get_size() == v.rect.size
            assert v.distance_to_stop_line() > 0
            dx, dy = v.heading
            line = stop_line(a)
            if v.axis == "NS":
                v.y = line - dy * L / 2   # put the FRONT exactly on the line
            else:
                v.x = line - dx * L / 2
            assert abs(v.distance_to_stop_line()) < 1e-6, f"{t}/{a} front"
            v.x, v.y = v.x + dx * 5, v.y + dy * 5
            assert abs(v.distance_to_stop_line() + 5) < 1e-6, f"{t}/{a} crossed"
    print("Vehicle self-check OK (24 combinations: lane, rect, front, stop line)")


def control(v: Vehicle, hold: bool, stop_mode: bool) -> None:
    """Demo 'driver': hold = stop everywhere, stop_mode = stop at the line."""
    if v.state == "crashed":
        return
    want = v.cruise_speed
    if hold:
        want = 0.0
    elif stop_mode:
        d = v.distance_to_stop_line()
        if 0.0 <= d <= v.speed ** 2 / (2 * BRAKE) + 4.0:
            want = 0.0
    v.target_speed = want


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Vehicle demo")
    self_check()
    road, font = Road(), pygame.font.Font(None, 24)
    clock = pygame.time.Clock()
    vehicles: list[Vehicle] = []
    ap_i = sp_i = 0
    boxes = dbg = hold = stop_mode = False
    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, MAX_DT)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                k = e.key
                if k == pygame.K_ESCAPE:
                    running = False
                elif pygame.K_1 <= k <= pygame.K_6:
                    vehicles.append(Vehicle(VEHICLE_TYPES[k - pygame.K_1],
                                            APPROACHES[ap_i], SPEEDS[sp_i]))
                elif k == pygame.K_a:
                    ap_i = (ap_i + 1) % len(APPROACHES)
                elif k == pygame.K_s:
                    sp_i = (sp_i + 1) % len(SPEEDS)
                elif k == pygame.K_c:
                    for v in reversed(vehicles):
                        if v.state != "crashed":
                            v.crash()
                            break
                elif k == pygame.K_b:
                    boxes = not boxes
                elif k == pygame.K_d:
                    dbg = not dbg
                elif k == pygame.K_SPACE:
                    hold = not hold
                elif k == pygame.K_l:
                    stop_mode = not stop_mode
                elif k == pygame.K_r:
                    vehicles.clear()
        for v in vehicles:
            control(v, hold, stop_mode)
            v.update(dt)
            if v.state == "crashed" and v.crash_timer > CRASH_CLEAR_TIME:
                v.alive = False
        vehicles = [v for v in vehicles if v.alive]

        road.draw(screen)
        for v in vehicles:
            v.draw(screen)
        if dbg:
            road.draw_debug(screen)
        if boxes:
            for v in vehicles:
                pygame.draw.rect(screen, (255, 0, 255), v.rect, 1)
                fx, fy = v.front_pos()
                pygame.draw.circle(screen, (0, 255, 255), (int(fx), int(fy)), 3)
                pygame.draw.circle(screen, (255, 255, 0), (int(v.x), int(v.y)), 2)
        lines = [f"spawn from: {APPROACHES[ap_i]}   speed x{SPEEDS[sp_i]}   "
                 f"vehicles: {len(vehicles)}   boxes:{boxes} debug:{dbg} "
                 f"hold:{hold} stop-line:{stop_mode}",
                 "1-6 spawn  A approach  S speed  C crash  B boxes  D debug  "
                 "SPACE hold  L stop line  R clear"]
        if vehicles:
            v = vehicles[-1]
            lines.append(f"newest: {v.vtype} from {v.approach}  {v.state}  "
                         f"speed {v.speed:.0f}/{v.target_speed:.0f}  "
                         f"dist to stop line {v.distance_to_stop_line():.1f}  "
                         f"wait {v.wait_time:.1f}s")
        for i, text in enumerate(lines):
            screen.blit(font.render(text, True, COLORS["white"], COLORS["black"]),
                        (8, HEIGHT - 84 + i * 26))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()