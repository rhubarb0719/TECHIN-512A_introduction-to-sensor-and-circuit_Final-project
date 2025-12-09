import time
import math
import random

import board
import busio
import displayio
import terminalio
import digitalio

from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306
import adafruit_adxl34x

from rotary_encoder import RotaryEncoder

import neopixel

import pwmio # buzzer


# ---------- 状态常量 ----------
STATE_SPLASH      = 0  # 上电动画
STATE_NAME_INPUT = 1      # Splash 后先进名字输入
STATE_MENU        = 2    # 名字输入完才进菜单
STATE_INIT_LEVEL  = 3   # 初始化当前关卡
STATE_WAIT_INPUT  = 4   # 等玩家完成这一关命令序列
STATE_LEVEL_RESULT = 5  # 显示结果（成功/失败）
STATE_HS_SHOW     = 6   # 新：显示排行榜


DIFFICULTIES = ["EASY", "MEDIUM", "HARD"]

BOMB_FRAMES = [
    " ( ) ",   # 空壳
    "(@ )",    # 点火
    "(@)",     # 引线燃烧
    "( * )",   # 爆炸中
]

# ---------- 动作类型 ----------
MOVE_DIAL      = 0   # 旋转编码器
MOVE_CUT_WIRE  = 1   # 按按钮
MOVE_STEADY    = 2   # 保持静止
MOVE_SHAKE     = 3   # 摇一摇

def command_name(cmd):
    if cmd == MOVE_DIAL:
        return "DIAL"
    if cmd == MOVE_CUT_WIRE:
        return "CUT WIRE"
    if cmd == MOVE_STEADY:
        return "STEADY"
    if cmd == MOVE_SHAKE:
        return "SHAKE"
    return "UNKNOWN"

# ---------- Level 配置（按你原来的表） ----------
LEVELS = [
    # Easy: Level 1-3, commands=1, time: 5.0, 4.5, 4.0
    {"level_num": 1, "commands": 1, "time_limit": 5.0},
    {"level_num": 2, "commands": 1, "time_limit": 4.5},
    {"level_num": 3, "commands": 1, "time_limit": 4.0},
    # Medium: Level 4-6, commands=2, time: 3.2, 3.0, 2.8
    {"level_num": 4, "commands": 2, "time_limit": 3.2},
    {"level_num": 5, "commands": 2, "time_limit": 3.0},
    {"level_num": 6, "commands": 2, "time_limit": 2.8},
    # Hard: Level 7-10, commands=4, time: 3.2,3.0，2.8，2.6
    {"level_num": 7, "commands": 4, "time_limit": 3.2},
    {"level_num": 8, "commands": 4, "time_limit": 3.0},
    {"level_num": 9, "commands": 4, "time_limit": 2.8},
    {"level_num": 10,"commands": 4, "time_limit": 2.6},
]

# 各难度对应 LEVELS 的 index 范围
DIFF_RANGE = {
    "EASY":   (0, 2),   # Level 1-3
    "MEDIUM": (3, 5),   # Level 4-6
    "HARD":   (6, 9),   # Level 7-10
}

# ---------- Steady / Shake 检测参数 ----------
STEADY_DIFF_THRESH = 0.4     # m/s^2，越小越严格
STEADY_HOLD_TIME   = 0.6     # 秒，保持这么久才算成功
SHAKE_DIFF_THRESH  = 6.0     # m/s^2，超过这个认为是摇动

# 低通滤波参数（为了过滤加速度噪声）
FILTER_ALPHA = 0.4           # 0~1，越小越平滑
filtered_diff = 0.0          # EMA 的初始值

# ---------- NeoPixel 设置 ----------
NEOPIXEL_PIN = board.D7      # 把这个改成你接 NeoPixel 的引脚
NUM_PIXELS   = 1             # 灯珠数量，改成你实际用的个数

pixels = neopixel.NeoPixel(NEOPIXEL_PIN, NUM_PIXELS, brightness=0.3, auto_write=True)

# 呼吸灯参数
breathe_phase = 0.0          # 用来累积时间
BREATHE_SPEED = 2.0          # 速度系数，越大呼吸越快

# ---------- Buzzer 初始化 ----------
BUZZER_PIN = board.D6  # 换成你实际接的引脚

