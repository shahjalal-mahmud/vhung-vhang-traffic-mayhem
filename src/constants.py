"""All fixed constants for VhungVhang: Traffic Mayhem."""

from types import SimpleNamespace

# --- Window / timing (coordinate system: origin top-left, +y points DOWN) ---
WIDTH = 1000
HEIGHT = 700
FPS = 60
CX = 500  # intersection center x
CY = 350  # intersection center y
MAX_DT = 0.05  # dt clamp (seconds) so lag spikes never teleport vehicles

# --- Road geometry ---
ROAD_W = 140
LANE_W = 70  # intersection square is CX±70, CY±70
CROSSWALK_W = 20  # crosswalk thickness, directly outside the square
STOP_DIST = 100  # stop line distance from center along the axis

# --- Game states ---
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAME_OVER = "game_over"
STATE_HELP = "help"

# --- Gameplay tuning ---
START_LIVES = 3
MIN_GREEN = 2.0
YELLOW_TIME = 1.5
ALL_RED_TIME = 0.7
CRASH_CLEAR_TIME = 2.5
SAFE_GAP = 14
ACCEL = 220  # px/s^2
BRAKE = 420  # px/s^2
MAX_LEVEL = 10
LEVEL_SCORE_STEP = 150
BASE_SPAWN_INTERVAL = 2.2
MIN_SPAWN_INTERVAL = 0.7
SPEED_MULT_PER_LEVEL = 0.06

HIGHSCORE_FILE = "highscore.json"

# --- Cartoon palette (RGB) ---
COLORS = {
    "grass": (104, 197, 96),
    "road": (74, 77, 89),
    "road_edge": (44, 46, 56),
    "lane_marking": (245, 242, 225),
    "footpath": (199, 190, 166),
    "white": (255, 255, 255),
    "black": (22, 22, 28),
    "red": (232, 69, 69),
    "yellow": (255, 205, 60),
    "green": (66, 201, 108),
    "ui_bg": (30, 34, 52),
    "ui_text": (246, 246, 252),
    "accent": (255, 143, 56),
}

# --- Vehicle specs: sizes/speeds in px and px/s, patience in seconds ---
VEHICLE_SPECS = {
    "rickshaw": SimpleNamespace(
        length=44, width=26, max_speed=90, points=10,
        patience=6, weight=20, color=(236, 92, 140)
    ),
    "cng": SimpleNamespace(
        length=50, width=28, max_speed=120, points=10,
        patience=6, weight=20, color=(52, 168, 98)
    ),
    "motorcycle": SimpleNamespace(
        length=34, width=16, max_speed=170, points=10,
        patience=4, weight=20, color=(64, 122, 232)
    ),
    "car": SimpleNamespace(
        length=58, width=30, max_speed=140, points=10,
        patience=8, weight=20, color=(240, 196, 52)
    ),
    "bus": SimpleNamespace(
        length=100, width=36, max_speed=100, points=25,
        patience=12, weight=10, color=(250, 140, 40)
    ),
    "truck": SimpleNamespace(
        length=90, width=34, max_speed=95, points=20,
        patience=10, weight=10, color=(132, 98, 210)
    ),
}