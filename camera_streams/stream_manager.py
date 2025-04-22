# camera_streams/stream_manager.py
# Manages multiple RTSP camera streams with threading for parallel processing

import threading
import queue
import time
import config
import logging
from .stream_handler import StreamHandler

logger = logging.getLogger(__name__)

class StreamManager:
    """
    Coordinates multiple camera streams in parallel threads.
    
    Manages concurrent stream connections, handles frame retrieval from
    all cameras, and provides a unified interface to access camera frames
    through a thread-safe queue system.
    """
    def __init__(self):
        """
        Creates and starts a thread for each configured camera stream.
        """
        self.streams = {}
        self.threads = {}
        self.frame_queue = queue.Queue()
        self._stop_event = threading.Event()

        logger.info("Initializing Stream Manager...")
        for camera_id, stream_config in config.CAMERA_STREAMS.items():
            if not stream_config or 'rtsp_url' not in stream_config:
                logger.warning(f"Skipping invalid config for camera_id: {camera_id}")
                continue

            logger.info(f"Creating handler for camera: {camera_id}")
            handler = StreamHandler(
                rtsp_url=stream_config['rtsp_url'],
                reconnect_delay=config.STREAM_RECONNECT_DELAY
            )
            self.streams[camera_id] = handler

            thread = threading.Thread(
                target=self._run_stream,
                args=(camera_id, handler),
                daemon=True
            )
            self.threads[camera_id] = thread
            thread.start()
            logger.info(f"Started stream thread for camera: {camera_id}")

        logger.info("Stream Manager initialized.")

    def _run_stream(self, camera_id, stream_handler):
        """
        Thread function that continuously fetches frames from a camera.
        
        Args:
            camera_id: Identifier for the camera being processed
            stream_handler: Handler object for the specific camera stream
        """
        logger.info(f"Stream thread started for {camera_id}")
        frame_gen = stream_handler.get_frame()

        while not self._stop_event.is_set():
            try:
                frame = next(frame_gen, None)

                if frame is not None:
                    try:
                        self.frame_queue.put((camera_id, frame), timeout=1)
                    except queue.Full:
                        logger.warning(f"Frame queue full for {camera_id}. Frame dropped.")
                else:
                    if not self._stop_event.is_set():
                        time.sleep(0.1)

            except StopIteration:
                logger.error(f"Frame generator stopped for {camera_id}")
                break
            except Exception as e:
                logger.exception(f"Error in stream thread for {camera_id}: {e}")
                if not self._stop_event.is_set():
                   time.sleep(config.STREAM_RECONNECT_DELAY)

        logger.info(f"Stopping stream thread for {camera_id}...")
        stream_handler.release()
        logger.info(f"Stream thread for {camera_id} finished.")


    def get_frame(self, timeout=1):
        """
        Gets the next available frame from any camera.
        
        Args:
            timeout: Maximum seconds to wait for a frame
            
        Returns:
            (camera_id, frame): Camera identifier and frame image,
                               or (None, None) if no frames available
        """
        try:
            return self.frame_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None, None

    def stop(self):
        """
        Gracefully stops all camera streams and threads.
        """
        logger.info("Stopping Stream Manager...")
        self._stop_event.set()

        for camera_id, thread in self.threads.items():
            logger.info(f"Waiting for stream thread {camera_id} to join...")
            thread.join()
            logger.info(f"Stream thread {camera_id} joined.")

        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        logger.info("Frame queue cleared.")
        logger.info("Stream Manager stopped.") 