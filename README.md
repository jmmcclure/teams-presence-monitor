# Teams Presence Monitor

Monitor your Microsoft Teams mic and webcam status and stream it to MQTT for real-time ESPHome automation. Run it in the background, install it as a Windows service, and trigger physical indicators when you’re "live."

## 💡 How It Works
Subscribes to teams/microphone and teams/camera
When the mic goes active, it turns on the LED (GPIO2 is the onboard LED for many ESP32 dev boards)
You can expand this easily to display status on an OLED, blink multiple LEDs, or drive a relay

## 🚀 Extension Ideas
Swap status_led for a multi-color RGB light that shows mic/cam status simultaneously
Use a small OLED or ePaper screen to show both mic/camera states with icons
Build a desktop cube with different light faces for “Mic Hot” and “Camera On”

## 🔧 Features

- 🎙️ System-level mic activity detection via Core Audio (pycaw)
- 📷 Webcam usage detection using Sysinternals Handle
- 📡 MQTT broadcast for ESPHome smart devices
- ♻️ Built-in watchdog to auto-restart on crash
- 📜 Rotating log files with up to 3 backups

---

## 🚀 Quick Setup

1. Clone or unzip the repo
2. Install Python packages:
   ```bash
   pip install -r requirements.txt

ESPHome Integration

sensor:
  - platform: mqtt_subscribe
    name: "Teams Mic"
    topic: "teams/microphone"

  - platform: mqtt_subscribe
    name: "Teams Camera"
    topic: "teams/camera"



## 🗜 Logging
Logs are stored in logs/teams_monitor.log

Each log rotates after 100 KB (3 files kept)

## 📁 Logs
All logs are written to logs/teams_monitor.log and rotated automatically:
   Max size: 100 KB per log
   Retention: 3 latest files

Check here for watchdog restarts, MQTT failures, or Bluetooth issues if re-enabled.

## 🧰 Advanced Usage & Ideas
   - 🛡️ Auto-start at boot	Use NSSM or Task Scheduler
   - 📦 Bundle as EXE	Use pyinstaller to generate a one-click app
   - 🔔 Alert on hot mic	Add email/Discord/TTS alerts inside publish_status()
   - 🧪 Add GUI preview	Use tkinter or pystray for tray icon status
   - 🛠️ Add config file	Externalize MQTT IP & interval to .ini or .yaml
   - 📋 Health API	Serve a local Flask HTTP endpoint for HA to poll
   - 🧩 Push updates	Use paho-mqtt's retain flag or birth messages for state memory
   - 🖥️ Show overlay	Use WinAPI or AutoHotKey to render mic/cam status visually
   - 👀 GUI overlay	Add a tray icon or floating widget
   - 🧱 ESP automation	Use on_value: to trigger lights/displays
   
## 🪄 Future Enhancements (Ideas)
   - Support Zoom/Google Meet by detecting process + device state
   - Add webhook sender for Home Assistant without MQTT
   - Write system tray app with color-coded icon (🟢 muted / 🔴 hot mic)
   - Package with installer for plug-and-play deployment

## 🔌 Hardware Expansion Ideas
   - 🌈 Swap status_led for RGB strip to show mic/camera states
   - 🖥️ Use OLED, LCD, or ePaper for text/icons display
   - 📦 Build a light-up desktop cube with sides for "Mic On" and "Camera On"

## 🛡 License
MIT — free to use, adapt, and share without restriction.

## 🙌 Credits
Crafted by Jason with precision, resilience, and a touch of ESPHome magic. Polished in partnership with Copilot.
