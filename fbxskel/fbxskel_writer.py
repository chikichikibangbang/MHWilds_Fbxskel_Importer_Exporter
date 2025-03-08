import bpy
from mathutils import Matrix, Vector, Euler, Quaternion

import struct
import math
import time
import numpy as np
import logging
logger = logging.getLogger("wilds_suite")

class Writer():
    def __init__(self):
        self.data = b""

    def tell(self):
        return len(self.data)

    def write(self, kind, value):
        self.data += struct.pack(kind, value)

    def write_list(self, kind, value):
        self.data += struct.pack(str(len(value))+kind, *value)

    def writeAt(self, kind, offset, value):
        self.data = self.data[:offset] + struct.pack(kind, value) + self.data[offset+struct.calcsize(kind):]

    def writeUInt64(self, value):
        self.write("Q", value)

    def writeUInt64s(self, value):
        self.write_list("Q", value)

    def writeUInt(self, value):
        self.write("I", value)

    def writeUInts(self, value):
        self.write_list("I", value)

    def writeUInt64At(self, offset, value):
        self.writeAt("Q", offset, value)

    def writeUIntAt(self, offset, value):
        self.writeAt("I", offset, value)

    def writeIntAt(self, offset, value):
        self.writeAt("i", offset, value)

    def writeFloat(self, value):
        self.write("f", value)

    def writeFloats(self, value):
        self.write_list("f", value)

    def writeHalf(self, value):
        self.write("e", value)

    def writeHalfs(self, value):
        self.write_list("e", value)

    def writeShort(self, value):
        self.write("h", value)

    def writeUShort(self, value):
        self.write("H", value)

    def writeUShorts(self, value):
        self.write_list("H", value)

    def writeUByte(self, value):
        if math.isnan(value):
            value = 0
        if value > 255:
            value = 255
        if value < 0:
            value = 0
        self.write("B", value)

    def writeUBytes(self, value):
        self.write_list("B", value)

    def writeByte(self, value):
        if math.isnan(value):
            value = 0
        if value > 127:
            value = 127
        if value < -128:
            value = -128
        self.write("b", value)

    def writeBytes(self, value):
        self.write_list("b", value)

    def writeString(self, value):
        for char in value:
            self.write("B", ord(char))
        self.write("B", 0)

    def writeStringUTF(self, value):
        for char in value:
            self.write("H", ord(char))
        self.write("H", 0)

    def padUntilAlligned(self, size):
        for pad_i in range((size - (len(self.data)%size))%size):
            self.writeUByte(0)

def murmurhash_32( key, seed = 0x0 ):
    def fmix( h ):
        h ^= h >> 16
        h  = ( h * 0x85ebca6b ) & 0xFFFFFFFF
        h ^= h >> 13
        h  = ( h * 0xc2b2ae35 ) & 0xFFFFFFFF
        h ^= h >> 16
        return h
    length = len( key )
    nblocks = int( length / 4 )
    h1 = seed
    c1 = 0xcc9e2d51
    c2 = 0x1b873593
    for block_start in range( 0, nblocks * 4, 4 ):
        k1 = key[ block_start + 3 ] << 24 | \
             key[ block_start + 2 ] << 16 | \
             key[ block_start + 1 ] <<  8 | \
             key[ block_start + 0 ]
        k1 = ( c1 * k1 ) & 0xFFFFFFFF
        k1 = ( k1 << 15 | k1 >> 17 ) & 0xFFFFFFFF
        k1 = ( c2 * k1 ) & 0xFFFFFFFF
        h1 ^= k1
        h1  = ( h1 << 13 | h1 >> 19 ) & 0xFFFFFFFF
        h1  = ( h1 * 5 + 0xe6546b64 ) & 0xFFFFFFFF
    tail_index = nblocks * 4
    k1 = 0
    tail_size = length & 3
    if tail_size >= 3:
        k1 ^= key[ tail_index + 2 ] << 16
    if tail_size >= 2:
        k1 ^= key[ tail_index + 1 ] << 8
    if tail_size >= 1:
        k1 ^= key[ tail_index + 0 ]
    if tail_size > 0:
        k1  = ( k1 * c1 ) & 0xFFFFFFFF
        k1  = ( k1 << 15 | k1 >> 17 ) & 0xFFFFFFFF
        k1  = ( k1 * c2 ) & 0xFFFFFFFF
        h1 ^= k1
    unsigned_val = fmix( h1 ^ length )
    return unsigned_val

