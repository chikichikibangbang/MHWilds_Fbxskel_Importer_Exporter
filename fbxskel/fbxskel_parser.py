import struct
import codecs
import json
from glob import glob
import os
import math
import numpy as np
import logging
logger = logging.getLogger("wilds_suite")

class Reader():
    def __init__(self, data):
        self.offset = 0
        self.data = data

    def read(self, kind, size):
        result = struct.unpack(kind, self.data[self.offset:self.offset+size])[0]
        self.offset += size
        return result

    def seek(self, offset, start = None):
        if start is None:
            self.offset = offset
        else:
            self.offset += offset

    def readUInt(self):
        return self.read("I", 4)

    def readInt(self):
        return self.read("i", 4)

    def readUInt64(self):
        return self.read("Q", 8)

    def readHalf(self):
        return self.read("e", 2)

    def readFloat(self):
        return self.read("f", 4)

    def readShort(self):
        return self.read("h", 2)

    def readUShort(self):
        return self.read("H", 2)

    def readByte(self):
        return self.read("b", 1)

    def readBytes(self, size):
        buf = self.data[self.offset:self.offset + size]
        if len(buf) != size:
            logger.warning("readBytes read " + str(len(buf)) + " instead of " + str(size))
        self.offset += size
        return buf

    def readUByte(self):
        return self.read("B", 1)

    def readString(self):
        text = ""
        while True:
            char = self.readUByte()
            if char == 0:
                break
            else:
                text += chr(char)
        return text

    def readStringUTF(self):
        text = ""
        while True:
            char = self.readUShort()
            if char == 0:
                break
            else:
                text += chr(char)
        return text

    def allign_soft(self, size, shift=0):
        if (self.offset-shift)%size == 0:
            pass
        else:
            self.allign(size)

    def allign(self, size):
        self.offset = (int((self.offset)/size)*size)+size

    def tell(self):
        return self.offset

    def getSize(self):
        return len(self.data)

class FbxskelParser():
    def __init__(self, path=None, streaming_path=None, data=None):
        self.path = path
        if streaming_path is not None:
            self.streaming_path = streaming_path
        else:
            self.streaming_path = self.path
            self.streaming_path = self.streaming_path.replace("natives/stm", "natives/stm/streaming")
        self.bs_streaming = None
        # print("self.streaming_path = ", self.streaming_path)
        try:
            with open(self.streaming_path, "rb") as file_in:
                streaming_data = file_in.read()
            self.bs_streaming = Reader(streaming_data)
        except:
            pass
        if data is None:
            with open(path, "rb") as file_in:
                data = file_in.read()
        self.bs = Reader(data)

    def read(self, LOD=0):
        debug = {}

        self.version = self.bs.readUInt()
        self.magic = self.bs.readUInt()
        if self.magic != 1852599155 or self.version != 7:
            raise RuntimeError(str(self.path) + " is not a Wilds mesh file (magic = " + str(self.magic) + ", version = " + str(self.version) + ")")

        _ = self.bs.readUInt64()

        bone_offset = self.bs.readUInt64()
        hash_offset = self.bs.readUInt64()

        bone_count = self.bs.readUShort()

        self.bs.seek(bone_offset)
        bone_infos = []
        for bone_i in range(bone_count):
            bone_info = {}
            bone_info["name_offset"] = self.bs.readUInt64()
            bone_info["name_hash"] = self.bs.readUInt()
            bone_info["parent"] = self.bs.readShort()
            bone_info["id"] = self.bs.readUShort()
            bone_info["rot_quat"] = [self.bs.readFloat() for _ in range(4)]
            bone_info["loc"] = [self.bs.readFloat() for _ in range(3)]
            bone_info["scl"] = [self.bs.readFloat() for _ in range(3)]
            bone_info["padding"] = self.bs.readUInt64()
            bone_infos.append(bone_info)

#         # Why does that even exists
#         self.bs.seek(hash_offset)
#         for bone_info in bone_infos:
#             bone_info["hash"] = self.bs.readUInt()
#
#             bone_info["haid"] = self.bs.readUInt()

        for bone_info in bone_infos:
            self.bs.seek(bone_info["name_offset"])
            bone_info["name"] = self.bs.readStringUTF()




        return bone_infos

if __name__ == "__main__":
    from glob import glob
    import json
    fbxskel_files = glob("ch07_000_0000.fbxskel.7", recursive=True)
    for fbxskel_file in fbxskel_files:
        try:
            parser = FbxskelParser(path=fbxskel_file)
            data = parser.read()
            print(json.dumps(data, indent="\t"))
        except Exception as e:
            import traceback
            traceback.print_exc()
