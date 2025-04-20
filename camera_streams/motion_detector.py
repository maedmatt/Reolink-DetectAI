# camera_streams/motion_detector.py
# Defines the MotionDetector class for detecting motion between consecutive frames.

import cv2
import numpy as np

class MotionDetector:
    """
    Implements a simple motion detection algorithm based on frame differencing.

    Compares the current frame with the previous one to identify areas of change.
    """
    def __init__(self, threshold, min_area):
        """
        Initializes the MotionDetector.

        Args:
            threshold (int): The threshold value for pixel intensity difference.
                             Pixels with a difference greater than this value are
                             considered potentially part of motion.
            min_area (int): The minimum number of pixels that need to change
                            (exceed the threshold) to trigger motion detection.
        """
        self.threshold = threshold  # Sensitivity for pixel difference
        self.min_area = min_area    # Minimum area (pixel count) to qualify as motion
        self.prev_frame = None      # Stores the previous frame for comparison

    def detect(self, frame):
        """
        Detects motion in the current frame compared to the previous one.

        Args:
            frame (numpy.ndarray): The current video frame (in BGR format).

        Returns:
            tuple: A tuple containing:
                - bool: True if motion exceeding min_area is detected, False otherwise.
                - int: The motion score (number of pixels exceeding the difference threshold).
        """
        # Convert the current frame to grayscale for simpler comparison
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # If this is the first frame, store it and return no motion
        if self.prev_frame is None:
            self.prev_frame = gray
            return False, 0 # No previous frame to compare against

        # 1. Calculate the absolute difference between the previous frame and the current gray frame
        diff = cv2.absdiff(self.prev_frame, gray)

        # 2. Apply a binary threshold:
        # Pixels with difference > self.threshold become white (255), others black (0).
        _, thresh = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)

        # 3. Calculate motion score: Count the number of white pixels in the thresholded image.
        # This represents the area where significant change occurred.
        motion_score = cv2.countNonZero(thresh)

        # 4. Determine if motion is detected by comparing the score to the minimum area threshold.
        motion_detected = motion_score > self.min_area

        # Update the previous frame for the next iteration
        self.prev_frame = gray

        # Return the detection status and the calculated score
        return motion_detected, motion_score