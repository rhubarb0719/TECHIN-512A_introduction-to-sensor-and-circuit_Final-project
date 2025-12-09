import time
import math
import board
import busio
import adafruit_adxl34x

i2c = busio.I2C(board.SCL, board.SDA)
accelerometer = adafruit_adxl34x.ADXL345(i2c)

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

threshold = baseline + 0.8
required_count = 5

motion_count = 0
motion_detected = False

print("Start monitoring motion...")

while True:
    x, y, z = accelerometer.acceleration
    mag = math.sqrt(x * x + y * y + z * z)

    if mag >= threshold:
        motion_count += 1
    else:
        motion_count = 0
        motion_detected = False 

    if motion_count >= required_count and not motion_detected:
        print("MOTION DETECTED")
        motion_detected = True

    print(
        f"Mag: {mag:.3f}  "
        f"Baseline: {baseline:.3f}  "
        f"Threshold: {threshold:.3f}  "
        f"Count: {motion_count}"
    )

    time.sleep(0.05)