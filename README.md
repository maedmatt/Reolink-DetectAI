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
* Two-phase detection: motion detection followed by YOLOv8 object detection
* Configurable detection classes and confidence thresholds
* Saves captured frames and annotated detection images
* Email alerts with annotated images
* Cooldown periods to prevent alert spam
* Creation of a personalized dataset for fine-tuning

## 🛠️ Installation

1. **Clone the repository and enter directory**
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure the application:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your camera details and other settings.

## ⚙️ Configuration

Key configuration options in `.env`:

| Setting | Description | Default |
|---------|-------------|---------|
| `CAMERA_1_RTSP` | RTSP URL for camera 1 | *Required* |
| `PIXEL_DIFF_THRESHOLD` | Motion sensitivity | 25 |
| `YOLO_CONFIDENCE_THRESHOLD` | Detection confidence threshold | 0.7 |
| `DETECTION_COOLDOWN` | Seconds between detection cycles | 5 |
| `SMTP_SERVER` | SMTP server for email alerts | *Optional* |

## 🚀 Usage

Run the application:
```bash
python main.py
```
> [!IMPORTANT] 
> For a background process: (logs are saved inside logs/app.log)
1) Create a systemd service file:  
```bash
sudo nano /etc/systemd/system/reolink-detectai.service
```
2) Paste this:  
```ini
[Unit]
Description=Reolink DetectAI
After=network.target

[Service]
ExecStart=/home/matt/reolink-detectai/venv/bin/python /home/matt/reolink-detectai/main.py
WorkingDirectory=/home/matt/reolink-detectai
Restart=always
RestartSec=5
User=matt

[Install]
WantedBy=multi-user.target
```
3) Enable and start it:  
```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable reolink-detectai
sudo systemctl start reolink-detectai
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [OpenCV](https://opencv.org/)
- [Reolink](https://reolink.com/) (works with any RTSP stream)
