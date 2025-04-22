# alerts/notifier.py
# This module contains functions for sending notifications, currently focused on email alerts.

import smtplib
import os
import logging # Import logging
from email.message import EmailMessage
# Consider adding 'imghdr' to determine image subtype dynamically for broader support
# import imghdr

# Get a logger instance for this module
logger = logging.getLogger(__name__)

def send_alert_email(subject, body, to_emails, image_path, smtp_settings):
    """
    Constructs and sends an email alert using SMTP.

    Optionally attaches an image file to the email.

    Args:
        subject (str): The subject line of the email.
        body (str): The main text content of the email.
        to_emails (list): A list of recipient email addresses.
        image_path (str or None): Path to the image file to attach. If None or the
                                  path doesn't exist, no image is attached.
        smtp_settings (dict): A dictionary containing SMTP configuration:
            { "server": str, "port": int, "from_email": str, "password": str }
            WARNING: Passing passwords directly is insecure. Consider using environment
                     variables or a secure configuration method.
    """
    logger.info(f"Preparing email alert for: {', '.join(to_emails)}")

    # Create the email message object
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_settings["from_email"]
    # Format the recipient list for the 'To' header
    msg["To"] = ", ".join(to_emails)
    # Set the plain text body content
    msg.set_content(body)

    # --- Attach Image (if provided and exists) ---
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img:
                img_data = img.read()
                # Determine image subtype (e.g., 'jpeg', 'png') dynamically if needed
                # subtype = imghdr.what(None, h=img_data)
                subtype = os.path.splitext(image_path)[1].lstrip('.') or "jpeg" # Basic subtype from extension

                msg.add_attachment(
                    img_data,
                    maintype="image",
                    subtype=subtype, # Use determined subtype
                    filename=os.path.basename(image_path)
                )
            logger.info(f"Attached image: {os.path.basename(image_path)}")
        except IOError as e:
            logger.error(f"Could not read image file {image_path}: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error attaching image {image_path}: {e}")
    elif image_path:
        logger.warning(f"Image path provided but file not found: {image_path}. Not attaching image.")
    else:
        logger.info("No image path provided. Not attaching image.")

    # --- Send Email via SMTP --- 
    try:
        # Connect to the SMTP server using SSL
        with smtplib.SMTP_SSL(smtp_settings["server"], smtp_settings["port"]) as smtp:
            # Log in to the SMTP server
            # SECURITY WARNING: Uses password directly from smtp_settings
            smtp.login(smtp_settings["from_email"], smtp_settings["password"])
            # Send the complete email message
            smtp.send_message(msg)
        logger.info(f"Email sent successfully to: {msg['To']}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed for {smtp_settings['from_email']}: {e}")
        logger.error("Check email address and password/app password.") # Keep specific advice
    except smtplib.SMTPException as e:
        logger.error(f"Failed to send email via SMTP ({smtp_settings['server']}:{smtp_settings['port']}): {e}")
    except OSError as e:
        # Catches potential network/socket errors
        logger.error(f"Network error connecting to SMTP server {smtp_settings['server']}: {e}")
    except Exception as e:
        # Catch any other unexpected errors during SMTP communication
        logger.exception(f"Unexpected error sending email: {e}")