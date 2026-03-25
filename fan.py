import glob
import time
import requests
import RPi.GPIO as GPIO

# ------------------------------------------------------------
#                   DS18B20 SENSOR SETUP
# ------------------------------------------------------------
base_dir = "/sys/bus/w1/devices/"
try:
    device_folder = glob.glob(base_dir + "28*")[0]
    device_file = device_folder + "/w1_slave"
except IndexError:
    device_file = None
    print("ERROR: DS18B20 sensor not found.")

def read_temp_raw():
    if not device_file:
        return None
    with open(device_file, "r") as f:
        return f.readlines()

def get_local_temp():
    """Reads DS18B20 and returns Fahrenheit."""
    lines = read_temp_raw()
    if lines is None:
        return None

    while lines[0].strip()[-3:] != "YES":
        time.sleep(0.2)
        lines = read_temp_raw()

    equals_pos = lines[1].find("t=")
    if equals_pos != -1:
        temp_c = float(lines[1][equals_pos + 2:]) / 1000.0
        temp_f = temp_c * 9/5 + 32
        return round(temp_f, 2)
    return None

# ------------------------------------------------------------
#                   WEATHER API (NWS)
# ------------------------------------------------------------
LAT, LON = 41.8781, -87.6298
POINT_URL = f"https://api.weather.gov/points/{LAT},{LON}"

def get_outdoor_temp():
    """Already Fahrenheit."""
    try:
        r = requests.get(POINT_URL, timeout=5)
        r.raise_for_status()

        hourly = requests.get(
            r.json()["properties"]["forecastHourly"], timeout=5
        ).json()

        temp_f = hourly["properties"]["periods"][0]["temperature"]
        return round(float(temp_f), 2)

    except Exception as e:
        print("Weather API error:", e)
        return None

# ------------------------------------------------------------
#                   GPIO + MOTOR CONTROL
# ------------------------------------------------------------
GPIO.setmode(GPIO.BCM)
ENA, IN1, IN2 = 18, 17, 27

GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

pwm = GPIO.PWM(ENA, 1000)
pwm.start(0)

def set_fan_speed(speed):
    speed = max(0, min(100, speed))
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)
    print(f"Fan speed set to {speed}%")

# ------------------------------------------------------------
#                   USER SETTINGS + DEMO MODE
# ------------------------------------------------------------
def get_user_settings():
    print("\n=== SMART FAN CONFIG (FAHRENHEIT) ===")

    demo_mode = input("Enable Demo Mode? (y/n): ").strip().lower()
    is_demo = demo_mode == "y"

    # Demo values initialize
    demo_in = None
    demo_out = None

    print("\nTemperature source:")
    print("1. Local Sensor (DS18B20)")
    print("2. Weather API (NWS)")
    while True:
        mode = input("Enter 1 or 2: ").strip()
        if mode in ("1", "2"):
            break

    # Demo: ask first values
    if is_demo:
        print("\n--- DEMO MODE ACTIVE ---")
        if mode == "1":
            demo_in = float(input("Enter DEMO indoor temperature (°F): "))
        else:
            demo_out = float(input("Enter DEMO outdoor temperature (°F): "))

    print("\n=== TEMPERATURE THRESHOLDS (°F) ===")
    def ask_float(msg, default):
        val = input(f"{msg} (default {default}°F): ").strip()
        return float(val) if val else default

    low_th = ask_float("LOW → MEDIUM threshold", 75)
    med_th = ask_float("MEDIUM → HIGH threshold", 82)

    print("\n=== FAN SPEEDS ===")
    def ask_int(msg, default):
        val = input(f"{msg} (default {default}%): ").strip()
        return int(val) if val else default

    low_sp = ask_int("LOW fan speed", 0)
    med_sp = ask_int("MEDIUM fan speed", 50)
    high_sp = ask_int("HIGH fan speed", 100)

    return {
        "mode": mode,
        "demo": is_demo,
        "demo_in": demo_in,
        "demo_out": demo_out,
        "low_th": low_th,
        "med_th": med_th,
        "low_sp": low_sp,
        "med_sp": med_sp,
        "high_sp": high_sp
    }

# ------------------------------------------------------------
#                   FAN CONTROL LOGIC
# ------------------------------------------------------------
def control_fan(settings):

    # DEMO MODE — ask for new temps EVERY cycle
    if settings["demo"]:
        if settings["mode"] == "1":  # demo indoor
            new_val = input("\nEnter DEMO indoor temperature (°F), or Enter to keep: ").strip()
            if new_val:
                settings["demo_in"] = float(new_val)
            temp = settings["demo_in"]
            print(f"[DEMO] Indoor Temperature: {temp}°F")

        else:  # demo outdoor
            new_val = input("\nEnter DEMO outdoor temperature (°F), or Enter to keep: ").strip()
            if new_val:
                settings["demo_out"] = float(new_val)
            temp = settings["demo_out"]
            print(f"[DEMO] Outdoor Temperature: {temp}°F")

    # REAL MODE
    else:
        if settings["mode"] == "1":
            temp = get_local_temp()
            src = "Local Sensor"
        else:
            temp = get_outdoor_temp()
            src = "Weather API"

        if temp is None:
            print(f"{src} unavailable — skipping.")
            return

        print(f"[{src}] Temperature: {temp}°F")

    # FAN LOGIC
    if temp < settings["low_th"]:
        set_fan_speed(settings["low_sp"])
    elif temp < settings["med_th"]:
        set_fan_speed(settings["med_sp"])
    else:
        set_fan_speed(settings["high_sp"])

# ------------------------------------------------------------
#                           MAIN
# ------------------------------------------------------------
try:
    settings = get_user_settings()
    print("\nSmart Fan running...\n")

    while True:
        control_fan(settings)
        time.sleep(2)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    pwm.stop()
    GPIO.cleanup()