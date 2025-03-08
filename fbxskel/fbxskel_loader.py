import bpy
from mathutils import Euler, Matrix, Vector, Quaternion

import os
import math
import logging
import numpy as np
logger = logging.getLogger("wilds_suite")

from .fbxskel_parser import FbxskelParser

def load_fbxskel(filepath, collection = None, fix_rotation=False, obj_name="", connect_bones=False):
    parser = FbxskelParser(path=filepath)
    fbxskel_data = parser.read()

    file_name = os.path.basename(filepath)
    file_sname = file_name.split(".")
    if len(file_sname) == 3 and file_sname[1] == "fbxskel" and file_sname[2] == "7":
        file_name = file_sname[0]

    if collection is None:
        master_collection = bpy.context.scene.collection
        col = bpy.data.collections.new(file_name + ".fbxskel")
        master_collection.children.link(col)
    else:
        col = collection

    if obj_name != "":
        armature_name = obj_name + " Armature" 
    else:
        armature_name = file_name + " Armature"

    armature_data = bpy.data.armatures.new(armature_name)
    armature_object = bpy.data.objects.new(armature_name, armature_data)
    armature_object.show_in_front = True
    armature_object.rotation_mode = "XYZ"
    if fix_rotation:
        armature_object.rotation_euler.rotate(Euler([math.radians(90),0,0]))

    col.objects.link(armature_object)
    bpy.context.view_layer.objects.active = armature_object
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    for bone_info in fbxskel_data:
        new_bone = armature_data.edit_bones.new(bone_info["name"])
        new_bone.head = (0.0, 0.0, 0.0)
        new_bone.tail = (0.0, 0.1, 0.0)
        bone_loc = Vector([bone_info["loc"][0], bone_info["loc"][1], bone_info["loc"][2]])
        bone_rot = Quaternion([bone_info["rot_quat"][3], bone_info["rot_quat"][0], bone_info["rot_quat"][1], bone_info["rot_quat"][2]])
        bone_scl = Vector([bone_info["scl"][0], bone_info["scl"][1], bone_info["scl"][2]])
        matrix = Matrix.LocRotScale(
            bone_loc,
            bone_rot,
            bone_scl
        )
        new_tfr = new_bone.matrix @ matrix

        if bone_info["parent"] != -1:
            new_bone.parent = armature_data.edit_bones[bone_info["parent"]]
            new_bone.matrix = new_bone.parent.matrix @ new_tfr
        else:
            new_bone.matrix = new_tfr
        new_bone["mhws_skel_id"] = bone_info["id"]   
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    armature_object.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    armature_object.select_set(False)

    return [armature_object]
