import os

TMPFS_PATH = os.environ.get("TMPFS_PATH", default='/home/robot/tmp/')

from .sensor_reader import SensorReader
from .sensor_writer import SensorWriter
