import time
import board
from rotary_encoder import RotaryEncoder

# change pins to the pins you're using
# if position does not increment properly swap pins (Ex. Using pins below, put D2 first and D3 second)
encoder = RotaryEncoder(board.D0, board.D1, debounce_ms=3, pulses_per_detent=3)

while True:
    changed = encoder.update()
    if changed:
        #d = encoder.get_delta()
        print("Position:", encoder.position)
        
    time.sleep(0.001)  
