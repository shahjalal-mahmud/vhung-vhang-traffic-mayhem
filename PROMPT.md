# 🚦 VhungVhang Build Plan (Prompt Pack)

## How to use this file

1. Open a **new Claude chat** for each phase. A new account is fine too.
2. In **one message**, paste **Part A (Master Context)** and then **one Phase prompt**. Part A is what makes every phase independent, because it fixes the file names, constants and class interfaces. Code from different phases and different accounts will therefore fit together.
3. Save the files Claude gives you into your project folder, run the test command it gives, then run `git commit`.
4. If a reply cuts off, send: `Continue from the last file, starting at <filename>. Don't repeat finished files.`
5. If something breaks, use the **Fix-it prompt** at the end. Paste only the broken file and the error, not the whole project.

### Phase overview

| #   | Phase                                                         | Output (approx.) |
| --- | ------------------------------------------------------------- | ---------------- |
| 1   | Skeleton, constants, game loop, stubs for all modules         | ~400 lines       |
| 2   | Road and intersection rendering                               | ~300 lines       |
| 3   | Traffic signals and key controls                              | ~300 lines       |
| 4   | Vehicles (6 cartoon types, drawn with code)                   | ~400 lines       |
| 5   | Traffic manager (spawning, queues, obeying signals)           | ~350 lines       |
| 6   | Chaos (red-runners), collisions, crashes                      | ~300 lines       |
| 7   | Gameplay integration, score, lives, difficulty, high score    | ~350 lines       |
| 8   | UI (menu, HUD, pause, game over, how-to-play)                 | ~400 lines       |
| 9   | Audio and visual polish (procedural sounds, particles, shake) | ~400 lines       |
| 10  | Balancing, bug-fix pass, README, EXE build, viva notes        | variable         |

---

## PART A: Master Context (paste this at the start of EVERY phase)

