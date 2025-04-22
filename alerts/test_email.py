# alerts/test_email.py
# This script provides a simple way to test the email notification functionality.

import logging # Import logging
import os
import sys

# Add project root to sys.path to allow importing config and notifier
# This makes the script runnable from the 'alerts' directory or the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from alerts.notifier import send_alert_email
import config

# --- Basic Logging Setup for Standalone Script ---
# If run standalone, configure basic logging to console
# If run after main.py, it will inherit the main config
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Send a Test Email ---
# Call the send_alert_email function with predefined test content.
# It uses the SMTP settings and recipient emails defined in config.py.
logger.info("Sending test email...")
send_alert_email(
    subject="🔔 Reolink-DetectAI Test Notification",
    body="This is a test email sent from the Reolink-DetectAI application.",
    # Use the list of emails from config.py
    to_emails=config.ALERT_EMAILS,
    image_path=None,  # Set to None to send without an attachment
    smtp_settings=config.SMTP_SETTINGS # Use SMTP settings from config
)
logger.info("Test email function called. Check recipient inbox(es) and console/log output for errors.")