import board
import time
import adafruit_adxl34x

i2c = board.I2C()  

accelerometer = adafruit_adxl34x.ADXL345(i2c)

#tap_count=2
accelerometer.enable_tap_detection(tap_count=2,threshold=20, duration=50)

while True:
    
    print("Tapped: {}".format(accelerometer.events["tap"]))
    time.sleep(0.5)
