import os
import time
import platform
import subprocess
import shutil
import logging
import configparser
import requests
import argparse
from logging.handlers import RotatingFileHandler
from pycaw.pycaw import AudioUtilities
from paho.mqtt import client as mqtt_client
from rich.console import Console
from rich.panel import Panel

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# General config
poll_interval = config.getint('general', 'poll_interval', fallback=5)
monitor_mic = config.getboolean('general', 'monitor_microphone', fallback=True)
monitor_cam = config.getboolean('general', 'monitor_camera', fallback=True)

# Logging config
log_dir = config.get('logging', 'log_dir', fallback='logs')
max_log_size = config.getint('logging', 'max_size', fallback=100_000)
log_backups = config.getint('logging', 'backup_count', fallback=3)
log_to_console_cfg = config.getboolean('logging', 'show_console', fallback=True)
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'teams_monitor.log')

# CLI arg parsing
parser = argparse.ArgumentParser(description="Teams Presence Monitor")
parser.add_argument('--debug', action='store_true', help='Force console logging')
args = parser.parse_args()
log_to_console = log_to_console_cfg or args.debug

# Set up logger
logger = logging.getLogger('TeamsMonitor')
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=log_backups)
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(file_handler)

# Optional console logging
if log_to_console:
    try:
        import colorlog
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'bold_red',
            }
        ))
        logger.addHandler(console_handler)
    except ImportError:
        fallback_handler = logging.StreamHandler()
        fallback_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logger.addHandler(fallback_handler)
        logger.warning("colorlog not found—console logging without colors")

# Rich dashboard
console = Console()

# MQTT setup
mqtt = None
mqtt_enabled = config.getboolean('mqtt', 'enable', fallback=False)
if mqtt_enabled:
    mqtt_broker = config.get('mqtt', 'broker')
    mqtt_port = config.getint('mqtt', 'port', fallback=1883)
    topic_mic = config.get('mqtt', 'topic_mic')
    topic_cam = config.get('mqtt', 'topic_cam')

    try:
        mqtt = mqtt_client.Client(client_id="", protocol=mqtt_client.MQTTv5, callback_api_version=5)
        mqtt.connect(mqtt_broker, mqtt_port)
    except TypeError:
        logger.warning("MQTTv5 not supported—falling back to MQTT v3.1.1")
        mqtt = mqtt_client.Client(protocol=mqtt_client.MQTTv311)
        mqtt.connect(mqtt_broker, mqtt_port)
    except Exception as e:
        mqtt = None
        logger.warning(f"MQTT setup failed: {e}")

# Home Assistant setup
ha_enabled = config.getboolean('homeassistant', 'enable', fallback=False)
ha_url = config.get('homeassistant', 'base_url', fallback='')
ha_mic = config.get('homeassistant', 'webhook_mic', fallback='')
ha_cam = config.get('homeassistant', 'webhook_cam', fallback='')

def get_handle_exe():
    exe = "handle64.exe" if platform.machine().endswith("64") else "handle.exe"
    path = shutil.which(exe)
    fallback = os.path.join(os.path.dirname(__file__), exe)
    return path or fallback if os.path.exists(fallback) else None

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
    if not exe or not os.path.exists(exe):
        logger.warning("handle.exe not found")
        return False
    try:
        output = subprocess.check_output([exe, "-a"], stderr=subprocess.DEVNULL, text=True)
        for line in output.lower().splitlines():
            if any(tag in line for tag in ["usbvideo", "usb#vid", "vid_", "camera"]):
                return True
    except subprocess.CalledProcessError:
        logger.warning("handle.exe returned non-zero exit status")
    except Exception as e:
        logger.warning(f"Camera detection failed: {e}")
    return False

def publish_status(mic_active, cam_active):
    mic_msg = "active" if mic_active else "muted"
    cam_msg = "on" if cam_active else "off"

    if mqtt_enabled and mqtt:
        try:
            if monitor_mic:
                mqtt.publish(topic_mic, mic_msg)
            if monitor_cam:
                mqtt.publish(topic_cam, cam_msg)
            logger.info(f"MQTT published: mic={mic_msg}, cam={cam_msg}")
        except Exception:
            logger.exception("MQTT publish failed")

    if ha_enabled:
        try:
            if monitor_mic:
                mic_url = f"{ha_url}/api/webhook/{ha_mic}"
                requests.post(mic_url, json={"state": mic_msg}, timeout=2)
            if monitor_cam:
                cam_url = f"{ha_url}/api/webhook/{ha_cam}"
                requests.post(cam_url, json={"state": cam_msg}, timeout=2)
            logger.info(f"HA webhooks sent: mic={mic_msg}, cam={cam_msg}")
        except Exception as e:
            logger.warning(f"Home Assistant webhook failed: {e}")

    if log_to_console:
        lines = []
        if monitor_mic:
            mic_str = "[bold green]ACTIVE[/bold green]" if mic_active else "[bold red]MUTED[/bold red]"
            lines.append(f"🎙️ Microphone: {mic_str}")
        if monitor_cam:
            cam_str = "[bold green]ON[/bold green]" if cam_active else "[bold red]OFF[/bold red]"
            lines.append(f"📷 Camera:     {cam_str}")
        console.clear()
        console.print(Panel.fit("\n".join(lines), title="Teams Presence Monitor"))

def monitor_loop():
    logger.info("Teams Presence Monitor started")
    while True:
        try:
            mic = is_microphone_active() if monitor_mic else False
            cam = is_webcam_in_use() if monitor_cam else False
            publish_status(mic, cam)
            time.sleep(poll_interval)
        except Exception:
            logger.exception("Loop error—retrying in 3 seconds")
            time.sleep(3)

if __name__ == "__main__":
    monitor_loop()
