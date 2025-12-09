import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306
 
# Releases any currently active display so we can initialize a new one
displayio.release_displays()

# Creates an I2C bus using the default SCL and SDA pins
i2c = busio.I2C(board.SCL, board.SDA)

# Sets up the I2C display bus with the SSD1306's I2C address (0x3C is common)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)

# Initializes the SSD1306 OLED display with a resolution of 128x64 pixels
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Creates a display group to hold graphical elements
main_group = displayio.Group()

# Creates a text label with the message “Yilu^-^” at position (x=45, y=30)
text_layer = label.Label(terminalio.FONT, text="Yilu^-^", x=45, y=30)

# Adds the text label to the display group
main_group.append(text_layer)
 
# Sets the display group as the root group to show on the OLED screen
display.root_group = main_group
