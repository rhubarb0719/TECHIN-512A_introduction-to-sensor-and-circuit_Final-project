import time
import board
import busio
import adafruit_adxl34x

# 初始化 I2C 和加速度计
i2c = busio.I2C(board.SCL, board.SDA)
accelerometer = adafruit_adxl34x.ADXL345(i2c)

THRESHOLD = 1.5      # 加速度阈值 (m/s^2)
ALPHA = 0.3          # EMA smoothing factor，越小越平滑
REQUIRED_COUNT = 4   # 至少连续 4 次同一方向，才确认“在该方向运动”

# EMA 初始化（先读一次）
x_raw, y_raw, z_raw = accelerometer.acceleration
x_filt = x_raw
y_filt = y_raw
z_filt = z_raw

last_direction = None   # 上一次判定的方向（字符串，比如 "Moving +X"）
stable_count = 0        # 当前方向连续出现次数

while True:
    # 1. 读取原始加速度
    x, y, z = accelerometer.acceleration

    # 2. 对三个轴做 EMA 低通滤波
    x_filt = ALPHA * x + (1 - ALPHA) * x_filt
    y_filt = ALPHA * y + (1 - ALPHA) * y_filt
    z_filt = ALPHA * z + (1 - ALPHA) * z_filt

    # 3. 选出“最主导”的轴：绝对值最大的那个
    abs_x = abs(x_filt)
    abs_y = abs(y_filt)
    abs_z = abs(z_filt)

    if abs_x >= abs_y and abs_x >= abs_z:
        axis = "X"
        value = x_filt
    elif abs_y >= abs_x and abs_y >= abs_z:
        axis = "Y"
        value = y_filt
    else:
        axis = "Z"
        value = z_filt

    # 4. 检查这个主导轴是否超过正/负阈值
    if abs(value) > THRESHOLD:
        if value > 0:
            direction = f"Moving +{axis}"
        else:
            direction = f"Moving -{axis}"
    else:
        direction = None

    # 5. 用计数器确认方向是否“稳定”
    if direction is None:
        # 没有明显方向时，清空状态
        last_direction = None
        stable_count = 0
    else:
        if direction == last_direction:
            stable_count += 1
        else:
            last_direction = direction
            stable_count = 1

        # 当同一方向连续出现 REQURIED_COUNT 次，就确认移动
        if stable_count == REQUIRED_COUNT:
            print(direction)

    # 6. 可选：打印调试信息（方便你观察和截图）
    print(
        f"Raw: x={x:.2f}, y={y:.2f}, z={z:.2f} | "
        f"Filt: x={x_filt:.2f}, y={y_filt:.2f}, z={z_filt:.2f} | "
        f"Dominant={axis}, value={value:.2f}, dir={direction}, count={stable_count}"
    )

    time.sleep(0.05)

