import json
import random
import time

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

def set_color(cmd):
    col = json.dumps(cmd.payload)
    colDict = json.loads(col)
    r, g, b = colDict['r'], colDict['g'], colDict['b']
    
    if not IS_PI or pixels is None:
        print(f"Simulated LED color: ({r}, {g}, {b})")
        return {"simulated": True, "r": r, "g": g, "b": b}

    for i in range(NUM_LEDS):
        pixels[i] = (r, g, b)
    pixels.show()

    return {"simulated": False, "r": r, "g": g, "b": b}


def set_mode(cmd):
    payload = cmd.payload
    mode = payload.get("mode")
    
    if not IS_PI or pixels is None:
        return {"simulated": True, "mode": mode}
    
    if mode == "off":
        off()
        return {"simulated": False, "mode": mode}
    
    return {"simulated": False, "mode": "unassigned"}
    

def fire():
    r = 255
    g = 96
    b = 12

    while(1):
        for i in range(NUM_LEDS):
            flicker = random.randint(0, 40)
            r1 = r-flicker
            g1 = g-flicker
            b1 = g-flicker
            if(r1 < 0):
                r1 = 0
            elif(g1 < 0):
                g1 = 0
            elif(b1 < 0):
                b1 = 0
            pixels[i] = (r1, g1, 0)

        pixels.show()
        rand = random.randint(50, 150)
        time.sleep(rand/1000)

def off():
    for i in range(NUM_LEDS):
        pixels[i] = (0, 0, 0)
    
    return {"Strip Power Off": True}