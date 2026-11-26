"""Effects + audio demo: python tests/demo_effects.py [--silent] [--fail-audio]

Mouse click = smoke + sparks + crash sound     1-6 = horn crash pass click start gameover
T floating text   B honk bubble (at mouse)     S screen shake
M mute (speaker icon)   A ambience on/off      X stress: 10 crashes at once   ESC quit
--silent      uses SDL's dummy audio driver    --fail-audio  simulates a missing device
"""
import os
import random
import sys

if "--silent" in sys.argv:
    os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from src.audio import SOUND_NAMES, AudioManager  # noqa: E402
from src.constants import COLORS, FPS, HEIGHT, MAX_DT, WIDTH  # noqa: E402
from src.effects import MAX_PARTICLES, EffectsSystem  # noqa: E402
from src.road import Road  # noqa: E402

KEYS = {pygame.K_1: "horn", pygame.K_2: "crash", pygame.K_3: "pass",
        pygame.K_4: "click", pygame.K_5: "start", pygame.K_6: "gameover"}
TEXTS = (("+10", "yellow"), ("+25", "yellow"), ("COMBO x2", "accent"),
         ("CRASH!", "red"))


def self_check(audio: AudioManager, fx: EffectsSystem) -> None:
    """Verify sounds build (or clean silent mode), caps and decay work."""
    if audio.enabled:
        assert all(n in audio._sounds for n in SOUND_NAMES), "missing sound"
        audio.play("horn")
        first = audio._last_horn
        audio.play("horn")
        assert audio._last_horn == first, "horn rate limit failed"
        audio.set_muted(True)
        audio.play("crash")
        audio.set_muted(False)
        print(f"Audio OK: {len(audio._sounds)} sounds + ambience, horn rate-limited")
    else:
        for n in SOUND_NAMES:  # must be harmless
            audio.play(n)
        audio.set_ambience(True)
        audio.toggle_mute()
        audio.toggle_mute()
        print("Audio unavailable -> silent mode works, no crash")
    for _ in range(80):
        fx.spawn_sparks((500, 350))
        fx.spawn_smoke((500, 350))
    assert fx.particle_count <= MAX_PARTICLES, "particle cap broken"
    fx.update(5.0)
    assert fx.particle_count == 0, "particles never expire"
    fx.shake(0.3, 10)
    fx.update(0.1)
    fx.update(1.0)
    assert fx.shake_offset == (0, 0), "shake must decay to zero"
    print("Effects OK: particle cap 300, expiry, shake decay")


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Effects demo")
    if "--fail-audio" in sys.argv:  # pretend there is no sound card
        def broken(*_a, **_k):
            raise pygame.error("simulated: no audio device")
        pygame.mixer.init = broken
    audio, fx, road = AudioManager(), EffectsSystem(), Road()
    self_check(audio, fx)
    world, font = pygame.Surface((WIDTH, HEIGHT)).convert(), pygame.font.Font(None, 24)
    clock, rng, ambience, running = pygame.time.Clock(), random.Random(), False, True
    ui_muted = False
    while running:
        dt = min(clock.tick(FPS) / 1000.0, MAX_DT)
        mouse = pygame.mouse.get_pos()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                fx.spawn_smoke(e.pos)
                fx.spawn_sparks(e.pos)
                audio.play("crash")
            elif e.type == pygame.KEYDOWN:
                k = e.key
                if k == pygame.K_ESCAPE:
                    running = False
                elif k in KEYS:
                    audio.play(KEYS[k])
                elif k == pygame.K_t:
                    text, col = rng.choice(TEXTS)
                    fx.floating_text(mouse, text, COLORS[col])
                elif k == pygame.K_b:
                    fx.spawn_bubble(mouse)
                elif k == pygame.K_s:
                    fx.shake(0.4, 8)
                elif k == pygame.K_m:
                    audio.toggle_mute()
                    ui_muted = audio.muted
                elif k == pygame.K_a:
                    ambience = not ambience
                elif k == pygame.K_x:
                    for _ in range(10):
                        p = (rng.randint(150, 850), rng.randint(150, 550))
                        fx.spawn_smoke(p)
                        fx.spawn_sparks(p)
                    fx.shake(0.4, 8)
                    audio.play("crash")
        audio.set_ambience(ambience)
        fx.update(dt)
        ox, oy = fx.shake_offset
        target = world if (ox or oy) else screen  # offscreen buffer + translation
        road.draw(target)
        fx.draw(target)
        if target is world:
            screen.fill(COLORS["grass"])
            screen.blit(world, (ox, oy))
        status = (f"FPS {clock.get_fps():4.0f}   particles {fx.particle_count}/{MAX_PARTICLES}"
                  f"   audio {'ON' if audio.enabled else 'silent'}"
                  f"   muted {ui_muted}   ambience {ambience}")
        for i, text in enumerate((status, "click: crash   1-6: sounds   T text   "
                                  "B bubble   S shake   M mute   A ambience   X stress")):
            screen.blit(font.render(text, True, COLORS["white"], COLORS["black"]),
                        (8, 8 + i * 26))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()