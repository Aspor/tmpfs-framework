import time
import cv2 as cv
from tmpfs_framework import SensorReader
from tmpfs_framework.sensor_writer import SensorWriter, pack_to_zip

class CircleFinder(SensorWriter):
    """
    CircleFinder detects circles in images received from a webcam and stores the results.

    This class uses OpenCV's Hough Circle Transform to identify circles in frames captured
    by a webcam. It writes detected circle data and count to a temporary storage and packages
    them into a zip file.

    Attributes:
        image_reader (SensorReader): Reads images from the webcam sensor.
    """

    def __init__(self, filename, webcam_number, tmpfs_path=None):
        """
        Initialize CircleFinder.

        Args:
            filename (str or int): Identifier for the CircleFinder instance.
            webcam_number (int): Index of the webcam to read images from.
            tmpfs_path (str, optional): Path to temporary filesystem for storing data.
        """
        super().__init__("circle_finder", str(filename), tmpfs_path)
        self.image_reader = SensorReader("webcam", webcam_number)
        # Attach a watchdog to trigger the worker method whenever a new image is available
        self.image_reader.attach_watchdog("image", self.worker)

    def find_circles(self, image):
        """
        Detect circles in the given image using Hough Circle Transform.

        Converts the image to grayscale, applies blurring, and detects circles.
        Writes detected circles and their count to storage and packages them into a zip file.

        Args:
            image (numpy.ndarray): Input image in BGR format.

        Returns:
            set: A set of keys representing the written data items.
        """
        grayscale = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        blurred = cv.blur(grayscale, (9, 9))
        rows = blurred.shape[0]
        circles = cv.HoughCircles(blurred, cv.HOUGH_GRADIENT, 1, rows / 8,
                                  param1=100, param2=30,
                                  minRadius=100, maxRadius=150)
        to_write = set()
        count = 0

        if circles is not None:
            for circle in circles[0, :]:
                radius = int(circle[2])
                centre = (int(circle[0]), int(circle[1]))
                if radius > 10:
                    self.write(f"circle_{count}", circle)
                    to_write.add(f"circle_{count}")
                    cv.circle(blurred, center=centre, radius=radius, color=(255, 0, 255), thickness=3)
                    count += 1

        self.write("count", count)
        to_write.add("count")
        pack_to_zip(to_write, base_dir=self.data_path)
        return to_write

    def worker(self, image):
        """
        Callback method triggered when a new image is available.

        Processes the image to find circles and writes the results as a zip file.

        Args:
            image (numpy.ndarray): Input image in BGR format.
        """
        to_write = self.find_circles(image)
        self.write_zip("shapes", to_write, keep=True)

if __name__ == "__main__":
    """
    Main execution block.

    Creates a CircleFinder instance, starts the image reader, and keeps the program running
    until interrupted by the user.
    """
    rf = CircleFinder(1, 0)
    rf.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
