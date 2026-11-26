"""Balance simulation (headless): python tests/demo_balance.py [options]

  --minutes 5        simulated minutes per run (60 FPS steps)
  --interval 10      bot: seconds between signal switches (alternate)
                     or minimum green time (smart)
  --bot alternate    'alternate' = switch every N s, 'smart' = serve the
                     axis with more stopped vehicles
  --seed 1 --runs 1  first seed / number of runs (averages if runs > 1)
A scoring + difficulty self-test runs first. Never writes highscore.json.
"""
import argparse
import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402,F401  (vehicles import it; dummy driver = no window)

from src import difficulty  # noqa: E402
from src.chaos import ChaosSystem  # noqa: E402
from src.collision import CollisionSystem  # noqa: E402
from src.constants import (BASE_SPAWN_INTERVAL, FPS, LEVEL_SCORE_STEP,  # noqa: E402
                           MAX_LEVEL, MIN_SPAWN_INTERVAL, START_LIVES)
from src.scoring import COMBO_BONUS, ScoreManager  # noqa: E402
from src.signals import SignalController  # noqa: E402
from src.traffic_manager import TrafficManager  # noqa: E402

DT = 1.0 / FPS


class Bot:
    """Stand-in player that operates the signals."""

    def __init__(self, mode: str, interval: float) -> None:
        self.mode, self.interval = mode, interval
        self.next_t, self.last_switch = (interval if mode == "alternate" else 1.0), 0.0

    def step(self, t: float, sig: SignalController, tm: TrafficManager) -> None:
        if t < self.next_t:
            return
        cur = sig.destination
        other = "EW" if cur == "NS" else "NS"
        if self.mode == "alternate":
            sig.request(other)
            self.next_t = t + self.interval
            return
        self.next_t = t + 1.0  # smart: look once per second
        waiting = {"NS": 0, "EW": 0}
        for v in tm.vehicles:
            if v.state == "stopped":
                waiting[v.axis] += 1
        if waiting[other] > waiting[cur] and t - self.last_switch >= self.interval:
            sig.request(other)
            self.last_switch = t


def simulate(minutes: float, interval: float, mode: str, seed: int) -> dict:
    """Run the full game logic without a window; return the statistics."""
    difficulty.seed(seed)
    sig, tm = SignalController(), TrafficManager(seed)
    chaos, coll, score = ChaosSystem(seed), CollisionSystem(), ScoreManager()
    score.reset()
    bot = Bot(mode, interval)
    r = dict(passed=0, crashes=0, runners=0, over_at=None, level_at_over=None,
             levels={}, queue_sum=0.0, queue_peak=0)
    steps = int(minutes * 60 * FPS)
    for step in range(steps):
        t = step * DT
        bot.step(t, sig, tm)
        level = score.level
        sig.update(DT)
        chaos.update(DT, tm.vehicles, level)
        for v in tm.vehicles:  # same order as Game.update
            if v.honk:
                v.honk = False
                r["runners"] += 1
        for v in tm.update(DT, sig, level):
            score.add_vehicle(v)
            r["passed"] += 1
        for _a, _b in coll.update(DT, tm.vehicles):
            score.lose_life()
            r["crashes"] += 1
            if score.is_game_over and r["over_at"] is None:
                r["over_at"], r["level_at_over"] = t, score.level
        r["levels"].setdefault(score.level, t)
        q = sum(1 for v in tm.vehicles if v.state == "stopped")
        r["queue_sum"] += q
        r["queue_peak"] = max(r["queue_peak"], q)
    r.update(score=score.score, level=score.level, combo=score.combo,
             avg_queue=r["queue_sum"] / steps, minutes=minutes)
    return r


def report(r: dict, label: str) -> None:
    """Print one run."""
    over = (f"{r['over_at']:.0f}s (level {r['level_at_over']})"
            if r["over_at"] is not None else f"survived {r['minutes']:g} min")
    timeline = " ".join(f"L{lv}@{t:.0f}s" for lv, t in sorted(r["levels"].items()))
    print(f"--- {label}")
    print(f"  vehicles passed : {r['passed']}")
    print(f"  crashes         : {r['crashes']}   (red-light runners: {r['runners']})")
    print(f"  final level     : {r['level']}  (score {r['score']})")
    print(f"  game over at    : {over}   [{START_LIVES} lives]")
    print(f"  avg queue       : {r['avg_queue']:.1f} stopped vehicles (peak {r['queue_peak']})")
    print(f"  level timeline  : {timeline}")


def selftest() -> None:
    """Scoring, combo, level, persistence and difficulty curves."""
    class V:  # minimal vehicle: add_vehicle only reads vtype
        vtype = "car"
    path = os.path.join(tempfile.mkdtemp(), "hs.json")
    s = ScoreManager(path)
    assert s.high_score == 0 and s.lives == START_LIVES and s.level == 1
    for _ in range(5):
        s.add_vehicle(V())
    assert s.score == 5 * 10 + COMBO_BONUS and s.combo == 5, "combo bonus"
    s.lose_life()
    assert s.combo == 0 and s.lives == START_LIVES - 1, "crash resets combo"
    s.score = LEVEL_SCORE_STEP * 3
    assert s.level == 4
    s.score = 10 ** 6
    assert s.level == MAX_LEVEL, "level capped"
    s.score = 120
    s.save_high_score()
    assert s.new_high_score and ScoreManager(path).high_score == 120, "persist"
    s2 = ScoreManager(path)
    s2.score = 50
    s2.save_high_score()
    assert not s2.new_high_score and ScoreManager(path).high_score == 120
    s.reset()
    assert s.score == 0 and s.high_score == 120 and not s.new_high_score
    close = lambda a, b: abs(a - b) < 1e-9  # noqa: E731
    assert close(difficulty.spawn_base(1), BASE_SPAWN_INTERVAL)
    assert close(difficulty.spawn_base(MAX_LEVEL), MIN_SPAWN_INTERVAL)
    assert all(difficulty.spawn_base(l) >= difficulty.spawn_base(l + 1)
               for l in range(1, MAX_LEVEL))
    for _ in range(300):
        v = difficulty.spawn_interval(5)
        base = difficulty.spawn_base(5)
        assert 0.85 * base - 1e-9 <= v <= 1.15 * base + 1e-9, "jitter range"
    assert close(difficulty.speed_multiplier(1), 1.0)
    assert close(difficulty.chaos_chance(1), 0.03)
    assert close(difficulty.chaos_chance(MAX_LEVEL), 0.18)
    print("Self-test OK (scoring, combo, level, high score, difficulty curves)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=5.0)
    ap.add_argument("--interval", type=float, default=10.0)
    ap.add_argument("--bot", choices=("alternate", "smart"), default="alternate")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--runs", type=int, default=1)
    a = ap.parse_args()
    selftest()
    runs = []
    for i in range(a.runs):
        r = simulate(a.minutes, a.interval, a.bot, a.seed + i)
        report(r, f"run {i + 1}: bot={a.bot} interval={a.interval:g}s seed={a.seed + i}")
        runs.append(r)
    if len(runs) > 1:
        n = len(runs)
        avg = lambda k: sum(r[k] for r in runs) / n  # noqa: E731
        print(f"=== average of {n}: passed {avg('passed'):.0f}, crashes "
              f"{avg('crashes'):.1f}, level {avg('level'):.1f}, avg queue "
              f"{avg('avg_queue'):.1f}")


if __name__ == "__main__":
    main()