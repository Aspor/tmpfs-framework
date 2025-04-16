#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 11:30:43 2021

@author: aspor
"""
import os
import time

from threading import Event
import numpy as np
from pathlib import Path
import threading
import zipfile
import shutil
import random
import string
#import umsgpack as msgpack
import  cbor2
import logging
# import msgpack_numpy as m
# m.patch()

tmpfsPath = '/home/robot'


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
      write_msgpack (os.path.join( self.hdfFile,name),data)
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

def get_temp_file(N=5):
  tmpdir = tmpfsPath
  tmpf =tmpdir+'/tmp'+"".join(random.choices(
      string.ascii_uppercase + string.digits, k=N)) +str(time.time()).split('.')[-1]
  return tmpf
  #tempFile = '/run/user/1000/'.join(random.choices(string.ascii_uppercase + string.digits, k=N))

#
# def write(filename, path, dataset, attributes={}):
#   tmpf = get_temp_file()
#   filename=filename+'/'+path
#   filename=filename.rstrip('/')
#   Path(filename).parent.mkdir(parents=True,exist_ok=True)
#
#   np.save(tmpf,dataset)
#   os.rename(tmpf+'.npy', filename)
#
#   for a in attributes:
#     tmpf = get_temp_file()
#     np.save(tmpf,attributes[a])
#     os.rename(tmpf+'.npy', f'{filename}_{a}')



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


dtype_map= {64:np.dtype(np.uint8,   ),#,'|'),
            65:np.dtype(np.uint16,  ),#,'>'),
            66:np.dtype(np.uint32,  ),#,'>'),
            67:np.dtype(np.uint64,  ),#,'>'),
            68:np.dtype(np.uint8,   ),#,'|'),
            69:np.dtype(np.uint16,  ),#,'<'),
            70:np.dtype(np.uint32,  ),#,'<'),
            71:np.dtype(np.uint64,  ),#,'<'),
            72:np.dtype(np.int8,    ),#,'|'),
            73:np.dtype(np.int16,   ),#,'>'),
            74:np.dtype(np.int32,   ),#,'>'),
            75:np.dtype(np.int64,   ),#'>'),
            #76 ##RESERVED##
            77:np.dtype(np.int16,   ),#,'<'),
            78:np.dtype(np.int32,   ),#,'<'),
            79:np.dtype(np.int64,   ),#,'<'),
            80:np.dtype(np.float16, ),#,'>'),
            81:np.dtype(np.float32, ),#,'>'),
            82:np.dtype(np.float64, ),#,'>'),
            83:np.dtype(np.float128,),#,'>'),
            84:np.dtype(np.float16, ),#,'|'),
            85:np.dtype(np.float32, ),#,'<'),
            86:np.dtype(np.float64, ),#,'<'),
            87:np.dtype(np.float128,),#,'<'),
          }
tag_map = dict((reversed(item) for item in dtype_map.items()))

def numpy_encoder(encoder, value):
  value = np.asanyarray(value)
  #print(f"{value.shape=}, {value=}")
  if len(value.shape)<2:
      encoder.encode_semantic(cbor2.CBORTag(tag_map[value.dtype],value.data.tobytes()) )

  else:
    encoder.encode_semantic(cbor2.CBORTag(40,[value.shape, value.flatten()]))




##TODO WRITE HAND PACKING FOR NUMPY##########
def write_msgpack(filename,data):

  tmpf = get_temp_file()

  Path(filename).parent.mkdir(parents=True,exist_ok=True)
  #print("write", filename.split("/")[-1])
  # try:
  #   data = data.tolist()
  # except Exception as e:
  #   pass
  with open(tmpf,'wb') as fd:
    encoder = cbor2.CBOREncoder(fd, default=numpy_encoder)
    encoder.encode(data)
  os.rename(tmpf, filename)
  #print("DONE")
