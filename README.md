# Reolink Detect AI

A Python application using OpenCV and YOLOv8 to monitor Reolink (or other RTSP) camera streams for motion, perform object detection (person, car, etc.), and send email alerts with detected images.

## Features

*   Connects to RTSP camera streams.
*   Simple motion detection to trigger deeper analysis.
*   Object detection using YOLOv8 model (`yolov8n.pt`).
*   Configurable detection classes (e.g., person, car).
*   Saves raw captured frames on motion.
*   Saves annotated frames with bounding boxes upon successful detection.
*   Sends email alerts (optionally with detected images) when specific objects (currently 'person' or 'car') are detected.
*   Cooldown periods for detection and email alerts to prevent spam.
*   Configuration managed via `config.py`.
*   Detailed logging with adjustable levels (INFO by default, DEBUG for diagnostics).

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
    *   Set `CAMERA_STREAMS` with your camera names and RTSP URLs.
    *   Adjust motion detection thresholds (`PIXEL_DIFF_THRESHOLD`, `MOTION_AREA_THRESHOLD`) if needed.
    *   Configure `DETECTION_CLASSES` (e.g., `["person", "car"]`) and `YOLO_CONFIDENCE_THRESHOLD`.
    *   **Email Alerts:**
        *   Update `ALERT_EMAILS` with recipient addresses.
        *   Configure `SMTP_SETTINGS` with your email provider's details.
        *   **SECURITY WARNING:** Storing passwords in `config.py` is insecure. Use environment variables or a secrets manager for production.

## Usage

Run the main script:

```bash
python main.py
```

The script will:
*   Connect to the specified RTSP streams.
*   Monitor for motion.
*   When motion is detected above the threshold (and not in cooldown):
    *   Save a frame to the `captures/` directory (e.g., `captures/cam1/YYYYMMDD-HHMMSS.jpg`).
    *   Run YOLO inference on the saved frame.
    *   If objects matching `DETECTION_CLASSES` are detected above the `YOLO_CONFIDENCE_THRESHOLD`:
        *   Save an annotated image to the `detections/` directory (e.g., `detections/cam1/YYYYMMDD-HHMMSS.jpg`).
        *   Log alert information.
        *   If a 'person' or 'car' is detected (and the email cooldown `EMAIL_COOLDOWN` has passed), send an email alert with the annotated image.

Logs are output to the console and saved to the `logs/app.log` file. For more detailed diagnostic information (e.g., raw detection details, filtering steps), you can change the logging level in `main.py` (around line 28) from `logging.INFO` to `logging.DEBUG`.

Press `Ctrl+C` to stop the script gracefully.

## Project Structure

```
.
├── captures/           # Raw frames saved on motion detection
├── camera_streams/     # Modules for stream handling, motion detection, inference
├── config.py           # Main configuration file
├── detections/         # Annotated frames with detected objects
├── logs/               # Log files (e.g., app.log)
├── main.py             # Main application script
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── training_data/      # (Optional) For fine-tuning data
├── utils/              # Helper utilities (e.g., path generation, email notifier)
├── venv/               # Python virtual environment (if used)
└── yolov8n.pt          # YOLOv8 model file (or other specified model)
```
