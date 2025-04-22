# utils/helpers.py
# This module provides utility functions used across the application,
# primarily related to file handling and formatting for images and annotations.

import os
import cv2
import time
import shutil
import config
import logging
from glob import glob
from pathlib import Path

logger = logging.getLogger(__name__)

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
    save_folder = os.path.join(output_dir, camera_id)
    os.makedirs(save_folder, exist_ok=True)

    annotated_img = None
    try:
        # Check if results is not None and has the plot method
        if results and hasattr(results[0], 'plot'):
            logger.debug(f"[{camera_id} - DEBUG] Generating annotated image using YOLO plot()...")
            annotated_img = results[0].plot()
        else:
            logger.error(f"[{camera_id} - ERROR] Invalid or empty results object passed to save_annotated_image. Cannot generate annotated image.")
            return # Cannot proceed without results
    except IndexError:
         logger.error(f"[{camera_id} - ERROR] results list appears empty. Cannot generate annotated image.")
         return
    except Exception as e:
        logger.exception(f"[{camera_id} - ERROR] Error during YOLO plot() for annotation: {e}")
        return # Cannot proceed if plotting fails

    if annotated_img is None:
        logger.error(f"[{camera_id} - ERROR] Failed to generate annotated image (annotated_img is None).")
        return

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_path = os.path.join(save_folder, f"{timestamp}.jpg")

    logger.info(f"[{camera_id} - INFO] Attempting to save annotated image to: {output_path}")
    try:
        # Save the annotated image using OpenCV
        success = cv2.imwrite(output_path, annotated_img)
        if success:
            logger.info(f"[{camera_id} - INFO] Annotated image successfully saved: {output_path}")
        else:
            # Log specific failure for imwrite, although it might not always return False
            logger.error(f"[{camera_id} - ERROR] cv2.imwrite failed to save annotated image to: {output_path}. Check permissions/disk space.")
    except Exception as e:
        logger.exception(f"[{camera_id} - ERROR] Exception during cv2.imwrite for annotated image {output_path}: {e}")


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
    try:
        # Read the image to get its dimensions (height, width)
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not read image for training sample: {image_path}")
            return
        height, width = img.shape[:2]
    except Exception as e:
        logger.exception(f"Error reading image {image_path} for training sample: {e}")
        return

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
    try:
        shutil.copy(image_path, img_out_path)
    except Exception as e:
        logger.exception(f"Error copying image {image_path} to {img_out_path}: {e}")
        return # Don't create label file if image copy failed

    # Create and write the YOLO format label file (.txt)
    try:
        with open(label_out_path, "w") as f:
            for det in detections:
                label = det["label"]
                try:
                    # Find the integer class ID corresponding to the label string.
                    # Assumes the order in config.DETECTION_CLASSES matches the desired IDs.
                    class_id = config.DETECTION_CLASSES.index(label)
                except ValueError:
                    logger.warning(f"Label '{label}' from {image_path} not found in config.DETECTION_CLASSES. Skipping for training sample.")
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
    except Exception as e:
        logger.exception(f"Error writing label file {label_out_path}: {e}")
        # Consider deleting the copied image if label writing fails
        try:
            os.remove(img_out_path)
            logger.info(f"Removed image {img_out_path} due to label writing failure.")
        except OSError as remove_err:
            logger.error(f"Failed to remove image {img_out_path} after label error: {remove_err}")
        return

    logger.info(f"[DATASET] Saved sample for training: {img_out_path}, {label_out_path}")