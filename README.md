# The Diffuser

## 🎮 Action Commands (Moves) Overview

| **Command**        | **User Action**                                                     | **Technical Implementation**                                                | **Description**                                                                      |
|--------------------|---------------------------------------------------------------------|----------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Dial**           | Rotate the rotary encoder           | Detect encoder rotation (clockwise or counterclockwise)        | Simple twist action; used for bomb tuning or parameter adjustment            |
| **Cut Wire**       | Press the encoder’s push button                                     | Detect encoder button press                                                | Fast-reaction action; simulates cutting a wire under time pressure                    |
| **Steady…**        | Hold the device completely still                                    | Use ADXL345; detect if acceleration stays within ±0.1 g                    | High-difficulty action—any shaking or slight movement results in failure              |
| **Shake**          | Shake the device sharply                                            | Detect sudden large acceleration spikes using ADXL345                      | Used in Hard Mode or higher levels as an extra challenge                              |

## 🧩 Difficulty Settings

1. **Easy: Level 1-3**
    - **Number of Commands:** 1
    - **Input Time:** 5 seconds → 4.0 seconds

    | Level | Commands | Time Limit |
    | ----- | -------- | ---------- |
    | 1     | 1        | 5.0 s      |
    | 2     | 1        | 4.5 s      |
    | 3     | 1        | 4.0 s      |

2. **Medium: Level 4-6**
    - **Number of Commands:** 2  
    - **Input Time:** 3.2 seconds → 2.8 seconds

    | Level | Commands | Time Limit |
    | ----- | -------- | ---------- |
    | 4     | 2        | 3.2 s      |
    | 5     | 2        | 3.0 s      |
    | 6     | 2        | 2.8 s      |

3. **Hard: Level 7-10**
    - **Number of Commands:** 4  
   - **Input Time:** 3.0 seconds → 2.4 seconds

    | Level | Commands | Time Limit |
    | ----- | -------- | ---------- |
    | 7     | 4        | 3.0 s      |
    | 8     | 4        | 2.8 s      |
    | 9     | 4        | 2.6 s      |
    | 10     | 4        | 2.4 s      |

## 🎮 How to Start & Change Difficulty

### Quick Summary for Users
| Action                     | How to Do It            |
| -------------------------- | ----------------------- |
| **Scroll difficulty**      | Rotate encoder          |
| **Select difficulty**      | Press encoder           |
| **Start game**             | Press encoder again     |
| **Restart after fail/win** | Press encoder           |
| **Power on/off**           | Use the physical switch |


1. **Power On**

    a. Slide the **On/Off switch** to turn on the device.

    b. The OLED displays the **Splash Screen**, followed by the **Difficulty Selection Menu**.

2. **Difficulty Selection**

    Use the Rotary Encoder to choose one of the three difficulty modes:
    * **Easy**
    * **Medium**
    * **Hard**
    
    🌟 How to select difficulty:
    
    Rotate the encoder → scroll through the difficulty options

    Press the encoder button → confirm the selected difficulty

    After confirming, the device enters **Level 1** of that difficulty.

3. **Start the Game**
    
    a. The OLED displays:
    * Level number
    * Number of commands
    * Time limit

    b. Press the encoder button again to begin.

4. **Restarting the Game**
    
    a. After Game Over or Game Win:
    * Press the encoder button once → Return to the Difficulty Selection Menu

    b. Rotate + Press to choose a new difficulty

    c. Start a new run without turning off the device

## Hardware
## 🧰 Hardware Components & Purpose

1. **Xiao ESP32-C3**

   Runs CircuitPython and controls all sensors, the display, LEDs, and the buzzer.

2. **SSD1306 OLED**

   Displays instructions, countdown, difficulty menu, and Game Over/Game Win screens.

3. **Rotary Encoder + Button**

   - Rotation: **Dial** action  
   - Press: **Cut** action  
   - Menu navigation: rotate to select, press to confirm.

4. **ADXL345 Accelerometer**

   - **Steady**: detect stillness  
   - **Shake**: detect high acceleration  
   - **Flip** (optional): detect Z-axis orientation change.

### ---------- ADXL345 ----------
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


5. **NeoPixel**

   Displays game state (action cues, failure, victory, start animation).

6. **Piezo Buzzer**

   Plays success tones, failure alerts, and warning sound effects.

7. **LiPo Battery & Power Switch**

   Provides portable power for the entire system.

## Circuit

1. SSD1306 OLED (I2C)
| Encoder Pin | ESP32-C3 Pin |
| ----------- | ------------ |
| SCL         | D5           | purple
| SDA         | D4           | orange
| VCC         | 3V3          | 
| GND         | GND          | 

2. Rotary Encoder + Button
| Encoder Pin | ESP32-C3 Pin | 
| ----------- | ------------ | 
| CLK         | D0           | white
| DT          | D1           | yellow
| SW          | D2           | red
| GND         | GND          | Ground

3. ADXL345 Accelerometer (I2C)
| ADXL345 Pin | ESP32-C3 Pin    |
| ----------- | --------------- |
| VCC         | 3V3             |
| GND         | GND             |
| SDA         | D4              | gray
| SCL         | D5              | blue

4. NeoPixel LED
| NeoPixel Pin | ESP32-C3 Pin |
| ------------ | ------------ |
| DIN          | D8           |
| VCC          | 3V3          |
| GND          | GND          |

5. Piezo Buzzer
| Buzzer Pin | ESP32-C3 Pin     |
| ---------- | ---------------- |
| +          | D7 (PWM capable) |
| -          | GND              |

## Box design idea

90s style handy game machine style