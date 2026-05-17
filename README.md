# Biometric Air Pass Security System

A contactless 2-Factor Authentication (2FA) door lock. To enter, the system must first **detect your face**, then you must perform a **secret sequence of hand gestures** in the air.

---

## Quick Setup

### 1. Arduino (The Lock)

* Open the Arduino sketch.
* Create a `secrets.h` file and add your WiFi `SSID` and `PASSWORD`.
* Upload the code to your **Arduino Uno R4 WiFi** (or similar).
* Open the Serial Monitor to find the **IP Address** of your Arduino.

### 2. Python (The Brain)

* Install the required libraries:
```bash
pip install mediapipe opencv-python

```

* In the Python script, update the `UDP_IP` variable with the Arduino IP you found in Step 1.
* Run the script: `python main.py`.

---

## How It Works

The system uses a **State Machine** to handle security levels:

1. **Face Check:** The camera looks for a human face. If no face is present, it ignores all hand gestures.
2. **Gesture Passcode:** Once a face is detected, you must perform the sequence:
* **Open Palm** ➔ **Closed Fist** ➔ **Victory (Peace)** ➔ **Thumb Up**


3. **Unlock:** If the sequence is correct, the Arduino moves the **Servo Motor** to unlock the door and displays "ACCESS GRANTED" on the **OLED screen**.

---

## Hardware Needed

* **Raspberry Pi 4/5** (or a laptop) + USB Webcam.
* **Arduino Uno R4 WiFi** (for wireless communication).
* **SG90 Servo Motor** (The physical latch).
* **SSD1306 OLED Display** (To show status).
* **RGB LED** (Visual feedback: Blue for "Ready", Green for "Open", Red for "Error").

---
