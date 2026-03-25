# 🌡️ IoT Climate Control System

Automated fan speed control using real-time indoor and outdoor temperature data, built with Raspberry Pi 4, Python, and the NWS Weather API.

---

## Hardware Components

| Component | Purpose |
|---|---|
| Raspberry Pi 4 | Main controller |
| L298N Motor Driver | PWM speed control |
| DS18B20 Temperature Sensor | Local indoor temperature readings |
| DC Motor + 3D-Printed Fan Blade | Fan actuator |
| 5V Adapter / Power Bank | Power supply |

---

## Features

- **Dual temperature sources** — choose between a local DS18B20 sensor or live NWS Weather API data
- **PWM fan speed control** — three-tier speed control (Low / Medium / High) via L298N motor driver
- **User-configurable** — set custom temperature thresholds and fan speed percentages at startup
- **Demo mode** — simulate temperature inputs for testing without sensor changes
- **Windows testing** — `test_fan_windows.py` mocks GPIO and sensor hardware for development on non-Pi machines

---

## Files

| File | Description |
|---|---|
| `fan.py` | Main script, runs on Raspberry Pi |
| `test_fan_windows.py` | Windows-compatible version with mocked GPIO and simulated sensor data |

---

## How It Works

```
Temperature Source (Sensor or API)
           │
           ▼
   Read Temperature (°F)
           │
  temp < low_threshold   →  LOW speed   (default: 0%)
  temp < med_threshold   →  MED speed   (default: 50%)
  temp ≥ med_threshold   →  HIGH speed  (default: 100%)
           │
           ▼
   PWM Signal → L298N → DC Motor
```

The control loop runs every 2 seconds, continuously adjusting fan speed based on the latest temperature reading.

---

## Authors
Ethan Charo, Theo Perez, Abraham Elkhatib
