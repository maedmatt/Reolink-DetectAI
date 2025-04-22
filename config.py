# config.py
# Central configuration settings for the Reolink DetectAI application.

import os
from dotenv import load_dotenv
import logging

# Load .env into environment
load_dotenv(override=True)

# Initialize logger in case config is imported before main logging setup
# This avoids errors if logging is used within this file during import
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

# -----------------------------------------------------------------------------
# --- 1. Camera Stream Configuration ---
# -----------------------------------------------------------------------------
# Define camera streams. Keys are unique identifiers (e.g., "cam1"),
# values are dictionaries containing the RTSP URL and optional display name.
CAMERA_STREAMS = {}

# Look for camera stream environment variables
for i in range(1, 10):  # Support up to 9 cameras
    env_key = f"CAMERA_{i}_RTSP"
    rtsp_url = os.getenv(env_key)
    if rtsp_url:
        CAMERA_STREAMS[f"cam{i}"] = {
            "rtsp_url": rtsp_url,
            "display_name": os.getenv(f"CAMERA_{i}_NAME", f"Camera {i}")
        }

if not CAMERA_STREAMS:
    logging.warning("No camera streams found in environment variables. Check your .env file.")

# Settings related to stream handling and reconnection
STREAM_RECONNECT_DELAY = int(os.getenv("STREAM_RECONNECT_DELAY", 5))
FRAME_BUFFER_FLUSH = int(os.getenv("FRAME_BUFFER_FLUSH", 3))

# -----------------------------------------------------------------------------
# --- 2. Frame Processing & Buffering ---
# -----------------------------------------------------------------------------
MAX_FRAME_BUFFER_SIZE = int(os.getenv("MAX_FRAME_BUFFER_SIZE", 30))

# -----------------------------------------------------------------------------
# --- 3. Motion Detection Settings ---
# -----------------------------------------------------------------------------
# Controls the sensitivity of the basic motion detection algorithm.
PIXEL_DIFF_THRESHOLD = int(os.getenv("PIXEL_DIFF_THRESHOLD", 25))
                                # Higher = less sensitive to small changes (lighting, noise).
MOTION_AREA_THRESHOLD = int(os.getenv("MOTION_AREA_THRESHOLD", 1500))
                                # Higher = requires larger movements.

# -----------------------------------------------------------------------------
# --- 4. Object Detection (YOLOv8) Settings ---
# -----------------------------------------------------------------------------
# Configuration for the YOLO object detection model.
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")  # Path to the YOLOv8 model file (e.g., .pt).
YOLO_CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", 0.6))
                                # Higher = fewer, but more certain, detections.
# Expects comma-separated string in .env, e.g., "person,car"
DETECTION_CLASSES = ["person", "car"]
# Get base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DETECTIONS_DIR = os.path.join(BASE_DIR, "detections") # Directory to save annotated images (with bounding boxes).

# -----------------------------------------------------------------------------
# --- 5. Timing & Cooldowns ---
# -----------------------------------------------------------------------------
FRAME_CAPTURE_DELAY = float(os.getenv("FRAME_CAPTURE_DELAY", 0.5))
                                # Seconds to wait after initial motion detection before capturing
                                # the frame for object detection. Allows motion to stabilize.
DETECTION_COOLDOWN = float(os.getenv("DETECTION_COOLDOWN", 5.0))
                                # Seconds to wait *per camera* after a detection event before allowing
                                # another detection cycle for that specific camera.
EMAIL_COOLDOWN = float(os.getenv("EMAIL_COOLDOWN", 60.0))
                                # Minimum time in seconds between sending consecutive email alerts
                                # (currently applied per-camera in main.py).
                                # Prevents spamming if detections occur rapidly.

# -----------------------------------------------------------------------------
# --- 6. File Paths ---
# -----------------------------------------------------------------------------
CAPTURE_DIR = os.path.join(BASE_DIR, "captures") # Base directory to save raw captured frames upon motion+detection.
TRAINING_DATA_DIR = os.path.join(BASE_DIR, "training_data")
LOG_DIR = os.path.join(BASE_DIR, "logs")                   # Directory for log files (used in main.py logging setup).

# -----------------------------------------------------------------------------
# --- 7. Email Alert Configuration ---
# -----------------------------------------------------------------------------
# Loads settings from environment variables (expected in .env file).

# Required environment variables:
#   SMTP_SERVER=smtp.example.com
#   SMTP_PORT=465
#   SMTP_USER=sender@example.com
#   SMTP_PASSWORD=YOUR_APP_PASSWORD_OR_SECRET
#   ALERT_EMAILS=recipient1@example.com,recipient2@example.com

ALERT_EMAILS = []
_alert_recipients_str = os.getenv("ALERT_EMAILS")
if _alert_recipients_str:
    # Split the comma-separated string into a list, stripping whitespace
    ALERT_EMAILS = [email.strip() for email in _alert_recipients_str.split(',') if email.strip()]
else:
    logging.warning("Environment variable ALERT_EMAILS not set or empty. Email alerts will not be sent.")

SMTP_SETTINGS = {}
_smtp_server = os.getenv("SMTP_SERVER")
_smtp_port_str = os.getenv("SMTP_PORT")
_smtp_user = os.getenv("SMTP_USER")
_smtp_password = os.getenv("SMTP_PASSWORD")

if _smtp_server and _smtp_port_str and _smtp_user and _smtp_password:
    try:
        _smtp_port = int(_smtp_port_str) # Convert port to integer
        SMTP_SETTINGS = {
            "server": _smtp_server,
            "port": _smtp_port,
            "from_email": _smtp_user,
            "password": _smtp_password
        }
        # Log success without revealing password
        logging.info(f"SMTP settings loaded from environment: Server={_smtp_server}, Port={_smtp_port}, From={_smtp_user}")
    except ValueError:
        logging.error(f"Invalid SMTP_PORT environment variable: '{_smtp_port_str}'. Must be an integer.")
        SMTP_SETTINGS = {} # Ensure settings are invalid
else:
    missing_vars = []
    if not _smtp_server: missing_vars.append("SMTP_SERVER")
    if not _smtp_port_str: missing_vars.append("SMTP_PORT")
    if not _smtp_user: missing_vars.append("SMTP_USER")
    if not _smtp_password: missing_vars.append("SMTP_PASSWORD")
    logging.warning(f"Missing required SMTP environment variables: {', '.join(missing_vars)}. Email alerts will be disabled.")

# --- Log Email Configuration Status ---
if SMTP_SETTINGS.get("from_email") and SMTP_SETTINGS.get("password") and ALERT_EMAILS:
    logging.info(f"Email alerting configured: Server={SMTP_SETTINGS['server']}:{SMTP_SETTINGS['port']}, From={SMTP_SETTINGS['from_email']}, Recipients={len(ALERT_EMAILS)}")
else:
    logging.warning("Email alerting partially or fully unconfigured. Check SMTP_USER, SMTP_PASSWORD, ALERT_EMAILS environment variables.")
    # Ensure dict is usable even if unconfigured, prevents KeyErrors later
    if "from_email" not in SMTP_SETTINGS: SMTP_SETTINGS["from_email"] = None
    if "password" not in SMTP_SETTINGS: SMTP_SETTINGS["password"] = None