buzzer = pwmio.PWMOut(
    BUZZER_PIN,
    duty_cycle=0,          # 先关掉
    frequency=440,         # 初始频率
    variable_frequency=True
)

# ---------- OLED 初始化 ----------
displayio.release_displays()

i2c = busio.I2C(board.SCL, board.SDA)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

main_group = displayio.Group()
display.root_group = main_group

status_label = label.Label(terminalio.FONT, text="", x=2, y=10)
main_group.append(status_label)

center_label = label.Label(terminalio.FONT, text="", x=6, y=36)
main_group.append(center_label)

bomb_label = label.Label(terminalio.FONT, text="", x=90, y=36)
main_group.append(bomb_label)

# 菜单4行
line_y_positions = [18, 30, 42, 54]
menu_labels = []
for i in range(4):
    lbl = label.Label(terminalio.FONT, text="", x=8, y=line_y_positions[i])
    menu_labels.append(lbl)
    main_group.append(lbl)

# ---------- Splash 动画用的图形元素 ----------
# 做一个 16x64 的白色竖条，当作扫描条
splash_bar_bitmap = displayio.Bitmap(16, 64, 2)         # 2 个颜色：0=黑，1=白
splash_bar_palette = displayio.Palette(2)
splash_bar_palette[0] = 0x000000
splash_bar_palette[1] = 0xFFFFFF

# 把这个小 bitmap 填成全白
for x in range(16):
    for y in range(64):
        splash_bar_bitmap[x, y] = 1

# 创建 TileGrid，把它一开始放在屏幕外面左边（x = -16）
splash_bar = displayio.TileGrid(
    splash_bar_bitmap,
    pixel_shader=splash_bar_palette,
    x=-16,
    y=0
)

# 加到 main_group 里
main_group.append(splash_bar)


# ---------- Rotary Encoder ----------
encoder = RotaryEncoder(
    board.D0,  # CLK
    board.D1,  # DT
    debounce_ms=6,
    pulses_per_detent=3,
)
last_position = encoder.position

# ---------- 按钮 ----------
button = digitalio.DigitalInOut(board.D2)
button.switch_to_input(pull=digitalio.Pull.UP)
last_button_value = button.value

# ---------- ADXL345 ----------
accel = adafruit_adxl34x.ADXL345(i2c)

baseline_x = 0.0
baseline_y = 0.0
baseline_z = 9.8

def calibrate_baseline(samples=20, delay=0.01):
    """简单求平均，作为当前姿态的基线"""
    global baseline_x, baseline_y, baseline_z
    sx = sy = sz = 0.0
    for _ in range(samples):
        x, y, z = accel.acceleration
        sx += x
        sy += y
        sz += z
        time.sleep(delay)
    baseline_x = sx / samples
    baseline_y = sy / samples
    baseline_z = sz / samples

def accel_diff_mag_filtered():
    """返回经过简单低通滤波后的差值长度"""
    global filtered_diff
    x, y, z = accel.acceleration
    dx = x - baseline_x
    dy = y - baseline_y
    dz = z - baseline_z
    raw = math.sqrt(dx*dx + dy*dy + dz*dz)

    # 一阶低通滤波：filtered = α*raw + (1-α)*prev
    filtered_diff = FILTER_ALPHA * raw + (1.0 - FILTER_ALPHA) * filtered_diff
    return filtered_diff

# ---------- Score ----------
score = 0
POINT_PER_COMMAND = 10   # 每个动作 +10 分
POINT_PER_LEVEL   = 50   # 通关一个 level +50 分

# ---------- High Score ----------
HIGHSCORE_FILE = "highscores.txt"
MAX_HISCORES   = 3

highscores = []  # [{"name": "AAA", "score": 123}, ...]

# ---------- 当前玩家名字（本次上电周期内一直使用） ----------
player_initials = ["A", "A", "A"]   # 编辑用
player_pos = 0                      # 当前在编辑第几位 (0/1/2)
player_last_position = 0           # Rotary 在名字编辑状态下的 position 记录
current_player_name = "AAA"        # 真正用于记分的名字

# ---------- 新增：Splash 动画计时 ------------
splash_start_time = 0.0

# 命令序列相关
current_sequence = []        # [MOVE_...]
required_commands = 0        # len(current_sequence)
current_cmd_index = 0        # 正在执行的命令的 index

