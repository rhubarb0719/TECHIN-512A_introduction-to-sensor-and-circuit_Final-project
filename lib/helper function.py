import time
import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306
import adafruit_adxl34x

displayio.release_displays()

i2c = busio.I2C(board.SCL, board.SDA)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

accelerometer = adafruit_adxl34x.ADXL345(i2c)


def displayText(line1="", line2="", line3="", line4=""):

     #create a displayio group
    main_group = displayio.Group()

    lines = [line1, line2, line3, line4]

    y_start = 4         
    line_spacing = 14 

    #enumerate through the input arguments creating label.Label objects for each
    for idx, text in enumerate(lines):
        if not text:  
            continue

        y = y_start + idx * line_spacing

        text_label = label.Label(
            terminalio.FONT,
            text=text,
            color=0xFFFFFF
        )
        text_label.anchor_point = (0.5, 0.0)
        text_label.anchored_position = (display.width // 2, y)

        #add each Label object to the displayio group
        main_group.append(text_label)

    # display the displayio group to the OLED
    display.root_group = main_group


displayText("119 Save my life! :)")
time.sleep(5)

while True:
    x, y, z = accelerometer.acceleration

    displayText(
        f"X-axis: {x:.3f}",
        f"Y-axis: {y:.3f}",
        f"Z-axis: {z:.3f}",
    )

    time.sleep(0.1)

