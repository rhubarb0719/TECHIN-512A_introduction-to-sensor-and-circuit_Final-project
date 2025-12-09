import time
import math
import board
import busio
import neopixel
import adafruit_adxl34x

# ---------- NeoPixel 设置 ----------
pixel_pin = board.D8       # 换成你实际接 NeoPixel 的脚
num_pixels = 1
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.3, auto_write=True)

RED = (255, 0, 0)
GREEN = (0, 255, 0)

# ---------- 加速度计初始化 ----------
i2c = busio.I2C(board.SCL, board.SDA)
accelerometer = adafruit_adxl34x.ADXL345(i2c)

# ---------- 先做静止校准，找到 baseline ----------
print("Calibrating... keep the board still...")

baseline_samples = 50
baseline_sum = 0.0

for i in range(baseline_samples):
    x, y, z = accelerometer.acceleration
    mag = math.sqrt(x * x + y * y + z * z)
    baseline_sum += mag
    time.sleep(0.02)

baseline = baseline_sum / baseline_samples
print(f"Baseline magnitude: {baseline:.3f}")

# 阈值与连续计数
threshold = baseline + 0.8   # 可以根据实验调节，比如 +0.5, +1.0
required_count = 5           # 连续 5 次超过阈值才算运动

motion_count = 0
motion_detected = False

# 初始状态：无运动 → 红灯
pixels[0] = RED

print("Start monitoring motion...")

while True:
    x, y, z = accelerometer.acceleration
    mag = math.sqrt(x * x + y * y + z * z)

    # 判断是否超过阈值
    if mag >= threshold:
        motion_count += 1
    else:
        motion_count = 0

    # 当连续多次超过阈值 → 判定为“检测到运动”
    if motion_count >= required_count and not motion_detected:
        motion_detected = True

        # 变绿 3 秒
        print("MOTION DETECTED")
        pixels[0] = GREEN
        time.sleep(3)

        # 恢复红色，重新开始检测
        pixels[0] = RED
        motion_count = 0
        motion_detected = False

    # 可选：打印调试信息（想干净一点可以注释掉）
    print(
        f"Mag: {mag:.3f}  "
        f"Baseline: {baseline:.3f}  "
        f"Threshold: {threshold:.3f}  "
        f"Count: {motion_count}"
    )

    time.sleep(0.05)

