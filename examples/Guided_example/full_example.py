from time import sleep

from tmpfs_framework import SensorReader, SensorWriter, TMPFS_PATH
from tmpfs_framework.sensor_writer import pack_to_zip
from tmpfs_framework.sensor_reader import read

import os
import shutil

class DummyWriter(SensorWriter):
    def __init__(self, filename):
        dir = "dummy"
        super().__init__(dir, filename)

    def writer_worker(self, number):
        self.write("number", number)
        self.write("number_x2", number*2)
        pack_to_zip(["number","number_x2"], self.data_path)


if __name__ == "__main__":

    dummy_writer = DummyWriter("first")
    dummy_writer.writer_worker(1)

    dummy_reader = SensorReader("dummy")

    #List attributes
    print(f"{dummy_reader.attributes=}")

    #Access data
    print(f"{dummy_reader.get_data('number')=}")
    print(f"{dummy_reader.number=}")
    print(f"{dummy_reader.get_data('number_x2')=}")
    print(f"{dummy_reader.get_data('measurement.zip')=}")

    #Check that reader and writer agrees on file content even if it changes
    for i in range(20):
        dummy_writer.writer_worker(i)
        assert(dummy_reader.number == i)
        assert(dummy_reader.number_x2 == i*2)

    #React to changes
    dummy_reader.attach_watchdog("number", print)
    print("Watchdog reacting to changes 0...19: ")
    for i in range(20):
        dummy_writer.writer_worker(i)
        #Give some time for other thread to act
        sleep(0.005)

    dummy_reader.disable_watchdog("number")

    dataset_path = os.path.join(TMPFS_PATH,"dummy_dataset")
    try:
        os.mkdir(dataset_path)
        dummy_reader.take_snapshot(dataset_path)
        zip_path = os.listdir(dataset_path)[0]
        print(read(os.path.join(dataset_path,zip_path)))
        shutil.rmtree(dataset_path)

        os.mkdir(dataset_path)
        dummy_reader.start_write(dataset_path)
        for i in range(20):
            dummy_writer.writer_worker(i)
            sleep(0.01)

        zip_list = os.listdir(dataset_path)
        print(f"Checking number of saved snapshots: {len(zip_list)=} should be 20")
        print("and file content should be number: 0...19 (not necessary in order): ")
        zip_files = os.listdir(dataset_path)
        for file in zip_files:
            print (read(os.path.join(dataset_path, file)))

        shutil.rmtree(dataset_path)
    except FileExistsError:
        print(f"Test directory at {dataset_path} already exists. Skipping dataset creation tests" )
