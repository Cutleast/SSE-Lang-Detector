"""
Copyright (c) Cutleast
"""

from io import BufferedReader
import struct



def int_(stream: BufferedReader, size: int):
    return int.from_bytes(stream.read(size), byteorder="big", signed=True)

def int8(stream: BufferedReader):
    return int_(stream, 1)

def int16(stream: BufferedReader):
    return int_(stream, 2)

def int32(stream: BufferedReader):
    return int_(stream, 4)

def int64(stream: BufferedReader):
    return int_(stream, 8)



def uint(stream: BufferedReader, size: int):
    return int.from_bytes(stream.read(size), byteorder="big")

def uint8(stream: BufferedReader):
    return uint(stream, 1)

def uint16(stream: BufferedReader):
    return uint(stream, 2)

def uint32(stream: BufferedReader):
    return uint(stream, 4)

def uint64(stream: BufferedReader):
    return uint(stream, 8)



def float32(stream: BufferedReader):
    return struct.unpack("f", stream.read(4))[0]

def float64(stream: BufferedReader):
    return struct.unpack("f", stream.read(8))[0]

