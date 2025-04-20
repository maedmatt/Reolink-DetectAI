# alerts/notifier.py
# This module contains functions for sending notifications, currently focused on email alerts.

import smtplib
import os
from email.message import EmailMessage
# Consider adding 'imghdr' to determine image subtype dynamically
# import imghdr

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
            WARNING: Passing passwords directly is insecure. Use environment variables
                     or a secure configuration method.
    """
    print(f"[ALERT] Preparing email for: {', '.join(to_emails)}")

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
                subtype = "jpeg" # Currently hardcoded

                msg.add_attachment(
                    img_data,
                    maintype="image",
                    subtype=subtype, # Use determined subtype
                    filename=os.path.basename(image_path) # Use the image's filename
                )
            print(f"[ALERT] Attached image: {os.path.basename(image_path)}")
        except IOError as e:
            print(f"[ERROR] Could not read or attach image file {image_path}: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error attaching image {image_path}: {e}")
    elif image_path:
        print(f"[WARN] Image path provided but file not found: {image_path}. Not attaching image.")
    else:
        print("[ALERT] No image path provided. Not attaching image.")

    # --- Send Email via SMTP --- 
    try:
        # Connect to the SMTP server using SSL
        with smtplib.SMTP_SSL(smtp_settings["server"], smtp_settings["port"]) as smtp:
            # Log in to the SMTP server
            # SECURITY WARNING: Uses password directly from smtp_settings
            smtp.login(smtp_settings["from_email"], smtp_settings["password"])
            # Send the complete email message
            smtp.send_message(msg)
        print(f"[ALERT] Email sent successfully to: {msg['To']}")
    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERROR] SMTP Authentication failed for {smtp_settings['from_email']}: {e}")
        print("        Check email address and password/app password.")
    except smtplib.SMTPException as e:
        print(f"[ERROR] Failed to send email via SMTP ({smtp_settings['server']}:{smtp_settings['port']}): {e}")
    except OSError as e:
        # Catches potential network/socket errors
        print(f"[ERROR] Network error connecting to SMTP server {smtp_settings['server']}: {e}")
    except Exception as e:
        # Catch any other unexpected errors during SMTP communication
        print(f"[ERROR] Unexpected error sending email: {e}")