```
You are my senior Python/Pygame game developer and mentor. I am a university student building a 2D arcade game for a Computer Graphics lab. I build it in phases, in separate chat sessions, so you will NOT remember earlier phases. Follow the fixed specification below EXACTLY so that files from different sessions work together.

=== PROJECT ===
Name: VhungVhang: Traffic Mayhem
Tech: Python 3.10+, Pygame 2.x, desktop (Windows/Linux).
Idea: The player controls the signals of a busy four-way intersection inspired by Bangladeshi roads. Keys: 1 = North-South gets green, 2 = East-West gets green, P = pause/resume, R = restart, ESC = quit. Vehicles: rickshaw, cng, motorcycle, car, bus, truck. Player earns points when vehicles pass safely. Impatient drivers sometimes run red lights, causing collisions. Collisions cost lives. Traffic gets denser and faster with the score. High score is saved. Cartoon 2D style, sound effects.

=== HARD RULES ===
- NO external asset files. All graphics use pygame.draw / Surfaces. All sounds are generated at runtime (wave synthesis using the standard `array` and `math` modules, NO numpy). The game must run after only `pip install pygame`.
- Time-based movement: every update uses dt in seconds (float). Fixed 60 FPS cap.
- Left-hand traffic (like Bangladesh). Vehicles go straight only (no turns).
- Each file should stay under ~350 lines. Use type hints and short docstrings.
- Add short comments naming the Computer Graphics concept used (translation, rotation transform, coordinate system, double buffering, frame-based animation, collision detection / AABB, etc.) because I must explain them in a viva.
- Code must be complete and runnable. NO placeholders like "...rest of code", no TODO stubs unless this phase says to create stubs.

=== FILE TREE (fixed) ===
vhung-vhang-traffic-mayhem/
  main.py                  -> creates Game and calls run()
  requirements.txt         -> pygame>=2.5
  .gitignore
  highscore.json           -> created at runtime
  src/__init__.py
  src/constants.py
  src/utils.py
  src/game.py              -> Game class, state machine, main loop
  src/road.py              -> Road class + helper functions
  src/signals.py           -> SignalController
  src/vehicles.py          -> Vehicle class + drawing of 6 vehicle types
  src/traffic_manager.py   -> TrafficManager
  src/chaos.py             -> ChaosSystem (red-light runners)
  src/collision.py         -> CollisionSystem
  src/scoring.py           -> ScoreManager
  src/difficulty.py        -> difficulty curve functions
  src/ui.py                -> UI (menu, HUD, pause, game over, help)
  src/audio.py             -> AudioManager
  src/effects.py           -> EffectsSystem (particles, floating text, shake)
  tests/demo_*.py          -> small standalone demo for each phase

=== FIXED CONSTANTS (src/constants.py must define these exact names) ===
WIDTH=1000, HEIGHT=700, FPS=60, CX=500, CY=350 (intersection center)
ROAD_W=140, LANE_W=70 (intersection square is CX±70, CY±70)
Crosswalk: 20px thick, directly outside the intersection square.
Stop line: 10px beyond the crosswalk, i.e. 100px from center along the axis.
STATE_MENU, STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER, STATE_HELP (strings)
START_LIVES=3, MIN_GREEN=2.0, YELLOW_TIME=1.5, ALL_RED_TIME=0.7, CRASH_CLEAR_TIME=2.5
SAFE_GAP=14, ACCEL=220, BRAKE=420 (px/s^2), MAX_LEVEL=10, LEVEL_SCORE_STEP=150
BASE_SPAWN_INTERVAL=2.2, MIN_SPAWN_INTERVAL=0.7, SPEED_MULT_PER_LEVEL=0.06
HIGHSCORE_FILE="highscore.json"
COLORS dict with keys: grass, road, road_edge, lane_marking, footpath, white, black, red, yellow, green, ui_bg, ui_text, accent
VEHICLE_SPECS = { type: dict(length, width, max_speed, points, patience, weight, color) }
  rickshaw:   length 44, width 26, max_speed 90,  points 10, patience 6,  weight 20
  cng:        length 50, width 28, max_speed 120, points 10, patience 6,  weight 20
  motorcycle: length 34, width 16, max_speed 170, points 10, patience 4,  weight 20
  car:        length 58, width 30, max_speed 140, points 10, patience 8,  weight 20
  bus:        length 100,width 36, max_speed 100, points 25, patience 12, weight 10
  truck:      length 90, width 34, max_speed 95,  points 20, patience 10, weight 10
  (choose nice cartoon colors; max_speed in px/s, patience in seconds)

=== GEOMETRY (fixed) ===
Approach = the side a vehicle comes FROM: "N","S","E","W". Axis: N,S -> "NS"; E,W -> "EW".
Heading (dx,dy): N->(0,1), S->(0,-1), W->(1,0), E->(-1,0).
Lane center lines (left-hand traffic): N: x=CX+35 | S: x=CX-35 | W: y=CY-35 | E: y=CY+35
Spawn just outside screen (60px): N y=-60, S y=HEIGHT+60, W x=-60, E x=WIDTH+60.
Vehicle is removed when 80px beyond the opposite screen edge.
Stop line position per approach: N y=CY-100, S y=CY+100, W x=CX-100, E x=CX+100 (a vehicle's FRONT stops there).

=== INTERFACES (fixed, implement/keep exactly) ===
road.py: class Road: __init__(), draw(surface). Module functions: spawn_pos(approach)->(x,y), stop_line(approach)->int, heading(approach)->(dx,dy), axis_of(approach)->str, lane_center(approach)->int, intersection_rect()->pygame.Rect
signals.py: class SignalController: state in {"NS_GREEN","NS_YELLOW","EW_GREEN","EW_YELLOW","ALL_RED"} (starts NS_GREEN); request(axis) ("NS"/"EW"); update(dt); light_for(approach)->"green"|"yellow"|"red"; time_in_state attribute; draw(surface); reset()
  Switch logic: request for the non-green axis -> current axis YELLOW (YELLOW_TIME) -> ALL_RED (ALL_RED_TIME) -> requested axis GREEN. Requests are ignored if the axis is already green/pending or if green has been active < MIN_GREEN (store one pending request instead of dropping it).
vehicles.py: class Vehicle: __init__(vtype, approach, speed_mult=1.0); attrs: vtype, approach, axis, heading, x, y (center), length, width, speed, max_speed, target_speed, state in {"moving","stopped","crashed"}, wait_time, patience, ignores_signal(bool), scored(bool), alive(bool), crash_timer; property rect (axis-aligned pygame.Rect of the rotated body); front_pos()->(x,y); distance_to_stop_line()->float (positive = not yet reached); update(dt); draw(surface); crash()
traffic_manager.py: class TrafficManager: vehicles(list), update(dt, signals, level)->list[Vehicle] (vehicles that exited the screen safely this frame), draw(surface), reset()
chaos.py: class ChaosSystem: update(dt, vehicles, level) -> None (sets vehicle.ignores_signal)
collision.py: class CollisionSystem: update(dt, vehicles)->list[tuple[Vehicle,Vehicle]] (NEW collisions this frame; also removes crashed vehicles after CRASH_CLEAR_TIME by setting alive=False)
scoring.py: class ScoreManager: score, lives, high_score, level (property), add_vehicle(vehicle), lose_life(), is_game_over (property), save_high_score(), reset(), new_high_score (bool)
difficulty.py: spawn_interval(level)->float, speed_multiplier(level)->float, chaos_chance(level)->float
ui.py: class UI: draw_menu(surface, mouse_pos), draw_help(surface), draw_hud(surface, score_mgr, signals), draw_pause(surface), draw_game_over(surface, score_mgr), handle_event(event, state)->str|None (returns an action like "play","help","back","quit","restart","menu")
audio.py: class AudioManager: play(name) with names "horn","crash","pass","click","gameover","start"; set_muted(bool); toggle_mute()
effects.py: class EffectsSystem: spawn_smoke(pos), spawn_sparks(pos), floating_text(pos,text,color), shake(duration,magnitude), update(dt), draw(surface), shake_offset (property -> (x,y))
game.py: class Game: run(); attributes: screen, clock, state, road, signals, traffic, chaos, collisions, score, ui, audio, effects. Main loop = handle events -> update(dt) -> draw -> display.flip() (double buffering).

=== HOW YOU MUST ANSWER (output rules) ===
1. Start with a 3-line summary and the list of files you will give (new / replaced / patched).
2. Give FULL code for every new or replaced file in separate code blocks with the file path as a heading. For small changes to an existing file, give an exact patch (find this -> replace with this), never a partial file without markers.
3. Then give "Step-by-step instructions": where to save files, commands to run, and exactly what I should see on screen if it works.
4. Then give a 5-item "Test checklist" and a one-line `git commit -m "..."` message.
5. Keep explanations short; spend the output on working code. Do not change the fixed constants/interfaces above. If you believe something must change, tell me at the end under "Interface notes" instead of silently changing it.
6. If the answer would be too long, split at a file boundary, tell me to say "continue", and never truncate code.

=== CURRENT PHASE ===
(The phase prompt follows below.)
```

