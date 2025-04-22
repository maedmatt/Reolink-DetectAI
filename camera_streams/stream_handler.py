# camera_streams/stream_handler.py
# Defines the StreamHandler class for managing RTSP video streams using OpenCV.

import cv2
import time
import config
import logging

logger = logging.getLogger(__name__)

class StreamHandler:
    """
    Handles connection to an RTSP camera stream, frame retrieval, and automatic
    reconnection attempts on failure.
    """
    def __init__(self, rtsp_url, reconnect_delay=5):
        """
        Initializes the StreamHandler.

        Args:
            rtsp_url (str): The RTSP URL of the camera stream.
            reconnect_delay (int): Seconds to wait before attempting
                                   to reconnect after a failure.
        """
        self.rtsp_url = rtsp_url
        self.reconnect_delay = reconnect_delay
        self.cap = None  # OpenCV VideoCapture object, initialized in connect()

    def connect(self):
        """
        Attempts to connect (or reconnect) to the RTSP stream.

        Initializes the OpenCV VideoCapture object. Consider adding a check here
        to see if the connection was immediately successful.
        """
        logger.info(f"Attempting to connect to stream: {self.rtsp_url}")
        # Use FFMPEG backend for potentially better RTSP compatibility
        self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        # Optional: Check self.cap.isOpened() here for immediate feedback
        # if not self.cap.isOpened():
        #     logger.error(f"Failed to open stream immediately: {self.rtsp_url}")

    def get_frame(self):
        """
        A generator function that continuously yields frames from the stream.

        Handles reconnection if the stream is not opened or fails during capture.
        Includes logic to grab several frames (buffer flushing) to potentially get
        a more recent one from live streams.

        Yields:
            numpy.ndarray: The captured video frame, or None if retrieval fails
                           after connection checks.
        """
        while True:
            # Check if the stream is disconnected or not initialized
            if self.cap is None or not self.cap.isOpened():
                logger.warning("Stream disconnected or not initialized. Attempting to connect...")
                self.connect() # Try to establish connection
                # Wait before checking again or trying to grab frames
                time.sleep(self.reconnect_delay)
                # If connection failed after delay, continue loop to retry
                if self.cap is None or not self.cap.isOpened():
                    logger.warning("Reconnect attempt failed. Retrying...")
                    continue
                else:
                    logger.info("Stream connected successfully.")

            try:
                # --- Frame Buffering/Skipping --- 
                # Grab (but don't decode) several frames to clear any buffer lag.
                # The number of frames to grab is set by FRAME_BUFFER_FLUSH in config.
                for _ in range(config.FRAME_BUFFER_FLUSH):
                    grabbed = self.cap.grab() # Fetches frame data without decoding
                    if not grabbed:
                        # If grab fails, likely a stream issue, break inner loop to reconnect
                        logger.warning("Frame grab failed during buffer flush.")
                        ret = False # Signal failure
                        break 
                else: # Only runs if the loop completed without break
                    # If grabs were successful, retrieve (decode) the *last* grabbed frame.
                    ret, frame = self.cap.retrieve()

                # Check if frame retrieval was successful
                if not ret:
                    logger.warning("Frame retrieve failed after grab. Reconnecting...")
                    # Release the potentially faulty capture object
                    if self.cap:
                        self.cap.release()
                    self.cap = None # Set to None to trigger reconnect in the next iteration
                    time.sleep(self.reconnect_delay)
                    continue # Continue to the next loop iteration to reconnect

                # Successfully retrieved a frame, yield it
                yield frame

            except cv2.error as e:
                 logger.error(f"OpenCV error during frame grab/retrieve: {e}. Reconnecting...")
                 if self.cap:
                    self.cap.release()
                 self.cap = None # Ensure reconnect is triggered
                 time.sleep(self.reconnect_delay)
                 continue
            except Exception as e:
                 # Catch other potential errors
                 logger.exception(f"Unexpected error in get_frame loop: {e}. Reconnecting...")
                 if self.cap:
                    self.cap.release()
                 self.cap = None # Ensure reconnect is triggered
                 time.sleep(self.reconnect_delay)
                 continue


    def release(self):
        """
        Releases the video capture resources.

        Should be called when the stream is no longer needed to free up resources.
        """
        logger.info(f"Releasing video stream resources for {self.rtsp_url}...")
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            logger.info(f"Video stream released for {self.rtsp_url}.")
        self.cap = None