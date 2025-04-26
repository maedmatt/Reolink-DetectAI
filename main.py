import cv2
import time
import os
import config
import logging
import logging.handlers
from collections import deque

# Import components from custom modules
from camera_streams.stream_manager import StreamManager
from camera_streams.motion_detector import MotionDetector
from camera_streams.inference_engine import InferenceEngine
from utils.helpers import generate_capture_path
from alerts.notifier import send_alert_email

# Set up logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(LOG_FILE, mode='a')
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

def main():
    """
    Main application function that implements the detection workflow:
    1. Capture frames from multiple camera streams
    2. Detect motion to trigger analysis
    3. Run object detection on frames with motion
    4. Send alerts when configured objects are detected
    """
    logging.info("Starting reolink-detectai...")

    # Initialize components
    stream_manager = StreamManager()
    inference = InferenceEngine()

    # Create required directories
    os.makedirs(config.CAPTURE_DIR, exist_ok=True)
    os.makedirs(config.DETECTIONS_DIR, exist_ok=True)
    os.makedirs(config.TRAINING_DATA_DIR, exist_ok=True)

    # Create per-camera objects and state tracking
    camera_ids = list(config.CAMERA_STREAMS.keys())
    
    # Create motion detector for each camera with configured thresholds
    motion_detectors = {
        cam_id: MotionDetector(
            threshold=config.PIXEL_DIFF_THRESHOLD,
            min_area=config.MOTION_AREA_THRESHOLD
        ) for cam_id in camera_ids
    }
    
    # Buffer to store recent frames
    frame_buffers = {
        cam_id: deque(maxlen=config.MAX_FRAME_BUFFER_SIZE) for cam_id in camera_ids
    }
    
    # Timestamps for cooldown periods
    last_alert_times = {cam_id: 0 for cam_id in camera_ids}
    last_email_times = {cam_id: 0 for cam_id in camera_ids}

    logging.info(f"Initialized components for cameras: {', '.join(camera_ids)}")

    try:
        # Main processing loop
        while True:
            # Get frame from any available camera
            camera_id, frame = stream_manager.get_frame(timeout=1.0)

            if camera_id is None:
                continue

            # Store frame in buffer
            frame_buffers[camera_id].append(frame)

            # Perform motion detection
            motion_detector = motion_detectors[camera_id]
            motion_detected, score = motion_detector.detect(frame)

            # Check if in cooldown period
            current_time = time.time()
            in_cooldown = (current_time - last_alert_times[camera_id]) < config.DETECTION_COOLDOWN

            # Process if motion detected and not in cooldown
            if motion_detected and not in_cooldown:
                time.sleep(config.FRAME_CAPTURE_DELAY)
                logging.info(f"[{camera_id} - MOTION DETECTED] Score: {score:.2f}")

                # Save the detected frame
                image_path = None
                save_successful = False
                try:
                    image_path = generate_capture_path(
                        camera_id=camera_id,
                        base_dir=config.CAPTURE_DIR
                    )
                    img_dir = os.path.dirname(image_path)
                    os.makedirs(img_dir, exist_ok=True)

                    logging.info(f"[{camera_id} - INFO] Attempting to save frame to: {image_path}")
                    
                    save_successful = cv2.imwrite(image_path, frame)
                    
                    if save_successful:
                        logging.info(f"[{camera_id} - INFO] Frame successfully saved to: {image_path}")
                    else:
                        logging.warning(f"[{camera_id} - WARN] Failed to save frame to: {image_path}")
                        save_successful = False 

                except Exception as e:
                    logging.exception(f"[{camera_id} - ERROR] Failed to save frame: {e}")
                    save_successful = False

                # Run object detection if frame was saved
                if save_successful and image_path:
                    logging.info(f"[{camera_id} - INFO] Running inference on: {image_path}")
                    detections = inference.run(image_path, camera_id=camera_id)

                    # Process detected objects
                    if detections:
                        last_alert_times[camera_id] = current_time
                        detected_labels = set(d["label"] for d in detections)
                        logging.info(f"[{camera_id} - ALERT] Detected: {list(detected_labels)}")

                        # Check if person or car detected
                        required_labels_for_alert = {"person", "car"}
                        alert_condition_met = any(label in detected_labels for label in required_labels_for_alert)
                        email_cooldown_passed = (current_time - last_email_times[camera_id]) >= config.EMAIL_COOLDOWN

                        if alert_condition_met and email_cooldown_passed:
                            # Get path to the annotated detection image
                            timestamp = os.path.splitext(os.path.basename(image_path))[0]
                            annotated_path = os.path.join(config.DETECTIONS_DIR, camera_id, f"{timestamp}.jpg")

                            if os.path.exists(annotated_path):
                                detected_alert_labels = list(detected_labels.intersection(required_labels_for_alert))
                                body = f"Detected { ' or '.join(detected_alert_labels) } on camera {camera_id}. All labels: {list(detected_labels)}"
                                
                                send_alert_email(
                                    body=body,
                                    to_emails=config.ALERT_EMAILS,
                                    image_path=annotated_path,
                                    smtp_settings=config.SMTP_SETTINGS
                                )
                                last_email_times[camera_id] = current_time
                                logging.info(f"[{camera_id} - INFO] Email alert sent for { ' or '.join(detected_alert_labels) }.")
                            else:
                                logging.warning(f"[{camera_id} - WARN] Annotated image not found: {annotated_path}")
                        elif alert_condition_met:
                            detected_alert_labels = list(detected_labels.intersection(required_labels_for_alert))
                            logging.info(f"[{camera_id} - INFO] { ' or '.join(detected_alert_labels).capitalize() } detected, but email cooldown active.")

    except KeyboardInterrupt:
        logging.info("\nKeyboard interrupt received. Exiting gracefully...")
    except Exception as e:
        logging.exception(f"\nAn unexpected error occurred in the main loop: {e}")
    finally:
        # Clean up resources
        logging.info("Initiating shutdown sequence...")
        if 'stream_manager' in locals():
            logging.info("Stopping stream manager...")
            stream_manager.stop()
            logging.info("Stream manager stopped.")
        else:
            logging.warning("Stream manager not found in local scope during shutdown.")
            
        logging.info("Application shut down.")

if __name__ == "__main__":
    main()