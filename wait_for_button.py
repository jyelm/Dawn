import RPi.GPIO as GPIO
import time
import subprocess

BUTTON_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Waiting for ON button press...")

try:
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # Button pressed
            print("Button pressed! Launching GUI...")
            subprocess.run(["python3", "/home/pi/your_project_folder/main.py"])
            break
        time.sleep(0.1)
finally:
    GPIO.cleanup()
