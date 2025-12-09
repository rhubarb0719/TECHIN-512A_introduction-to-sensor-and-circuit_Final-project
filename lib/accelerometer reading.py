import time
import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306
import adafruit_adxl34x
import i2cdisplaybus

displayio.release_displays()

i2c = board.I2C()

display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

main_group = displayio.Group()
display.root_group = main_group

text_layer = label.Label(terminalio.FONT, text="X:0.00\nY:0.00\nZ:0.00")
text_layer.anchor_point = (0.5, 0.5)
text_layer.anchored_position = (64, 32)
main_group.append(text_layer)

accelerometer = adafruit_adxl34x.ADXL345(i2c)

alpha = 0.2
fx = fy = fz = None

while True:
    x, y, z = accelerometer.acceleration

    if fx is None:
        fx, fy, fz = x, y, z
    else:
        fx = (1 - alpha) * fx + alpha * x
        fy = (1 - alpha) * fy + alpha * y
        fz = (1 - alpha) * fz + alpha * z

    text = f"X:{fx:.2f}\nY:{fy:.2f}\nZ:{fz:.2f}"
    print(text)
    text_layer.text = text

    time.sleep(0.1)

