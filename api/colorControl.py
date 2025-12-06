import json
import random
import time
import math
import threading

try:
    import board
    import neopixel
    IS_PI = True
except ImportError:
    IS_PI = False
    board = None
    neopixel = None

NUM_LEDS = 20
pixels = None
LAMP_COUNT = 3

if IS_PI:
    pixels = neopixel.NeoPixel(board.D18, NUM_LEDS, auto_write=False)

current_mode = "static"
current_color = (0, 0, 0)
_lock = threading.Lock()
_loop_started = False

def _wheel(pos):
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    pos -= 170
    return (0, pos * 3, 255 - pos * 3)

def _animation_loop():
    global current_mode, current_color

    phase = 0
    last_mode = None
    last_color = None
    sleep_ms = 30

    era_initialized = False
    era_lamps = []
    era_surge_frames = 0
    era_surge_total = 0
    era_surge_strength = 0.0
    era_buzz_phase = 0.0
    era_lamp_level = []
    era_lamp_target = []

    while True:
        with _lock:
            mode = current_mode
            color = current_color

        if mode == "static":
            if mode != last_mode or color != last_color:
                r, g, b = color
                if IS_PI and pixels is not None:
                    for i in range(NUM_LEDS):
                        pixels[i] = (r, g, b)
                    pixels.show()

        elif mode == "fire":
            base_r, base_g, base_b = 255, 96, 12

            if IS_PI and pixels is not None:
                for i in range(NUM_LEDS):
                    flicker = random.randint(0, 40)
                    r1 = max(base_r - flicker, 0)
                    g1 = max(base_g - flicker, 0)
                    b1 = max(base_b - flicker, 0)
                    pixels[i] = (r1, g1, b1)

                pixels.show()

            sleep_ms = random.randint(50, 150)
            continue

        elif mode == "eras":
            if not era_initialized:
                era_lamps = []
                leds_per_lamp = NUM_LEDS / float(LAMP_COUNT)
                for lamp_idx in range(LAMP_COUNT):
                    start = int(round(lamp_idx * leds_per_lamp))
                    end = int(round((lamp_idx + 1) * leds_per_lamp)) - 1
                    if start > end:
                        continue
                    start = max(0, min(NUM_LEDS - 1, start))
                    end = max(0, min(NUM_LEDS - 1, end))
                    era_lamps.append((start, end))
                era_lamp_level = [random.uniform(0.6, 0.9) for _ in era_lamps]
                era_lamp_target = list(era_lamp_level)
                era_initialized = True

            if not IS_PI or pixels is None or not era_lamps:
                sleep_ms = 40
                time.sleep(sleep_ms / 1000.0)
                continue

            base_temp = 2250.0

            era_buzz_phase += 0.25
            mains_mod = 0.97 + 0.03 * math.sin(era_buzz_phase)

            if era_surge_frames <= 0 and random.random() < 0.002:
                era_surge_total = random.randint(8, 18)
                era_surge_frames = era_surge_total
                era_surge_strength = random.uniform(-0.35, 0.25)

            if era_surge_frames > 0 and era_surge_total > 0:
                progress = (era_surge_total - era_surge_frames) / float(max(1, era_surge_total))
                surge_scale = 1.0 + era_surge_strength * math.sin(progress * math.pi)
                era_surge_frames -= 1
            else:
                surge_scale = 1.0

            for idx, (start, end) in enumerate(era_lamps):
                if random.random() < 0.08:
                    delta = random.uniform(-0.05, 0.05)
                    era_lamp_target[idx] = max(0.55, min(1.05, era_lamp_target[idx] + delta))

                era_lamp_level[idx] += (era_lamp_target[idx] - era_lamp_level[idx]) * 0.2

                k_jitter = random.gauss(0.0, 50.0)
                k = max(1900.0, min(2600.0, base_temp + k_jitter))

                r, g, b = _kelvin_to_rgb(k)

                lamp_scale = mains_mod * surge_scale * era_lamp_level[idx]
                lamp_scale = max(0.18, min(1.0, lamp_scale))

                length = max(1, end - start + 1)
                for i in range(start, end + 1):
                    if 0 <= i < NUM_LEDS:
                        if length > 1:
                            pos = (i - start) / float(length - 1)
                        else:
                            pos = 0.5
                        edge_dim = 0.8 + 0.2 * (1.0 - abs(0.5 - pos) * 2.0)
                        s = lamp_scale * edge_dim
                        rr = int(max(0, min(255, r * s)))
                        gg = int(max(0, min(255, g * s * 0.92)))
                        bb = int(max(0, min(255, b * s * 0.6)))
                        pixels[i] = (rr, gg, bb)

            pixels.show()
            sleep_ms = random.randint(35, 55)
            time.sleep(sleep_ms / 1000.0)
            last_mode = mode
            last_color = color
            continue

        elif mode == "off":
            if mode != last_mode:
                if IS_PI and pixels is not None:
                    for i in range(NUM_LEDS):
                        pixels[i] = (0, 0, 0)
                    pixels.show()

        last_mode = mode
        last_color = color
        time.sleep(sleep_ms / 1000.0)

def _ensure_loop():
    global _loop_started
    if _loop_started:
        return
    t = threading.Thread(target=_animation_loop, daemon=True)
    t.start()
    _loop_started = True

def set_color(r, g, b):
    global current_color, current_mode
    _ensure_loop()

    if not IS_PI or pixels is None:
        print(f"Simulated LED color: ({r}, {g}, {b})")
        return {"simulated": True, "r": r, "g": g, "b": b}

    with _lock:
        current_color = (r, g, b)
        current_mode = "static"

    return {"simulated": False, "r": r, "g": g, "b": b}

def _kelvin_to_rgb(k):
    k = k / 100.0

    if k <= 66:
        r = 255
    else:
        r = 329.698727446 * ((k - 60) ** -0.1332047592)
        r = max(0, min(255, r))

    if k <= 66:
        g = 99.4708025861 * math.log(k) - 161.1195681661
    else:
        g = 288.1221695283 * ((k - 60) ** -0.0755148492)
    g = max(0, min(255, g))

    if k >= 66:
        b = 255
    elif k <= 19:
        b = 0
    else:
        b = 138.5177312231 * math.log(k - 10) - 305.0447927307
    b = max(0, min(255, b))

    return (int(r), int(g), int(b))

def set_mode(mode):
    global current_mode
    _ensure_loop()

    if not IS_PI or pixels is None:
        return {"simulated": True, "mode": mode}

    with _lock:
        current_mode = mode

    return {"simulated": False, "mode": "unassigned"}
