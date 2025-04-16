import numpy as np

tags = [r for r in range(64,87)] #typed arrays
tags.append(40) #array of two arrays

def decodeTags(decoder,tag,shareable_index=None ):
  if tag.tag not in tags:
    #Standard cbor tag
    return tag
  if tag.tag ==40:
     return decodeTag40(decoder,tag)
  else:
     return decodeHomogenousArary(decoder,tag)

def decodeTag40(decoder,tag,shareable_index=None):
  print(tag)
  shape = tag.value[0]
  print(shape)
  #arr = np.zeroes(shape)
  values = np.asanyarray(tag.value[1])
  return values.reshape(shape)

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

def decodeHomogenousArary(decoder,tag,shareable_index=None):

   dtype = dtype_map[tag.tag]

   array =np.frombuffer(tag.value,dtype=dtype)
   return array
