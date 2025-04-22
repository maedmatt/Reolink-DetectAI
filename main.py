import cv2
import time
import os
import config
import logging # Import logging
import logging.handlers # For file handler
from collections import deque # Import deque for frame buffers

# --- Custom Modules ---
# Import necessary components
# Removed StreamHandler, added StreamManager
from camera_streams.stream_manager import StreamManager
from camera_streams.motion_detector import MotionDetector
from camera_streams.inference_engine import InferenceEngine
from utils.helpers import generate_capture_path # generate_capture_path already handles camera_id
from alerts.notifier import send_alert_email

# --- Global Logger Setup ---
# Create logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger() # Get root logger
logger.setLevel(logging.DEBUG) # Set minimum logging level

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# File Handler (Rotates logs, keeping 5 backups of 5MB each)
# Use RotatingFileHandler for production to prevent log files from growing indefinitely
# file_handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5)
# For simplicity in this learning project, using a standard FileHandler:
file_handler = logging.FileHandler(LOG_FILE, mode='a') # Append mode
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Get a logger instance specific to this module (optional, inherits root config)
# logger = logging.getLogger(__name__)

def main():
    """
    Main function to initialize components and run the detection loop
    for multiple camera streams.
    """
    logging.info("Starting reolink-detectai...")

    # --- Initialization ---
    # Initialize the stream manager (starts fetching frames from all cameras)
    stream_manager = StreamManager()

    # Initialize Inference Engine (shared by all streams)
    inference = InferenceEngine()

    # Ensure the base directories exist
    os.makedirs(config.CAPTURE_DIR, exist_ok=True)
    os.makedirs(config.DETECTIONS_DIR, exist_ok=True)
    os.makedirs(config.TRAINING_DATA_DIR, exist_ok=True) # Ensure training dir exists too

    # --- Per-Camera State Initialization ---
    # Use dictionaries to store state for each camera_id defined in config
    camera_ids = list(config.CAMERA_STREAMS.keys())
    motion_detectors = {
        cam_id: MotionDetector(
            threshold=config.PIXEL_DIFF_THRESHOLD,
            min_area=config.MOTION_AREA_THRESHOLD
        ) for cam_id in camera_ids
    }
    # Frame buffers using deque with max length
    frame_buffers = {
        cam_id: deque(maxlen=config.MAX_FRAME_BUFFER_SIZE) for cam_id in camera_ids
    }
    # Cooldown timers, initialized to 0
    last_alert_times = {cam_id: 0 for cam_id in camera_ids}
    last_email_times = {cam_id: 0 for cam_id in camera_ids}

    logging.info(f"Initialized components for cameras: {', '.join(camera_ids)}")

    try:
        # --- Main Processing Loop ---
        while True:
            # 1. Get the next available frame from any stream
            camera_id, frame = stream_manager.get_frame(timeout=1.0) # Wait up to 1 second

            # --- Check if a frame was received ---
            if camera_id is None:
                # Timeout occurred, no frame received from any stream
                continue # Skip rest of the loop and try getting a frame again

            # Store the frame in the buffer for the corresponding camera
            frame_buffers[camera_id].append(frame)

            # 2. Motion Detection (using the detector specific to this camera_id)
            motion_detector = motion_detectors[camera_id]
            motion_detected, score = motion_detector.detect(frame)

            current_time = time.time()
            # Check if this camera is in its detection cooldown period
            in_cooldown = (current_time - last_alert_times[camera_id]) < config.DETECTION_COOLDOWN

            # 3. Process Motion Event (if detected and not in cooldown for this camera)
            if motion_detected and not in_cooldown:
                # Optional delay
                time.sleep(config.FRAME_CAPTURE_DELAY)
                logging.info(f"[{camera_id} - MOTION DETECTED] Score: {score:.2f}")

                # --- Frame Saving --- 
                image_path = None # Initialize image_path
                save_successful = False
                try:
                    # 4. Generate Path & Save Frame (raw frame before inference)
                    image_path = generate_capture_path(
                        camera_id=camera_id,
                        base_dir=config.CAPTURE_DIR
                    )
                    # Make sure the directory exists before saving
                    img_dir = os.path.dirname(image_path)
                    os.makedirs(img_dir, exist_ok=True)

                    logging.info(f"[{camera_id} - INFO] Attempting to save frame to: {image_path}")
                    
                    # Attempt to save the frame
                    save_successful = cv2.imwrite(image_path, frame)
                    
                    if save_successful:
                        logging.info(f"[{camera_id} - INFO] Frame successfully saved to: {image_path}")
                    else:
                        # cv2.imwrite might not return False reliably, but we check anyway
                        logging.warning(f"[{camera_id} - WARN] cv2.imwrite returned False for path: {image_path}. Check permissions and disk space.")
                        # Explicitly set false if imwrite returned false/None
                        save_successful = False 

                except Exception as e:
                    logging.exception(f"[{camera_id} - ERROR] Failed during frame saving process for path {image_path or 'unknown'}: {e}")
                    save_successful = False # Ensure flag is false on exception

                # --- Inference & Alerting (only if frame saving was successful) ---
                if save_successful and image_path:
                    # 5. Object Detection (Inference)
                    logging.info(f"[{camera_id} - INFO] Running inference on: {image_path}") # Log before inference
                    # Pass camera_id for correct output folder organization
                    detections = inference.run(image_path, camera_id=camera_id)

                    # 6. Process Detections & Alerting
                    if detections:
                        # Update the last successful detection time for this camera
                        last_alert_times[camera_id] = current_time
                        # Use a set for efficient checking of required labels
                        detected_labels = set(d["label"] for d in detections)
                        logging.info(f"[{camera_id} - ALERT] Detected: {list(detected_labels)}")

                        # --- Email Alert Condition ---
                        # Check if EITHER person or car is detected
                        required_labels_for_alert = {"person", "car"}
                        # Check if any of the required labels are present in the detected labels
                        alert_condition_met = any(label in detected_labels for label in required_labels_for_alert)

                        # Check if email cooldown for this camera has passed
                        email_cooldown_passed = (current_time - last_email_times[camera_id]) >= config.EMAIL_COOLDOWN

                        if alert_condition_met and email_cooldown_passed:
                            # Reconstruct path to the annotated image saved by inference.run
                            # (This relies on inference.run saving correctly with timestamp)
                            timestamp = os.path.splitext(os.path.basename(image_path))[0]
                            annotated_path = os.path.join(config.DETECTIONS_DIR, camera_id, f"{timestamp}.jpg")

                            if os.path.exists(annotated_path):
                                # Construct a more dynamic subject/body based on what was detected
                                detected_alert_labels = list(detected_labels.intersection(required_labels_for_alert))
                                subject = f"🔔 Alert [{camera_id}]: { ' or '.join(detected_alert_labels).capitalize() } Detected"
                                body = f"Detected { ' or '.join(detected_alert_labels) } on camera {camera_id}. All labels: {list(detected_labels)}"
                                
                                send_alert_email(
                                    subject=subject,
                                    body=body,
                                    to_emails=config.ALERT_EMAILS,
                                    image_path=annotated_path,
                                    smtp_settings=config.SMTP_SETTINGS
                                )
                                # Update the last email time for this camera
                                last_email_times[camera_id] = current_time
                                logging.info(f"[{camera_id} - INFO] Email alert sent for { ' or '.join(detected_alert_labels) }.")
                            else:
                                logging.warning(f"[{camera_id} - WARN] Annotated image not found for alert: {annotated_path}")
                        elif alert_condition_met:
                            detected_alert_labels = list(detected_labels.intersection(required_labels_for_alert))
                            logging.info(f"[{camera_id} - INFO] { ' or '.join(detected_alert_labels).capitalize() } detected, but email cooldown active.")
                        # else: # Optional: Log if other detections happened but didn't meet alert criteria
                        #     logging.debug(f"[{camera_id} - DEBUG] Detections occurred but did not meet alert criteria (Person OR Car). Labels: {list(detected_labels)}")

    except KeyboardInterrupt:
        logging.info("\nKeyboard interrupt received. Exiting gracefully...")
    except Exception as e:
        logging.exception(f"\nAn unexpected error occurred in the main loop: {e}") # Use logging.exception to include traceback
        # import traceback
        # traceback.print_exc() # No longer needed, logging.exception handles it
    finally:
        # --- Graceful Shutdown ---
        # Ensure StreamManager is stopped regardless of how the loop exits
        if 'stream_manager' in locals():
            stream_manager.stop() # StreamManager should use logging internally now
        logging.info("Application shut down.")

# --- Script Execution ---
if __name__ == "__main__":
    main()