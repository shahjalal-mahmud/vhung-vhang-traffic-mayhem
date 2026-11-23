"""Road and intersection rendering (Phase 2).

CG concepts: pre-rendered buffer (static scene cached in an off-screen Surface,
blitted every frame), coordinate system (origin top-left, +y down), painter's
algorithm (back-to-front draw order), mirroring with sign flips (sx, sy).
"""
from __future__ import annotations

import random

import pygame

from .constants import (COLORS, CROSSWALK_W, CX, CY, HEIGHT, LANE_W, ROAD_W,
                        SPAWN_MARGIN, STOP_DIST, WIDTH)
from .utils import clamp

APPROACHES = ("N", "S", "E", "W")
_HALF = ROAD_W // 2        # half road width (70)
_LANE_HALF = LANE_W // 2   # lane center offset from the road axis (35)
_HEADINGS = {"N": (0, 1), "S": (0, -1), "W": (1, 0), "E": (-1, 0)}

# ---- drawing-only constants (decoration, not gameplay geometry) ----
_SEED = 2026
_STOP_LINE_W = 6           # stop line paint thickness (outer edge = STOP_DIST)
_FOOT, _CORNER_R = 14, 22  # footpath width, rounded curb radius
_BLOCK_U, _BLOCK_V = CX - _HALF, CY - _HALF  # corner block size (430 x 280)
_DASH, _GAP, _DASH_T = 24, 18, 4
_ZEBRA_BAR, _ZEBRA_PITCH = 10, 20
_ARROW_DISTS = (170, 290)  # arrow distance from center along each lane
_BANNER = 16
_TREE = (46, 140, 72)
_PALETTE = [(255, 183, 120), (255, 140, 140), (150, 205, 255),
            (255, 225, 120), (190, 160, 235), (140, 220, 190)]
_BANNERS = [COLORS["red"], (52, 120, 210), (40, 150, 90), (140, 80, 190)]
_NAMES = ("PHARMACY", "BAZAR", "SWEETS", "MOBILE", "TAILORS", "CAFE",
          "BOOKS", "SALON")
_BOARDS = ("VHUNG!", "CHA 5TK", "SALE 50%", "MOBILE")
_ORDER = {"shop": 0, "side": 0, "tea": 1, "board": 1, "tree": 2, "lamp": 3}

# Block-local layout: (kind, u, v, w, h) / (tree, u, v, r) / (lamp, u, v).
# u = distance from the vertical road edge, v = from the horizontal road edge.
# Nothing is placed with u < 90 AND v < 90: that corner is kept clear for lights.
_LAYOUT_A = [
    ("shop", 100, 24, 92, 62), ("shop", 198, 24, 84, 62),
    ("shop", 288, 24, 120, 62), ("side", 24, 100, 62, 80),
    ("side", 24, 186, 62, 84), ("tea", 118, 150, 56, 38),
    ("board", 250, 200, 96, 44), ("tree", 210, 120, 18),
    ("tree", 330, 150, 24), ("tree", 392, 220, 22), ("tree", 150, 232, 20),
    ("lamp", 9, 130), ("lamp", 9, 230), ("lamp", 150, 9), ("lamp", 270, 9),
    ("lamp", 390, 9)]
_LAYOUT_B = [
    ("shop", 100, 24, 150, 62), ("shop", 258, 24, 150, 62),
    ("side", 24, 100, 62, 170), ("shop", 112, 108, 100, 84),
    ("tree", 262, 140, 22), ("tree", 350, 135, 20), ("tea", 120, 215, 56, 38),
    ("board", 250, 214, 100, 46), ("tree", 395, 230, 20),
    ("lamp", 9, 130), ("lamp", 9, 230), ("lamp", 150, 9), ("lamp", 270, 9),
    ("lamp", 390, 9)]

_MAGENTA, _CYAN, _RED, _ORANGE = (255, 0, 255), (0, 255, 255), (255, 0, 0), (255, 140, 0)


# ------------------------------------------------------------------ geometry
def axis_of(approach: str) -> str:
    """'N'/'S' -> 'NS', 'E'/'W' -> 'EW'."""
    return "NS" if approach in ("N", "S") else "EW"


def heading(approach: str) -> tuple[int, int]:
    """Unit direction (dx, dy) a vehicle travels when coming FROM approach."""
    return _HEADINGS[approach]