---

## PHASE 1: Skeleton, constants, game loop, stubs

```
PHASE 1: Project skeleton and running game loop (nothing exists yet).

GOAL: A window that opens, runs at 60 FPS with a working state machine, and every module in the file tree exists as a minimal working STUB that matches the Master Context interfaces, so later phases only replace files.

CREATE:
1. requirements.txt, .gitignore (python, __pycache__, highscore.json, build/, dist/), main.py, src/__init__.py
2. src/constants.py: ALL fixed constants from the Master Context, exactly named. Pick a pleasant cartoon palette for COLORS and VEHICLE_SPECS colors.
3. src/utils.py: clamp(), lerp(), load_json(path, default), save_json(path, data) (safe: handles missing/corrupt file), draw_text(surface, text, font, color, pos, center=False), draw_text_shadow(...).
4. src/game.py: the real Game class with:
   - window creation, caption "VhungVhang: Traffic Mayhem", clock, dt in seconds (clamp dt to max 0.05)
   - state machine with STATE_MENU, STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER, STATE_HELP
   - key handling: ENTER/SPACE starts game from menu, 1 and 2 (just print/log in PLAYING for now), P toggles pause, R restarts, ESC quits (from any state; from PLAYING it may go back to menu, but keep ESC = quit as in the README), H opens help from menu
   - each state draws simple placeholder text screens so I can see state changes work
   - a tiny FPS counter toggled with F3
5. STUB files (class + methods exactly as in the Master Context interfaces, doing the minimal harmless thing and with a docstring saying "STUB - replaced in Phase N"): road.py, signals.py, vehicles.py, traffic_manager.py, chaos.py, collision.py, scoring.py, difficulty.py, ui.py, audio.py, effects.py. Game must import and instantiate them already (road.draw fills the background, scoring works with simple ints, etc.).
6. tests/demo_skeleton.py: imports every module and asserts each class has the required methods/attributes (a quick interface check I can run any time).

TEST: `python main.py` shows a window; menu -> play -> pause -> game over flow works with keys; `python tests/demo_skeleton.py` prints "All interfaces OK".
```

---

## PHASE 2: Road and intersection rendering

