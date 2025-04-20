# utils/helpers.py
# This module provides utility functions used across the application,
# primarily related to file handling and formatting for images and annotations.

import os
import cv2
import time
import shutil
import config
from glob import glob
from pathlib import Path # Moved from save_yolo_training_sample

# Note: This function appears unused in the current main.py flow.
# The InferenceEngine likely handles saving annotated images directly or indirectly.
# Consider refactoring or removing if truly redundant.
def save_annotated_image(results, camera_id, output_dir):
    """
    Saves an image annotated by Ultralytics YOLO results.

    Uses the built-in plot() method of the YOLO results object to draw
    bounding boxes and labels, then saves the image to a specified directory
    with a timestamped filename.

    Args:
        results: The results object returned by a YOLO model prediction (e.g., model(image)).
                 Expected to have a .plot() method returning a NumPy array (the annotated image).
        camera_id (str): Identifier for the camera (used for subfolder naming).
        output_dir (str): The base directory where the annotated image subfolder will be created.
    """
    # Construct the full path for the camera-specific save folder
    save_folder = os.path.join(output_dir, camera_id)
    # Create the folder if it doesn't exist
    os.makedirs(save_folder, exist_ok=True)

    # Generate the annotated image as a NumPy array using YOLO's plot() method
    # Assumes results[0] contains the primary detection result
    annotated_img = results[0].plot()

    # Generate a timestamp string for the filename (YYYYMMDD-HHMMSS)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    # Construct the full output path for the annotated image file
    output_path = os.path.join(save_folder, f"{timestamp}.jpg")

    # Save the annotated image using OpenCV
    cv2.imwrite(output_path, annotated_img)
    print(f"[INFO] Annotated image saved: {output_path}")


def generate_capture_path(camera_id, base_dir, suffix="jpg"):
    """
    Generates a standardized, timestamped file path for saving captured frames.

    Creates a subdirectory based on the camera_id within the base_dir if it
    doesn't exist.

    Args:
        camera_id (str): Identifier for the camera (used for subfolder naming).
        base_dir (str): The base directory where the capture subfolder will be created.
        suffix (str, optional): The file extension for the image. Defaults to "jpg".

    Returns:
        str: The full, absolute path for the new capture file.
    """
    # Generate a timestamp string for the filename (YYYYMMDD-HHMMSS)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    # Construct the path for the camera-specific subfolder
    folder_path = os.path.join(base_dir, camera_id)
    # Create the subfolder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)

    # Create the filename using the timestamp
    filename = f"{timestamp}"
    # Append the suffix (file extension)
    filename += f".{suffix}"

    # Return the full path by joining the folder path and filename
    return os.path.join(folder_path, filename)


def save_yolo_training_sample(image_path, detections, camera_id, output_dir):
    """
    Saves an image and its corresponding detections in YOLO annotation format.

    This is useful for collecting data to potentially fine-tune the YOLO model.
    It copies the original image and creates a .txt file with bounding box
    information normalized according to YOLO standards.

    Args:
        image_path (str): Path to the original captured image.
        detections (list): A list of detection dictionaries, where each dict contains
                           'label' (str) and 'bbox' (list/tuple of [x1, y1, x2, y2]).
        camera_id (str): Identifier for the camera (used for subfolder naming).
        output_dir (str): The base directory where the training data subfolder will be created.
    """
    # Read the image to get its dimensions (height, width)
    img = cv2.imread(image_path)
    if img is None:
        print(f"[ERROR] Could not read image for training sample: {image_path}")
        return
    height, width = img.shape[:2]

    # Extract the base filename (without extension) from the image path
    base_name = Path(image_path).stem
    # Construct the path for the camera-specific training data subfolder
    camera_dir = os.path.join(output_dir, camera_id)
    # Create the subfolder if it doesn't exist
    os.makedirs(camera_dir, exist_ok=True)

    # Define the output paths for the image copy and the label file
    img_out_path = os.path.join(camera_dir, f"{base_name}.jpg")
    label_out_path = os.path.join(camera_dir, f"{base_name}.txt")

    # Copy the original image to the training data directory
    shutil.copy(image_path, img_out_path)

    # Create and write the YOLO format label file (.txt)
    with open(label_out_path, "w") as f:
        for det in detections:
            label = det["label"]
            try:
                # Find the integer class ID corresponding to the label string.
                # Assumes the order in config.DETECTION_CLASSES matches the desired IDs.
                # WARNING: This will fail if a detected label is not in config.DETECTION_CLASSES.
                class_id = config.DETECTION_CLASSES.index(label)
            except ValueError:
                print(f"[WARN] Label '{label}' not found in config.DETECTION_CLASSES. Skipping for training sample.")
                continue # Skip this detection if the label is not recognized

            # Extract bounding box coordinates (x_min, y_min, x_max, y_max)
            x1, y1, x2, y2 = det["bbox"]

            # --- Normalize coordinates for YOLO format --- 
            # x_center = (x_min + x_max) / 2 / image_width
            # y_center = (y_min + y_max) / 2 / image_height
            # bbox_width = (x_max - x_min) / image_width
            # bbox_height = (y_max - y_min) / image_height
            x_center = ((x1 + x2) / 2) / width
            y_center = ((y1 + y2) / 2) / height
            bbox_width = (x2 - x1) / width
            bbox_height = (y2 - y1) / height

            # Write the line in YOLO format: class_id x_center y_center width height
            f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}\n")

    print(f"[DATASET] Saved sample for training: {img_out_path}, {label_out_path}")