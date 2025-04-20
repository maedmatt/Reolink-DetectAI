# camera_streams/inference_engine.py
# This module defines the InferenceEngine class responsible for running the YOLO object detection model.

from ultralytics import YOLO
import config
# Import helper functions for saving annotated images and training data
from utils.helpers import save_yolo_training_sample, save_annotated_image

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
        print("[INFO] Loading YOLOv8 model...")
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
        # Run inference. Assumes results is a list, taking the first element.
        # Consider adding error handling for model execution.
        results = self.model(image_path, conf=self.conf_threshold)[0]
        detections = [] # Initialize list to store filtered detections

        # Iterate through each bounding box detected in the results
        for box in results.boxes:
            # Get the class ID and corresponding label name
            cls_id = int(box.cls)
            label = results.names[cls_id]
            # Get the confidence score of the detection
            conf = float(box.conf)

            # Check if the detected label is one of the target classes we care about
            if label in self.target_classes:
                # Get bounding box coordinates (top-left and bottom-right)
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                # Append detection info to our list
                detections.append({
                    "label": label,
                    "confidence": conf,
                    "bbox": (x1, y1, x2, y2)
                })

        # If any target objects were detected and a camera_id was provided:
        if detections and camera_id:
            # Save the image with annotations drawn on it
            # Note: This helper function saves the image. main.py currently reconstructs
            # this path. Consider returning the path from this `run` method instead.
            save_annotated_image(
                results=[results],  # Pass the results object to the helper
                camera_id=camera_id,
                output_dir=config.DETECTIONS_DIR # Save to the configured detections directory
            )
            # Save the raw image and detection data in YOLO training format
            save_yolo_training_sample(
                image_path=image_path,       # Path to the original image
                detections=detections,       # The filtered list of detections
                camera_id=camera_id,
                output_dir=config.TRAINING_DATA_DIR # Save to the configured training data directory
            )

        # Return the list of filtered detections
        return detections