```
PHASE 2: Road and intersection rendering.
Prerequisite: Phase 1 is done and saved. Replace src/road.py (stub) and add tests/demo_road.py. Do not modify other files unless you give an exact patch.

GOAL: A beautiful cartoon four-way intersection, drawn ONCE into a cached background Surface at startup (performance + a "pre-rendered buffer" CG concept), then blitted every frame.

REQUIREMENTS:
1. Implement ALL module-level helper functions from the Master Context exactly: spawn_pos, stop_line, heading, axis_of, lane_center, intersection_rect. They must use constants only (no magic numbers).
2. class Road with __init__() building the cached surface and draw(surface) blitting it.
3. Drawing details (use pygame.draw only):
   - Grass background with subtle cartoon texture (random small tufts, seeded random so it is stable).
   - Vertical road (x from CX-70 to CX+70) and horizontal road (y from CY-70 to CY+70), road edges, footpaths/curbs along the sides.
   - Dashed yellow center line on each road (not inside the intersection square), white dashed lane separators if needed.
   - Four zebra crossings (20px thick, directly outside the intersection square) and four white stop lines at the exact positions in the Master Context.
   - Four corner blocks with cartoon decoration: simple Dhaka-style buildings (flat colored rectangles with windows, shop sign banners), trees, lamp posts, a small tea stall or billboard. Keep it fast and colorful; decorations must not overlap roads or the space needed for traffic lights near the corners of the intersection.
   - Tiny arrow marks painted on each lane showing travel direction (left-hand traffic).
4. Add a debug mode: Road.draw_debug(surface) draws lane center lines, stop lines, spawn points and the intersection rect in bright colors (toggle in the demo with the D key).
5. tests/demo_road.py: standalone window showing the road, D toggles debug overlay, ESC quits, and it prints the coordinates of all helper function outputs for the 4 approaches so I can verify them.

TEST: run `python tests/demo_road.py`; roads are centered, symmetrical, stop lines sit 100px from center, debug overlay lines match.
After the code, add a short "CG concepts used" list (3-5 bullets) for my viva.
```

---

## PHASE 3: Traffic signals and key controls

```
PHASE 3: Traffic signal system.
Prerequisite: Phases 1-2 done and saved. Replace src/signals.py (stub) and add tests/demo_signals.py. If game.py must change (e.g. to call signals.request on keys 1/2 and draw signals), give exact patches.

GOAL: A reliable signal state machine plus cartoon traffic-light drawing.

REQUIREMENTS:
1. SignalController exactly as in the Master Context. Logic:
   - Start in NS_GREEN. request("NS"/"EW") for the axis that is not green starts: current YELLOW (YELLOW_TIME) -> ALL_RED (ALL_RED_TIME) -> requested GREEN.
   - If the current green has been active for less than MIN_GREEN, store ONE pending request and execute it as soon as MIN_GREEN passes.
   - Ignore a request for the axis that is already green or already being switched to. Repeated key mashing must never break the state machine.
   - time_in_state is updated each frame; reset() restores NS_GREEN.
   - light_for(approach) returns "green", "yellow" or "red" for each approach (both approaches of the active axis share the color; in ALL_RED everything is "red").
2. Drawing (cartoon): a traffic-light pole with a rounded black housing and 3 lamps (red/yellow/green) at each of the four corners of the intersection, placed OUTSIDE the road next to each stop line, facing the approaching traffic. The active lamp glows (draw a soft translucent circle halo with an alpha Surface). Also draw a small countdown/progress arc or bar near each light showing how long the current state has lasted.
3. A small on-screen control hint drawn by the controller is NOT needed (the HUD does that in Phase 8), but add a method `pending_request` property so the HUD can show it later.
4. Wire into game.py (patch): keys 1 and 2 call signals.request("NS") / request("EW") in PLAYING; signals.update(dt) in update; signals.draw in draw after the road; R resets signals.
5. tests/demo_signals.py: standalone window with Road + SignalController, keys 1/2 to request, shows the current state and time_in_state as text, and includes an automatic self-test mode (key T) that mashes requests randomly for 20 seconds and asserts the state never becomes invalid or both axes green.

TEST: lights switch with the right yellow/all-red timing; mashing 1 and 2 never breaks it.
Finish with "CG concepts used" for my viva (alpha blending, layering/draw order, etc.).
```

---

## PHASE 4: Vehicles

