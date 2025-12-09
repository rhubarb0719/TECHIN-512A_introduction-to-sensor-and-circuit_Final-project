import time
import board
import adafruit_adxl34x

# Initialize I2C and accelerometer
i2c = board.I2C()
accelerometer = adafruit_adxl34x.ADXL345(i2c)

# === STEP 1: Collect samples ===
NUM_SAMPLES = 20

sum_x = 0
sum_y = 0
sum_z = 0

print("Collecting baseline readings... Keep the sensor flat and still.")

for i in range(NUM_SAMPLES):
    x, y, z = accelerometer.acceleration
    sum_x += x
    sum_y += y
    sum_z += z

    print(f"Sample {i+1}: x={x:.2f}, y={y:.2f}, z={z:.2f}")
    time.sleep(0.1)

# === STEP 2: Compute baseline ===
baseline_x = sum_x / NUM_SAMPLES
baseline_y = sum_y / NUM_SAMPLES
baseline_z = sum_z / NUM_SAMPLES

print("\n=== Baseline (Zero Offset) ===")
print(f"baseline_x = {baseline_x:.2f}")
print(f"baseline_y = {baseline_y:.2f}")
print(f"baseline_z = {baseline_z:.2f}\n")

# === STEP 3: Print raw vs calibrated ===
print("Printing raw and calibrated values...\n")

while True:
    raw_x, raw_y, raw_z = accelerometer.acceleration

    # Calibrated:
    cal_x = raw_x - baseline_x
    cal_y = raw_y - baseline_y
    cal_z = raw_z - baseline_z

    print(
        f"RAW: x={raw_x:6.2f}, y={raw_y:6.2f}, z={raw_z:6.2f}  |  "
        f"CAL: x={cal_x:6.2f}, y={cal_y:6.2f}, z={cal_z:6.2f}"
    )

    time.sleep(0.2)

