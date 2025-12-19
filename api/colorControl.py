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

            st = globals().get("_aurora_v4")
            if st is None or mode != last_mode or st.get("n") != n:
                st = {
                    "n": n,
                    "t_last": t,
                    "p": random.uniform(0.0, 6.0),
                    "d1": random.uniform(0.010, 0.020),
                    "d2": random.uniform(-0.018, -0.010),
                    "d3": random.uniform(0.007, 0.014),
                    "warp": random.uniform(0.10, 0.18),
                    "shear": random.uniform(-0.40, 0.40),
                    "energy": random.uniform(0.65, 0.85),
                    "energy_target": random.uniform(0.70, 0.95),
                    "event": 0.0,
                    "event_t": 0.0,
                    "event_dur": 0.0,
                    "event_amp": 0.0,
                    "prev": [(0, 0, 0)] * n,
                    "blobs": [
                        {"c": random.uniform(0.0, 1.0), "w": random.uniform(0.08, 0.18), "v": random.uniform(-0.06, 0.06), "h": random.uniform(0.0, 6.0)},
                        {"c": random.uniform(0.0, 1.0), "w": random.uniform(0.06, 0.14), "v": random.uniform(-0.08, 0.08), "h": random.uniform(0.0, 6.0)},
                        {"c": random.uniform(0.0, 1.0), "w": random.uniform(0.05, 0.12), "v": random.uniform(-0.10, 0.10), "h": random.uniform(0.0, 6.0)},
                    ],
                }
                globals()["_aurora_v4"] = st

            dt = t - st["t_last"]
            if dt < 0.0:
                dt = 0.0
            if dt > 0.06:
                dt = 0.06
            st["t_last"] = t

            def _clamp01(v):
                return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)

            def _smooth01(x):
                x = _clamp01(x)
                return x * x * (3.0 - 2.0 * x)

            def _gauss(d, w):
                return math.exp(-(d * d) / max(1e-6, 2.0 * w * w))

            if random.random() < 0.020 * dt:
                st["energy_target"] = random.uniform(0.65, 1.00)
            st["energy"] += (st["energy_target"] - st["energy"]) * (0.55 * dt)
            st["energy"] = max(0.50, min(1.0, st["energy"]))

            if random.random() < 0.010 * dt:
                st["shear"] += random.uniform(-0.20, 0.20)
                st["shear"] = max(-0.75, min(0.75, st["shear"]))

            if random.random() < 0.020 * dt:
                st["d1"] += random.uniform(-0.0025, 0.0025)
                st["d2"] += random.uniform(-0.0025, 0.0025)
                st["d3"] += random.uniform(-0.0020, 0.0020)
                st["d1"] = max(0.006, min(0.030, st["d1"]))
                st["d2"] = max(-0.030, min(-0.006, st["d2"]))
                st["d3"] = max(0.004, min(0.022, st["d3"]))

            if st["event_dur"] <= 0.0 and random.random() < 0.0060 * dt:
                st["event_dur"] = random.uniform(2.2, 5.5)
                st["event_t"] = 0.0
                st["event_amp"] = random.uniform(0.45, 1.10)

            if st["event_dur"] > 0.0:
                st["event_t"] += dt
                u = st["event_t"] / st["event_dur"]
                if u >= 1.0:
                    st["event_dur"] = 0.0
                    st["event_t"] = 0.0
                    st["event"] = 0.0
                else:
                    st["event"] = st["event_amp"] * (math.sin(math.pi * u) ** 1.3)
            else:
                st["event"] = 0.0

            st["p"] += 0.65 * dt

            d1, d2, d3 = st["d1"], st["d2"], st["d3"]
            warp_amp = st["warp"]
            shear = st["shear"]

            base_energy = 0.75 + 0.55 * st["energy"]
            substorm = st["event"]

            base_green = (10.0, 255.0, 45.0)
            cyan_edge  = (20.0, 210.0, 255.0)
            deep_blue  = (5.0, 35.0, 180.0)
            pink       = (255.0, 35.0, 175.0)
            purple     = (175.0, 55.0, 255.0)
            warm       = (255.0, 200.0, 55.0)

            raw = [(0.0, 0.0, 0.0)] * n

            blobs = st["blobs"]
            for b in blobs:
                b["h"] += dt
                if b["h"] > 1.0:
                    b["h"] = 0.0
                    b["v"] += random.uniform(-0.05, 0.05)
                    b["v"] = max(-0.14, min(0.14, b["v"]))
                    b["w"] += random.uniform(-0.03, 0.03)
                    b["w"] = max(0.05, min(0.22, b["w"]))
                b["c"] += b["v"] * dt
                if b["c"] < -0.2:
                    b["c"] = 1.2
                elif b["c"] > 1.2:
                    b["c"] = -0.2

            for i in range(n):
                x = i / float(n - 1)

                warp = warp_amp * (
                    0.55 * math.sin(2 * math.pi * (0.16 * x + d3 * t) + 1.1 + 0.25 * math.sin(0.09 * t + 0.4))
                    + 0.45 * math.sin(2 * math.pi * (0.33 * x - 0.70 * d3 * t) + 2.2 + 0.22 * math.sin(0.07 * t + 2.1))
                )
                xw = x + warp + shear * (x - 0.5) * 0.10

                curtain = (
                    0.50
                    + 0.34 * math.sin(2 * math.pi * (0.55 * xw + d1 * t) + 0.8 + 0.22 * math.sin(0.05 * t + 1.1))
                    + 0.22 * math.sin(2 * math.pi * (1.05 * xw + d2 * t) + 2.1 + 0.18 * math.sin(0.04 * t + 2.4))
                    + 0.12 * math.sin(2 * math.pi * (0.26 * xw - 0.60 * d1 * t) + 3.5 + 0.14 * math.sin(0.035 * t + 0.7))
                )
                curtain = _clamp01(curtain)
                curtain = _smooth01((curtain - 0.08) / 0.92)

                folds = (
                    0.50
                    + 0.26 * math.sin(2 * math.pi * (1.55 * xw - 1.9 * d1 * t) + 1.0 + st["p"])
                    + 0.20 * math.sin(2 * math.pi * (2.55 * xw + 1.4 * d2 * t) + 2.8 - 0.55 * st["p"])
                    + 0.14 * math.sin(2 * math.pi * (3.30 * xw - 1.1 * d3 * t) + 0.3 + 0.20 * math.sin(0.045 * t + 1.7))
                )
                folds = _clamp01(folds)
                folds = _smooth01((folds - 0.14) / 0.86)
                folds = folds ** 1.10

                ray_f = 4.0 + 6.5 * _smooth01(0.20 + 0.80 * curtain)
                rays = 0.5 + 0.5 * math.sin(2 * math.pi * (ray_f * xw - 0.020 * t) + 4.8 * folds + 1.4 * curtain)
                rays = _clamp01(rays)
                rays = _smooth01((rays - 0.32) / 0.68)
                rays = rays ** 1.25

                I = (0.12 + 0.88 * curtain) * (0.25 + 0.75 * folds) * (0.35 + 0.65 * rays)
                I *= base_energy * (1.0 + 1.05 * substorm)
                I = _clamp01(I)
                I = I ** 0.78

                edge = _smooth01((rays - 0.22) / 0.78)

                hue_mix = 0.5 + 0.5 * math.sin(2 * math.pi * (0.14 * xw + 0.0028 * t) + 0.8 + 0.35 * st["p"])
                hue_mix = _clamp01(hue_mix)
                hue_mix = _smooth01(hue_mix)

                gR = base_green[0] * (1.0 - 0.40 * hue_mix) + cyan_edge[0] * (0.34 * hue_mix) + deep_blue[0] * (0.06 * edge)
                gG = base_green[1] * (1.0 - 0.32 * hue_mix) + cyan_edge[1] * (0.28 * hue_mix) + deep_blue[1] * (0.04 * edge)
                gB = base_green[2] * (1.0 - 0.22 * hue_mix) + cyan_edge[2] * (0.38 * hue_mix) + deep_blue[2] * (0.18 * edge)

                bloom_field = 0.0
                for b in blobs:
                    d = xw - b["c"]
                    d = d - math.floor(d + 0.5)
                    bloom_field += _gauss(d, b["w"])
                bloom_field = _clamp01(bloom_field / 2.2)

                activity = _smooth01((I - 0.06) / 0.94)

                pink_w = activity * _smooth01((bloom_field - 0.18) / 0.82) * (0.55 + 0.70 * substorm)
                purple_w = activity * _smooth01((bloom_field - 0.22) / 0.78) * (0.40 + 0.85 * substorm) * (0.35 + 0.65 * edge)
                warm_w = activity * _smooth01((bloom_field - 0.30) / 0.70) * (0.18 + 1.10 * substorm)

                pink_w = _clamp01(2.6 * pink_w)
                purple_w = _clamp01(2.2 * purple_w)
                warm_w = _clamp01(1.6 * warm_w)

                keep = _clamp01(1.0 - 0.65 * (pink_w + purple_w + warm_w))

                R = gR * keep + pink[0] * pink_w + purple[0] * purple_w + warm[0] * warm_w
                G = gG * keep + pink[1] * pink_w + purple[1] * purple_w + warm[1] * warm_w
                B = gB * keep + pink[2] * pink_w + purple[2] * purple_w + warm[2] * warm_w

                R *= I
                G *= I
                B *= I

                raw[i] = (R, G, B)

            w0, w1, w2, w3 = 1, 6, 15, 20
            denom = float(w0 + w1 + w2 + w3 + w2 + w1 + w0)
            blur = [(0.0, 0.0, 0.0)] * n
            for i in range(n):
                r0, g0, b0 = raw[max(0, i - 3)]
                r1, g1, b1 = raw[max(0, i - 2)]
                r2, g2, b2 = raw[max(0, i - 1)]
                r3, g3, b3 = raw[i]
                r4, g4, b4 = raw[min(n - 1, i + 1)]
                r5, g5, b5 = raw[min(n - 1, i + 2)]
                r6, g6, b6 = raw[min(n - 1, i + 3)]
                r = (w0 * r0 + w1 * r1 + w2 * r2 + w3 * r3 + w2 * r4 + w1 * r5 + w0 * r6) / denom
                g = (w0 * g0 + w1 * g1 + w2 * g2 + w3 * g3 + w2 * g4 + w1 * g5 + w0 * g6) / denom
                b = (w0 * b0 + w1 * b1 + w2 * b2 + w3 * b3 + w2 * b4 + w1 * b5 + w0 * b6) / denom
                blur[i] = (r, g, b)

            def _gamma(v):
                v = max(0.0, min(255.0, v))
                return 255.0 * ((v / 255.0) ** 1.80)

            a = 1.0 - math.exp(-dt / 0.22)
            if a < 0.05:
                a = 0.05
            if a > 0.18:
                a = 0.18

            prev = st["prev"]
            out = [(0, 0, 0)] * n
            for i in range(n):
                pr, pg, pb = prev[i]
                nr, ng, nb = blur[i]
                rr = pr + (nr - pr) * a
                gg = pg + (ng - pg) * a
                bb = pb + (nb - pb) * a
                rr = int(_gamma(rr))
                gg = int(_gamma(gg))
                bb = int(_gamma(bb))
                out[i] = (rr, gg, bb)
                pixels[i] = out[i]

            st["prev"] = out

            pixels.show()
            sleep_ms = 20
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