# Steady 检测用
steady_start_time = None     # 开始进入“足够稳定”的时间戳（用于累计）

# ---------- 状态变量 ----------
state = STATE_SPLASH          # 开机先进 Splash（正确）

# 主菜单光标：0=Player, 1=EASY, 2=MEDIUM, 3=HARD
selected_menu_index = 1        # 默认选 EASY

# 难度索引：0=EASY, 1=MEDIUM, 2=HARD
selected_diff_index = 0        # 只在开始游戏时由 selected_menu_index 决定

current_level_index = 0        # LEVELS 的 index
current_level_num = 1

# 默认 time_limit 用第一个关卡（但实际开始时会重新赋值）
time_limit = LEVELS[0]["time_limit"]

level_start_time = 0.0
result_is_success = False


# -------- UI function --------
def clear_menu():
    for lbl in menu_labels:
        lbl.text = ""

def draw_menu(selected: int) -> None:
    clear_menu()
    status_label.text = "Main Menu"
    center_label.text = ""

    pixels_solid((0, 0, 40))

    # 0: Player 行
    prefix = "> " if selected == 0 else "  "
    menu_labels[0].text = prefix + "Player: {}".format(current_player_name)

    # 1~3: 难度行
    for i, name in enumerate(DIFFICULTIES):
        row_index = i + 1
        prefix = "> " if selected == row_index else "  "
        menu_labels[row_index].text = prefix + name


def show_level_intro():
    clear_menu()
    diff_name = DIFFICULTIES[selected_diff_index]
    status_label.text = "{}  Lv{}".format(diff_name, current_level_num)  # Show current score on the screen
    center_label.text = "Cmds:{} Time:{:.1f}s  Score:{}".format(
        required_commands, time_limit, score
    )

    pixels_solid((0, 80, 0))
    
def show_level_play(remaining: float):
    clear_menu()
    cmd_idx = current_cmd_index
    cmd = current_sequence[cmd_idx]
    cmd_text = command_name(cmd)

    status_label.text = "Lv{} {}/{} {:.1f}s".format(
        current_level_num,
        cmd_idx + 1,
        required_commands,
        max(0, remaining),
    )
    center_label.text = "{}  Score:{}".format(cmd_text, score)

    # 🔵 不同动作不同颜色
    pixels_for_command(cmd)

def show_level_result(success: bool, is_last_level: bool):
    clear_menu()
    if success:
        if is_last_level:
            status_label.text = "YOU WIN!"
            center_label.text = "Score: {}".format(score)
            pixels_flash((0, 255, 0), times=4, delay=0.1)
        else:
            status_label.text = "Level {} Clear!".format(current_level_num)
            center_label.text = "Score: {}".format(score)
            pixels_flash((0, 255, 0), times=2, delay=0.1)
    else:
        status_label.text = "GAME OVER"
        center_label.text = "Score: {}".format(score)
        pixels_flash((255, 0, 0), times=3, delay=0.1)

def generate_sequence_for_level(level_cfg):
    """根据关卡规则生成该关的命令序列（随机）"""
    n = level_cfg["commands"]

    # 动作池：按难度控制复杂度
    ALL_MOVES   = [MOVE_CUT_WIRE, MOVE_DIAL, MOVE_STEADY, MOVE_SHAKE]

    seq = []
    for _ in range(n):
        seq.append(random.choice(ALL_MOVES))
    return seq

# High score ranking
def show_highscore_board():
    clear_menu()
    status_label.text = "HIGH SCORES"

    # 显示前 3 名
    for i, entry in enumerate(highscores[:3]):
        name = entry["name"]
        s = entry["score"]
        menu_labels[i].text = "{}. {}  {}".format(i + 1, name, s)

    # 不再用 center_label 作为提示
    center_label.text = ""

    # 把提示放到最下面
    menu_labels[2].text = "Press → Menu"


# ---------- Buzzer 工具函数 ----------

def sfx_startup_mario():
    """马里奥风格开机音效（短版）"""
    play_tone(660, 0.10)   # E5
    time.sleep(0.04)
    play_tone(660, 0.10)   # E5 again
    time.sleep(0.04)
    play_tone(660, 0.10)   # E5 again
    time.sleep(0.10)

    play_tone(510, 0.10)   # C5
    time.sleep(0.04)
    play_tone(660, 0.10)   # E5
    time.sleep(0.04)
    play_tone(770, 0.12)   # G5 (Mario trademark upward!)

