import time
import board
import digitalio
import neopixel

from adafruit_debouncer import Debouncer

# -----------------------------
# 按钮设置（D9）
# -----------------------------
pin = digitalio.DigitalInOut(board.D2)
pin.direction = digitalio.Direction.INPUT
pin.pull = digitalio.Pull.UP

btn = Debouncer(pin)

# -----------------------------
# NeoPixel 设置（D10）
# -----------------------------
pixel_pin = board.D0     # 根据你的接线改
num_pixels = 1

pixels = neopixel.NeoPixel(
    pixel_pin, 
    num_pixels, 
    brightness=0.3, 
    auto_write=True
)

# 准备 5 个颜色
RED   = (255, 0, 0)
BLUE  = (0, 0, 255)
GREEN = (0, 255, 0)
YELL  = (255, 255, 0)
CYAN  = (0, 255, 255)

colors = [RED, BLUE, GREEN, YELL, CYAN]
index = 0
pixels[0] = colors[index]

# -----------------------------
# 主循环
# -----------------------------
while True:
    btn.update()

    # btn.fell = 从高到低 → 按钮按下
    if btn.fell:
        index = (index + 1) % len(colors)
        pixels[0] = colors[index]
        print("Button pressed → Color index:", index)

    time.sleep(0.01)
