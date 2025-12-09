import time
import board
import busio
import adafruit_adxl34x

# 1. 初始化 I2C 和加速度计
i2c = busio.I2C(board.SCL, board.SDA)
accelerometer = adafruit_adxl34x.ADXL345(i2c)

# 2. 高通滤波的 alpha，范围通常 0.3 ~ 0.95
alpha = 0.7

# 3. 初始化“上一帧原始值”和“滤波值”
#   老师提示是从 0 开始，这里就都设为 0
xPrev = yPrev = zPrev = 0.0
xFiltered = yFiltered = zFiltered = 0.0

while True:
    # 4. 读取当前原始加速度值（x, y, z）
    x, y, z = accelerometer.acceleration

    # 5. 对三个轴分别应用一阶 IIR 高通滤波
    xFiltered = alpha * (xFiltered + x - xPrev)
    yFiltered = alpha * (yFiltered + y - yPrev)
    zFiltered = alpha * (zFiltered + z - zPrev)

    # 6. 更新上一帧的原始值，为下一次循环做准备
    xPrev, yPrev, zPrev = x, y, z

    # 7. 打印原始值和滤波后的值（方便截图 & Plotter）
    #print(f"X  Raw: {x:.3f}   Filtered: {xFiltered:.3f}")
    #print(f"Y  Raw: {y:.3f}   Filtered: {yFiltered:.3f}")
    print(f"Z  Raw: {z:.3f}   Filtered: {zFiltered:.3f}")
    #print("-----------------------------")

    time.sleep(0.05)  # 稍微慢一点，方便观察

