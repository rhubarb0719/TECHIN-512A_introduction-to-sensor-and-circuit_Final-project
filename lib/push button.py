import time
import board
from digitalio import DigitalInOut, Direction, Pull
import neopixel

# ---------- 按钮设置 ----------
btn = DigitalInOut(board.D2)      # 换成你实际接按钮的脚
btn.direction = Direction.INPUT
btn.pull = Pull.UP                # 内部上拉，没按时为 True，按下接地为 False

# ---------- NeoPixel 设置 ----------
pixel_pin = board.D0             # 换成你接 NeoPixel Din 的脚
num_pixels = 1
pixels = neopixel.NeoPixel(pixel_pin, num_pixels,
                           brightness=0.3, auto_write=True)

# 五种要循环的颜色（你可以自己换）
RED   = (255, 0, 0)
BLUE  = (0, 0, 255)
GREEN = (0, 255, 0)
YELL  = (255, 255, 0)
CYAN  = (0, 255, 255)

colors = [RED, BLUE, GREEN, YELL, CYAN]

# 当前颜色索引
color_index = 0
pixels[0] = colors[color_index]

# 按钮前一次状态（用来检测“边沿”）
prev_state = btn.value  # True = 未按, False = 按下

while True:
    cur_state = btn.value

    # 检测状态变化（按下或松开）
    if cur_state != prev_state:
        # 简单防抖：稍微等一下再读一次
        time.sleep(0.02)
        cur_state = btn.value

        if cur_state != prev_state:
            prev_state = cur_state

            # 只在“按下”的瞬间触发（高 → 低）
            if cur_state is False:   # 按钮被按下
                # 切换到下一种颜色
                color_index = (color_index + 1) % len(colors)
                pixels[0] = colors[color_index]
                print("Button pressed, color index:", color_index)

    time.sleep(0.01)

