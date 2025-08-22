import random
import string
from pathlib import Path
import os

import time

import numpy as np

import cbor2
import logging

#from tmpfs_framework import tmpfs_path
import tmpfs_framework

_tags = [r for r in range(64,87)] #typed arrays
_tags.append(40) #array of arrays

_dtype_map= {64:np.dtype(np.uint8,   ),#,'|'),
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

_tag_map = dict((reversed(item) for item in _dtype_map.items()))


def decode_tags(decoder,tag,shareable_index=None ):
  if tag.tag not in _tags:
    #Standard cbor tag
    return tag
  if tag.tag ==40:
     return _decode_tag_40(decoder,tag)
  else:
     return _decode_homogenous_arary(decoder,tag)

def _decode_tag_40(decoder,tag,shareable_index=None):
  logging.debug(tag)
  shape = tag.value[0]
  logging.debug(shape)
  #arr = np.zeroes(shape)
  values = np.asanyarray(tag.value[1])
  return values.reshape(shape)


def _decode_homogenous_arary(decoder,tag,shareable_index=None):

   dtype = _dtype_map[tag.tag]

   array =np.frombuffer(tag.value,dtype=dtype)
   return array

def _numpy_encoder(encoder, value):
  value = np.asanyarray(value)
  #print(f"{value.shape=}, {value=}")
  if len(value.shape)<2:
      encoder.encode_semantic(cbor2.CBORTag(_tag_map[value.dtype],value.data.tobytes()) )
  else:
    encoder.encode_semantic(cbor2.CBORTag(40,[value.shape, value.flatten()]))

def write_cbor(filename,data):
  tmpf = get_temp_file()
  Path(filename).parent.mkdir(parents=True,exist_ok=True)
  with open(tmpf,'wb') as fd:
    encoder = cbor2.CBOREncoder(fd, default=_numpy_encoder)
    encoder.encode(data)
  os.rename(tmpf, filename)

def get_temp_file(N=5,tmpfs_path=None):
  tmpdir = tmpfs_path if tmpfs_path is not None else tmpfs_framework.TMPFS_PATH

  #tmpdir = tmpfs_path
  tmpf =tmpdir+'/tmp'+"".join(random.choices(
      string.ascii_uppercase + string.digits, k=N)) +str(time.time()).split('.')[-1]
  return tmpf
