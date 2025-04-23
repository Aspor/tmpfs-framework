#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 11:30:43 2021

@author: aspor
"""
import os
import time
import zipfile
import shutil
import random
import string

from threading import Event
from pathlib import Path

import numpy as np

from .cbor_utils import write_cbor, get_temp_file, tmpfsPath


class SensorWriter():
  def __init__(self, dirPath, filename):
    self.tmpfsPath = tmpfsPath
    d = f'{self.tmpfsPath}/{dirPath}/'
    os.makedirs(d,exist_ok=True)
    self.hdfFile = d+filename
    Path(self.hdfFile).mkdir(parents=True,exist_ok=True)

    self.filename=filename
    self.stop_event=Event()


  def start(self):
    pass

  def stop(self):
    self.stop_event.set()

  def write_loop(self, wait=None):
    self.stop_event.clear()
    pass

  def write(self,name,data,attributes=None):
    if type (data) is dict:
      for d in data:
        self.write(os.path.join(name,str(d)),data[d])
    else:
      write_cbor(os.path.join( self.hdfFile,name),data)
    if attributes is not None:
      self.write(name+"_attr",attributes)

  def writeZip(self, name, data, compress=False, keep=False):
    self.write(name,data)
    p=os.path.join(self.hdfFile,name)

    compression=zipfile.ZIP_DEFLATED
    if(not compress):
      compression=zipfile.ZIP_STORED
    tmpF=get_temp_file()
    with zipfile.ZipFile(f'{tmpF}.zip','w',compression=compression,compresslevel=3) as z:
          for root, _, files in os.walk(os.path.join(self.hdfFile,name)):
            for file in files:
              fn=Path(root, file)
              afn=fn.relative_to(self.hdfFile)
              z.write(filename=fn,arcname=afn)
            # shutil.copy2(f'{self.hdfFile}/{f}',f'{p}/{f}')
    if not keep:
      shutil.rmtree(os.path.join(self.hdfFile,name),ignore_errors=True)
    os.rename(f'{tmpF}.zip',f'{p}.zip')



def pack_to_zip(files,base_dir="." ,zipname="measurement",compress=False  ):
    path = zipname
    root = base_dir#os.path.dirname(zipname)

    compression=zipfile.ZIP_DEFLATED
    if(not compress):
      compression=zipfile.ZIP_STORED

    tmpF=get_temp_file()
    with zipfile.ZipFile(f'{tmpF}.zip','w',compression=compression,compresslevel=3) as z:
      for file in files:
              fn=Path(root, file)
              afn=file #fn.relative_to(self.hdfFile)
              z.write(filename=fn,arcname=afn)
            # shutil.copy2(f'{self.hdfFile}/{f}',f'{p}/{f}')
    path = os.path.join(root,path)
    os.rename(f'{tmpF}.zip',f'{path}.zip')
