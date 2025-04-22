# camera_streams/inference_engine.py
# This module defines the InferenceEngine class responsible for running the YOLO object detection model.

from ultralytics import YOLO
import config
import logging
from utils.helpers import save_yolo_training_sample, save_annotated_image

logger = logging.getLogger(__name__)

class InferenceEngine:
    """
    Wraps the YOLOv8 model for performing object detection inference.

    Loads the model and configuration upon initialization and provides a method
    to run inference on a given image path.
    """
    def __init__(self):
        """
        Initializes the InferenceEngine.

        - Loads the YOLOv8 model specified in the config file.
        - Stores the target detection classes and confidence threshold from config.
        """
        logger.info(f"Loading YOLOv8 model from {config.YOLO_MODEL_PATH}...")
        # Load the YOLO model from the path specified in the configuration
        # Ensure the model file (e.g., yolov8n.pt) exists at this path.
        self.model = YOLO(config.YOLO_MODEL_PATH)
        # Store the list of classes we are interested in detecting (e.g., ["person", "car"])
        self.target_classes = config.DETECTION_CLASSES
        # Store the minimum confidence score required to consider a detection valid
        self.conf_threshold = config.YOLO_CONFIDENCE_THRESHOLD

    def run(self, image_path, camera_id=None):
        """
        Runs YOLOv8 object detection on the specified image.

        - Performs inference using the loaded model.
        - Filters results based on configured target classes and confidence threshold.
        - Saves the annotated image (with bounding boxes) if detections are found.
        - Saves the image and detections in YOLO training format if detections are found.
        - Returns a list of filtered detections.

        Args:
            image_path (str): The path to the image file to process.
            camera_id (str, optional): The identifier of the camera source. Used for
                                       organizing saved output files. Defaults to None.

        Returns:
            list: A list of dictionaries, where each dictionary represents a detected
                  object matching the criteria. Each dict has keys: 'label', 
                  'confidence', 'bbox' (tuple: x1, y1, x2, y2).
                  Returns an empty list if no target objects are detected.
        """
        results = None # Initialize results
        try:
            # Log model conf threshold being used
            logger.debug(f"[{camera_id} - DEBUG] Running YOLO model with conf_threshold={self.conf_threshold}")
            results_list = self.model(image_path, conf=self.conf_threshold) # Keep separate conf for model call
            # Check if results list is not empty
            if results_list:
                results = results_list[0] # Assume the first result is the one we want
                logger.info(f"[{camera_id} - INFO] YOLO inference completed. Found {len(results.boxes)} total boxes initially.")
            else:
                 logger.warning(f"[{camera_id} - WARN] YOLO inference returned empty results list for {image_path}.")
                 return [] # No results to process
        except Exception as e:
            logger.exception(f"[{camera_id} - ERROR] YOLO inference failed for image {image_path}: {e}")
            return [] # Return empty list on inference error

        if results is None:
            logger.warning(f"[{camera_id} - WARN] YOLO results object is None after inference attempt for {image_path}, cannot proceed.")
            return []

        filtered_detections = [] # Initialize list to store filtered detections

        # Iterate through each bounding box detected in the results
        for box in results.boxes:
            cls_id = int(box.cls)
            label = results.names.get(cls_id, f"Unknown_ID_{cls_id}") # Use .get for safety
            conf = float(box.conf)

            # Log the raw detection before filtering (consider DEBUG level)
            logger.debug(f"[{camera_id} - DEBUG] Raw detection: Label='{label}', Confidence={conf:.2f}")

            # Check if the detected label is one of the target classes we care about
            # Confidence filter is already applied by the model call
            if label in self.target_classes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                filtered_detections.append({
                    "label": label,
                    "confidence": conf,
                    "bbox": (x1, y1, x2, y2)
                })
                logger.debug(f"[{camera_id} - DEBUG] Kept detection: Label='{label}', Confidence={conf:.2f} (Target class matched)")
            else:
                logger.debug(f"[{camera_id} - DEBUG] Filtered out detection: Label='{label}' (Not in target classes: {self.target_classes})")

        logger.info(f"[{camera_id} - INFO] Found {len(filtered_detections)} detections matching target classes {self.target_classes} and confidence > {self.conf_threshold}.")

        # If any target objects were detected and a camera_id was provided:
        if filtered_detections and camera_id:
            # Log before saving annotated image
            logger.info(f"[{camera_id} - INFO] Saving annotated image for {len(filtered_detections)} detection(s)...")
            save_annotated_image(
                results=[results], # Pass the original results for plotting
                camera_id=camera_id,
                output_dir=config.DETECTIONS_DIR
            )
            
            # Log before saving training sample
            logger.info(f"[{camera_id} - INFO] Saving YOLO training sample for {len(filtered_detections)} detection(s)...")
            save_yolo_training_sample(
                image_path=image_path,
                detections=filtered_detections, # Pass the filtered list
                camera_id=camera_id,
                output_dir=config.TRAINING_DATA_DIR
            )
        elif camera_id:
             logger.info(f"[{camera_id} - INFO] No target objects detected meeting criteria. Skipping saving of annotated image and training data.")

        # Return the list of filtered detections
        return filtered_detections