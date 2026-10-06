#!/usr/bin/env python3
import time
import math
import random
import sys

import board
from neopixel import NeoPixel


# -------------------------------
#  CONFIG
# -------------------------------
PIXEL_PIN = board.D18
NUM_PIXELS = 150
BRIGHTNESS = 0.3  # Keep dim — 1910s lighting was *dark*
FPS_DELAY = 0.02  # ~50 FPS

# Number of virtual “lamps” along the strip
LAMP_COUNT = 6
# -------------------------------


# -------------------------------------------------------------------
#  Kelvin → RGB Conversion (warm-light approximation)
# -------------------------------------------------------------------
def kelvin_to_rgb(k):
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


# -------------------------------------------------------------------
#  Lighting Modes (historically accurate)
# -------------------------------------------------------------------

# --- Mode 1: Early 1910 Tungsten (subtle shimmer)
def tungsten_flicker(zone_index, t):
    base_k = 2300 + random.uniform(-40, 40)
    r, g, b = kelvin_to_rgb(base_k)

    flicker = (
        0.03 * math.sin(t * 1.1 + zone_index) +
        0.02 * random.uniform(-1, 1) +
        0.01 * math.sin(t * 12.3 + random.random())
    )

    brightness = max(0.70, min(1.0, 0.85 + flicker))
    return (int(r * brightness), int(g * brightness), int(b * brightness))


# --- Mode 2: Carbon-Filament Bulb (MOST COMMON c. 1910)
def carbon_filament(zone_index, t):
    base_k = 1900 + random.uniform(-80, 80)
    r, g, b = kelvin_to_rgb(base_k)

    flicker = (
        0.05 * math.sin(t * 0.6 + zone_index * 0.7) +
        0.04 * random.uniform(-1, 1)
    )

    # Rare voltage sag (historically accurate)
    if random.random() < 0.0005:
        flicker -= random.uniform(0.10, 0.20)

    brightness = max(0.50, min(1.0, 0.75 + flicker))
    return (int(r * brightness), int(g * brightness), int(b * brightness))


# --- Mode 3: Gas Mantle Lamp (breathing, jitter, impurities)
def gas_mantle(zone_index, t):
    base_k = 2500 + random.uniform(-120, 120)
    r, g, b = kelvin_to_rgb(base_k)

    # Slight green/magenta tint noise
    tint_shift = random.uniform(-8, 8)
    g = max(0, min(255, g + tint_shift))

    breathing = 0.08 * math.sin(t * random.uniform(0.7, 1.5))
    jitter = 0.04 * (random.random() - 0.5)
    flare = 0.15 if random.random() < 0.001 else 0

    brightness = max(0.40, min(1.0, 0.75 + breathing + jitter + flare))
    return (int(r * brightness), int(g * brightness), int(b * brightness))


# --- Mode 4: Candle Cluster (chaotic & soft)
def candle_flicker(zone_index, t):
    base_k = 1650 + random.uniform(-100, 100)
    r, g, b = kelvin_to_rgb(base_k)

    flicker = (
        0.20 * math.sin(t * 3.3 + random.random()) +
        0.10 * random.uniform(-1, 1) +
        0.05 * math.sin(t * 30 + random.random())
    )

    brightness = max(0.35, min(1.0, 0.65 + flicker))
    return (int(r * brightness), int(g * brightness), int(b * brightness))


# -------------------------------------------------------------------
#  Mode Selector
# -------------------------------------------------------------------
MODES = {
    "tungsten": tungsten_flicker,
    "carbon": carbon_filament,   # MOST UBIQUITOUS 1910s bar lighting
    "gas": gas_mantle,
    "candle": candle_flicker
}

DEFAULT_MODE = "carbon"


# -------------------------------------------------------------------
#  LED Setup & Lamp Zone Partitioning
# -------------------------------------------------------------------
pixels = NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)

zone_size = NUM_PIXELS // LAMP_COUNT
LAMP_ZONES = [(i * zone_size, (i + 1) * zone_size) for i in range(LAMP_COUNT)]


# -------------------------------------------------------------------
#  Main Loop
# -------------------------------------------------------------------
def run(mode_name):
    print(f"Running mode: {mode_name}")
    mode_func = MODES[mode_name]

    t0 = time.time()
    while True:
        t = time.time() - t0

        for zone_index, (start, end) in enumerate(LAMP_ZONES):
            color = mode_func(zone_index, t)

            for i in range(start, end):
                # Per-pixel micro variation to simulate natural shadow flutter
                micro = random.uniform(0.96, 1.04)
                r = int(color[0] * micro)
                g = int(color[1] * micro)
                b = int(color[2] * micro)
                pixels[i] = (r, g, b)

        pixels.show()
        time.sleep(FPS_DELAY)


# -------------------------------------------------------------------
#  CLI Handling
# -------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode not in MODES:
            print("Invalid mode. Choose from:", ", ".join(MODES.keys()))
            sys.exit(1)
    else:
        mode = DEFAULT_MODE

    run(mode)