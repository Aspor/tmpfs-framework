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

from .cbor_utils import decodeTags

tmpfsPath = '/home/robot'


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SensorNotInitializedError(Exception):
    pass

class SensorReader:
    def __init__(self, dirPath, filename=None, sensorName=None, datadir="collected_data/", to_watch="measurement.zip", **kwargs):
        """
        Initialize the SensorReader object.

        Parameters:
        dirPath (str): Directory path where sensor data is stored.
        filename (str or int, optional): Filename of the sensor data. Defaults to None.
        sensorName (str, optional): Name of the sensor. Defaults to None.
        datadir (str, optional): Directory to store collected data. Defaults to "collected_data/".
        to_watch (str, optional): File to watch for changes. Defaults to "measurement.zip".
        """
        self.tmpfsPath = tmpfsPath
        self.datadir = datadir
        d = os.path.join(tmpfsPath, dirPath)

        if filename is None or isinstance(filename, int):
            if filename is None:
                filename = -1
            files = os.listdir(d)
            filename = files[filename]

        self.sensorPath = os.path.join(d, filename)
        self.filename = filename
        self.sensorName = filename.replace(" ", "_") if sensorName is None else sensorName
        self.has_zip = False
        self.has_metaFile = False

        if os.path.isdir(self.sensorPath):
            self.attributes = os.listdir(self.sensorPath)
            if os.path.isfile(os.path.join(self.sensorPath, 'measurement.zip')):
                self.has_zip = True
            if os.path.isfile(os.path.join(self.sensorPath, 'metadata.zip')):
                self.has_metaFile = True
            self.attributes = [file for file in self.attributes if "measurement" not in file and "metadata" not in file]
        elif os.path.isfile(self.sensorPath):
            self.attributes = [filename]
        else:
            raise FileNotFoundError(f"No datafile found, {self.sensorPath}")

        if not self.attributes:
            raise SensorNotInitializedError(f"Measurements not initialized, {self.sensorPath}")


        files =os.listdir(self.sensorPath)
        if to_watch in files:
          self.to_watch = to_watch
        else:
          to_watch = files[0]
          for fn in files:
            print(fn, os.path.isfile(os.path.join(self.sensorPath,fn)))
            if os.path.isfile(os.path.join(self.sensorPath,fn)):
              to_watch = fn
              break
          self.to_watch=to_watch

        self.waitTime = 0.01
        self.workerThread = multiprocessing.Process(target=self.writerWorker)
        self.saveEvent = multiprocessing.Event()
        self.saveEvent.clear()
        self.waitEvent = multiprocessing.Event()
        self.waitEvent.clear()
        self.first = False
        self.prevStat = os.stat(self.sensorPath)
        self.prev_ts = time.time()
        self.observers = {}
        self.init_attributes()
        self.observer = Observer()


    def init_attributes(self):
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
                    self.__setattr__(f"get_{attribute}", self.attribute_function(filename))
                attribute_name = attribute.replace(" ", "_")
                cleaned_attributes.append(attribute_name)
                if not hasattr(self, attribute_name):
                    prop = property(fget=self.attribute_function(filename), doc=f"{attribute} getter property")
                    setattr(self.__class__, attribute_name, prop)
            except Exception as e:
                logging.debug(e)

        self.attributes = cleaned_attributes
        self.attributes.append("attributes")

        if self.has_metaFile:
            self.__setattr__("get_metadata", self.attribute_function("metadata.zip"))
            prop = property(fget=self.attribute_function("metadata.zip"), doc="metadata getter property")
            setattr(self.__class__, "metadata", prop)
            self.attributes.append("metadata")

        if self.has_zip:
            self.__setattr__("get_measurement", self.attribute_function("measurement.zip"))
            prop = property(fget=self.attribute_function("measurement.zip"), doc="measurement getter property")
            setattr(self.__class__, "measurement", prop)
            self.attributes.append("measurement")

    def attribute_function(self, attribute):
        """
        Create a getter function for the given attribute.

        Parameters:
        attribute (str): Attribute name.

        Returns:
        function: Getter function for the attribute.
        """
        def func(self):
            return self.getValue(attribute)
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
        path = '/' + path
        data, intrinsics = read(self.sensorPath, path)
        return data, intrinsics

    def takeSnapShot(self, path, compresslevel=0):
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
        timestamp=str(int(os.stat(os.path.join(self.sensorPath,self.to_watch)).st_mtime_ns/1e6)) # in milliseconds
        #timestamp = str(int(time.time_ns() / 1e6))  # in milliseconds
        compresslevel = compresslevel

        if self.first and self.has_metaFile:
            snapShotFile = os.path.join(path, self.sensorName + "_metadata")
            if compresslevel == 0:
                shutil.copy2(f'{self.sensorPath}/metadata.zip', f'{snapShotFile}.zip')
            else:
                with zipfile.ZipFile(f'{self.sensorPath}/metadata.zip', 'r') as myZip:
                    files = myZip.namelist()
                    with zipfile.ZipFile(f'{snapShotFile}.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compresslevel) as compressed:
                        for file in files:
                            compressed.writestr(file, myZip.read(file))
            self.first = False

        snapShotFile = f'{path}{timestamp}_{self.sensorName}'

        if self.has_zip:
            if compresslevel == 0:
                shutil.copy2(f'{self.sensorPath}/measurement.zip', f'{snapShotFile}.zip')
            else:
                with zipfile.ZipFile(f'{self.sensorPath}/measurement.zip', 'r') as myZip:
                    files = myZip.namelist()
                    with zipfile.ZipFile(f'{snapShotFile}.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compresslevel) as compressed:
                        for file in files:
                            compressed.writestr(file, myZip.read(file))
            return True


        with zipfile.ZipFile(f'{snapShotFile}.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compresslevel) as zipArchive:
            for name in self.filenames:
                if "metadata" in name:
                    continue
                filePath = os.path.join(self.sensorPath, name)
                if os.path.exists(filePath + '.zip'):
                    continue
                elif name.endswith(".zip"):
                    zipArchive.write(filename=filePath, arcname=name)
                elif os.path.isdir(filePath):
                    for root, dirs, files in os.walk(filePath):
                        for file in files:
                            fn = Path(root, file)
                            afn = fn.relative_to(self.sensorPath)
                            if os.path.exists(fn):
                                zipArchive.write(filename=fn, arcname=afn)
                            else:
                                zipArchive.write(filename=filePath, arcname=name)
            return True

    def updateAttributes(self):
        """
        Update attributes for the SensorReader object.
        """
        self.attributes = os.listdir(self.sensorPath)
        self.init_attributes()

    def getValue(self, name):
        """
        Get the value of the given attribute.

        Parameters:
        name (str): Attribute name.

        Returns:
        Any: Value of the attribute.
        """
        return read(os.path.join(self.sensorPath, name))

    def getBinary(self, name):
        """
        Get the binary data of the given attribute.

        Parameters:
        name (str): Attribute name.

        Returns:
        bytes: Binary data of the attribute.
        """
        if name in ("metadata", "metaData"):
            name = "metadata.zip"
        try:
            with open(self.getValueFilePath(name), 'rb') as file:
                return file.read(-1)
        except:
            try:
                with open(self.getValueFilePath(name + ".zip"), 'rb') as file:
                    return file.read(-1)
            except:
                with open(self.getValueFilePath(name[:-4] + ".jpg"), 'rb') as file:
                    return file.read(-1)

    def getValueFilePath(self, name):
        """
        Get the file path for the given attribute.

        Parameters:
        name (str): Attribute name.

        Returns:
        str: File path of the attribute.
        """
        return os.path.join(self.sensorPath, name)

    def startWrite(self, datadir=None):
        """
        Start writing sensor data.

        Parameters:
        datadir (str, optional): Directory to store data. Defaults to None.
        """
        self.first = True
        self.init_watchdog(datadir)

    def writerWorker(self, datadir=None):
        """
        Worker function to write sensor data.

        Parameters:
        datadir (str, optional): Directory to store data. Defaults to None.
        """
        if self.waitEvent.is_set():
            return
        ts = time.time()
        time_step = time.time() - self.prev_ts
        if time_step < self.waitTime:
            self.waitEvent.set()
            time.sleep(self.waitTime - time_step)
            self.waitEvent.clear()
        self.prev_ts = time.time()
        self.takeSnapShot(datadir, compresslevel=3)

    def init_watchdog(self, datadir):
        """
        Initialize the watchdog to monitor changes in sensor data.

        Parameters:
        datadir (str, optional): Directory to store data. Defaults to self.datadir.
        """
        if datadir is None:
            datadir = self.datadir
        os.makedirs(datadir, exist_ok=True)

        class EventHandler(FileSystemEventHandler):
            def __init__(self, parent):
                self.parent = parent
                super().__init__()

            def on_created(self, event):
                if event.is_directory:
                    return
                basename = os.path.basename(event.src_path)
                if basename == self.parent.to_watch:
                    self.parent.writerWorker(datadir)

        self.observer = Observer()
        eh = EventHandler(self)
        self.observer.schedule(eh, self.sensorPath, recursive=True)
        self.observer.start()

    def stop_watchdog(self):
        """
        Stop the watchdog monitoring.
        """
        try:
            self.observer.stop()
            self.waitEvent.clear()
            del self.observer
            self.observer = Observer()

        except:
            pass

    def get_packed_data_location(self):
        """
        Get the location of packed data.

        Returns:
        str: Location of packed data.
        """
        if self.has_zip:
            return os.path.join(self.sensorPath,'measurement.zip')
        return self.sensorPath

    def get_metadata_location(self):
        """
        Get the location of metadata.

        Returns:
        str: Location of metadata.
        """
        if self.has_metaFile:
           return os.path.join(self.sensorPath,'metadata.zip')
        return self.sensorPath

    def attach_watchdog(self, value_to_watch, callback):
        """
        Attach a watchdog to monitor changes in the specified value.

        Parameters:
        value_to_watch (str): Value to watch for changes.
        callback (function): Callback function to execute when changes are detected.
        """
        path = self.getValueFilePath(value_to_watch)
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
        eh = EventHandler(self)
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
    Read data from the specified file.

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
            names = zf.namelist()
            ret = {}
            for file in names:
                path = file.split('/')
                r = ret
                for part in path[1:-1]:
                    #populate directory recursevely
                    r[part] = r.get(part, {})
                    r = r[part]
                decoder = cbor2.CBORDecoder(zf.open(file), tag_hook=decodeTags)
                r[path[-1]] = decoder.decode()
            return ret

    with open(filename, 'rb') as fd:
        decoder = cbor2.CBORDecoder(fd, tag_hook=decodeTags)
        return decoder.decode()



def parseZip(filename):
    #Creates dictionary hiararchy from file hierachy in zip file and parses cbor data
    #print(filename)
    try:
      with open(filename,'rb') as f:
         return parseBinaryZip(f)
    except Exception as e:
       print(e, filename, os.getcwd() )

    return {}


def parseBinaryZip(zipdata):
    #Creates dictionary hiararchy from file hierachy in zip file and parses cbor data
    #Handles nested zip archives
    data = {}
    with zipfile.ZipFile(zipdata,'r') as zf:
      names = zf.namelist()
      for file in names:
        path = file.split("/")
        d=data
        if len(path)>1:
          d =data
          for part in path[:-1]:
            if part not in d:
              d[part]={}
            d=d[part]
          if(file.endswith("zip")):
            d[path[-1][:-4]] = parseBinaryZip(zf.open(file))
            continue
          d[path[-1]] = cbor2.load(zf.open(file), tag_hook=decodeTags)
        else:
          if(file.endswith("zip")):
            d[file.split('/')[-1][:-4] ] = parseBinaryZip(zf.open(file))
            continue
          d[file.split('/')[-1]]=cbor2.load(zf.open(file),  tag_hook=decodeTags )
    return data



def create_sensor(dirPath, filename, sensorName=None, *args, **kwarg):
  """Create a sensor object from provided directory path and sensor file name

  Args:
      dirPath (_type_): _description_
      filename (_type_): _description_
      sensorName (_type_, optional): _description_. Defaults to None.

  Returns:
      _type_: _description_
  """
  try:
    n = filename if sensorName is None else sensorName

    #Create a sensor type that inherits SensorReader. This will allow modifying class features online
    Sensor = type(n, (SensorReader,), {})

    sensor = Sensor(dirPath= dirPath, filename=filename, sensorName=None, **kwarg)
    return sensor
  except Exception as e:
    print(e, "no sensor", filename)
