# camera_streams/stream_manager.py
# Defines the StreamManager class for handling multiple camera streams concurrently.

import threading
import queue
import time
import config
import logging
from .stream_handler import StreamHandler

logger = logging.getLogger(__name__)

class StreamManager:
    """
    Manages multiple StreamHandler instances, each in its own thread,
    and provides a unified queue to access frames from all streams.
    """
    def __init__(self):
        """
        Initializes the StreamManager.

        - Creates StreamHandler instances based on config.CAMERA_STREAMS.
        - Starts a separate thread for each stream to fetch frames.
        - Sets up a queue to collect frames from all threads.
        """
        self.streams = {}          # Stores {camera_id: StreamHandler instance}
        self.threads = {}          # Stores {camera_id: Thread instance}
        self.frame_queue = queue.Queue() # Queue for (camera_id, frame) tuples
        self._stop_event = threading.Event() # Signal for stopping threads gracefully

        logger.info("Initializing Stream Manager...")
        for camera_id, stream_config in config.CAMERA_STREAMS.items():
            if not stream_config or 'rtsp_url' not in stream_config:
                logger.warning(f"Skipping invalid config for camera_id: {camera_id}")
                continue

            logger.info(f"Creating handler for camera: {camera_id}")
            # Pass camera-specific config and global stream settings
            handler = StreamHandler(
                rtsp_url=stream_config['rtsp_url'],
                reconnect_delay=config.STREAM_RECONNECT_DELAY
                # FRAME_BUFFER_FLUSH config is used inside StreamHandler.get_frame
            )
            self.streams[camera_id] = handler

            # Create and start a thread for this stream handler
            thread = threading.Thread(
                target=self._run_stream,
                args=(camera_id, handler),
                daemon=True # Daemon threads exit when the main program exits
            )
            self.threads[camera_id] = thread
            thread.start()
            logger.info(f"Started stream thread for camera: {camera_id}")

        logger.info("Stream Manager initialized.")

    def _run_stream(self, camera_id, stream_handler):
        """
        Internal method run by each thread to continuously fetch frames.

        Gets frames from the associated StreamHandler and puts them into the
        shared frame_queue.
        """
        logger.info(f"Stream thread started for {camera_id}")
        frame_gen = stream_handler.get_frame() # Get the frame generator

        while not self._stop_event.is_set():
            try:
                # Get the next frame from the generator
                # The generator handles connection and retries internally
                frame = next(frame_gen, None)

                if frame is not None:
                    # Put the frame and its camera ID into the queue
                    # Use blocking put with a timeout to prevent deadlocks if queue is full
                    # (though unlikely with a simple consumer)
                    try:
                        self.frame_queue.put((camera_id, frame), timeout=1)
                    except queue.Full:
                        logger.warning(f"Frame queue full for {camera_id}. Frame dropped.")
                        # Optional: Consider alternative strategies if the queue frequently fills up,
                        # e.g., clearing the queue, dropping older frames first.
                        pass
                else:
                    # If frame is None, stream_handler might be reconnecting or failed
                    # Add a small delay to prevent tight looping if errors persist
                    if not self._stop_event.is_set(): # Avoid sleeping if stopping
                        time.sleep(0.1)

            except StopIteration:
                # Generator finished unexpectedly (should not happen with current StreamHandler loop)
                logger.error(f"Frame generator stopped unexpectedly for {camera_id}. Exiting thread.")
                break
            except Exception as e:
                # Catch unexpected errors in this thread's loop
                logger.exception(f"Unexpected error in stream thread for {camera_id}: {e}. Attempting recovery...") # Use exception here
                # Add a small delay before trying again
                if not self._stop_event.is_set():
                   time.sleep(config.STREAM_RECONNECT_DELAY)

        # --- Cleanup --- 
        # Thread is stopping (either by _stop_event or error)
        logger.info(f"Stopping stream thread for {camera_id}...")
        stream_handler.release() # Ensure OpenCV resource is released by the handler
        logger.info(f"Stream thread for {camera_id} finished.")


    def get_frame(self, timeout=1):
        """
        Retrieves the next available frame from any camera stream.

        Args:
            timeout (int, optional): Maximum time in seconds to wait for a frame.
                                     Defaults to 1.

        Returns:
            tuple: A tuple containing (camera_id, frame), or (None, None)
                   if no frame is available within the timeout.
        """
        try:
            # Get a (camera_id, frame) tuple from the queue
            return self.frame_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            # No frame available within the timeout period
            return None, None

    def stop(self):
        """
        Signals all stream threads to stop and waits for them to terminate.
        """
        logger.info("Stopping Stream Manager...")
        self._stop_event.set() # Signal all threads to stop

        # Wait for all threads to complete
        for camera_id, thread in self.threads.items():
            logger.info(f"Waiting for stream thread {camera_id} to join...")
            thread.join() # Wait for the thread to finish execution
            logger.info(f"Stream thread {camera_id} joined.")

        # Clear the queue after stopping to prevent old frames being processed on restart
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        logger.info("Frame queue cleared.")
        logger.info("Stream Manager stopped.") 