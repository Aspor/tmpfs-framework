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
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


from cbor_uitils import decodeTags


tmpfsPath = '/home/robot'

class SensorNotInitializedError(Exception):
    pass


class SensorReader():
  def __init__(self, dirPath, filename=None, sensorName=None,  datadir="collected_data/" ,
                to_watch = "measurement.zip", **kwargs):
#    super().__init__(**kwargs)

    self.tmpfsPath = tmpfsPath
    self.datadir=datadir
    d = os.path.join(tmpfsPath,dirPath)

    if filename is None or type(filename) is int:
        if(filename is None):
          filename=-1

        files =os.listdir(d)
        filename = files[filename]

    self.hdfFile = os.path.join( d,filename)
    self.filename=filename
    self.sensorName=filename.replace(" ", "_") if sensorName is None else sensorName
    isFile=False

    print(self.hdfFile, dirPath, d, filename)
    self.has_zip=False
    self.has_metaFile=False
    if os.path.isdir(self.hdfFile):
      self.attributes=os.listdir(self.hdfFile)
      if os.path.isfile(self.hdfFile+'/measurement.zip'):
         self.has_zip=True
      if os.path.isfile(self.hdfFile+'/metadata.zip'):
         self.has_metaFile=True

      #iterate backwards so we can safely remove items
      for file in self.attributes[::-1]:
        if "measurement" in file:
          #if file.startswith("measurement.zip"):
          self.attributes.remove(file)
        if "metadata" in  file:
          self.attributes.remove(file)

    elif os.path.isfile(self.hdfFile):
          self.attributes=[filename]
          isFile=True
    else:
      raise FileNotFoundError(f"No datafile found, {self.hdfFile}")

    if not isFile and len(self.attributes)<1:
      raise SensorNotInitializedError(f"Measurements not initialised, {self.hdfFile}")

    self.waitTime=0.01
    self.workerThread = multiprocessing.Process(target=self.writerWorker)

    self.saveEvent = multiprocessing.Event()
    self.saveEvent.clear()

    self.waitEvent = multiprocessing.Event()
    self.waitEvent.clear()


    self.first=False
    self.prevStat = os.stat(self.hdfFile)

    self.to_watch = to_watch
    self.prev_ts = time.time()
    self.observers = {}

    self.init_attributes()



  def init_attributes(self):
    cleaned_attributes=[]
    self.filenames=self.attributes
    for attribute in self.attributes:
      #attribute = attribute.replace(" ","_")
      try:
        filename = attribute
        attribute = attribute.replace(" ","_")
        attribute = attribute.replace(".","_")
        if not hasattr(self,f"get_{attribute}" ):
          self.__setattr__(f"get_{attribute}", self.attribute_function(filename))
          #setattr(self.__class__,f"get_{attribute}", self.attribute_function(attribute))

          attribute_name = attribute.replace(" ","_")
          cleaned_attributes.append(attribute_name)
          if not hasattr(self,f"{attribute_name}"):
            prop = property(fget= self.attribute_function(filename),fset=None,fdel=None , doc=f"{attribute} getter property" )
            setattr(self.__class__,attribute_name,prop)

      except Exception as e:
        print(e)
    self.attributes = cleaned_attributes

    self.attributes.append("attributes")
    if self.has_metaFile:

          self.__setattr__(f"get_metadata", self.attribute_function("metadata.zip"))
          #setattr(self.__class__,f"get_metadata", self.attribute_function("metadata.zip"))

          #if not hasattr(self,f"metadata"):
          prop = property(fget= self.attribute_function("metadata.zip"),fset=None,fdel=None , doc=f"{attribute} getter property" )
          setattr(self.__class__,"metadata",prop)
          self.attributes.append("metadata")
            #print(prop)
            #print(prop.fget(self))
    if self.has_zip:

          self.__setattr__(f"get_measurement", self.attribute_function("measurement.zip"))
          #setattr(self.__class__,f"get_measurement", self.attribute_function("measurement.zip"))

          #if not hasattr(self,f"metadata"):
          prop = property(fget= self.attribute_function("measurement.zip"),fset=None,fdel=None , doc=f"{attribute} getter property" )
          setattr(self.__class__,"measurement",prop)
          self.attributes.append("measurement")
            #print(prop)
            #print(prop.fget(self))


  def attribute_function(self, attribute):
    def func(self):
      return self.getValue(attribute)
    func.__doc__=f"Getter function for attribute {attribute}. Reads value from tmpfs as numpy array"
    return func

  def get_data(self,path=''):
    path = '/'+path
    data,intrinsics = read(self.hdfFile,path)
    return data, intrinsics


  def takeSnapShot(self, path, compress=False):
    if(path[-1]!='/'):
        path+='/'

    timestamp=str(int(time.time_ns()/1e6)) # in milliseconds

    if self.first and self.has_metaFile:
      snapShotFile= os.path.join(path,self.sensorName+"_metadata")
      if(not compress):
        shutil.copy2(f'{self.hdfFile}/metadata.zip',f'{snapShotFile}.zip')
      else:
        with zipfile.ZipFile(f'{self.hdfFile}/metadata.zip','r') as myZip:
          files = myZip.namelist()
          with zipfile.ZipFile(f'{snapShotFile}.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as compressed:
            for file in files:
              compressed.writestr(file,myZip.read(file))
    self.first=False

    snapShotFile= f'{path}{timestamp}_{self.sensorName}'

    if self.has_zip:
      if(not compress):
        shutil.copy2(f'{self.hdfFile}/measurement.zip',f'{snapShotFile}.zip')
      else:
        with zipfile.ZipFile(f'{self.hdfFile}/measurement.zip','r') as myZip:
          files = myZip.namelist()
          with zipfile.ZipFile(f'{snapShotFile}.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as compressed:
            for file in files:
              compressed.writestr(file,myZip.read(file))
      return True

    if(not compress):
      os.makedirs(snapShotFile,exist_ok=True)
      for f in self.filenames:
        src=f'{self.hdfFile}/{f}'
        dst=f'{snapShotFile}/{f}'
        if ("metadata" in f):
          continue

        if(os.path.isdir(src)):
          shutil.copytree(src,dst)
        else:
          shutil.copy2(f'{self.hdfFile}/{f}',f'{snapShotFile}/{f}')
      return True

    with zipfile.ZipFile(f'{snapShotFile}.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for name in self.filenames:
          if "metadata" in name:
            continue
          filePath =os.path.join(self.hdfFile,name)
          if os.path.exists(filePath+'.zip'):
            continue
          elif name.endswith(".zip"):
            print("ZIP", name, self.attributes)
            z.write(filename=filePath,arcname=name)
          elif os.path.isdir(filePath) :
            for root, dirs, files in os.walk(filePath):
              for file in files:
                fn=Path(root, file)
                afn=fn.relative_to(self.hdfFile)
                if os.path.exists(fn):
                  z.write(filename=fn,arcname=afn)
          else:
            z.write(filename=filePath,arcname=name)
          # shutil.copy2(f'{self.hdfFile}/{f}',f'{p}/{f}')
    return True

  def updateAttributes(self):
        self.attributes=os.listdir(self.hdfFile)
        self.init_attributes()


  def getValue(self,name):
        return read(os.path.join(self.hdfFile,name))

  def getBinary(self,name):
      ret = None
      if name in ("metadata","metaData"):
        name="metadata.zip"

      try:
        with open(self.getValueFilePath(name),'rb') as file:
          ret = file.read(-1)
      except:
        try:
          with open(self.getValueFilePath(name+".zip"),'rb') as file:
            ret = file.read(-1)
        except:
          with open(self.getValueFilePath(name[:-4]+".jpg"),'rb') as file:
            ret = file.read(-1)
      return ret

  def getValueFilePath(self,name):
        return os.path.join(self.hdfFile,name)

  def startWrite(self, datadir=None):
    self.first=True
    self.init_watchdog(datadir)


  def writerWorker(self,datadir=None):
    if self.waitEvent.is_set():
       return

    ts = time.time()
    time_step=time.time() - self.prev_ts
    if(time_step<self.waitTime):
      self.waitEvent.set()
      time.sleep(self.waitTime-time_step)
      self.waitEvent.clear()
    self.prev_ts = time.time()
    self.takeSnapShot(datadir,compress=True)


  def init_watchdog(self,datadir):
    if datadir is None:
       datadir=self.datadir
    os.makedirs(datadir,exist_ok=True)
    #self.waitTime=wait_time

    class eventHandler(FileSystemEventHandler):

        def __init__(self, parent):
            self.parent= parent
            super().__init__()

        def on_created(self, event):
            print("event", event, datadir)
            if event.is_directory:
                return
            basename = os.path.basename(event.src_path)
            print(basename, self.parent.to_watch)
            if basename== self.parent.to_watch:
                self.parent.writerWorker(datadir)

    self.observer = Observer()
    eh = eventHandler(self)
    self.observer.schedule(eh, self.hdfFile, recursive=True)
    self.observer.start()


  def stop_watchdog(self):
    try:
      self.observer.stop()
      self.waitEvent.clear()
      del self.observer
    except:
       pass

  def get_packed_data_location(self):
    n=self.hdfFile.split('/')[-2:]
    n=(n[0]+'/'+n[1])
    if(self.has_zip):
      n+='/measurement.zip'
    return n

  def get_metadata_location(self):
    n=self.hdfFile.split('/')[-2:]
    n=(n[0]+'/'+n[1])
    if(self.has_metaFile):
      n+='/metadata.zip'
      return n
    return None

  def attach_watchdog(self, value_to_watch, callback):
    path = self.getValueFilePath(value_to_watch)
    dirpath, basename = os.path.split(path)
    class eventHandler(FileSystemEventHandler):

      def __init__(self, parent):
            self.parent= parent
            super().__init__()

      def on_created(self, event):
        if event.is_directory:
          return
        if os.path.basename(event.src_path) == basename:
          data = read(event.src_path)
          callback(data)

    observer = Observer()
    eh = eventHandler(self)
    observer.schedule(eh, dirpath, recursive=True)
    observer.start()
    self.observers[value_to_watch] = observer

  def disable_watchdog(self, value_to_watch):
    obs = self.observers.pop(value_to_watch)
    try:
      obs.stop()
      del obs
    except:
       pass

def read(filename, attribute=None):
  filename=os.path.join(filename,attribute) if attribute is not None else filename
  print(f"{filename=}")

  if(os.path.isdir(filename)):
    ret={}
    for f in os.listdir(filename):
      print(f"DIRECTORY, f  {filename=} {f=}")
      ret[f]=read(filename, attribute=f)
    return ret

  #zip file
  if(filename.endswith('.zip')):
    with zipfile.ZipFile(filename,'r') as zf:

        names = zf.namelist()
        ret={}
        for file in names:
          path=file.split('/')
          #confusing python references
          #creates nested dictionaries with same path as files in zip
          r=ret
          for part in path[1:-1]:
            r[part]=r.get(part,{})
            r=r[part]
          decoder = cbor2.CBORDecoder(zf.open(file),tag_hook=decodeTags)
          r[path[-1]] =decoder.decode()
    return ret
  with open(filename,'rb') as fd:
        decoder = cbor2.CBORDecoder(fd,tag_hook=decodeTags)
        return decoder.decode()