```
PHASE 4: Vehicle class and six cartoon vehicle types.
Prerequisite: Phases 1-3 done and saved. Replace src/vehicles.py (stub) and add tests/demo_vehicles.py. Do not touch other files unless you give exact patches.

GOAL: Fully drawn, animated vehicles that move correctly along lanes in all 4 approaches.

REQUIREMENTS:
1. Vehicle class exactly as in the Master Context. Constructor places the vehicle at spawn_pos(approach) with the correct lane center offset (use road.py helpers lane_center, spawn_pos, heading, axis_of), sets length/width/max_speed/patience from VEHICLE_SPECS, speed = 0 or small initial speed, target_speed = max_speed * speed_mult, state "moving", alive True.
2. Movement: update(dt) accelerates speed toward target_speed using ACCEL (and brakes using BRAKE when target_speed < speed), then moves x,y along heading. state is "stopped" when speed < 1 and target_speed == 0. When state == "crashed": speed 0, crash_timer increases by dt, and a tilt/rotation wobble is drawn. wait_time increases while stopped and resets to 0 when moving again.
3. rect property: AABB of the vehicle body for its heading (swap length/width for vertical vehicles). front_pos() is the center of the front edge; distance_to_stop_line() is positive when the front has not yet reached the stop line for that approach and negative when it has crossed it.
4. Drawing: each of the 6 types (rickshaw, cng, motorcycle, car, bus, truck) is drawn top-down in cartoon style on a local Surface facing RIGHT using pygame.draw, then cached per (type) and ROTATED to the heading using pygame.transform.rotate (rotation transform concept) and blitted at (x,y) as its center. Make them recognizable:
   - rickshaw: colorful hood with floral/pattern stripes, rider, small wheels, slight left-right wobble animation
   - cng: green/blue compact body with roof and visible cage lines
   - motorcycle: narrow body, rider with helmet, handlebar
   - car: sedan with windshield and headlights
   - bus: long colorful Bangladeshi bus with window strip, stripes, dents
   - truck: cab plus colorful cargo box with decorative pattern
   Add frame-based animation (wheel/rider bob, rickshaw wobble, brake lights glowing red when braking, headlights, and a small sprite flicker is NOT needed).
5. crash(): sets state "crashed", speed 0, crash_timer 0.
6. tests/demo_vehicles.py: standalone window with the Road background where I can press 1-6 to spawn a vehicle of each type from the approach cycled by pressing A (N,S,E,W), vehicles drive straight across the screen, a key S cycles speed multiplier, a key C crashes the newest vehicle, and a toggle B shows rect bounding boxes. Remove vehicles when beyond the despawn distance.

TEST: all 6 vehicles look right in all 4 directions, stay perfectly in their lane centers, and the rects match the visuals.
Finish with "CG concepts used" (rotation transform, translation, frame-based animation, sprite caching).
```

---

## PHASE 5: Traffic manager (spawning, queues, obeying signals)

```
PHASE 5: Traffic manager.
Prerequisite: Phases 1-4 done and saved. Replace src/traffic_manager.py (stub) and add tests/demo_traffic.py. Patch game.py only if needed (give exact patches).

GOAL: Realistic flow: vehicles spawn, drive, queue behind each other, stop at red/yellow, go on green, exit the screen, and are reported for scoring.

REQUIREMENTS:
1. TrafficManager exactly as in the Master Context.
2. Spawning: timer-based using difficulty.spawn_interval(level) (that file is a stub right now; if it returns a constant, that is fine) and speed multiplier from difficulty.speed_multiplier(level). Pick approach randomly (but avoid the same approach 3 times in a row) and vehicle type by VEHICLE_SPECS weights. Do NOT spawn when the spawn area of that approach is occupied (another vehicle within length + SAFE_GAP + 20 of the spawn point).
3. Per frame, for each approach/lane, sort vehicles by progress along the heading, then compute each vehicle's target_speed:
   - Follow the leader: keep SAFE_GAP between this vehicle's front and the leader's rear; slow down smoothly (use required braking distance v^2/(2*BRAKE)) and stop if needed.
   - Signal obedience: let L = signals.light_for(approach). If L is "red": stop at the stop line unless the vehicle has already crossed it. If L is "yellow": stop if it can brake to a stop before the line using BRAKE, otherwise continue ("committed"). Vehicles whose ignores_signal is True never stop for signals (they still follow the leader in front of them if the leader is in the same lane).
   - Crashed vehicles are obstacles: following vehicles must stop behind them. Vehicles already inside the intersection square never stop in the middle.
   - Otherwise target_speed = max_speed * speed multiplier.
4. update() returns the list of vehicles that left the screen this frame while not crashed and with scored False (set scored True). Remove dead vehicles (alive False) and off-screen vehicles from the list.
5. Queue overflow rule: if a queue reaches the spawn point (a vehicle stopped within 80px of spawn), keep it simple: just stop spawning for that approach (this avoids overlap bugs).
6. draw(surface): draw vehicles sorted so that crashed ones are drawn below moving ones, and draw buses/trucks above small vehicles.
7. tests/demo_traffic.py: Road + SignalController + TrafficManager in a standalone window with keys 1/2 for signals, a visible count of passed vehicles, and a text line showing the number of vehicles per approach. Add a stress option (key F) that sets level 10 for 30 seconds. Include an assert-based check that no two vehicles in the same lane ever overlap (print a warning if they do).

TEST: queues form neatly at red, release smoothly on green, no overlaps, vehicles exit and are counted.
Finish with a short note on the algorithm used (distance-based following, braking distance) for my viva.
```

