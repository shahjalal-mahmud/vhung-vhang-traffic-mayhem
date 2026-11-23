"""Interface check: run `python tests/demo_skeleton.py` from the project root."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # no window needed
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from src import constants as C  # noqa: E402
from src import difficulty, road, utils  # noqa: E402
from src.audio import AudioManager  # noqa: E402
from src.chaos import ChaosSystem  # noqa: E402
from src.collision import CollisionSystem  # noqa: E402
from src.effects import EffectsSystem  # noqa: E402
from src.game import Game  # noqa: E402
from src.scoring import ScoreManager  # noqa: E402
from src.signals import SignalController  # noqa: E402
from src.traffic_manager import TrafficManager  # noqa: E402
from src.ui import UI  # noqa: E402
from src.vehicles import Vehicle  # noqa: E402


def need(obj, names, label, call=True):
    """Assert obj has every name (and that it is callable if call=True)."""
    for n in names:
        assert hasattr(obj, n), f"{label} is missing '{n}'"
        if call:
            assert callable(getattr(obj, n)), f"{label}.{n} is not callable"


def main() -> None:
    pygame.init()
    pygame.display.set_mode((C.WIDTH, C.HEIGHT))

    # constants
    names = ("WIDTH HEIGHT FPS CX CY ROAD_W LANE_W STATE_MENU STATE_PLAYING "
             "STATE_PAUSED STATE_GAME_OVER STATE_HELP START_LIVES MIN_GREEN "
             "YELLOW_TIME ALL_RED_TIME CRASH_CLEAR_TIME SAFE_GAP ACCEL BRAKE "
             "MAX_LEVEL LEVEL_SCORE_STEP BASE_SPAWN_INTERVAL "
             "MIN_SPAWN_INTERVAL SPEED_MULT_PER_LEVEL HIGHSCORE_FILE "
             "COLORS VEHICLE_SPECS").split()
    need(C, names, "constants", call=False)
    keys = ("grass road road_edge lane_marking footpath white black red "
            "yellow green ui_bg ui_text accent").split()
    assert all(k in C.COLORS for k in keys), "COLORS key missing"
    assert set(C.VEHICLE_SPECS) == {"rickshaw", "cng", "motorcycle", "car",
                                    "bus", "truck"}
    for spec in C.VEHICLE_SPECS.values():
        need(spec, "length width max_speed points patience weight color".split(),
             "spec", call=False)

    # utils
    need(utils, "clamp lerp load_json save_json draw_text draw_text_shadow".split(),
         "utils")
    assert utils.clamp(5, 0, 3) == 3 and utils.lerp(0, 10, 0.5) == 5
    assert utils.load_json("does_not_exist.json", {"a": 1}) == {"a": 1}

    # road geometry
    need(road, "spawn_pos stop_line heading axis_of lane_center "
               "intersection_rect".split(), "road")
    assert road.spawn_pos("N") == (C.CX + 35, -60)
    assert road.stop_line("S") == C.CY + 100
    assert road.heading("E") == (-1, 0) and road.axis_of("W") == "EW"
    assert road.intersection_rect().size == (140, 140)
    need(road.Road(), ["draw"], "Road")

    # signals
    s = SignalController()
    need(s, "request update light_for draw reset".split(), "SignalController")
    need(s, ["state", "time_in_state"], "SignalController", call=False)
    assert s.state == "NS_GREEN" and s.light_for("N") == "green"
    assert s.light_for("E") == "red"

    # vehicles
    v = Vehicle("car", "N")
    need(v, "front_pos distance_to_stop_line update draw crash".split(), "Vehicle")
    need(v, "vtype approach axis heading x y length width speed max_speed "
            "target_speed state wait_time patience ignores_signal scored "
            "alive crash_timer rect".split(), "Vehicle", call=False)
    assert isinstance(v.rect, pygame.Rect)
    assert v.distance_to_stop_line() > 0

    # other systems
    need(TrafficManager(), "update draw reset".split(), "TrafficManager")
    need(TrafficManager(), ["vehicles"], "TrafficManager", call=False)
    need(ChaosSystem(), ["update"], "ChaosSystem")
    need(CollisionSystem(), ["update"], "CollisionSystem")
    sm = ScoreManager()
    need(sm, "add_vehicle lose_life save_high_score reset".split(), "ScoreManager")
    need(sm, "score lives high_score level is_game_over new_high_score".split(),
         "ScoreManager", call=False)
    need(difficulty, "spawn_interval speed_multiplier chaos_chance".split(),
         "difficulty")
    need(UI(), "draw_menu draw_help draw_hud draw_pause draw_game_over "
               "handle_event".split(), "UI")
    need(AudioManager(), "play set_muted toggle_mute".split(), "AudioManager")
    fx = EffectsSystem()
    need(fx, "spawn_smoke spawn_sparks floating_text shake update draw".split(),
         "EffectsSystem")
    assert fx.shake_offset == (0, 0)

    # Game smoke test: state machine without opening a real window
    g = Game()
    need(g, "run".split(), "Game")
    need(g, "screen clock state road signals traffic chaos collisions score "
            "ui audio effects".split(), "Game", call=False)
    assert g.state == C.STATE_MENU
    g._on_key(pygame.K_RETURN)
    assert g.state == C.STATE_PLAYING
    g._on_key(pygame.K_p)
    assert g.state == C.STATE_PAUSED
    g._on_key(pygame.K_p)
    assert g.state == C.STATE_PLAYING
    g.update(0.016)
    g.draw()
    for _ in range(C.START_LIVES):
        g.score.lose_life()
    g.update(0.016)
    assert g.state == C.STATE_GAME_OVER
    g.draw()

    print("All interfaces OK")


if __name__ == "__main__":
    main()