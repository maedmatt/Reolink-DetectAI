# Reolink Detect AI

A Python application using OpenCV and YOLOv8 to monitor Reolink (or other RTSP) camera streams for motion, perform object detection (person, car, etc.), and send email alerts with detected images.

## Features

*   Connects to RTSP camera streams.
*   Simple motion detection to trigger deeper analysis.
*   Object detection using YOLOv8 model (`yolov8n.pt`).
*   Configurable detection classes (person, car, dog, cat by default).
*   Saves raw captured frames on motion.
*   Saves annotated frames with bounding boxes upon successful detection.
*   Sends email alerts (optionally with detected images) when specified objects (e.g., 'person') are detected.
*   Cooldown periods for detection and email alerts to prevent spam.
*   Configuration managed via `config.py`.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd reolink-detectai
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Ensure you have compatible versions of PyTorch, CUDA, etc. if using GPU acceleration for YOLO.)*

4.  **Download YOLO model:**
    The default configuration expects `yolov8n.pt` in the root directory. You can download it or use a different YOLOv8 model by updating `YOLO_MODEL_PATH` in `config.py`.

5.  **Configure the application:**
    Edit `config.py`:
    *   Set `CAMERA_1_RTSP` to your camera's RTSP URL.
    *   Adjust motion detection thresholds (`PIXEL_DIFF_THRESHOLD`, `MOTION_AREA_THRESHOLD`) if needed.
    *   Modify `FPS_LIMIT` to control frame processing rate.
    *   Configure `DETECTION_CLASSES` and `YOLO_CONFIDENCE_THRESHOLD`.
    *   **Email Alerts:**
        *   Update `ALERT_EMAILS` with recipient addresses.
        *   Configure `SMTP_SETTINGS` with your email provider's details.
        *   **SECURITY WARNING:** The current setup stores the SMTP password directly in `config.py`. This is insecure! For production or shared environments, use environment variables, a secrets management tool (like HashiCorp Vault, AWS Secrets Manager), or Python's `keyring` library to handle sensitive credentials securely. Do **NOT** commit your actual password to version control. Consider using an "App Password" if your email provider supports it (like Gmail).

## Usage

Run the main script:

```bash
python main.py
```

The script will:
*   Connect to the specified RTSP stream.
*   Monitor for motion.
*   When motion is detected above the threshold:
    *   Save a frame to the `captures/` directory (e.g., `captures/cam1/YYYYMMDD_HHMMSS_ms.jpg`).
    *   Run YOLO inference on the saved frame.
    *   If specified objects are detected above the confidence threshold:
        *   Save an annotated image to the `detections/` directory (e.g., `detections/cam1/YYYYMMDD_HHMMSS_ms.jpg`).
        *   Print alert information to the console.
        *   If a 'person' is detected (and email cooldown has passed), send an email alert with the annotated image.

Press `Ctrl+C` to stop the script gracefully.

## Project Structure

```
.
├── captures/           # Raw frames saved on motion detection
├── camera_streams/     # Modules for stream handling, motion detection, inference
├── config.py           # Main configuration file
├── detections/         # Annotated frames with detected objects
├── logs/               # (Optional) For logging output
├── main.py             # Main application script
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── training_data/      # (Optional) For fine-tuning data
├── utils/              # Helper utilities (e.g., path generation, email notifier)
├── venv/               # Python virtual environment (if used)
└── yolov8n.pt          # YOLOv8 model file
```