---

## PHASE 6: Chaos, collisions, crashes

```
PHASE 6: Red-light runners, collision detection, crash handling.
Prerequisite: Phases 1-5 done and saved. Replace src/chaos.py and src/collision.py (stubs) and add tests/demo_collision.py. Patch other files only with exact patches.

GOAL: Chaotic drivers create dangerous situations and collisions are detected correctly.

REQUIREMENTS:
1. ChaosSystem.update(dt, vehicles, level):
   - For each stopped vehicle waiting at a red light (wait_time > patience for its type, not crashed), roll a chance (per second) equal to difficulty.chaos_chance(level) (stub constant is fine for now; use a local fallback such as 0.04 + 0.03*level per second) to set ignores_signal = True. The vehicle then accelerates through the red light.
   - Small types (motorcycle, rickshaw) are more reckless (multiply chance by 1.5), buses and trucks less (multiply by 0.5).
   - Add a "honk warning": when a vehicle sets ignores_signal, add an attribute vehicle.honk = True (for audio/effects later) that the game can read and clear.
   - Vehicles with ignores_signal reset to False once they exit the intersection square or crash.
2. CollisionSystem.update(dt, vehicles):
   - Use AABB collision detection (pygame.Rect.colliderect on slightly shrunk rects, shrink by about 15% so near-misses do not count).
   - Only vehicles of DIFFERENT axes can create a new collision when both are not already crashed. Vehicles in the same lane should never collide (but if they do due to a bug, ignore it and print a debug warning).
   - A collision calls crash() on both vehicles, and returns them as a tuple in the result list (only NEW collisions this frame; each pair reported once).
   - Crashed vehicles stay in place as obstacles for CRASH_CLEAR_TIME seconds (crash_timer from Vehicle), then alive=False so the traffic manager removes them.
   - Add helper `get_crash_point(a, b)` returning the midpoint of the overlap rect (used later for particles).
3. Patch game.py minimally so that in PLAYING: chaos.update, traffic.update, collisions.update are called in the correct order, and each collision calls score.lose_life() and prints "CRASH" to the console. (The full integration comes next phase.)
4. tests/demo_collision.py: scripted deterministic scenario with no randomness: one rickshaw from N and one motorcycle from W that will cross the intersection at the same time (set ignores_signal manually), verify that exactly one collision is reported, both become "crashed", they are removed after CRASH_CLEAR_TIME, and print PASS/FAIL. Also include an interactive mode with the full simulation and chaos enabled.

TEST: scripted test prints PASS; in interactive mode, after waiting at red, impatient vehicles eventually run the light and crash.
Finish with "CG concepts used" (AABB collision detection, bounding boxes).
```

---

## PHASE 7: Gameplay integration, score, lives, difficulty, high score

```
PHASE 7: Full gameplay loop.
Prerequisite: Phases 1-6 done and saved. Replace src/scoring.py, src/difficulty.py, src/game.py, and add tests/demo_balance.py. Patch other files only with exact patches.

GOAL: A complete playable game from MENU to GAME OVER and restart, using simple placeholder UI text (the full UI comes in Phase 8).

REQUIREMENTS:
1. difficulty.py:
   - spawn_interval(level): linear/eased from BASE_SPAWN_INTERVAL (level 1) down to MIN_SPAWN_INTERVAL (level MAX_LEVEL), with a small random jitter (+-15%).
   - speed_multiplier(level): 1.0 + SPEED_MULT_PER_LEVEL*(level-1).
   - chaos_chance(level): per-second chance, e.g. 0.03 at level 1 rising to ~0.18 at level 10 (document your formula in comments).
2. scoring.py: ScoreManager exactly as in the Master Context:
   - score, lives (START_LIVES), level = min(MAX_LEVEL, 1 + score // LEVEL_SCORE_STEP)
   - add_vehicle(vehicle) adds VEHICLE_SPECS[vtype]["points"] (+ small combo bonus: every 5 consecutive safe vehicles without a crash gives +10; a crash resets the combo)
   - lose_life(), is_game_over, high_score loaded from HIGHSCORE_FILE at start, save_high_score() only when the score beats it (sets new_high_score True), reset() for restart.
   - expose `combo` and `last_event` attributes for the HUD.
3. game.py (complete, final logic; UI drawing still placeholder text via utils.draw_text):
   - MENU -> PLAYING resets everything (road stays), PAUSED freezes updates, GAME_OVER when score.is_game_over (save high score here), R restarts immediately in PLAYING/PAUSED/GAME_OVER, ESC quits.
   - update order per frame: signals.update -> chaos.update -> traffic.update (returns exited vehicles -> score.add_vehicle for each) -> collisions.update (for each collision: score.lose_life(), effects/audio calls guarded so stubs are fine) -> check game over.
   - Level is passed to traffic/chaos from score.level. Show level-up as a short on-screen text for 2 seconds ("LEVEL 3!").
   - Keep all system calls using the fixed interfaces so Phase 8 and 9 just replace ui.py/audio.py/effects.py.
4. tests/demo_balance.py: headless simulation (no window, pygame dummy video driver `SDL_VIDEODRIVER=dummy`) with a simple bot that alternates the signals every N seconds; simulate 5 minutes at 60 FPS steps and print: vehicles passed, crashes, final level, average queue length. Use it so I can tune numbers without playing.

TEST: I can play a full round; lives drop only on crashes; score and level go up; high score persists between runs; R and P work; demo_balance prints stats without crashing.
Finish with a list of the 5 constants I can tweak to make the game easier or harder.
```

