import time
import board
from rotary_encoder import RotaryEncoder

import busio
import displayio
import terminalio
from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306

# Release any previously used display resources before initializing a new one
displayio.release_displays()

# Initialize the I2C bus and OLED display (SSD1306, 128x64)
i2c = busio.I2C(board.SCL, board.SDA)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Create the main display group (a container for all displayed elements)
main_group = displayio.Group()

# Create a text label to show the encoder position, starting at "0"
text_layer = label.Label(terminalio.FONT, text="0", x=62, y=30)
main_group.append(text_layer)

# Set the main group as the display’s root so it becomes visible
display.root_group = main_group

# Initialize the rotary encoder with pins D0 and D1
encoder = RotaryEncoder(board.D0, board.D1, debounce_ms=3, pulses_per_detent=3)

# Track the last position to avoid unnecessary display updates
last_position = encoder.position

# Main loop — constantly check for encoder rotation
while True:
    changed = encoder.update()
    if changed:
        position = encoder.position
        if position != last_position:
            text_layer.text = str(position)
            last_position = position
            print("Position:", position)
    
    # Small delay to reduce CPU usage
    time.sleep(0.001)
