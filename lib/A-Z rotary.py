import time
import board
from rotary_encoder import RotaryEncoder

import busio
import displayio
import terminalio
from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306

# Release any previously used display resources
displayio.release_displays()

# Initialize I2C and SSD1306 OLED display (128x64)
i2c = busio.I2C(board.SCL, board.SDA)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Create the main display group to hold all visual elements
main_group = displayio.Group()

# Start with letter "A" (position 0)
text_layer = label.Label(terminalio.FONT, text="A", x=62, y=30)
main_group.append(text_layer)

# Show the display group
display.root_group = main_group

# Initialize the rotary encoder on pins D0 and D1
encoder = RotaryEncoder(board.D0, board.D1, debounce_ms=3, pulses_per_detent=3)


last_index = 0

def pos_to_letter_index(pos: int) -> int:
    return pos % 26

def index_to_letter(idx: int) -> str:
    return chr(ord('A') + idx)

while True:
    changed = encoder.update()
            
    # Only update if letter actually changed
    if changed:
        idx = pos_to_letter_index(encoder.position)
        if idx != last_index:
            letter = index_to_letter(idx)
            text_layer.text = letter
            last_index = idx
            print("Letter:", letter)
        
    # Small delay to avoid CPU overload
    time.sleep(0.001)


