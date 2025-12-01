import json

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
    print({"simulated": False, "r": r, "g": g, "b": b})
    return {"simulated": False, "r": r, "g": g, "b": b}
