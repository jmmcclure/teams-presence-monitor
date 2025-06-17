import os
import time
import platform
import subprocess
import shutil
import logging
import configparser
import requests
from logging.handlers import RotatingFileHandler
from pycaw.pycaw import AudioUtilities
from paho.mqtt import client as mqtt_client

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# General settings
poll_interval = config.getint('general', 'poll_interval', fallback=5)

# Logging settings
log_dir = config.get('logging', 'log_dir', fallback='logs')
max_log_size = config.getint('logging', 'max_size', fallback=100_000)
log_backups = config.getint('logging', 'backup_count', fallback=3)
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'teams_monitor.log')

# Logging setup
logger = logging.getLogger('TeamsMonitor')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=log_backups)
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(handler)

# MQTT config
mqtt_enabled = config.getboolean('mqtt', 'enable', fallback=False)
if mqtt_enabled:
    mqtt_broker = config.get('mqtt', 'broker')
    mqtt_port = config.getint('mqtt', 'port', fallback=1883)
    topic_mic = config.get('mqtt', 'topic_mic')
    topic_cam = config.get('mqtt', 'topic_cam')
    mqtt = mqtt_client.Client()
    try:
        mqtt.connect(mqtt_broker, mqtt_port)
    except Exception as e:
        logger.exception("Failed to connect to MQTT broker")

# Home Assistant config
ha_enabled = config.getboolean('homeassistant', 'enable', fallback=False)
ha_url = config.get('homeassistant', 'base_url', fallback='')
ha_mic = config.get('homeassistant', 'webhook_mic', fallback='')
ha_cam = config.get('homeassistant', 'webhook_cam', fallback='')

def get_handle_exe():
    exe = "handle64.exe" if platform.machine().endswith("64") else "handle.exe"
    path = shutil.which(exe)
    if path:
        return path
    fallback = os.path.join(os.path.dirname(__file__), exe)
    return fallback if os.path.exists(fallback) else None

def is_microphone_active():
    try:
        for session in AudioUtilities.GetAllSessions():
            if session.Process and not session.SimpleAudioVolume.GetMute() and session.State == 1:
                return True
    except Exception as e:
        logger.warning(f"Mic detection failed: {e}")
    return False

def is_webcam_in_use():
    exe = get_handle_exe()
    if not exe:
        logger.warning("handle.exe not found")
        return False
    try:
        output = subprocess.check_output([exe, "-a"], stderr=subprocess.DEVNULL, text=True)
        for line in output.lower().splitlines():
            if any(tag in line for tag in ["usbvideo", "usb#vid", "vid_", "camera"]):
                return True
    except Exception as e:
        logger.warning(f"Camera detection failed: {e}")
    return False

def publish_status(mic_active, cam_active):
    mic_msg = "active" if mic_active else "muted"
    cam_msg = "on" if cam_active else "off"

    if mqtt_enabled:
        try:
            mqtt.publish(topic_mic, mic_msg)
            mqtt.publish(topic_cam, cam_msg)
            logger.info(f"MQTT published: mic={mic_msg}, cam={cam_msg}")
        except Exception:
            logger.exception("MQTT publish failed")

    if ha_enabled:
        try:
            mic_url = f"{ha_url}/api/webhook/{ha_mic}"
            cam_url = f"{ha_url}/api/webhook/{ha_cam}"
            requests.post(mic_url, json={"state": mic_msg}, timeout=2)
            requests.post(cam_url, json={"state": cam_msg}, timeout=2)
            logger.info(f"HA webhooks sent: mic={mic_msg}, cam={cam_msg}")
        except Exception as e:
            logger.warning(f"Home Assistant webhook failed: {e}")

def monitor_loop():
    logger.info("Teams Presence Monitor started")
    while True:
        try:
            mic = is_microphone_active()
            cam = is_webcam_in_use()
            publish_status(mic, cam)
            time.sleep(poll_interval)
        except Exception:
            logger.exception("Loop crashed — restarting in 3 seconds")
            time.sleep(3)

if __name__ == "__main__":
    monitor_loop()