def export_fbxskel(selected_objects):
    beware = False

    # Sanity checks
    # Bunch of janky filters to avoid crashing during the real export
    armatures = []

    for obj in selected_objects:
        try:
            if obj.type == "ARMATURE":
                armatures.append(obj)
            else:
                beware = True
                raise RuntimeError("Not a mesh or armature! ")
        except Exception as e:
            beware = True
            logger.warning("Skipped object " + obj.name + ", reason = " + str(e))
            continue

    if len(armatures) == 0:
        beware = True
        raise RuntimeError("No armature found in the selected objects. ")

    if len(armatures) > 1:
        beware = True
        raise RuntimeError("More than one armature in the selected objects. ")

    armature = armatures[0]
    armature_data = armature.data
    armature_matrix = armature.matrix_world

    bone_dict = {}
    for bone_i, bone in enumerate(armature_data.bones):
        bone_dict[bone.name] = bone_i

    bone_infos = []
    for bone_i, bone in enumerate(armature_data.bones):
        bone_info = {}

        rot4 = Matrix.Rotation(math.radians(-90.0), 4, 'X')
        scale_mat = Matrix.LocRotScale(None, None, armature_matrix.to_scale())

        if bone.parent is None:
            local_mat = rot4 @ (armature_matrix @ armature_data.bones[bone.name].matrix_local)
        else:
            local_mat = scale_mat @ (armature_data.bones[bone.parent.name].matrix_local.inverted() @ armature_data.bones[bone.name].matrix_local)

        loc, rot, scl = local_mat.decompose()
        bone_info["name"] = bone.name
        bone_info["parent"] = None if bone.parent is None else bone.parent.name
        bone_info["index"] = bone_i
        bone_info["id"] = bone["mhws_skel_id"]
        bone_info["parent_id"] = -1 if bone.parent is None else bone_dict[bone.parent.name]
        bone_info["loc"] = [x for x in loc]
        bone_info["rot"] = [rot[1], rot[2], rot[3], rot[0]]
        bone_info["scl"] = [x for x in scl]

        bone_infos.append(bone_info)

    return bone_infos, beware

def write_fbxskel(bone_infos):
    beware = False

    writer = Writer()
    writer.writeUInt(7)
    writer.writeUInt(1852599155)
    writer.writeUInt64(0)

    bone_offset = writer.tell()
    writer.writeUInt64(0) # bone_offset
    hash_offset = writer.tell()
    writer.writeUInt64(0) # hash_offset

    writer.writeUInt64(len(bone_infos))
    writer.writeUInt64(0)

    writer.writeUInt64At(bone_offset, writer.tell())

    for bone_info in bone_infos:
        bone_info["name_offset"] = writer.tell()
        writer.writeUInt64(0) # name_offset
        writer.writeUInt(murmurhash_32(bone_info["name"].encode("utf-16LE"), 0xFFFFFFFF))
        writer.writeShort(bone_info["parent_id"])
        writer.writeUShort(bone_info["id"])
        [writer.writeFloat(x) for x in bone_info["rot"]]
        [writer.writeFloat(x) for x in bone_info["loc"]]
        [writer.writeFloat(x) for x in bone_info["scl"]]
        writer.writeUInt64(0)

    writer.writeUInt64At(hash_offset, writer.tell())

    bone_hashes = [(murmurhash_32(bone_info["name"].encode("utf-16LE"), 0xFFFFFFFF), bone_info["index"]) for bone_info in bone_infos]
    bone_hashes.sort(key=lambda a: a[0])
    #print(bone_hashes)

    for bone_hash in bone_hashes:
        writer.writeUInt(bone_hash[0])
        writer.writeUInt(bone_hash[1])

    for bone_info in bone_infos:
        writer.writeUInt64At(bone_info["name_offset"], writer.tell())
        writer.writeStringUTF(bone_info["name"])

    return writer.data, beware