---

## PHASE 8: UI (menu, HUD, pause, game over, help)

```
PHASE 8: Full user interface.
Prerequisite: Phases 1-7 done and saved. Replace src/ui.py (stub) and patch src/game.py to use it. Do not change gameplay logic.

GOAL: A polished cartoon UI that matches the theme.

REQUIREMENTS:
1. UI class exactly as in the Master Context. Use pygame.font.SysFont with a safe fallback list (e.g. "comicsansms","arialrounded","verdana","arial") and cache fonts. No external font files.
2. Main menu (draw_menu): the animated road background (reuse the Road surface) with a few decorative vehicles driving across the top/bottom (use Vehicle objects created inside UI, looped and unrelated to the game), a big bouncing title "VhungVhang" with outline/shadow and subtitle "Traffic Mayhem", buttons: PLAY, HOW TO PLAY, QUIT with mouse hover highlight and keyboard navigation (UP/DOWN + ENTER) and a high-score display. Name credit at the bottom: "Md Shahajalal Mahmud | 11230321539 | NUBTK".
3. How to play (draw_help): controls table (1, 2, P, R, ESC, M mute), rules summary, scoring table with the 6 vehicles and their points (draw tiny vehicle icons from Vehicle.draw on a small area or simple shapes), BACK button.
4. HUD (draw_hud): top bar with Score, High Score, Level, hearts for lives (drawn with pygame.draw polygons/circles), combo text, current signal status indicator (NS / EW with green/yellow/red dots) and the pending request indicator, plus bottom hint "1 = North-South | 2 = East-West | P = Pause". Keep it semi-transparent so the road remains visible.
5. Pause overlay: dark translucent layer, "PAUSED", hint text. Game over: overlay, "GAME OVER" with shake-in animation, final score, high score, "NEW HIGH SCORE!" blinking when score.new_high_score, and buttons RESTART and MENU.
6. handle_event(event, state) returns action strings ("play","help","back","quit","restart","menu") and game.py uses them to change state.
7. Level-up banner: draw_banner(surface, text) used by game.py for "LEVEL n!". Show it with a slide/fade animation.
8. tests/demo_ui.py: opens each screen by pressing 1-5 (menu, help, hud with fake score values, pause, game over) so I can check the UI without playing.

TEST: every screen looks clean at 1000x700, buttons work with mouse and keyboard, no flicker, no crash if high score is 0.
Finish with "CG concepts used" (alpha blending overlays, easing animation, layered rendering).
```

---

## PHASE 9: Audio and visual polish

