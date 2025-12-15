#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 10:11:37 2020
@author: aspor
"""

import os
import time
import shutil
import zipfile
import multiprocessing
from pathlib import Path
import logging
import cbor2

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .cbor_utils import decode_tags
import tmpfs_framework


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SensorNotInitializedError(Exception):
    pass

class SensorReader:
    def __init__(self, directory, filename=None, sensor_name=None, data_dir="collected_data/",
                  to_watch="measurement.zip", tmpfs_path = None, **kwargs):
        """
        Initialize the SensorReader object.

        Parameters:
        directory (str): Directory path where sensor data is stored.
        filename (str or int, optional): Filename of the sensor data. Defaults to None.
        sensor_name (str, optional): Name of the sensor. Defaults to None.
        data_dir (str, optional): Directory to store collected data. Defaults to "collected_data/".
        to_watch (str, optional): File to watch for changes. Defaults to "measurement.zip".
        """
        self.tmpfs_path = tmpfs_path if tmpfs_path is not None else tmpfs_framework.TMPFS_PATH
        self.data_dir = data_dir
        d = os.path.join(self.tmpfs_path, directory)

        if filename is None or isinstance(filename, int):
            if filename is None:
                filename = -1
            files = os.listdir(d)
            filename = files[filename]

        self.sensor_path = os.path.join(d, filename)
        self.filename = filename
        self.sensor_name = filename.replace(" ", "_") if sensor_name is None else sensor_name
        self.has_zip = False
        self.has_metaFile = False

        if os.path.isdir(self.sensor_path):
            self.attributes = os.listdir(self.sensor_path)
            if os.path.isfile(os.path.join(self.sensor_path, 'measurement.zip')):
                self.has_zip = True
            if os.path.isfile(os.path.join(self.sensor_path, 'metadata.zip')):
                self.has_metaFile = True
            self.attributes = [file for file in self.attributes if "measurement" not in file and "metadata" not in file]
        elif os.path.isfile(self.sensor_path):
            self.attributes = [filename]
        else:
            raise FileNotFoundError(f"No datafile found, {self.sensor_path}")

        if not self.attributes:
            raise SensorNotInitializedError(f"Measurements not initialized, {self.sensor_path}")

        self.wait_time = 0.01
        self.worker_thread = multiprocessing.Process(target=self._writer_worker)
        self.save_event = multiprocessing.Event()
        self.save_event.clear()
        self.wait_event = multiprocessing.Event()
        self.wait_event.clear()
        self.first = False
        self.prev_stat = os.stat(self.sensor_path)
        self.to_watch = to_watch
        self.prev_ts = time.time()
        self.observers = {}
        self._init_attributes()
        self.observer = Observer()

    def _init_attributes(self):
        """
        Initialize attributes for the SensorReader object.
        """
        cleaned_attributes = []
        self.filenames = self.attributes

        for attribute in self.attributes:
            try:
                filename = attribute
                attribute = attribute.replace(" ", "_").replace(".", "_")
                if not hasattr(self, f"get_{attribute}"):
                    self.__setattr__(f"get_{attribute}", self._create_attribute_function(filename))
                attribute_name = attribute.replace(" ", "_")
                cleaned_attributes.append(attribute_name)
                if not hasattr(self, attribute_name):
                    prop = property(fget=self._create_attribute_function(filename), doc=f"{attribute} getter property")
                    setattr(self.__class__, attribute_name, prop)
            except Exception as e:
                logging.debug(e)

        self.attributes = cleaned_attributes
        self.attributes.append("attributes")

        if self.has_metaFile:
            self.__setattr__("get_metadata", self._create_attribute_function("metadata.zip"))
            prop = property(fget=self._create_attribute_function("metadata.zip"), doc="metadata getter property")
            setattr(self.__class__, "metadata", prop)
            self.attributes.append("metadata")

        if self.has_zip:
            self.__setattr__("get_measurement", self._create_attribute_function("measurement.zip"))
            prop = property(fget=self._create_attribute_function("measurement.zip"), doc="measurement getter property")
            setattr(self.__class__, "measurement", prop)
            self.attributes.append("measurement")

    def _create_attribute_function(self, attribute):
        """
        Create a getter function for the given attribute.

        Parameters:
        attribute (str): Attribute name.

        Returns:
        function: Getter function for the attribute.
        """
        def func(self):
            return self.get_value(attribute)
        func.__doc__ = f"Getter function for attribute {attribute}. Reads value from tmpfs as numpy array"
        return func

    def get_data(self, path=''):
        """
        Get data from the sensor.

        Parameters:
        path (str, optional): Path to the data. Defaults to ''.

        Returns:
        tuple: Data and intrinsics.
        """
        #path = '/' + path
        #data, intrinsics = read(self.sensor_path, path)
        data = read(self.sensor_path, path)

        return data#, intrinsics

    def take_snapshot(self, path, compresslevel=0):
        """
        Take a snapshot of the sensor data.

        Parameters:
        path (str): Path to save the snapshot.
        compress (bool, optional): Whether to compress the snapshot. Defaults to False.

        Returns:
        bool: True if snapshot is taken successfully, False otherwise.
        """
        if path[-1] != '/':
            path += '/'
        timestamp = str(int(time.time_ns() / 1e6))  # in milliseconds
        compresslevel = compresslevel

        if self.first and self.has_metaFile:
            snapShotFile = os.path.join(path, self.sensor_name + "_metadata")
            if compresslevel == 0:
                shutil.copy2(f'{self.sensor_path}/metadata.zip', f'{snapShotFile}.zip')
            else:
                with zipfile.ZipFile(f'{self.sensor_path}/metadata.zip', 'r') as myZip:
                    files = myZip.namelist()
                    with zipfile.ZipFile(f'{snapShotFile}.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compresslevel) as compressed:
                        for file in files:
                            compressed.writestr(file, myZip.read(file))
            self.first = False

        snapShotFile = f'{path}{timestamp}_{self.sensor_name}'

        if self.has_zip:
            if compresslevel == 0:
                shutil.copy2(f'{self.sensor_path}/measurement.zip', f'{snapShotFile}.zip')
            else:
                with zipfile.ZipFile(f'{self.sensor_path}/measurement.zip', 'r') as myZip:
                    files = myZip.namelist()
                    with zipfile.ZipFile(f'{snapShotFile}.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compresslevel) as compressed:
                        for file in files:
                            compressed.writestr(file, myZip.read(file))
            return True


        with zipfile.ZipFile(f'{snapShotFile}.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compresslevel) as zipArchive:
            for name in self.filenames:
                if "metadata" in name:
                    continue
                filePath = os.path.join(self.sensor_path, name)
                if os.path.exists(filePath + '.zip'):
                    continue
                elif name.endswith(".zip"):
                    zipArchive.write(filename=filePath, arcname=name)
                elif os.path.isdir(filePath):
                    for root, dirs, files in os.walk(filePath):
                        for file in files:
                            fn = Path(root, file)
                            afn = fn.relative_to(self.sensor_path)
                            if os.path.exists(fn):
                                zipArchive.write(filename=fn, arcname=afn)
                            else:
                                zipArchive.write(filename=filePath, arcname=name)
            return True

    def update_attributes(self):
        """
        Update attribute array for the SensorReader object. Can be used to detec new
        variables if they were not available at start up
        """
        self.attributes = os.listdir(self.sensor_path)
        self._init_attributes()

    def get_value(self, name):
        """
        Get the value of the given attribute.

        Parameters:
        name (str): Attribute name.

        Returns:
        Any: Value of the attribute.
        """
        if name =="attributes":
            return self.attributes
        return read(os.path.join(self.sensor_path, name))

    def get_binary(self, name):
        """
        Get the binary data of the given attribute.
        Reads the file without decoding it. Useful when tranferring data to other machines

        Parameters:
        name (str): Attribute name.

        Returns:
        bytes: Binary data of the attribute.
        """
        print(name)
        if name in ("metadata", "metaData"):
            name = "metadata.zip"
        try:
            with open(self.get_value_path(name), 'rb') as file:
                return file.read(-1)
        except:
            try:
                with open(self.get_value_path(name + ".zip"), 'rb') as file:
                    return file.read(-1)
            except:
                with open(self.get_value_path(name[:-4] + ".jpg"), 'rb') as file:
                    return file.read(-1)

    def get_value_path(self, name):
        """
        Get the file path for the given attribute.

        Parameters:
        name (str): Attribute name.

        Returns:
        str: File path of the attribute.
        """
        return os.path.join(self.sensor_path, name)

    def start_write(self, data_dir=None):
        """
        Start writing sensor data to hard disk. Used when creating datasets for later use

        Parameters:
        data_dir (str, optional): Directory to store data. Defaults to None.
        """
        self.first = True
        self.init_watchdog(data_dir)

    def _writer_worker(self, data_dir=None):
        """
        Takes snapshots of data. Used for creating datasets

        Parameters:
        data_dir (str, optional): Directory to store data. Defaults to None.
        """
        if self.wait_event.is_set():
            return
        ts = time.time()
        time_step = time.time() - self.prev_ts
        if time_step < self.wait_time:
            self.wait_event.set()
            time.sleep(self.wait_time - time_step)
            self.wait_event.clear()
        self.prev_ts = time.time()
        self.take_snapshot(data_dir, compresslevel=3)

    def init_watchdog(self, data_dir=None):
        """
        Initialize the watchdog to monitor changes in sensor data. When new data arrives
        Write it to given path

        Parameters:
        data_dir (str, optional): Directory to store data. Defaults to self.data_dir.
        """
        if data_dir is None:
            data_dir = self.data_dir
        os.makedirs(data_dir, exist_ok=True)

        class EventHandler(FileSystemEventHandler):
            def __init__(self, parent):
                self.parent = parent
                super().__init__()

            def on_created(self, event):
                if event.is_directory:
                    return
                basename = os.path.basename(event.src_path)
                if basename == self.parent.to_watch:
                    self.parent._writer_worker(data_dir)

        self.observer = Observer()
        eh = EventHandler(self)
        self.observer.schedule(eh, self.sensor_path, recursive=True)
        self.observer.start()

    def stop_watchdog(self):
        """
        Stop the watchdog monitoring.
        """
        try:
            self.observer.stop()
            self.wait_event.clear()
            del self.observer
            self.observer = Observer()

        except:
            pass

    def get_packed_data_location(self):
        """
        Get the location of packed data. Useful if user wants the whole measurement.

        Returns:
        str: Location of packed data.
        """
        if self.has_zip:
            return os.path.join(self.sensor_path,'measurement.zip')
        return self.sensor_path

    def get_metadata_location(self):
        """
        Get the location of metadata.

        Returns:
        str: Location of metadata.
        """
        if self.has_metaFile:
           return os.path.join(self.sensor_path,'metadata.zip')
        return self.sensor_path

    def attach_watchdog(self, value_to_watch, callback):
        """
        Attach a watchdog to monitor changes in the specified value.

        Parameters:
        value_to_watch (str): Value to watch for changes.
        callback (function): Callback function to execute when changes are detected.
        """
        path = self.get_value_path(value_to_watch)
        dirpath, basename = os.path.split(path)

        class EventHandler(FileSystemEventHandler):
            def __init__(self):

                super().__init__()

            def on_created(self, event):
                if event.is_directory:
                    return
                if os.path.basename(event.src_path) == basename:
                    data = read(event.src_path)
                    callback(data)

        observer = Observer()
        eh = EventHandler()
        observer.schedule(eh, dirpath, recursive=True)
        observer.start()
        self.observers[value_to_watch] = observer


    def disable_watchdog(self, value_to_watch):
        """
        Disable the watchdog monitoring the specified value.

        Parameters:
        value_to_watch (str): Value to stop watching.
        """
        obs = self.observers.pop(value_to_watch)
        try:
            obs.stop()
            del obs
        except:
            pass

def read(filename, attribute=None):
    """
    Read and decode data from the specified file.

    Parameters:
    filename (str): File name.
    attribute (str, optional): Attribute to read. Defaults to None.

    Returns:
    Any: Data read from the file.
    """
    filename = os.path.join(filename, attribute) if attribute is not None else filename
    if os.path.isdir(filename):
        ret = {}
        for attribute in os.listdir(filename):
            ret[attribute] = read(filename, attribute=attribute)
        return ret

    if filename.endswith('.zip'):
        with zipfile.ZipFile(filename, 'r') as zf:
            archive_content = zf.infolist()
            ret = {}
            for file in archive_content:
                path = file.filename.split('/')
                r = ret
                for part in path[1:-1]:
                    #populate directory recursevely
                    r[part] = r.get(part, {})
                    r = r[part]
                if file.is_dir():
                  continue
                decoder = cbor2.CBORDecoder(zf.open(file), tag_hook=decode_tags)
                r[path[-1]] = decoder.decode()

            return ret

    with open(filename, 'rb') as fd:
        decoder = cbor2.CBORDecoder(fd, tag_hook=decode_tags)
        return decoder.decode()
