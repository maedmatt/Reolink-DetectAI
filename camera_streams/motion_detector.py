# camera_streams/motion_detector.py
# Implements lightweight motion detection to trigger more intensive object detection

import cv2
import numpy as np

class MotionDetector:
    """
    Detects motion by comparing consecutive frames.
    
    Uses pixel-by-pixel comparison to identify changes between frames,
    triggering deeper analysis only when significant motion is detected.
    This acts as an efficient first-pass filter before running 
    more computationally expensive object detection.
    """
    def __init__(self, threshold, min_area):
        """
        Initialize motion detector with sensitivity settings.
        
        Args:
            threshold: Pixel intensity difference threshold (0-255)
                      Higher values require more significant changes in brightness
            min_area: Minimum number of changed pixels to trigger detection
                     Higher values require larger moving objects
        """
        self.threshold = threshold
        self.min_area = min_area
        self.prev_frame = None

    def detect(self, frame):
        """
        Analyzes a frame for motion compared to previous frame.
        
        Args:
            frame: BGR format image from camera
            
        Returns:
            (motion_detected, motion_score): Boolean detection result and numeric score
        """
        # Convert to grayscale for simpler comparison
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # First frame case
        if self.prev_frame is None:
            self.prev_frame = gray
            return False, 0

        # Calculate absolute difference between frames
        diff = cv2.absdiff(self.prev_frame, gray)

        # Apply threshold to identify significant changes
        _, thresh = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)

        # Count changed pixels to measure motion amount
        motion_score = cv2.countNonZero(thresh)

        # Determine if motion exceeds threshold
        motion_detected = motion_score > self.min_area

        # Update previous frame for next comparison
        self.prev_frame = gray

        return motion_detected, motion_score