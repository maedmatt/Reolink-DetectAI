# camera_streams/inference_engine.py
# Handles object detection using YOLOv8 model

from ultralytics import YOLO
import config
import logging
from utils.helpers import save_yolo_training_sample, save_annotated_image

logger = logging.getLogger(__name__)

class InferenceEngine:
    """
    YOLOv8 object detection engine that processes images to identify objects.
    
    This class loads the YOLOv8 model and provides methods to detect objects
    in images with configurable confidence thresholds and target classes.
    """
    def __init__(self):
        """
        Initializes the YOLOv8 model with configuration settings.
        """
        logger.info(f"Loading YOLOv8 model from {config.YOLO_MODEL_PATH}...")
        self.model = YOLO(config.YOLO_MODEL_PATH)
        self.target_classes = config.DETECTION_CLASSES
        self.conf_threshold = config.YOLO_CONFIDENCE_THRESHOLD

    def run(self, image_path, camera_id=None):
        """
        Performs object detection on an image and filters for target objects.
        
        Args:
            image_path (str): Path to the image file for analysis
            camera_id (str, optional): Camera identifier for organizing outputs
            
        Returns:
            list: Filtered detections matching target classes with format:
                 [{'label': 'person', 'confidence': 0.95, 'bbox': (x1,y1,x2,y2)}, ...]
        """
        results = None
        try:
            logger.debug(f"[{camera_id} - DEBUG] Running YOLO with confidence threshold {self.conf_threshold}")
            results_list = self.model(image_path, conf=self.conf_threshold)
            
            if results_list:
                results = results_list[0]
                logger.info(f"[{camera_id} - INFO] Found {len(results.boxes)} total detections")
            else:
                logger.warning(f"[{camera_id} - WARN] No inference results for {image_path}")
                return []
        except Exception as e:
            logger.exception(f"[{camera_id} - ERROR] Inference failed: {e}")
            return []

        if results is None:
            logger.warning(f"[{camera_id} - WARN] YOLO returned no results for {image_path}")
            return []

        filtered_detections = []
        for box in results.boxes:
            cls_id = int(box.cls)
            label = results.names.get(cls_id, f"Unknown_ID_{cls_id}")
            conf = float(box.conf)

            logger.debug(f"[{camera_id} - DEBUG] Detection: {label}, confidence={conf:.2f}")

            if label in self.target_classes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                filtered_detections.append({
                    "label": label,
                    "confidence": conf,
                    "bbox": (x1, y1, x2, y2)
                })
                logger.debug(f"[{camera_id} - DEBUG] Keeping {label} detection (confidence={conf:.2f})")
            else:
                logger.debug(f"[{camera_id} - DEBUG] Ignoring {label} (not in target classes)")

        logger.info(f"[{camera_id} - INFO] Found {len(filtered_detections)} matching detections")

        if filtered_detections and camera_id:
            logger.info(f"[{camera_id} - INFO] Saving annotated detection image")
            save_annotated_image(
                results=[results],
                camera_id=camera_id,
                output_dir=config.DETECTIONS_DIR
            )
            
            logger.info(f"[{camera_id} - INFO] Saving detection data for training")
            save_yolo_training_sample(
                image_path=image_path,
                detections=filtered_detections,
                camera_id=camera_id,
                output_dir=config.TRAINING_DATA_DIR
            )
        elif camera_id:
            logger.info(f"[{camera_id} - INFO] No target objects detected")

        return filtered_detections