from tmpfs_framework.sensor_writer import SensorWriter, pack_to_zip
import cv2 as cv
import threading
import time
import sys

class WebcamReader(SensorWriter):
    """
    WebcamReader captures frames from a webcam or video device and writes them using SensorWriter.

    This class runs a background thread to continuously read frames from the specified device
    and store them in a temporary filesystem or other configured storage.

    Attributes:
        wait (float): Time interval between frames based on maximum framerate.
        device (str or int): Webcam index or video file path.
        write_thread (threading.Thread): Thread that runs the frame capture loop.
    """

    def __init__(self, filename, maximum_framerate=None, tmpfs_path=None):
        """
        Initialize WebcamReader.

        Args:
            filename (str or int): Device identifier (e.g., webcam index or video file path).
            maximum_framerate (float, optional): Maximum frames per second. Defaults to None.
            tmpfs_path (str, optional): Path to temporary filesystem for storing frames.
        """
        self.wait = 0 if maximum_framerate is None else 1 / maximum_framerate
        self.device = filename
        super().__init__("webcam", str(filename), tmpfs_path)
        self.write_thread = threading.Thread(target=self._write_loop)

    def start(self):
        """
        Start the frame capture thread.

        This method launches a background thread that continuously captures frames
        and writes them using the SensorWriter interface.
        """
        self.write_thread.start()

    def _write_loop(self):
        """
        Internal loop for capturing and writing frames.

        Opens the video capture device and continuously reads frames until interrupted.
        Each frame is written using the SensorWriter's write method.

        Raises:
            KeyboardInterrupt: Stops the loop when a keyboard interrupt occurs.
        """
        try:
            cap = cv.VideoCapture(self.device)
            if not cap.isOpened():
                print("Cannot open camera")

            while True:
                try:
                    ret, frame = cap.read()
                    if not ret:
                        continue
                    self.write("image", frame)
                    time.sleep(self.wait)
                except KeyboardInterrupt:
                    break
        finally:
            cap.release()

if __name__ == "__main__":
    """
    Main execution block.

    Parses command-line arguments for device index and optional maximum framerate,
    initializes a WebcamReader instance, and starts the frame capture process.
    """
    device = int(sys.argv[1] if len(sys.argv) > 1 else 0)
    maximum_framerate = float(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"{device=} {maximum_framerate=} {sys.argv=}")

    webcam_reader = WebcamReader(device, maximum_framerate)
    webcam_reader.start()
    webcam_reader.write_thread.join()
