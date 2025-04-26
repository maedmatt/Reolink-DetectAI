# alerts/notifier.py
# Email notification system for object detection alerts

import smtplib
import os
import logging
from email.message import EmailMessage
from email.utils import make_msgid

# Get a logger instance for this module
logger = logging.getLogger(__name__)

def send_alert_email(body, to_emails, image_path, smtp_settings):
    """
    Sends an email alert with an optional detected object image.
    
    Creates and sends an email notification when objects are detected,
    including the detected image with bounding boxes to help users
    quickly verify the detection.
    
    Args:
        subject: Email subject line (will be ignored in favor of fixed subject)
        body: Plain text email content
        to_emails: List of recipient email addresses
        image_path: Path to detection image to attach (or None)
        smtp_settings: Dictionary with email server settings:
                      {server, port, from_email, password}
    """
    logger.info(f"Preparing email alert for: {', '.join(to_emails)}")

    # Create email message with fixed subject for threading
    msg = EmailMessage()
    msg["Subject"] = "Reolink Detection Alert"
    msg["From"] = smtp_settings["from_email"]
    msg["To"] = ", ".join(to_emails)
    
    # Add email threading headers to keep emails in the same thread
    # Use a fixed Message-ID reference for the thread
    thread_id = smtp_settings.get("thread_id", make_msgid(domain=smtp_settings["server"]))
    
    # If this is the first message, it establishes the thread
    # Otherwise, it references the original thread
    if smtp_settings.get("is_first_message", True):
        # Store the thread ID for future messages
        smtp_settings["thread_id"] = thread_id
        smtp_settings["is_first_message"] = False
    else:
        msg["In-Reply-To"] = thread_id
        msg["References"] = thread_id
    
    msg.set_content(body)

    # Attach image if available
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img:
                img_data = img.read()
                subtype = os.path.splitext(image_path)[1].lstrip('.') or "jpeg"

                msg.add_attachment(
                    img_data,
                    maintype="image",
                    subtype=subtype,
                    filename=os.path.basename(image_path)
                )
            logger.info(f"Attached image: {os.path.basename(image_path)}")
        except IOError as e:
            logger.error(f"Could not read image file {image_path}: {e}")
        except Exception as e:
            logger.exception(f"Error attaching image {image_path}: {e}")
    elif image_path:
        logger.warning(f"Image not found: {image_path}")
    else:
        logger.info("No image path provided")

    # Send email via SMTP 
    try:
        with smtplib.SMTP_SSL(smtp_settings["server"], smtp_settings["port"]) as smtp:
            smtp.login(smtp_settings["from_email"], smtp_settings["password"])
            smtp.send_message(msg)
        logger.info(f"Email sent successfully to: {msg['To']}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {e}")
        logger.error("Check email address and password/app password")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
    except OSError as e:
        logger.error(f"Network error connecting to SMTP server: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error sending email: {e}")