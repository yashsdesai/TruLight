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

NUM_LEDS = 60
pixels = None
LAMP_COUNT = 2

if IS_PI:
    pixels = neopixel.NeoPixel(board.D18, NUM_LEDS, auto_write=False)

current_mode = "static"
current_color = (0, 0, 0)
_lock = threading.Lock()
_loop_started = False

# store prev state for test
prev_mode = None
prev_color = (0, 0, 0)

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
    era_centers = []
    era_lamp_level = []
    era_lamp_target = []
    era_temps = []
    era_surge_frames = 0
    era_surge_total = 0
    era_surge_strength = 0.0
    era_buzz_phase = 0.0

    cin_initialized = False
    cin_centers = []
    cin_lamp_level = []
    cin_lamp_target = []
    cin_temps = []
    cin_surge_frames = 0
    cin_surge_total = 0
    cin_surge_strength = 0.0
    cin_phase = 0.0

    test_initialized = False
    test_start = 0.0
    test_duration = 0.5

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
            time.sleep(sleep_ms / 1000.0)
            last_mode = mode
            last_color = color
            continue

        elif mode == "eras":
            if not era_initialized:
                era_centers = []
                era_lamp_level = []
                era_lamp_target = []
                era_temps = []
                for lamp_idx in range(LAMP_COUNT):
                    center = (lamp_idx + 0.5) / float(LAMP_COUNT)
                    era_centers.append(center)
                    level = random.uniform(0.8, 1.0)
                    era_lamp_level.append(level)
                    era_lamp_target.append(level)
                    base_temp = 2200.0 + (lamp_idx - (LAMP_COUNT - 1) / 2.0) * 80.0
                    era_temps.append(base_temp)
                era_initialized = True

            if not IS_PI or pixels is None or not era_centers:
                sleep_ms = 40
                time.sleep(sleep_ms / 1000.0)
                last_mode = mode
                last_color = color
                continue

            era_buzz_phase += 0.25
            mains_mod = 0.97 + 0.03 * math.sin(era_buzz_phase)

            if era_surge_frames <= 0 and random.random() < 0.003:
                era_surge_total = random.randint(10, 24)
                era_surge_frames = era_surge_total
                era_surge_strength = random.uniform(-0.25, 0.15)

            if era_surge_frames > 0 and era_surge_total > 0:
                progress = (era_surge_total - era_surge_frames) / float(max(1, era_surge_total))
                surge_scale = 1.0 + era_surge_strength * math.sin(progress * math.pi)
                era_surge_frames -= 1
            else:
                surge_scale = 1.0

            lamp_r = [0] * LAMP_COUNT
            lamp_g = [0] * LAMP_COUNT
            lamp_b = [0] * LAMP_COUNT

            for idx in range(LAMP_COUNT):
                if random.random() < 0.06:
                    delta = random.uniform(-0.04, 0.04)
                    era_lamp_target[idx] = max(0.75, min(1.05, era_lamp_target[idx] + delta))
                era_lamp_level[idx] += (era_lamp_target[idx] - era_lamp_level[idx]) * 0.18

                k_base = era_temps[idx]
                k_jitter = random.gauss(0.0, 40.0)
                k = max(1900.0, min(2600.0, k_base + k_jitter))
                r, g, b = _kelvin_to_rgb(k)

                lamp_r[idx] = r
                lamp_g[idx] = g
                lamp_b[idx] = b

            radius = 0.55 / float(LAMP_COUNT)
            gamma = 1.8
            floor = 0.08

            for i in range(NUM_LEDS):
                gpos = i / float(NUM_LEDS - 1) if NUM_LEDS > 1 else 0.5
                best_idx = -1
                best_w = 0.0
                for idx, center in enumerate(era_centers):
                    d = abs(gpos - center)
                    if d >= radius:
                        continue
                    w = 1.0 - d / radius
                    w = w ** gamma
                    if w > best_w:
                        best_w = w
                        best_idx = idx

                if best_idx == -1:
                    pixels[i] = (0, 0, 0)
                else:
                    base_scale = mains_mod * surge_scale * era_lamp_level[best_idx]
                    base_scale = max(0.7, min(1.05, base_scale))
                    s = floor + (1.0 - floor) * best_w
                    s = s * base_scale
                    r = int(max(0, min(255, lamp_r[best_idx] * s)))
                    g = int(max(0, min(255, lamp_g[best_idx] * s * 0.94)))
                    b = int(max(0, min(255, lamp_b[best_idx] * s * 0.7)))
                    pixels[i] = (r, g, b)

            pixels.show()
            sleep_ms = random.randint(40, 55)
            time.sleep(sleep_ms / 1000.0)
            last_mode = mode
            last_color = color
            continue

        elif mode == "cinematic":
            if not cin_initialized:
                cin_centers = []
                cin_lamp_level = []
                cin_lamp_target = []
                cin_temps = []
                for lamp_idx in range(LAMP_COUNT):
                    center = (lamp_idx + 0.5) / float(LAMP_COUNT)
                    cin_centers.append(center)
                    level = random.uniform(0.8, 1.1)
                    cin_lamp_level.append(level)
                    cin_lamp_target.append(level)
                    base_temp = 2100.0 + (lamp_idx - (LAMP_COUNT - 1) / 2.0) * 120.0
                    cin_temps.append(base_temp)
                cin_initialized = True

            if not IS_PI or pixels is None or not cin_centers:
                sleep_ms = 40
                time.sleep(sleep_ms / 1000.0)
                last_mode = mode
                last_color = color
                continue

            cin_phase += 0.03
            vignette_shift = 0.5 + 0.1 * math.sin(cin_phase)
            global_dark = 0.35 + 0.25 * (1.0 - abs(0.5 - vignette_shift) * 2.0)

            if cin_surge_frames <= 0 and random.random() < 0.015:
                cin_surge_total = random.randint(8, 20)
                cin_surge_frames = cin_surge_total
                cin_surge_strength = random.uniform(-0.6, 0.4)

            if cin_surge_frames > 0 and cin_surge_total > 0:
                progress = (cin_surge_total - cin_surge_frames) / float(max(1, cin_surge_total))
                surge_scale = 1.0 + cin_surge_strength * math.sin(progress * math.pi)
                cin_surge_frames -= 1
            else:
                surge_scale = 1.0

            lamp_r = [0] * LAMP_COUNT
            lamp_g = [0] * LAMP_COUNT
            lamp_b = [0] * LAMP_COUNT

            for idx in range(LAMP_COUNT):
                if random.random() < 0.18:
                    delta = random.uniform(-0.18, 0.18)
                    cin_lamp_target[idx] = max(0.4, min(1.4, cin_lamp_target[idx] + delta))
                cin_lamp_level[idx] += (cin_lamp_target[idx] - cin_lamp_level[idx]) * 0.22

                k_base = cin_temps[idx]
                k_jitter = random.gauss(0.0, 90.0)
                k = max(1800.0, min(2600.0, k_base + k_jitter))
                r, g, b = _kelvin_to_rgb(k)

                lamp_r[idx] = r
                lamp_g[idx] = g
                lamp_b[idx] = b

            radius = 0.4 / float(LAMP_COUNT)
            gamma = 2.2
            floor = 0.03

            for i in range(NUM_LEDS):
                if NUM_LEDS > 1:
                    gpos = i / float(NUM_LEDS - 1)
                else:
                    gpos = 0.5

                best_idx = -1
                best_w = 0.0
                for idx, center in enumerate(cin_centers):
                    d = abs(gpos - center)
                    if d >= radius:
                        continue
                    w = 1.0 - d / radius
                    w = w ** gamma
                    if w > best_w:
                        best_w = w
                        best_idx = idx

                if best_idx == -1:
                    pixels[i] = (0, 0, 0)
                else:
                    lamp_base = cin_lamp_level[best_idx] * surge_scale
                    lamp_base = max(0.4, min(1.3, lamp_base))

                    if NUM_LEDS > 1:
                        global_profile = global_dark + (1.0 - global_dark) * (1.0 - min(1.0, abs(gpos - 0.5) * 2.0))
                    else:
                        global_profile = global_dark

                    glitch = 1.0
                    if random.random() < 0.04:
                        glitch = random.uniform(0.4, 1.5)

                    s = floor + (1.0 - floor) * best_w
                    s = s * lamp_base * global_profile * glitch

                    r = int(max(0, min(255, lamp_r[best_idx] * s)))
                    g = int(max(0, min(255, lamp_g[best_idx] * s * 0.75)))
                    b = int(max(0, min(255, lamp_b[best_idx] * s * 0.3)))
                    pixels[i] = (r, g, b)

            pixels.show()
            sleep_ms = random.randint(45, 70)
            time.sleep(sleep_ms / 1000.0)
            last_mode = mode
            last_color = color
            continue

        elif mode == "alert":
            if not IS_PI or pixels is None:
                sleep_ms = 40
                time.sleep(sleep_ms / 1000.0)
                last_mode = mode
                last_color = color
                continue

            phase += 0.12
            level = (math.sin(phase) + 1.0) / 2.0
            level = level * level
            r = int(255 * level)
            g = 0
            b = 0

            for i in range(NUM_LEDS):
                pixels[i] = (r, g, b)

            pixels.show()
            sleep_ms = 40
            time.sleep(sleep_ms / 1000.0)
            last_mode = mode
            last_color = color
            continue

        elif mode == "water":
            if not IS_PI or pixels is None:
                sleep_ms = 40
                time.sleep(sleep_ms / 1000.0)
                last_mode = mode
                last_color = color
                continue

            t = time.time()
            num_pixels = NUM_LEDS
            if num_pixels <= 1:
                pixels.show()
                sleep_ms = 40
                time.sleep(sleep_ms / 1000.0)
                last_mode = mode
                last_color = color
                continue

            base_brightness = 0.15
            caustic_strength = 0.85

            freq1 = 1.2
            freq2 = 2.7
            freq3 = 7.5

            speed1 = 0.04
            speed2 = -0.07
            speed3 = 0.18

            for i in range(num_pixels):
                x = i / float(num_pixels - 1)

                w1 = math.sin(2 * math.pi * (freq1 * x - speed1 * t))
                w2 = math.sin(2 * math.pi * (freq2 * x - speed2 * t))
                w3 = 0.4 * math.sin(2 * math.pi * (freq3 * x - speed3 * t))

                w = (w1 + w2 + w3) / 2.4
                intensity = (w * 0.5 + 0.5)
                intensity = intensity * intensity
                intensity += random.uniform(-0.03, 0.03)
                intensity = max(0.0, min(1.0, intensity))

                brightness = base_brightness + caustic_strength * intensity
                brightness = max(0.0, min(1.0, brightness))

                r_base, g_base, b_base = 0, 20, 80
                r_hi, g_hi, b_hi = 10, 180, 255

                r = int(r_base + (r_hi - r_base) * intensity)
                g = int(g_base + (g_hi - g_base) * intensity)
                b = int(b_base + (b_hi - b_base) * intensity)

                r = int(r * brightness)
                g = int(g * brightness)
                b = int(b * brightness)

                pixels[i] = (r, g, b)

            pixels.show()
            sleep_ms = 20
            time.sleep(sleep_ms / 1000.0)
            last_mode = mode
            last_color = color
            continue

        elif mode == "cove_warm":
            target_r, target_g, target_b = _kelvin_to_rgb(3200)

            if not IS_PI or pixels is None:
                last_mode = mode
                last_color = color
                time.sleep(0.04)
                continue

            if mode != last_mode:
                phase = 0

            if phase < 100:
                phase += 1
                a = phase / 100.0
                a = a * a * (3.0 - 2.0 * a)

                r = int(target_r * a)
                g = int(target_g * a)
                b = int(target_b * a)

                for i in range(NUM_LEDS):
                    pixels[i] = (r, g, b)
                pixels.show()

                sleep_ms = 25
                time.sleep(sleep_ms / 1000.0)
                last_mode = mode
                last_color = color
                continue

            for i in range(NUM_LEDS):
                pixels[i] = (target_r, target_g, target_b)
            pixels.show()

            sleep_ms = 80
            time.sleep(sleep_ms / 1000.0)
            last_mode = mode
            last_color = color
            continue
        
        elif mode == "cove_warm_test":
            target_r, target_g, target_b = _kelvin_to_rgb(2600)

            if not IS_PI or pixels is None:
                last_mode = mode
                last_color = color
                time.sleep(0.04)
                continue

            if mode != last_mode:
                phase = 0

            if phase < 100:
                phase += 1
                a = phase / 100.0
                a = a * a * (3.0 - 2.0 * a)
                a = a ** 2.2

                r = int(target_r * a)
                g = int(target_g * a)
                b = int(target_b * a)

                for i in range(NUM_LEDS):
                    pixels[i] = (r, g, b)
                pixels.show()

                sleep_ms = 25
                time.sleep(sleep_ms / 1000.0)
                last_mode = mode
                last_color = color
                continue

            for i in range(NUM_LEDS):
                pixels[i] = (target_r, target_g, target_b)
            pixels.show()

            sleep_ms = 80
            time.sleep(sleep_ms / 1000.0)
            last_mode = mode
            last_color = color
            continue

        elif mode == "aurora":
            if not IS_PI or pixels is None:
                sleep_ms = 40
                time.sleep(sleep_ms / 1000.0)
                last_mode = mode
                last_color = color
                continue

            t = time.time()
            n = NUM_LEDS
            if n <= 1:
                pixels.show()
                sleep_ms = 40
                time.sleep(sleep_ms / 1000.0)
                last_mode = mode
                last_color = color
                continue

            st = globals().get("_aurora_state")
            if st is None or mode != last_mode or st.get("n") != n:
                st = {
                    "n": n,
                    "t_last": t,
                    "phase": 0.0,
                    "dx1": random.uniform(0.0010, 0.0035),
                    "dx2": random.uniform(-0.0030, -0.0008),
                    "dx3": random.uniform(0.0006, 0.0020),
                    "h_bias": random.uniform(-0.04, 0.04),
                    "h_rate": random.uniform(0.0005, 0.0016),
                    "shear": random.uniform(-0.25, 0.25),
                    "energy": random.uniform(0.55, 0.80),
                    "energy_target": random.uniform(0.55, 0.85),
                    "event": 0.0,
                    "event_t": 0.0,
                    "event_dur": 0.0,
                    "event_amp": 0.0,
                    "pseed": [random.uniform(0.0, 2.0 * math.pi) for _ in range(n)],
                }
                globals()["_aurora_state"] = st

            dt = t - st["t_last"]
            if dt < 0.0:
                dt = 0.0
            if dt > 0.2:
                dt = 0.2
            st["t_last"] = t

            st["phase"] += 0.6 * dt

            if random.random() < 0.020:
                st["dx1"] += random.uniform(-0.00035, 0.00035)
                st["dx2"] += random.uniform(-0.00035, 0.00035)
                st["dx3"] += random.uniform(-0.00025, 0.00025)
                st["dx1"] = max(0.0004, min(0.0045, st["dx1"]))
                st["dx2"] = max(-0.0045, min(-0.0003, st["dx2"]))
                st["dx3"] = max(0.0002, min(0.0030, st["dx3"]))

            if random.random() < 0.010:
                st["shear"] += random.uniform(-0.12, 0.12)
                st["shear"] = max(-0.65, min(0.65, st["shear"]))

            if random.random() < 0.006:
                st["energy_target"] = random.uniform(0.50, 0.92)

            st["energy"] += (st["energy_target"] - st["energy"]) * (0.35 * dt)
            st["energy"] = max(0.45, min(1.0, st["energy"]))

            if st["event_dur"] <= 0.0 and random.random() < 0.0025:
                st["event_dur"] = random.uniform(2.5, 7.5)
                st["event_t"] = 0.0
                st["event_amp"] = random.uniform(0.25, 0.85)

            if st["event_dur"] > 0.0:
                st["event_t"] += dt
                u = st["event_t"] / st["event_dur"]
                if u >= 1.0:
                    st["event_dur"] = 0.0
                    st["event_t"] = 0.0
                    st["event"] = 0.0
                else:
                    st["event"] = st["event_amp"] * math.sin(math.pi * u)
            else:
                st["event"] = 0.0

            def _clamp01(v):
                return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)

            def _smooth01(x):
                x = _clamp01(x)
                return x * x * (3.0 - 2.0 * x)

            def _hsv_to_rgb(h, s, v):
                h = (h % 1.0)
                s = _clamp01(s)
                v = _clamp01(v)
                i = int(h * 6.0)
                f = h * 6.0 - i
                p = v * (1.0 - s)
                q = v * (1.0 - f * s)
                tt = v * (1.0 - (1.0 - f) * s)
                i = i % 6
                if i == 0:
                    r, g, b = v, tt, p
                elif i == 1:
                    r, g, b = q, v, p
                elif i == 2:
                    r, g, b = p, v, tt
                elif i == 3:
                    r, g, b = p, q, v
                elif i == 4:
                    r, g, b = tt, p, v
                else:
                    r, g, b = v, p, q
                return int(r * 255), int(g * 255), int(b * 255)

            dx1 = st["dx1"]
            dx2 = st["dx2"]
            dx3 = st["dx3"]
            shear = st["shear"]
            base_energy = st["energy"]
            substorm = st["event"]

            st["h_bias"] += (random.uniform(-1.0, 1.0) * 0.0025) * dt
            st["h_bias"] = max(-0.10, min(0.10, st["h_bias"]))

            st["h_rate"] += random.uniform(-0.00025, 0.00025) * dt
            st["h_rate"] = max(0.0003, min(0.0030, st["h_rate"]))

            h_shift = (st["h_rate"] * t + st["h_bias"]) % 1.0

            rgb = [(0, 0, 0)] * n

            for i in range(n):
                x = i / float(n - 1)

                warp = (
                    0.08 * math.sin(2 * math.pi * (0.14 * x + dx3 * t) + 1.2 * math.sin(0.10 * t + 0.4))
                    + 0.05 * math.sin(2 * math.pi * (0.31 * x - 0.65 * dx3 * t) + 0.9 * math.sin(0.13 * t + 2.1))
                )
                xw = x + warp + shear * (x - 0.5) * 0.06

                curtain = (
                    0.50
                    + 0.24 * math.sin(2 * math.pi * (0.55 * xw + dx1 * t) + 0.7 + 0.8 * math.sin(0.06 * t))
                    + 0.18 * math.sin(2 * math.pi * (1.05 * xw + dx2 * t) + 2.1 + 0.6 * math.sin(0.045 * t + 1.2))
                    + 0.10 * math.sin(2 * math.pi * (0.24 * xw - 0.55 * dx1 * t) + 3.4 + 0.5 * math.sin(0.03 * t + 2.2))
                )
                curtain = _clamp01(curtain)
                curtain = _smooth01((curtain - 0.16) / 0.84)
                curtain = curtain ** 1.20

                folds = (
                    0.50
                    + 0.22 * math.sin(2 * math.pi * (2.1 * xw - 2.8 * dx1 * t) + 1.3 + st["phase"])
                    + 0.14 * math.sin(2 * math.pi * (1.6 * xw + 2.1 * dx2 * t) + 2.7 - 0.6 * st["phase"])
                    + 0.08 * math.sin(2 * math.pi * (3.7 * xw - 1.7 * dx3 * t) + 0.4 + 0.4 * math.sin(0.05 * t))
                )
                folds = _clamp01(folds)
                folds = _smooth01((folds - 0.26) / 0.74)
                folds = folds ** 1.55

                ray_f = 7.0 + 10.0 * _smooth01(0.25 + 0.75 * curtain)
                rays = 0.5 + 0.5 * math.sin(2 * math.pi * (ray_f * xw - 0.060 * t) + 5.2 * folds + 1.6 * curtain + 0.35 * math.sin(0.08 * t))
                rays = _clamp01(rays)
                rays = _smooth01((rays - 0.38) / 0.62)
                rays = rays ** 2.05

                shimmer = 0.5 + 0.5 * math.sin(2 * math.pi * (18.0 * xw - 0.20 * t) + 2.4 * rays + 1.4 * folds + 0.35 * math.sin(st["pseed"][i] + 0.12 * t))
                shimmer = _clamp01(shimmer)
                shimmer = 0.78 + 0.22 * (shimmer ** 2.6)

                intensity = (0.07 + 0.93 * curtain) * (0.22 + 0.78 * folds) * (0.32 + 0.68 * rays)
                intensity *= shimmer
                intensity *= (0.55 + 0.65 * base_energy)
                intensity *= (1.0 + 0.70 * substorm)
                intensity = _clamp01(intensity)
                intensity = intensity ** 0.90

                hue_wave = (
                    0.50
                    + 0.22 * math.sin(2 * math.pi * (0.18 * xw + 0.0020 * t) + 0.7 + 0.7 * st["phase"])
                    + 0.14 * math.sin(2 * math.pi * (0.11 * xw - 0.0016 * t) + 2.1 - 0.4 * st["phase"])
                    + 0.10 * math.sin(2 * math.pi * (0.07 * xw + 0.0011 * t) + 4.4 + 0.3 * math.sin(0.05 * t))
                )
                hue_wave = _clamp01(hue_wave)

                h_green = 0.30 + 0.06 * (hue_wave - 0.5)
                h_cyan  = 0.48 + 0.08 * (hue_wave - 0.5)
                h_blue  = 0.62 + 0.06 * (hue_wave - 0.5)

                base_mix = _smooth01(0.20 + 0.80 * hue_wave)
                h0 = (1.0 - base_mix) * h_green + base_mix * h_blue
                h0 = 0.55 * h0 + 0.45 * h_cyan
                h0 = (h0 + 0.10 * (h_shift - 0.5)) % 1.0

                bloom = (
                    0.50
                    + 0.22 * math.sin(2 * math.pi * (0.16 * xw + 0.0014 * t) + 1.6 + 0.9 * st["phase"])
                    + 0.16 * math.sin(2 * math.pi * (0.09 * xw + 0.0011 * t) + 3.9 + 0.6 * math.sin(0.03 * t))
                    + 0.10 * math.sin(2 * math.pi * (0.05 * xw - 0.0009 * t) + 0.2 + 0.4 * math.sin(0.04 * t + 1.2))
                )
                bloom = _clamp01(bloom)

                activity = _smooth01((intensity - 0.38) / 0.62)
                sub = _clamp01(substorm * 1.15)

                pink_gate = activity * _smooth01((bloom - 0.46) / 0.54) * (0.35 + 0.65 * sub)
                purple_gate = activity * _smooth01((rays - 0.45) / 0.55) * _smooth01((bloom - 0.40) / 0.60) * (0.25 + 0.75 * sub)
                yellow_gate = activity * _smooth01((folds - 0.40) / 0.60) * _smooth01((bloom - 0.52) / 0.48) * (0.15 + 0.85 * sub)

                pink_gate *= 1.10
                purple_gate *= 0.90
                yellow_gate *= 0.65

                h_pink = (0.92 - 0.06 * (0.5 + 0.5 * math.sin(2 * math.pi * (0.06 * xw + 0.0012 * t) + 0.4 + 0.5 * st["phase"]))) % 1.0
                h_purple = (0.78 + 0.05 * (0.5 + 0.5 * math.sin(2 * math.pi * (0.05 * xw - 0.0010 * t) + 2.4 - 0.4 * st["phase"]))) % 1.0
                h_yellow = 0.14 + 0.03 * (0.5 + 0.5 * math.sin(2 * math.pi * (0.04 * xw + 0.0008 * t) + 1.2 + 0.3 * st["phase"]))
                h_yellow = _clamp01(h_yellow)

                h = h0
                h = (1.0 - yellow_gate) * h + yellow_gate * h_yellow
                h = (1.0 - pink_gate) * h + pink_gate * h_pink
                h = (1.0 - purple_gate) * h + purple_gate * h_purple
                h = h % 1.0

                s = 0.55 + 0.40 * _smooth01((intensity - 0.08) / 0.92)
                v = 0.10 + 0.90 * intensity
                v = v ** 0.80

                r, g, b = _hsv_to_rgb(h, s, v)
                rgb[i] = (r, g, b)

            w0, w1, w2 = 1, 3, 7
            denom = (w0 + w1 + w2 + w1 + w0)
            for i in range(n):
                r0, g0, b0 = rgb[max(0, i - 2)]
                r1, g1, b1 = rgb[max(0, i - 1)]
                r2, g2, b2 = rgb[i]
                r3, g3, b3 = rgb[min(n - 1, i + 1)]
                r4, g4, b4 = rgb[min(n - 1, i + 2)]
                r = (w0 * r0 + w1 * r1 + w2 * r2 + w1 * r3 + w0 * r4) // denom
                g = (w0 * g0 + w1 * g1 + w2 * g2 + w1 * g3 + w0 * g4) // denom
                b = (w0 * b0 + w1 * b1 + w2 * b2 + w1 * b3 + w0 * b4) // denom
                pixels[i] = (int(r), int(g), int(b))

            pixels.show()
            sleep_ms = 25
            time.sleep(sleep_ms / 1000.0)
            last_mode = mode
            last_color = color
            continue

        elif mode == "test":
            if not IS_PI or pixels is None:
                sleep_ms = 40
                time.sleep(sleep_ms / 1000.0)
                last_mode = mode
                last_color = color
                continue

            if not test_initialized:
                test_initialized = True
                test_start = time.time()

            elapsed = time.time() - test_start

            if elapsed >= test_duration:
                with _lock:
                    target_mode = prev_mode if prev_mode is not None else "off"
                    target_color = prev_color if prev_color is not None else (0, 0, 0)
                    current_mode = target_mode
                    current_color = target_color
                test_initialized = False
                sleep_ms = 10
                time.sleep(sleep_ms / 1000.0)
                last_mode = mode
                last_color = color
                continue

            phase = elapsed / test_duration
            level = math.sin(math.pi * phase)
            if level < 0.0:
                level = 0.0

            r = int(255 * level)
            g = int(255 * level)
            b = int(255 * level)

            for i in range(NUM_LEDS):
                pixels[i] = (r, g, b)

            pixels.show()
            sleep_ms = 20
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
    global current_mode, prev_color, prev_mode
    _ensure_loop()

    if not IS_PI or pixels is None:
        return {"simulated": True, "mode": mode}

    with _lock:
        if mode == "test":
            prev_mode = current_mode
            prev_color = current_color

        current_mode = mode

    return {"simulated": False, "mode": "unassigned"}
