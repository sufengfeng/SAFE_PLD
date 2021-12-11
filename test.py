import struct
from ctypes import *
# import _thread
# import time
# import signal
# import sys
# import ctypes

class VCI_CAN_OBJ(Structure):
    _fields_ = [
        ('ID', c_uint),
        ('TimeStamp', c_uint),
        ('TimeFlag', c_byte),
        ('SendType', c_byte),
        ('RemoteFlag', c_byte),
        ('ExternFlag', c_byte),
        ('DataLen', c_byte),
        ('Data', c_byte * 8),
        ('Reserved', c_byte * 3)
    ]
send_msg = VCI_CAN_OBJ(ID=0x64, DataLen=8, ExternFlag=0, RemoteFlag=0, SendType=0, TimeFlag=1, TimeStamp=0x12345678)

a=35
b=258
str=struct.pack('ii',a,b) #转换成字节流，虽然还是字符串，但是可以在网络上传输
print(len(str)) #ii 表示两个int
print(struct.calcsize('ii'))
with open('test.bin', mode='wb+') as f:
    f.seek(0x4, 0)
    f.write(struct.pack('i', 956506))

    f.seek(0x10, 0)
    f.write(str)
    f.seek(0x20, 0)
    #f.write(struct.pack(send_msg))


class SSHead(BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        # (字段名, c类型 )
        ('nTotalSize', c_uint32),
        ('nSourceID', c_int32),
        ('sourceType', c_uint8),
        ('destType', c_uint8),
        ('transType', c_uint8),
        ('nDestID', c_int32),
        ('nFlag', c_uint8),
        ('nOptionalLength', c_uint16),
        ('arrOptional', c_char * 20),
    ]

    def encode(self):
        return string_at(addressof(self), sizeof(self))

    def decode(self, data):
        memmove(addressof(self), data, sizeof(self))
        return len(data)

    def pack(self):
        buffer = struct.pack("!IIBBBIBH20s", self.nTotalSize, self.nSourceID, self.sourceType
                             , self.destType, self.transType, self.nDestID, self.nFlag, self.nOptionalLength,
                             self.arrOptional)
        return buffer

    def unpack(self, data):
        (self.nTotalSize, self.nSourceID, self.sourceType, self.destType, self.transType, self.nDestID,
         self.nFlag, self.nOptionalLength, self.arrOptional) = struct.unpack("!IIBBBIBH20s", data)


# ---------------------------
# 测试
s = SSHead()
s.arrOptional = b'hello'

ss = SSHead()
ss.unpack(s.encode())
print(ss.arrOptional)