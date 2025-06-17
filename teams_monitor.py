import time
import subprocess
import traceback
import psutil
from pycaw.pycaw import AudioUtilities
from paho.mqtt import client as mqtt_client
import logging
from logging.handlers import RotatingFileHandler
import os

# Setup rotating logs
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'teams_monitor.log')

logger = logging.getLogger('TeamsMonitor')
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(log_file, maxBytes=100_000, backupCount=3)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# MQTT config
BROKER = "your_mqtt_broker_ip"
PORT = 1883
TOPIC_MIC = "teams/microphone"
TOPIC_CAM = "teams/camera"

client = mqtt_client.Client()
client.connect(BROKER, PORT)

def is_microphone_active():
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        try:
            if session.Process and session.Process.name():
                if not session.SimpleAudioVolume.GetMute() and session.State == 1:
                    return True
        except Exception:
            continue
    return False

def is_webcam_in_use():
    try:
        result = subprocess.check_output(["handle.exe", "-a"], stderr=subprocess.DEVNULL, text=True)
        webcam_keys = ["vid", "usbvideo", "usb#vid", "camera"]
        for line in result.lower().splitlines():
            if any(key in line for key in webcam_keys):
                return True
    except Exception:
        logger.warning("Handle.exe detection failed")
    return False

def publish_status(mic_active, cam_active):
    mic_msg = "active" if mic_active else "muted"
    cam_msg = "on" if cam_active else "off"
    try:
        client.publish(TOPIC_MIC, mic_msg)
        client.publish(TOPIC_CAM, cam_msg)
        logger.info(f"Published: mic={mic_msg}, cam={cam_msg}")
    except Exception as e:
        logger.exception("MQTT publish failed")

def monitor_loop():
    while True:
        try:
            mic = is_microphone_active()
            cam = is_webcam_in_use()
            publish_status(mic, cam)
            time.sleep(5)
        except Exception:
            logger.exception("Monitoring loop crashed. Restarting...")
            time.sleep(3)

if __name__ == "__main__":
    logger.info("Starting Teams Presence Monitor")
    monitor_loop()
