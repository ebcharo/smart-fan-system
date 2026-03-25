import sys
import platform
import random
import time
import requests

WINDOWS = platform.system() == "Windows"

print("\n=== WINDOWS TEST MODE (FAHRENHEIT) ===\n")

# ------------------------------------------------------------
#                 MOCK GPIO + PWM (Windows Only)
# ------------------------------------------------------------
if WINDOWS:
    class MockPWM:
        def __init__(self, pin, freq):
            self.pin = pin

        def start(self, duty):
            print(f"[MOCK PWM] Start at {duty}%")

        def ChangeDutyCycle(self, duty):
            print(f"[MOCK PWM] → {duty}%")

        def stop(self):
            print("[MOCK PWM] Stopped")

    class MockGPIO:
        BCM = None
        OUT = None
        HIGH = 1
        LOW = 0

        def setmode(self, mode): pass
        def setup(self, pin, mode): pass
        def output(self, pin, val):
            print(f"[MOCK GPIO] Pin {pin} = {val}")
        def cleanup(self): print("[MOCK GPIO] Cleanup")
        def PWM(self, pin, freq): return MockPWM(pin, freq)

    GPIO = MockGPIO()

else:
    import RPi.GPIO as GPIO  # For Pi use only


# ------------------------------------------------------------
#                   MOCKED LOCAL TEMPERATURE
# ------------------------------------------------------------
def get_local_temp():
    """Simulates DS18B20 readings, but in Fahrenheit."""
    temp_f = round(random.uniform(65, 95), 2)
    print(f"[MOCK SENSOR] Local temp: {temp_f}°F")
    return temp_f


# ------------------------------------------------------------
#                 WEATHER API (NWS — already °F)
# ------------------------------------------------------------
LAT, LON = 41.8781, -87.6298
POINT_URL = f"https://api.weather.gov/points/{LAT},{LON}"

def get_outdoor_temp():
    try:
        r = requests.get(POINT_URL, timeout=5)
        r.raise_for_status()
        url = r.json()["properties"]["forecastHourly"]
        forecast = requests.get(url, timeout=5).json()
        temp_f = float(forecast["properties"]["periods"][0]["temperature"])
        print(f"[NWS] Outdoor temp: {temp_f}°F")
        return temp_f
    except Exception as e:
        print("[NWS ERROR]", e)
        return None


# ------------------------------------------------------------
#                MOCK FAN SPEED
# ------------------------------------------------------------
def set_fan_speed(speed):
    speed = max(0, min(100, speed))
    print(f"[MOCK FAN] Speed set to {speed}%\n")


# ------------------------------------------------------------
#           USER CONFIGURATION — °F VERSION
# ------------------------------------------------------------
def get_user_settings():
    print("=== FAN CONFIG (FAHRENHEIT) ===")
    print("1. Local Sensor")
    print("2. Weather API")

    while True:
        mode = input("Enter 1 or 2: ").strip()
        if mode in ("1", "2"): break

    def ask_float(msg, default):
        v = input(f"{msg} (default {default}°F): ").strip()
        return float(v) if v else default

    low_th = ask_float("LOW → MEDIUM threshold", 75)
    med_th = ask_float("MEDIUM → HIGH threshold", 82)

    def ask_int(msg, d):
        v = input(f"{msg} (default {d}%): ").strip()
        return int(v) if v else d

    low_sp = ask_int("LOW speed", 0)
    med_sp = ask_int("MEDIUM speed", 50)
    high_sp = ask_int("HIGH speed", 100)

    return {
        "mode": mode,
        "low_th": low_th,
        "med_th": med_th,
        "low_sp": low_sp,
        "med_sp": med_sp,
        "high_sp": high_sp
    }


# ------------------------------------------------------------
#                     FAN CONTROL
# ------------------------------------------------------------
def control_fan(settings):
    if settings["mode"] == "1":
        temp = get_local_temp()
        src = "Local (Simulated)"
    else:
        temp = get_outdoor_temp()
        src = "Weather API"

    if temp is None:
        print(f"[WARNING] {src} unavailable.\n")
        return

    print(f"[TEMP] {src}: {temp}°F")

    if temp < settings["low_th"]:
        set_fan_speed(settings["low_sp"])
    elif temp < settings["med_th"]:
        set_fan_speed(settings["med_sp"])
    else:
        set_fan_speed(settings["high_sp"])


# ------------------------------------------------------------
#                          MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    settings = get_user_settings()

    try:
        while True:
            control_fan(settings)
            time.sleep(5)
    except KeyboardInterrupt:
        print("Exiting...")