import json
import random
import time
import threading

try:
    import board
    import neopixel
    IS_PI = True

except ImportError:
    IS_PI = False
    board = None
    neopixel = None

NUM_LEDS = 8
pixels = None

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
            for i in range(NUM_LEDS):
                idx = (int(i * 256 / NUM_LEDS) + phase) & 255
                pixels[i] = _wheel(idx)
            pixels.show()
            phase = (phase + 1) % 256


        elif mode == "off":
            if mode != last_mode:
                for i in range(NUM_LEDS):
                    pixels[i] = (0, 0, 0)
                pixels.show()

        last_mode = mode
        last_color = color
        time.sleep(0.03)

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


def set_mode(mode):
    global current_mode
    _ensure_loop()
    
    if not IS_PI or pixels is None:
        return {"simulated": True, "mode": mode}
    
    with _lock:
        current_mode = mode 
    
    return {"simulated": False, "mode": "unassigned"}
    

# def fire():
#     r = 255
#     g = 96
#     b = 12

#     while(1):
#         for i in range(NUM_LEDS):
#             flicker = random.randint(0, 40)
#             r1 = r-flicker
#             g1 = g-flicker
#             b1 = g-flicker
#             if(r1 < 0):
#                 r1 = 0
#             elif(g1 < 0):
#                 g1 = 0
#             elif(b1 < 0):
#                 b1 = 0
#             pixels[i] = (r1, g1, 0)

#         pixels.show()
#         rand = random.randint(50, 150)
#         time.sleep(rand/1000)

# def off():
#     for i in range(NUM_LEDS):
#         pixels[i] = (0, 0, 0)
    
#     pixels.show()
#     return {"Strip Power Off": True}