def lane_center(approach: str) -> int:
    """Lane center line (left-hand traffic): x for N/S, y for W/E."""
    return {"N": CX + _LANE_HALF, "S": CX - _LANE_HALF,
            "W": CY - _LANE_HALF, "E": CY + _LANE_HALF}[approach]


def spawn_pos(approach: str) -> tuple[int, int]:
    """Spawn point SPAWN_MARGIN px outside the screen, on the lane center."""
    c = lane_center(approach)
    return {"N": (c, -SPAWN_MARGIN), "S": (c, HEIGHT + SPAWN_MARGIN),
            "W": (-SPAWN_MARGIN, c), "E": (WIDTH + SPAWN_MARGIN, c)}[approach]


def stop_line(approach: str) -> int:
    """Coordinate where a vehicle's FRONT must stop (y for N/S, x for W/E)."""
    return {"N": CY - STOP_DIST, "S": CY + STOP_DIST,
            "W": CX - STOP_DIST, "E": CX + STOP_DIST}[approach]


def intersection_rect() -> pygame.Rect:
    """The central square, CX±70 by CY±70."""
    return pygame.Rect(CX - _HALF, CY - _HALF, ROAD_W, ROAD_W)


def _crosswalk_rect(a: str) -> pygame.Rect:
    """Crosswalk strip, CROSSWALK_W thick, directly outside the square."""
    return {"N": pygame.Rect(CX - _HALF, CY - _HALF - CROSSWALK_W, ROAD_W, CROSSWALK_W),
            "S": pygame.Rect(CX - _HALF, CY + _HALF, ROAD_W, CROSSWALK_W),
            "W": pygame.Rect(CX - _HALF - CROSSWALK_W, CY - _HALF, CROSSWALK_W, ROAD_W),
            "E": pygame.Rect(CX + _HALF, CY - _HALF, CROSSWALK_W, ROAD_W)}[a]


def _stop_rect(a: str) -> pygame.Rect:
    """Stop-line paint over the approach lane. Its OUTER edge is stop_line(a),
    so a stopped vehicle's front touches it and the paint stays visible."""
    s, c, t = stop_line(a), lane_center(a), _STOP_LINE_W
    if a == "N":
        return pygame.Rect(c - _LANE_HALF, s, LANE_W, t)
    if a == "S":
        return pygame.Rect(c - _LANE_HALF, s - t, LANE_W, t)
    if a == "W":
        return pygame.Rect(s, c - _LANE_HALF, t, LANE_W)
    return pygame.Rect(s - t, c - _LANE_HALF, t, LANE_W)


# ------------------------------------------------------------ local helpers
def _shade(color: tuple, k: float) -> tuple:
    """Multiply an RGB color by k (darker if k < 1)."""
    return tuple(max(0, min(255, int(ch * k))) for ch in color)


def _rect(sx: int, sy: int, u: int, v: int, w: int, h: int) -> pygame.Rect:
    """Block-local rect -> screen rect. sx/sy = -1/+1 mirror (reflection)."""
    x = CX + _HALF + u if sx > 0 else CX - _HALF - u - w
    y = CY + _HALF + v if sy > 0 else CY - _HALF - v - h
    return pygame.Rect(x, y, w, h)


def _pt(sx: int, sy: int, u: float, v: float) -> tuple[int, int]:
    """Block-local point -> screen point."""
    return (int(CX + sx * (_HALF + u)), int(CY + sy * (_HALF + v)))


