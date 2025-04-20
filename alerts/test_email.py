# alerts/test_email.py
# This script provides a simple way to test the email notification functionality.

# Import the email sending function and the application configuration
from alerts.notifier import send_alert_email
import config

# --- Send a Test Email ---
# Call the send_alert_email function with predefined test content.
# It uses the SMTP settings and recipient emails defined in config.py.
print("[TEST] Sending test email...")
send_alert_email(
    subject="🔔 Reolink-DetectAI Test Notification",
    body="This is a test email sent from the Reolink-DetectAI application.",
    # Use the list of emails from config.py (Corrected from ALERT_EMAIL to ALERT_EMAILS)
    to_emails=config.ALERT_EMAILS, # Corrected parameter name from to_email to to_emails
    image_path=None,  # Set to None to send without an attachment
    smtp_settings=config.SMTP_SETTINGS # Use SMTP settings from config
)
print("[TEST] Test email function called. Check recipient inbox(es) and console output for errors.")