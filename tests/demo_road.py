"""Road demo: run `python tests/demo_road.py` from the project root.

D = toggle debug overlay, ESC = quit. Prints all helper outputs on start.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from src.constants import (COLORS, CX, CY, FPS, HEIGHT, ROAD_W, STOP_DIST,  # noqa: E402
                           WIDTH)
from src.road import (APPROACHES, Road, axis_of, heading,  # noqa: E402
                      intersection_rect, lane_center, spawn_pos, stop_line)


def print_geometry() -> None:
    """Print every helper's output for the 4 approaches."""
    print(f"{'app':<5}{'axis':<6}{'heading':<9}{'lane_center':<13}"
          f"{'spawn_pos':<14}stop_line")
    for a in APPROACHES:
        print(f"{a:<5}{axis_of(a):<6}{str(heading(a)):<9}{lane_center(a):<13}"
              f"{str(spawn_pos(a)):<14}{stop_line(a)}")
    print("intersection_rect:", intersection_rect())


def self_check() -> None:
    """Assert the geometry matches the Master Context."""
    for a in APPROACHES:
        centre = CY if axis_of(a) == "NS" else CX
        assert abs(stop_line(a) - centre) == STOP_DIST, f"stop line {a}"
    r = intersection_rect()
    assert r.center == (CX, CY) and r.size == (ROAD_W, ROAD_W)
    assert lane_center("N") - CX == CX - lane_center("S") == 35
    assert lane_center("E") - CY == CY - lane_center("W") == 35
    assert spawn_pos("N") == (CX + 35, -60) and spawn_pos("S") == (CX - 35, HEIGHT + 60)
    assert spawn_pos("W") == (-60, CY - 35) and spawn_pos("E") == (WIDTH + 60, CY + 35)
    print("Geometry self-check OK")


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Road demo - D: debug, ESC: quit")
    print_geometry()
    self_check()
    t0 = time.perf_counter()
    road = Road()
    print(f"Road cache built in {(time.perf_counter() - t0) * 1000:.0f} ms")
    font = pygame.font.Font(None, 26)
    clock, debug, running = pygame.time.Clock(), False, True
    while running:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_d:
                debug = not debug
        road.draw(screen)
        if debug:
            road.draw_debug(screen)
        label = font.render(f"D = debug ({'ON' if debug else 'OFF'})   ESC = quit",
                            True, COLORS["white"], COLORS["black"])
        screen.blit(label, (10, HEIGHT - 28))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()