# ------------------------------------------------------------- corner blocks
def _draw_footpath(surf: pygame.Surface, sx: int, sy: int) -> None:
    """Footpath block with a rounded curb corner at the intersection."""
    ext = 12  # extend past the screen so the curb outline only shows by the road
    key = f"border_{'top' if sy > 0 else 'bottom'}_{'left' if sx > 0 else 'right'}_radius"
    r = _rect(sx, sy, 0, 0, _BLOCK_U + ext, _BLOCK_V + ext)
    pygame.draw.rect(surf, COLORS["footpath"], r, **{key: _CORNER_R})
    pygame.draw.rect(surf, COLORS["road_edge"], r, 3, **{key: _CORNER_R})
    inner = _rect(sx, sy, _FOOT, _FOOT, _BLOCK_U + ext - _FOOT, _BLOCK_V + ext - _FOOT)
    pygame.draw.rect(surf, COLORS["grass"], inner, **{key: _CORNER_R // 2})


def _draw_tufts(surf: pygame.Surface, sx: int, sy: int, rng: random.Random) -> None:
    """Seeded random grass texture (same every run)."""
    dark, light = _shade(COLORS["grass"], 0.78), _shade(COLORS["grass"], 1.12)
    lo = _FOOT + 16
    for _ in range(16):  # light patches
        e = pygame.Rect(0, 0, rng.randint(14, 28), rng.randint(6, 12))
        e.center = _pt(sx, sy, rng.randint(lo, _BLOCK_U - 20), rng.randint(lo, _BLOCK_V - 20))
        pygame.draw.ellipse(surf, light, e)
    for _ in range(50):  # three-blade tufts
        x, y = _pt(sx, sy, rng.randint(lo, _BLOCK_U - 20), rng.randint(lo, _BLOCK_V - 20))
        for bx, by in ((-3, -5), (0, -7), (3, -5)):
            pygame.draw.line(surf, dark, (x, y), (x + bx, y + by), 2)


def _building(surf, r, color, face, name, small, rng) -> None:
    """Flat cartoon shop: wall, roof panel, window grid, sign on the road side."""
    pygame.draw.rect(surf, _shade(COLORS["grass"], 0.6), r.move(4, 5), border_radius=5)
    pygame.draw.rect(surf, color, r, border_radius=5)
    pygame.draw.rect(surf, _shade(color, 1.12), r.inflate(-10, -10), border_radius=4)
    t, area = _BANNER, r.inflate(-20, -20)
    if face == "bottom":
        b = pygame.Rect(r.left + 6, r.bottom - t - 3, r.width - 12, t)
        area.height -= t + 4
    elif face == "top":
        b = pygame.Rect(r.left + 6, r.top + 3, r.width - 12, t)
        area.top += t + 4
        area.height -= t + 4
    elif face == "right":
        b = pygame.Rect(r.right - t - 3, r.top + 6, t, r.height - 12)
        area.width -= t + 4
    else:
        b = pygame.Rect(r.left + 3, r.top + 6, t, r.height - 12)
        area.left += t + 4
        area.width -= t + 4
    cols, rows = max(1, area.width // 24), max(1, area.height // 22)
    for i in range(cols):
        for j in range(rows):
            w = pygame.Rect(0, 0, 14, 11)
            w.center = (area.left + int((i + 0.5) * area.width / cols),
                        area.top + int((j + 0.5) * area.height / rows))
            pygame.draw.rect(surf, (170, 220, 245), w, border_radius=2)
            pygame.draw.rect(surf, COLORS["black"], w, 1, border_radius=2)
            pygame.draw.rect(surf, COLORS["white"], (w.left + 2, w.top + 2, 4, 3))
    if face in ("top", "bottom"):  # text banner
        pygame.draw.rect(surf, rng.choice(_BANNERS), b, border_radius=3)
        txt = small.render(name, True, COLORS["white"])
        surf.blit(txt, txt.get_rect(center=b.center))
    else:  # striped awning
        for k in range(0, b.height, 8):
            c = COLORS["red"] if (k // 8) % 2 == 0 else COLORS["white"]
            pygame.draw.rect(surf, c, (b.left, b.top + k, b.width, min(8, b.height - k)))
    pygame.draw.rect(surf, COLORS["black"], b, 2, border_radius=3)
    pygame.draw.rect(surf, COLORS["black"], r, 3, border_radius=5)


def _tea_stall(surf, r, small) -> None:
    """Small tea stall: striped canopy, 'CHA' sign and two stools."""
    pygame.draw.rect(surf, _shade(COLORS["grass"], 0.6), r.move(3, 4), border_radius=4)
    for k in range(0, r.width, 8):
        c = COLORS["red"] if (k // 8) % 2 == 0 else COLORS["white"]
        pygame.draw.rect(surf, c, (r.left + k, r.top, min(8, r.width - k), r.height))
    pygame.draw.rect(surf, COLORS["black"], r, 3, border_radius=4)
    tag = pygame.Rect(0, 0, 34, 16)
    tag.center = r.center
    pygame.draw.rect(surf, COLORS["white"], tag, border_radius=4)
    surf.blit(small.render("CHA", True, COLORS["black"]),
              small.render("CHA", True, COLORS["black"]).get_rect(center=tag.center))
    for dx in (-10, r.width + 10):
        pygame.draw.circle(surf, (150, 100, 60), (r.left + dx, r.centery), 6)
        pygame.draw.circle(surf, COLORS["black"], (r.left + dx, r.centery), 6, 2)


def _billboard(surf, r, text, color, big) -> None:
    """Billboard: two posts, a colored face and a text slogan."""
    for x in (r.left + 14, r.right - 18):
        pygame.draw.rect(surf, COLORS["black"], (x, r.bottom - 2, 4, 12))
    pygame.draw.rect(surf, color, r, border_radius=4)
    pygame.draw.rect(surf, COLORS["black"], r, 3, border_radius=4)
    txt = big.render(text, True, COLORS["black"])
    surf.blit(txt, txt.get_rect(center=r.center))


def _tree(surf, p, r) -> None:
    """Round cartoon tree seen from above: shadow, canopy, highlights."""
    x, y = p
    pygame.draw.circle(surf, _shade(COLORS["grass"], 0.55), (x + 4, y + 5), r)
    pygame.draw.circle(surf, _TREE, p, r)
    pygame.draw.circle(surf, COLORS["black"], p, r, 2)
    pygame.draw.circle(surf, _shade(_TREE, 1.45), (x - r // 3, y - r // 3), r // 2)
    pygame.draw.circle(surf, _shade(_TREE, 1.9), (x - r // 2, y - r // 2), r // 5 + 1)


def _lamp(surf, p) -> None:
    """Lamp post on the footpath (top view: glowing head)."""
    pygame.draw.circle(surf, (255, 238, 160), p, 6)
    pygame.draw.circle(surf, COLORS["black"], p, 6, 1)
    pygame.draw.circle(surf, COLORS["black"], p, 2)


def _decorate(surf, sx, sy, layout, rng, small, big) -> None:
    """Draw a block's decorations back-to-front (painter's algorithm)."""
    for kind, *a in sorted(layout, key=lambda e: _ORDER[e[0]]):
        if kind in ("shop", "side"):
            if kind == "shop":
                face = "bottom" if sy < 0 else "top"   # side facing the horizontal road
            else:
                face = "right" if sx < 0 else "left"   # side facing the vertical road
            _building(surf, _rect(sx, sy, *a), rng.choice(_PALETTE), face,
                      rng.choice(_NAMES), small, rng)
        elif kind == "tea":
            _tea_stall(surf, _rect(sx, sy, *a), small)
        elif kind == "board":
            _billboard(surf, _rect(sx, sy, *a), rng.choice(_BOARDS),
                       rng.choice(_PALETTE), big)
        elif kind == "tree":
            _tree(surf, _pt(sx, sy, a[0], a[1]), a[2])
        else:
            _lamp(surf, _pt(sx, sy, a[0], a[1]))


# ----------------------------------------------------------------- markings
def _dashes(surf, color, origin, direction) -> None:
    """Dashed line from origin outward (symmetric on both sides of the center)."""
    ox, oy = origin
    dx, dy = direction
    for k in range(40):
        off = k * (_DASH + _GAP) + _DASH / 2
        r = pygame.Rect(0, 0, *((_DASH_T, _DASH) if dy else (_DASH, _DASH_T)))
        r.center = (round(ox + dx * off), round(oy + dy * off))
        pygame.draw.rect(surf, color, r)


def _zebra(surf, a: str, color) -> None:
    """Zebra crossing bars (parallel to the traffic direction)."""
    r, off = _crosswalk_rect(a), (_ZEBRA_PITCH - _ZEBRA_BAR) // 2
    if axis_of(a) == "NS":
        for x in range(r.left + off, r.right - _ZEBRA_BAR + 1, _ZEBRA_PITCH):
            pygame.draw.rect(surf, color, (x, r.top, _ZEBRA_BAR, r.height))
    else:
        for y in range(r.top + off, r.bottom - _ZEBRA_BAR + 1, _ZEBRA_PITCH):
            pygame.draw.rect(surf, color, (r.left, y, r.width, _ZEBRA_BAR))


def _arrow(surf, center, head, color, length=36, shaft=6, wing=10, tip=12) -> None:
    """Lane arrow. Local axes: a along heading, b = heading rotated 90 degrees
    (perpendicular). pt() converts local (a, b) -> world: a rotation transform."""
    hx, hy = head
    px, py = -hy, hx

    def pt(a: float, b: float) -> tuple[float, float]:
        return (center[0] + hx * a + px * b, center[1] + hy * a + py * b)

    L = length / 2
    pygame.draw.polygon(surf, color, [
        pt(-L, -shaft / 2), pt(L - tip, -shaft / 2), pt(L - tip, -wing), pt(L, 0),
        pt(L - tip, wing), pt(L - tip, shaft / 2), pt(-L, shaft / 2)])


def _draw_markings(surf: pygame.Surface) -> None:
    """Center dashes, zebra crossings, stop lines and direction arrows."""
    white = COLORS["lane_marking"]
    for s in (-1, 1):  # yellow dashes start at the stop-line distance
        _dashes(surf, COLORS["yellow"], (CX, CY + s * STOP_DIST), (0, s))
        _dashes(surf, COLORS["yellow"], (CX + s * STOP_DIST, CY), (s, 0))
    for a in APPROACHES:
        _zebra(surf, a, white)
        pygame.draw.rect(surf, white, _stop_rect(a))
        c, (hx, hy) = lane_center(a), heading(a)
        for d in _ARROW_DISTS:
            pos = (CX - hx * d if hx else c, CY - hy * d if hy else c)
            _arrow(surf, pos, (hx, hy), white)


# --------------------------------------------------------------------- Road
class Road:
    """Pre-rendered road scene. Built once, blitted every frame."""

    def __init__(self) -> None:
        self.rect = intersection_rect()
        self._font: pygame.font.Font | None = None
        self._bg = self._build()

    def _build(self) -> pygame.Surface:
        """Render the whole static scene into one off-screen Surface."""
        pygame.font.init()
        surf = pygame.Surface((WIDTH, HEIGHT))
        rng = random.Random(_SEED)  # seeded -> identical texture every run
        small, big = pygame.font.Font(None, 16), pygame.font.Font(None, 22)
        surf.fill(COLORS["grass"])
        pygame.draw.rect(surf, COLORS["road"], (CX - _HALF, 0, ROAD_W, HEIGHT))
        pygame.draw.rect(surf, COLORS["road"], (0, CY - _HALF, WIDTH, ROAD_W))
        for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
            _draw_footpath(surf, sx, sy)
            _draw_tufts(surf, sx, sy, rng)
            _decorate(surf, sx, sy, _LAYOUT_A if i in (0, 3) else _LAYOUT_B,
                      rng, small, big)
        _draw_markings(surf)
        if pygame.display.get_surface() is not None:
            surf = surf.convert()  # match display format -> faster blits
        return surf

    def draw(self, surface: pygame.Surface) -> None:
        """Blit the cached background (one fast copy per frame)."""
        surface.blit(self._bg, (0, 0))

    def _label(self, surface, text: str, pos: tuple) -> None:
        """Small readable debug label kept inside the screen."""
        if self._font is None:
            self._font = pygame.font.Font(None, 20)
        img = self._font.render(text, True, (255, 255, 0), (0, 0, 0))
        r = img.get_rect(topleft=(int(pos[0]), int(pos[1])))
        r.clamp_ip(surface.get_rect())
        surface.blit(img, r)

    def draw_debug(self, surface: pygame.Surface) -> None:
        """Overlay: lane centers (cyan), stop lines (red), spawns (orange),
        intersection rect (magenta). Off-screen spawns are clamped to the edge."""
        pygame.draw.rect(surface, _MAGENTA, self.rect, 2)
        pygame.draw.circle(surface, _MAGENTA, (CX, CY), 4)
        for a in APPROACHES:
            c, s, sp = lane_center(a), stop_line(a), spawn_pos(a)
            if axis_of(a) == "NS":
                pygame.draw.line(surface, _CYAN, (c, 0), (c, HEIGHT), 1)
                pygame.draw.line(surface, _RED, (c - _LANE_HALF, s), (c + _LANE_HALF, s), 2)
            else:
                pygame.draw.line(surface, _CYAN, (0, c), (WIDTH, c), 1)
                pygame.draw.line(surface, _RED, (s, c - _LANE_HALF), (s, c + _LANE_HALF), 2)
            tag = {"N": (c + 4, s - 18), "S": (c + 4, s + 4),
                   "W": (s - 84, c - 8), "E": (s + 6, c - 8)}[a]
            self._label(surface, f"{a} stop={s}", tag)
            mark = (int(clamp(sp[0], 10, WIDTH - 10)), int(clamp(sp[1], 10, HEIGHT - 10)))
            pygame.draw.circle(surface, _ORANGE, mark, 8)
            self._label(surface, f"{a} spawn {sp}", (mark[0] + 10, mark[1] + 10))