def play_tone(freq, duration, volume=0.3):
    """播放一个固定频率的方波音调"""
    buzzer.frequency = freq
    buzzer.duty_cycle = int(65535 * volume)  # 0~65535
    time.sleep(duration)
    buzzer.duty_cycle = 0  # 关掉声音

def sfx_move_ok():
    """正确完成一个动作时的短“滴”声"""
    play_tone(1400, 0.05, 0.25)

def sfx_level_clear():
    """关卡通过：上升的小旋律"""
    play_tone(800, 0.08)
    time.sleep(0.03)
    play_tone(1000, 0.08)
    time.sleep(0.03)
    play_tone(1300, 0.1)

def sfx_game_over():
    """Game Over：下降的“失败”音"""
    play_tone(600, 0.12)
    time.sleep(0.04)
    play_tone(400, 0.18)

def sfx_game_win():
    """通关所有关卡：胜利音效"""
    play_tone(900, 0.08)
    time.sleep(0.03)
    play_tone(1200, 0.08)
    time.sleep(0.03)
    play_tone(1500, 0.12)


# ---------- NeoPixel 工具函数 ----------

def pixels_off():
    for i in range(NUM_PIXELS):
        pixels[i] = (0, 0, 0)

def pixels_solid(color):
    for i in range(NUM_PIXELS):
        pixels[i] = color

def pixels_flash(color, times=3, delay=0.1):
    for _ in range(times):
        pixels_solid(color)
        time.sleep(delay)
        pixels_off()
        time.sleep(delay)

def pixels_for_command(cmd):
    """不同动作显示不同颜色（游戏中使用）"""
    if cmd == MOVE_DIAL:
        pixels_solid((255, 255, 0))   # 黄：Dial
    elif cmd == MOVE_CUT_WIRE:
        pixels_solid((255, 255, 255)) # 白：Cut Wire
    elif cmd == MOVE_STEADY:
        pixels_solid((0, 150, 255))   # 蓝：Steady
    elif cmd == MOVE_SHAKE:
        pixels_solid((255, 0, 255))   # 紫：Shake
    else:
        pixels_off()

def pixels_breathe(base_color, t):
    """
    Splash Screen 动画用的呼吸灯效果
    t = 当前动画已进行时间（秒）
    """
    phase = (math.sin(t * BREATHE_SPEED) + 1.0) * 0.5    # 0~1
    brightness_scale = 0.2 + 0.8 * phase                 # 0.2~1.0

    r, g, b = base_color
    for i in range(NUM_PIXELS):
        pixels[i] = (
            int(r * brightness_scale),
            int(g * brightness_scale),
            int(b * brightness_scale),
        )

#  ---------- 读写文件high score函数 ----------

def load_highscores():
    global highscores
    highscores = []
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) != 2:
                    continue
                name = parts[0].strip()
                try:
                    s = int(parts[1])
                except:
                    s = 0
                highscores.append({"name": name, "score": s})
    except OSError:
        # 文件不存在时，初始化默认
        highscores = [
            {"name": "AAA", "score": 0},
            {"name": "BBB", "score": 0},
            {"name": "CCC", "score": 0},
        ]

    highscores = sorted(highscores, key=lambda x: x["score"], reverse=True)
    highscores = highscores[:MAX_HISCORES]


def save_highscores():
    with open(HIGHSCORE_FILE, "w") as f:
        for entry in highscores:
            f.write("{},{}\n".format(entry["name"], entry["score"]))


def check_highscore(current_score):
    """返回插入位置 index（0..len）或 -1 表示进不了榜"""
    if len(highscores) < MAX_HISCORES:
        return len(highscores)
    for i, entry in enumerate(highscores):
        if current_score > entry["score"]:
            return i
    return -1


def show_highscore_board():
    clear_menu()
    status_label.text = "HIGH SCORES"
    for i, entry in enumerate(highscores[:3]):
        menu_labels[i].text = "{}. {}  {}".format(
            i + 1, entry["name"], entry["score"]
        )
    center_label.text = "Press → Menu"

# ------- 玩家名字编辑 ---------
def player_initials_str():
    return "".join(player_initials)


