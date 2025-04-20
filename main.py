import cv2
import time
import os
import config

# --- Custom Modules ---
# Import necessary components from other parts of the application
from camera_streams.stream_handler import StreamHandler      # Handles connecting to and reading frames from the RTSP stream
from camera_streams.motion_detector import MotionDetector    # Performs basic motion detection based on frame differences
from camera_streams.inference_engine import InferenceEngine  # Runs the YOLO object detection model on captured frames
from utils.helpers import generate_capture_path              # Utility function to create standardized file paths for captures
from alerts.notifier import send_alert_email                 # Handles sending email notifications


def main():
    """
    Main function to initialize components and run the detection loop.
    """
    print("[INFO] Starting reolink-detectai...")

    # --- Initialization ---
    # Get camera identifier from config
    camera_id = config.CAMERA_IDS["camera_1"]

    # Initialize the stream handler for the specified camera RTSP URL
    stream = StreamHandler(rtsp_url=config.CAMERA_1_RTSP)

    # Initialize the motion detector with thresholds from config
    motion_detector = MotionDetector(
        threshold=config.PIXEL_DIFF_THRESHOLD,
        min_area=config.MOTION_AREA_THRESHOLD
    )

    # Get the frame generator from the stream handler
    frame_gen = stream.get_frame()

    # Initialize the inference engine (loads the YOLO model)
    inference = InferenceEngine()

    # Ensure the base directory for saving captured frames exists
    os.makedirs(config.CAPTURE_BASE_DIR, exist_ok=True)

    # --- Cooldown Timers ---
    # Initialize timers to manage cooldown periods for detections and alerts
    last_alert_time   = 0  # Timestamp of the last detected event (motion + inference)
    last_email_time   = 0  # Timestamp of the last email alert sent

    try:
        # --- Main Processing Loop ---
        # Continuously process frames from the camera stream
        for frame in frame_gen:
            if frame is None:
                # Handle potential stream errors or end-of-stream
                print("[WARN] Received empty frame, potentially stream issue. Retrying...")
                time.sleep(1) # Add a small delay before retrying
                continue

            # 1. Motion Detection
            # Check the current frame for motion compared to the previous one
            motion_detected, score = motion_detector.detect(frame)

            current_time = time.time()
            # Check if the system is currently in the detection cooldown period
            in_cooldown = (current_time - last_alert_time) < config.DETECTION_COOLDOWN

            # 2. Process Motion Event (if detected and not in cooldown)
            if motion_detected and not in_cooldown:
                # Optional delay: Wait briefly to allow the object to fully enter the frame
                time.sleep(config.FRAME_CAPTURE_DELAY)
                print(f"[MOTION DETECTED] Score: {score:.2f}") # Log motion detection

                # 3. Save Frame
                # Generate a unique path for the captured frame
                image_path = generate_capture_path(
                    camera_id=camera_id,
                    base_dir=config.CAPTURE_BASE_DIR
                )
                # Save the current frame (raw, without annotations) to disk
                cv2.imwrite(image_path, frame)
                print(f"[INFO] Frame saved: {image_path}")

                # 4. Object Detection (Inference)
                # Run the YOLO model on the saved frame
                # The InferenceEngine saves the annotated image to DETECTIONS_DIR
                detections = inference.run(image_path, camera_id=camera_id)

                # 5. Process Detections & Alerting
                if detections:
                    # Update the time of the last successful detection event
                    last_alert_time = current_time
                    # Extract labels of detected objects
                    labels = [d["label"] for d in detections]
                    print(f"[ALERT] Detected: {labels}")

                    # Check if a 'person' was detected and if the email cooldown has passed
                    if "person" in labels and (current_time - last_email_time) >= config.EMAIL_COOLDOWN:
                        # Reconstruct the path to the *annotated* image saved by InferenceEngine
                        # (Consider having inference.run return this path directly for robustness)
                        timestamp = os.path.splitext(os.path.basename(image_path))[0]
                        annotated_path = os.path.join(config.DETECTIONS_DIR, camera_id, f"{timestamp}.jpg")

                        # Check if the annotated file actually exists before sending
                        if os.path.exists(annotated_path):
                            # Send email alert
                            send_alert_email(
                                subject="🔔 Alert: Person Detected",
                                body=f"Detected person on camera {camera_id}.",
                                to_emails=config.ALERT_EMAILS,
                                image_path=annotated_path, # Attach the image with bounding boxes
                                smtp_settings=config.SMTP_SETTINGS
                            )
                            # Update the time of the last email sent
                            last_email_time = current_time
                        else:
                            print(f"[WARN] Annotated image not found for alert: {annotated_path}")


            # --- Frame Rate Limiting ---
            # Introduce a small delay to limit the frame processing rate (controls CPU usage)
            # If FPS_LIMIT is 0 or negative, this sleep has no effect.
            if config.FPS_LIMIT > 0:
                time.sleep(1 / config.FPS_LIMIT)

    except KeyboardInterrupt:
        # --- Graceful Shutdown ---
        print("\n[INFO] Keyboard interrupt received. Exiting gracefully...")
        # Release the video stream resources
        stream.release()
    except Exception as e:
        # --- General Error Handling ---
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        # Attempt to release resources even on error
        if 'stream' in locals() and stream:
            stream.release()


# --- Script Execution ---
if __name__ == "__main__":
    # Run the main function when the script is executed directly
    main()