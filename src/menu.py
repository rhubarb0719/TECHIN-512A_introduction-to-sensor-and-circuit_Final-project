import time
import board
import busio
import displayio
import terminalio
import digitalio

from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306

from rotary_encoder import RotaryEncoder

# ---------- 状态常量 ----------
STATE_MENU = 0        # 选择难度
STATE_INIT_GAME = 1   # 确认难度后（现在先占位）

DIFFICULTIES = ["EASY", "MEDIUM", "HARD"]

# ---------- OLED 初始化（用你之前确认可用的方式） ----------
displayio.release_displays()

i2c = busio.I2C(board.SCL, board.SDA)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

main_group = displayio.Group()
display.root_group = main_group

# 顶部提示文字
status_label = label.Label(terminalio.FONT, text="", x=5, y=8)
main_group.append(status_label)

# 三行菜单文字
line_y_positions = [24, 38, 52]
menu_labels = []
for i in range(3):
    lbl = label.Label(terminalio.FONT, text="", x=12, y=line_y_positions[i])
    menu_labels.append(lbl)
    main_group.append(lbl)

# ---------- Rotary Encoder 初始化 ----------
# 先用你测试代码里的参数；如果太不灵敏，可以之后把 pulses_per_detent 改小
encoder = RotaryEncoder(
    board.D0,           # CLK
    board.D1,           # DT
    debounce_ms=2,
    pulses_per_detent=2
)

last_position = encoder.position  # 上一次的 position

# ---------- 按钮初始化 ----------
# 右侧 VCC 脚接到 D2，另一脚接 GND
button = digitalio.DigitalInOut(board.D2)
button.switch_to_input(pull=digitalio.Pull.UP)  # 内部上拉：未按 True，按下 False
last_button_value = button.value

# ---------- 状态变量 ----------
state = STATE_MENU
selected_index = 0        # 0=EASY,1=MEDIUM,2=HARD
init_start_time = 0.0


# ---------- UI 函数 ----------
def draw_menu(selected: int) -> None:
    """在 OLED 上绘制难度菜单"""
    status_label.text = "Select Difficulty"
    for i, name in enumerate(DIFFICULTIES):
        prefix = "> " if i == selected else "  "
        menu_labels[i].text = prefix + name


def show_starting_screen(selected: int) -> None:
    """按下确认后的提示界面"""
    diff_name = DIFFICULTIES[selected]
    status_label.text = "Let's: " + diff_name
    for lbl in menu_labels:
        lbl.text = ""


# 先画一次菜单
draw_menu(selected_index)

# ---------- 主循环 ----------
while True:
    now = time.monotonic()

    # 1. 处理旋转（使用 encoder.update()）
    changed = encoder.update()
    if changed:
        position = encoder.position

        if position != last_position:
            delta = position - last_position
            # 顺时针 / 逆时针只移动一格菜单
            if delta > 0:
                selected_index += 1
            elif delta < 0:
                selected_index -= 1

            # 限制在 0~len-1
            if selected_index < 0:
                selected_index = 0
            if selected_index > len(DIFFICULTIES) - 1:
                selected_index = len(DIFFICULTIES) - 1

            last_position = position

            if state == STATE_MENU:
                draw_menu(selected_index)

            # 调试：你可以在串口里看看 position 变化
            print("Encoder position:", position, " selected:", selected_index)

    # 2. 处理按钮（检测“刚刚按下”的瞬间）
    raw = button.value           # True = 没按，False = 按下
    button_pressed = (last_button_value is True) and (raw is False)
    last_button_value = raw

    # 3. 状态机
    if state == STATE_MENU:
        if button_pressed:
            # 按下确认难度
            show_starting_screen(selected_index)
            init_start_time = now
            state = STATE_INIT_GAME

    elif state == STATE_INIT_GAME:
        # 先简单停 2 秒，之后在这里做真正的游戏初始化
        if now - init_start_time > 2.0:
            state = STATE_MENU
            draw_menu(selected_index)

    time.sleep(0.001)

