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

# Pixels Config
NUM_LEDS = 10
pixels = None
# Only for Eras:
LAMP_COUNT = 6


if IS_PI:
    pixels = neopixel.NeoPixel(board.D18, NUM_LEDS, auto_write=False)

current_mode = "static"
current_color = (0, 0, 0)
_lock = threading.Lock()
_loop_started = False

# Use later for when you get rainbow and other cycling animations going
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

    while True:
        with _lock:
            mode = current_mode
            color = current_color

        if mode == "static":
            if mode != last_mode or color != last_color:
                r, g, b = color
                for i in range(NUM_LEDS):
                    pixels[i] = (r, g, b)
                pixels.show()

        elif mode == "fire":
            base_r, base_g, base_b = 255, 96, 12

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
            # Add logic for each decade along with choice of light (tungsten, gas, carbon, etc.)
            # Default to carbon filament ~1910s

            # -> Testing just 1910s carbon filament with lamp zones

            pass

        elif mode == "off":
            if mode != last_mode:
                for i in range(NUM_LEDS):
                    pixels[i] = (0, 0, 0)
                pixels.show()

        last_mode = mode
        last_color = color
        time.sleep(sleep_ms / 1000)

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

# Temp to color (warm light approximation)
def _kelvin_to_rgb(k):
    k = k / 100.0

    # Red
    if k <= 66:
        r = 255
    else:
        r = 329.698727446 * ((k - 60) ** -0.1332047592)
        r = max(0, min(255, r))

    # Green
    if k <= 66:
        g = 99.4708025861 * math.log(k) - 161.1195681661
    else:
        g = 288.1221695283 * ((k - 60) ** -0.0755148492)
    g = max(0, min(255, g))

    # Blue
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
    