from tmpfs_framework import SensorReader
import cv2 as cv
import numpy as np

# Main execution block
if __name__ == "__main__":
    # Create a SensorReader to read images from the webcam sensor
    image_reader = SensorReader("webcam", "0")
    # Create another SensorReader to read circle detection results from CircleFinder
    circle_reader = SensorReader("circle_finder")

    # Infinite loop to continuously display images and detected circles
    while True:
        # Get the latest image from the webcam
        image = image_reader.image
        # Make a copy of the original image for drawing detected circles
        circeled_image = image.copy()

        try:
            # Retrieve measurement data (circle detection results) from CircleFinder
            shapes = circle_reader.measurement
            for key in shapes:
                # Check if the key corresponds to a detected circle
                if "circle" in key:
                    # Convert the circle data to an integer NumPy array [x, y, radius]
                    shape = np.array(shapes[key], dtype=np.int32)
                    # Draw the detected circle on the copied image
                    cv.circle(circeled_image, (shape[0], shape[1]), shape[2], (0, 255, 255), 5)
        except:
            # If no shapes are available or an error occurs, ignore and continue
            pass

        # Display the original image
        cv.imshow('orginal', image)
        # Display the image with detected circles drawn
        cv.imshow('detected circles', circeled_image)
        # Wait briefly to update the display (required for OpenCV windows)
        cv.waitKey(1)
