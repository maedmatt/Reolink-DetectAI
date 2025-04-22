# Reolink Detect AI 📹 🤖

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![YOLOv8](https://img.shields.io/badge/YOLO-v8-darkgreen.svg)](https://github.com/ultralytics/ultralytics)

A Python application using OpenCV and YOLOv8 to monitor Reolink (or other RTSP) camera streams for motion, perform object detection (person, car, etc.), and send email alerts with detected images.

<p align="center">
  <img src="https://github.com/ultralytics/assets/raw/main/yolov8/yolo-comparison-plots.png" alt="YOLOv8 Performance" width="600">
</p>

## ✨ Features

* Connects to multiple RTSP camera streams simultaneously
* Resource-efficient using two-phase detection:
  * Initial lightweight motion detection to trigger analysis
  * Deep learning object detection using YOLOv8 only when motion is detected
* Object detection with configurable classes (person, car, etc.)
* Customizable detection confidence thresholds
* Saves captured frames and annotated detection images
* Sends email alerts with annotated images
* Cooldown periods to prevent alert spam
* Environment-based configuration (.env)
* Comprehensive logging system

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Pip package manager
- (Optional) CUDA-compatible GPU for faster inference

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/reolink-detectai.git
   cd reolink-detectai
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download the YOLO model:**
   The default configuration uses `yolov8n.pt` (the smallest and fastest YOLOv8 model). You can download it with:
   ```bash
   pip install ultralytics
   python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
   ```
   Alternative models: `yolov8s.pt` (small), `yolov8m.pt` (medium), `yolov8l.pt` (large), `yolov8x.pt` (extra large)

5. **Configure the application:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your camera details and other settings.

## ⚙️ Configuration

The application is configured via environment variables (in `.env` file) and `config.py`:

### Key Configuration Options

| Category | Setting | Description | Default |
|----------|---------|-------------|---------|
| Camera | `CAMERA_1_RTSP` | RTSP URL for camera 1 | *Required* |
| Motion | `PIXEL_DIFF_THRESHOLD` | Motion sensitivity (pixel threshold) | 25 |
| Motion | `MOTION_AREA_THRESHOLD` | Motion sensitivity (area size) | 1500 |
| Detection | `YOLO_CONFIDENCE_THRESHOLD` | Object detection confidence threshold | 0.7 |
| Timing | `DETECTION_COOLDOWN` | Seconds between detection cycles per camera | 5 |
| Email | `SMTP_SERVER` | SMTP server for email alerts | *Required for alerts* |

For complete configuration options, see `.env.example` and detailed comments in `config.py`.

## 🚀 Usage

### Basic Operation

Run the application:
```bash
python main.py
```

For a persistent background process (Linux/macOS):
```bash
nohup python main.py > nohup.out 2>&1 &
```

### Directory Structure

The application creates and uses these directories:
- `captures/` - Raw frames saved when motion is detected
- `detections/` - Annotated frames with detection bounding boxes
- `logs/` - Application logs
- `training_data/` - (Optional) For custom model training

## 🔍 How It Works

1. **Parallel Stream Processing**:
   - The `StreamManager` class handles connections to multiple camera streams
   - Each camera stream runs in a separate thread

2. **Motion Detection**:
   - For each frame, a basic motion detection algorithm is applied
   - Uses background subtraction and contour analysis
   - Only triggers further analysis if motion exceeds thresholds

3. **Object Detection**:
   - When motion is detected, the frame is saved
   - YOLOv8 is used to analyze the frame for objects
   - Detection confidence is compared to the threshold

4. **Alert Processing**:
   - If configured objects are detected (person, car), an alert is triggered
   - Annotated frame is saved with bounding boxes
   - Email alerts are sent with the annotated image
   - Cooldown period prevents too many alerts

## 🔮 Future Improvements

This project is actively being developed. Here are some planned enhancements:

### Motion Detection Enhancements
- Implement advanced background subtraction methods (MOG2, KNN)
- Add Gaussian filtering for noise reduction
- Integrate optical flow for tracking movement direction
- Implement region of interest (ROI) masks to ignore areas prone to false positives

### Performance Optimizations
- Add hardware acceleration support for video decoding
- Implement frame skipping for high-FPS streams
- Add batch processing for multiple motion events
- Explore TensorRT conversion for faster YOLO inference

### Feature Additions
- Create a web interface for real-time monitoring
- Add webhook support for integration with home automation systems
- Implement push notifications (mobile apps, Telegram, etc.)
- Add object tracking across multiple frames
- Support for PTZ camera control (move to follow detected objects)

### Visualization & Analytics
- Add heatmap generation to visualize motion patterns
- Create time-lapse videos of detections
- Implement basic analytics (objects per hour, peak detection times)
- Generate weekly/monthly detection reports

### Robustness & Testing
- Add comprehensive unit and integration tests
- Implement automated recovery from network interruptions
- Add camera health monitoring and status alerts
- Create a benchmark suite for performance testing

If you'd like to contribute to any of these improvements, please check the [Contributing](CONTRIBUTING.md) guide.

## 📚 API Reference

### Main Components

- **StreamManager**: Manages multiple camera streams in separate threads
- **MotionDetector**: Performs lightweight motion detection
- **InferenceEngine**: Handles YOLOv8 object detection
- **Notifier**: Sends email alerts

### Key Files

- `main.py`: Application entry point and main loop
- `config.py`: Configuration settings and environment variables
- `camera_streams/stream_manager.py`: Multi-camera handling
- `camera_streams/inference_engine.py`: YOLOv8 detection logic
- `alerts/notifier.py`: Email notification system

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please make sure your code follows the existing style and includes appropriate tests.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for the object detection model
- [OpenCV](https://opencv.org/) for image processing capabilities
- [Reolink](https://reolink.com/) for camera hardware (though this works with any RTSP stream)