```
PHASE 9: Procedural audio and visual effects.
Prerequisite: Phases 1-8 done and saved. Replace src/audio.py and src/effects.py (stubs) and patch src/game.py (exact patches) to call them. Do not change gameplay balance.

GOAL: The game feels alive and chaotic, still without any asset files.

REQUIREMENTS:
1. audio.py: AudioManager generates all sounds at startup with the `array` and `math` modules (no numpy) into pygame.mixer.Sound objects (initialize mixer with 22050 Hz, mono/16-bit, handle init failure gracefully so the game still runs silently when no audio device exists):
   - "horn": two-tone honk (e.g. 400/500 Hz square-ish wave with envelope)
   - "crash": noise burst with decay + low thud
   - "pass": short pleasant ding for scoring
   - "click": UI click, "start": rising arpeggio, "gameover": descending sad tones
   - A soft looping city/engine ambience (low-volume filtered noise) played in PLAYING, stopped in other states, and toggled by M (mute) with a speaker icon shown in the HUD.
   - Rate-limit horns (min 0.25 s between plays) so many honks do not become noise.
2. effects.py: EffectsSystem exactly as in the Master Context:
   - particles: smoke puffs (grey circles growing and fading) and orange/yellow sparks (fast small lines/circles with gravity-free motion) at crash points
   - floating text: "+10", "+25", "COMBO x2", "CRASH!" rising and fading, drawn with the UI font
   - screen shake with decay; game.py renders the world into an offscreen Surface then blits it with shake_offset (offscreen buffer concept)
   - honk bubbles: tiny comic speech bubbles near vehicles with ignores_signal ("Pom pom!", "Horn!", "Boom!" etc. random Banglish) appear when vehicle.honk is True
   - use object pooling or capped particle counts (max 300) for performance
3. Patch game.py: play "pass" and spawn "+points" floating text when a vehicle exits safely; on collision play "crash", spawn smoke + sparks at get_crash_point, floating "CRASH!", shake(0.4, 8); on vehicle.honk play "horn" and spawn a bubble then clear the flag; UI button events play "click"; "start" on game start, "gameover" on game over.
4. tests/demo_effects.py: standalone window where mouse click spawns smoke+sparks, keys 1-6 play each sound, T spawns floating text, S shakes the screen, and M toggles mute.

TEST: all sounds play without numpy, game still runs if audio init fails, FPS stays near 60 during multiple crashes.
Finish with "CG concepts used" (particle systems, double buffering/offscreen rendering, alpha blending).
```

---

## PHASE 10: Balance, bug-fix pass, README, EXE, viva notes

```
PHASE 10: Final polish and delivery.
Prerequisite: Phases 1-9 done and saved. I will paste my current bug list and (if needed) the broken files below this prompt. If I paste nothing, do a careful review based on the Master Context.

GOAL: Make the project stable, balanced, documented and ready to submit.

DELIVER:
1. BUG-FIX PASS: Analyze the bug list / files I pasted and give exact patches (find -> replace) or full replaced files. Also review for these common problems and tell me how to check each one: vehicle overlap in lanes, vehicles stopping inside the intersection, signal state edge cases, dt spikes after window drag, high-score file corruption, crash when the audio device is missing, memory growth (lists not cleaned), restarting resets all systems (including effects, chaos flags, signals).
2. BALANCE GUIDE: a table of the 8 most important constants (what they do, current value, safe range) and recommended values for "Easy / Normal / Hard", plus a patch that adds an optional difficulty selector to the menu ONLY if it needs fewer than 40 lines.
3. REAL README.md: update my README with correct final controls (add M = mute, F3 = FPS), final features, project structure tree, how to run, and a "Computer Graphics Concepts" section that maps each concept to the exact file/class where it is used (translation, rotation transform, coordinate system, frame animation, AABB collision, alpha blending, particle system, double buffering, pre-rendered surfaces).
4. SCREENSHOT GUIDE: exact steps and a small script `tools/screenshot.py` or an in-game F12 key patch that saves screenshots into /screenshots as main_menu.png, gameplay.png and game_over.png.
5. BUILD EXECUTABLE: PyInstaller commands for Windows and Linux (onefile, windowed, name VhungVhang) and the exact fix for resource paths (use a helper `resource_path()` in utils.py, patch highscore file location to be user-writable).
6. VIVA NOTES: 12 likely viva questions with short, simple answers about this project (game loop, dt, collision detection, rotation, rendering order, double buffering, why no assets, how difficulty scales, etc.), plus a 60-second demo script I can speak while presenting.
7. FINAL CHECKLIST: 15-item submission checklist (repo clean, requirements.txt, README images load, tags/commit history, etc.).

Bug list / pasted files (if any) are below:
```

---

## 🔧 FIX-IT PROMPT (use any time something breaks)

```
Use the Master Context above (pasted in this message) as the fixed specification.

PROBLEM:
I ran: <command>
Expected: <what should happen>
Actual: <what happened>

ERROR / TRACEBACK:
<paste the full traceback>

RELEVANT FILE(S) (only the ones involved):
<paste file path and code>

Rules: Find the root cause first (2-3 lines), then give an exact patch (find -> replace) or the full corrected file. Do not change the fixed interfaces or constants. Tell me the exact test to run to confirm the fix.
```

---

