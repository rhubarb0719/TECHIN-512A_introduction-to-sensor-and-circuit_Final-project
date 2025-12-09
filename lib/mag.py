import time
import math
import board
import busio
import adafruit_adxl34x

i2c = busio.I2C(board.SCL, board.SDA)
accelerometer = adafruit_adxl34x.ADXL345(i2c)

while True:
    #todo get raw accelerometer readings
    x, y, z = accelerometer.acceleration

    #todo implement magnitude filter
    mag = math.sqrt(x * x + y * y + z * z)

    #todo print raw and filtered readings
    print(f"X: {x:.3f}   Y: {y:.3f}   Z: {z:.3f}   |  Mag: {mag:.3f}")

    time.sleep(0.05)