def show_name_input():
    clear_menu()
    status_label.text = "SET PLAYER"

    s = player_initials_str()
    if player_pos == 0:
        center_label.text = ">{} {} {}".format(s[0], s[1], s[2])
    elif player_pos == 1:
        center_label.text = "{} >{} {}".format(s[0], s[1], s[2])
    else:
        center_label.text = "{} {} >{}".format(s[0], s[1], s[2])

    # 提示放在最下面一行，避免和中间的 A A A 重叠
    menu_labels[0].text = ""
    menu_labels[1].text = ""
    menu_labels[2].text = "Rot:A-Z  Press:OK"


# 启动时先进入 Splash 状态
state = STATE_SPLASH
splash_start_time = time.monotonic()

status_label.text = ""
center_label.text = "DIFFUSER"  # 或你的游戏名字
clear_menu()  # 菜单先清空

sfx_startup_mario() # 开机马里奥音效（只播放一次）

# ---------- 初始化 high score 数据 ----------
load_highscores()

# ---------- while True: 主循环 ----------
while True:
    now = time.monotonic()

    # 1. 旋钮更新
    dial_changed = False
    changed = encoder.update()
    position = encoder.position

    if changed:
        if state == STATE_MENU:
            if position != last_position:
                delta = position - last_position

                if delta > 0:
                    selected_menu_index += 1
                elif delta < 0:
                    selected_menu_index -= 1

                # 菜单共有 4 行：0=Player, 1=EASY, 2=MEDIUM, 3=HARD
                if selected_menu_index < 0:
                    selected_menu_index = 0
                if selected_menu_index > 3:
                    selected_menu_index = 3

                last_position = position
                draw_menu(selected_menu_index)
        else:
            # 游戏中，把旋转视作 DIAL 动作的输入事件
            dial_changed = True
            last_position = position


    # 2. 按钮边沿检测
    raw = button.value
    button_pressed = (last_button_value is True) and (raw is False)
    last_button_value = raw

    # 3. 状态机
    if state == STATE_SPLASH:
        elapsed = now - splash_start_time

        # ① 文本从左往右滑入
        text_duration = 1.8
        t_prog = min(elapsed / text_duration, 1.0)
        text_x = int(-60 + (8 + 60) * t_prog)
        center_label.x = text_x
        center_label.text = "DIFFUSER"

        # ② 扫描条从左往右移动
        bar_duration = 2.2
        b_prog = min(elapsed / bar_duration, 1.0)
        splash_bar.x = int(-16 + (128 + 16) * b_prog)

        # ③ 顶部标题固定
        status_label.text = "Bomb Diffuse Game"

        # ④ 炸弹 ASCII 图标变形
        frame_index = int(elapsed / 0.2) % len(BOMB_FRAMES)
        bomb_label.text = BOMB_FRAMES[frame_index]

        # ⑤ NeoPixel 呼吸效果
        pixels_breathe((255, 80, 0), elapsed)

        # ⑥ 动画结束后 → 直接进入名字输入（不是菜单）
        if elapsed > 3.0:
            bomb_label.text = ""
            center_label.text = ""
            center_label.x = 6
            splash_bar.x = -16
            pixels_solid((0, 0, 40))

            # ★ 改这里：直接进入名字输入
            player_pos = 0
            player_last_position = encoder.position
            show_name_input()
            state = STATE_NAME_INPUT


    elif state == STATE_NAME_INPUT:
        # 旋钮：修改当前字母
        if changed:
            delta = position - player_last_position
            if delta != 0:
                c = player_initials[player_pos]
                code = ord(c) - ord("A")
                if delta > 0:
                    code += 1
                elif delta < 0:
                    code -= 1
                code %= 26
                player_initials[player_pos] = chr(ord("A") + code)
                show_name_input()
            player_last_position = position

        # 短按 → 下一个字母
        if button_pressed:
            if player_pos < 2:
                player_pos += 1
                show_name_input()
            else:
                # ★ 名字输入完成 → 进入菜单选难度
                current_player_name = "".join(player_initials)
                selected_menu_index = 1  # 默认光标在 EASY（第一个难度选项）
                draw_menu(selected_menu_index)
                state = STATE_MENU


    elif state == STATE_MENU:
        # ★ 菜单现在只用来选难度，不再有 Player 选项
        # 光标在难度行 (1=EASY, 2=MEDIUM, 3=HARD) + 短按 → 开始游戏
        if button_pressed and (selected_menu_index >= 1):
            #score = 0
            selected_diff_index = selected_menu_index - 1

            diff_name = DIFFICULTIES[selected_diff_index]
            start_idx, end_idx = DIFF_RANGE[diff_name]
            current_level_index = start_idx

            level_cfg = LEVELS[current_level_index]
            current_level_num = level_cfg["level_num"]
            time_limit = level_cfg["time_limit"]

            current_sequence = generate_sequence_for_level(level_cfg)
            required_commands = len(current_sequence)
            current_cmd_index = 0

            calibrate_baseline()
            level_start_time = now
            steady_start_time = None

            show_level_intro()
            state = STATE_INIT_LEVEL

    elif state == STATE_INIT_LEVEL:
        if now - level_start_time > 1.0:
            level_start_time = now
            steady_start_time = None
            state = STATE_WAIT_INPUT

    elif state == STATE_WAIT_INPUT:
        elapsed = now - level_start_time
        remaining = time_limit - elapsed

        show_level_play(remaining)

        cmd = current_sequence[current_cmd_index]
        success_this_cmd = False

        if cmd == MOVE_CUT_WIRE:
            if button_pressed:
                success_this_cmd = True
        elif cmd == MOVE_DIAL:
            if dial_changed:
                success_this_cmd = True
        elif cmd == MOVE_STEADY:
            diff_mag = accel_diff_mag_filtered()
            if diff_mag < STEADY_DIFF_THRESH:
                if steady_start_time is None:
                    steady_start_time = now
                if (now - steady_start_time) >= STEADY_HOLD_TIME:
                    success_this_cmd = True
            else:
                # 一旦超出阈值，重新计时
                steady_start_time = None

        elif cmd == MOVE_SHAKE:
            diff_mag = accel_diff_mag_filtered()
            if diff_mag > SHAKE_DIFF_THRESH:
                success_this_cmd = True

        # 当前命令完成 → correct move
        if success_this_cmd:
            score += POINT_PER_COMMAND
            sfx_move_ok()
            current_cmd_index += 1
            steady_start_time = None

            if current_cmd_index >= required_commands:
                score += POINT_PER_LEVEL
                sfx_level_clear()
                result_is_success = True
                diff_name = DIFFICULTIES[selected_diff_index]
                start_idx, end_idx = DIFF_RANGE[diff_name]
                is_last = (current_level_index >= end_idx)
                show_level_result(True, is_last)
                state = STATE_LEVEL_RESULT

        elif remaining <= 0:
            sfx_game_over()
            result_is_success = False
            is_last = False
            show_level_result(False, False)
            state = STATE_LEVEL_RESULT

    elif state == STATE_LEVEL_RESULT:
        if button_pressed:
            if result_is_success and not is_last:
                # ★ 过关但还有下一关 → 继续下一关（不显示排行榜）
                current_level_index += 1
                level_cfg = LEVELS[current_level_index]
                current_level_num = level_cfg["level_num"]
                time_limit = level_cfg["time_limit"]

                current_sequence = generate_sequence_for_level(level_cfg)
                required_commands = len(current_sequence)
                current_cmd_index = 0

                calibrate_baseline()
                level_start_time = now
                steady_start_time = None

                show_level_intro()
                state = STATE_INIT_LEVEL

            elif is_last:
                # ★ 通关当前难度 → 返回菜单（分数保留）
                selected_menu_index = 1
                draw_menu(selected_menu_index)
                state = STATE_MENU

            else:
                # ★ Game Over 或通关最后一关 → 检查排行榜
                idx = check_highscore(score)
                if idx >= 0:
                    entry = {"name": current_player_name, "score": score}
                    highscores.append(entry)
                    highscores.sort(key=lambda x: x["score"], reverse=True)
                    highscores[:] = highscores[:MAX_HISCORES]
                    save_highscores()

                show_highscore_board()
                state = STATE_HS_SHOW


    elif state == STATE_HS_SHOW:
        if button_pressed:
            # ★ 排行榜后 → 回到名字输入（新一轮游戏）
            score = 0
            player_pos = 0
            player_initials = ["A", "A", "A"]  # 重置名字
            player_last_position = encoder.position
            show_name_input()
            state = STATE_NAME_INPUT

    time.sleep(0.005)