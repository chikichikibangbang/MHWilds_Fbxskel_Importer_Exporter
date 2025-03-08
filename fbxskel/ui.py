import bpy
from bpy.types import Panel
from bpy_extras.io_utils import ImportHelper, ExportHelper
import addon_utils

import os
import json
import logging
logger = logging.getLogger("fbxskel_tools")

from .fbxskel_loader import load_fbxskel
from .fbxskel_writer import export_fbxskel, write_fbxskel

def SetLoggingLevel(level):
    if level == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif level == "INFO":
        logger.setLevel(logging.INFO)
    elif level == "WARNING":
        logger.setLevel(logging.WARNING)
    elif level == "ERROR":
        logger.setLevel(logging.ERROR)


class FBXSKEL_ImportFbxskel(bpy.types.Operator, ImportHelper):
    """Import from Wilds fbxskel file format (.fbxskel.7)"""
    bl_idname = "fbxskel_import.fbxskel"
    bl_label = 'Import WILDS Fbxskel'
    bl_options = {'UNDO'}

    filename_ext = ".fbxskel"
    
    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    filter_glob: bpy.props.StringProperty(default=".fbxskel;*.fbxskel.*")

    def execute(self, context):
        candidate_modules = [mod for mod in addon_utils.modules() if mod.bl_info["name"] == "MHWilds Fbxskel Importer Exporter"]
        if len(candidate_modules) > 1:
            logger.warning("Inconsistencies while loading the addon preferences: make sure you don't have multiple versions of the addon installed.")
        mod = candidate_modules[0]
        addon_prefs = context.preferences.addons[mod.__name__].preferences
        SetLoggingLevel(addon_prefs.logging_level)
        
        if self.files:
            folder = (os.path.dirname(self.filepath))
            filepaths = [os.path.join(folder, x.name) for x in self.files]
        else:
            filepaths = [str(self.filepath)]

        for filepath in filepaths:
            try:
                objs = load_fbxskel(filepath, collection=None, fix_rotation=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.warning("Unable to load fbxskel of path " + str(filepath) + ", reason = " + str(e))
                self.report({"WARNING"}, "Unable to load fbxskel of path " + str(filepath) + ", reason = " + str(e))
                continue
        return {"FINISHED"}

class FBXSKEL_ExportFbxskel(bpy.types.Operator, ExportHelper):
    """Export to WILDS fbxskel file format (.fbxskel.7)"""
    bl_idname = "wilds_export.wilds_fbxskel"
    bl_label = 'Export WILDS Fbxskel'
    filename_ext = ".7"
    # filter_glob: bpy.props.StringProperty(default="*.fbxskel", options={'HIDDEN'})

    def execute(self, context):
        selected_objects = context.selected_objects
        beware = False
        try:
            bone_infos, beware_export = export_fbxskel(selected_objects)
            data, beware_write = write_fbxskel(bone_infos)
            with open(self.filepath, "wb") as file_out:
                file_out.write(data)
            beware = beware_export or beware_write
        except Exception as e:
            self.report({"ERROR"}, "Could not export fbxskel, reason = " + str(e))
            import traceback
            traceback.print_exc()
            return {"CANCELLED"}
        if beware:
            logger.warning("Export to " + self.filepath + " done, but warning were generated: make sure everything went correctly by checking the system console, found in Window->Toggle System Console")
            self.report({"WARNING"}, "Export done, but warning were generated: make sure everything went correctly by checking the system console, found in Window->Toggle System Console")
        else:
            logger.info("Export to " + self.filepath + " done! ")
            self.report({"INFO"}, "Export done!")
        return {"FINISHED"}

        
