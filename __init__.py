bl_info = {
    "name": "MHWilds Fbxskel Importer Exporter",
    "author": "Feuleur, 诸葛不太亮",
    "blender": (2, 93, 0),
    "version": (1, 0),
    "description": "Import and export MHWilds fbxskel file.",
    "warning": "",
    "doc_url": "https://github.com/chikichikibangbang/MHWilds_Fbxskel_Importer_Exporter",
    "tracker_url": "https://github.com/chikichikibangbang/MHWilds_Fbxskel_Importer_Exporter/issues",
    "category": "Import-Export",
}

import bpy
from bpy.types import Context, Menu, Panel, Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper

import os
import platform
import numpy as np
import logging
logger = logging.getLogger("fbxskel_tools")
logger.propagate = False
import sys

from .fbxskel.ui import FBXSKEL_ImportFbxskel
from .fbxskel.ui import FBXSKEL_ExportFbxskel

class ColoredFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ANSI Coloring
        grey = "\x1b[38;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        _reset = "\x1b[0m"
        self.FORMATS = {
            logging.DEBUG: f"{grey}{self._fmt}{_reset}",
            logging.INFO: f"{grey}{self._fmt}{_reset}",
            logging.WARNING: f"{yellow}{self._fmt}{_reset}",
            logging.ERROR: f"{red}{self._fmt}{_reset}",
            logging.CRITICAL: f"{bold_red}{self._fmt}{_reset}"
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s | %(message)s')
colored_formatter = formatter
is_windows = platform.system() == "Windows"
if not (is_windows and int(platform.release()) < 10):
    if is_windows:
        os.system("color")
    colored_formatter = ColoredFormatter('%(levelname)s | %(message)s')
handler.setFormatter(colored_formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class FBXSKEL_CustomAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    logging_level: bpy.props.EnumProperty(
        name="Logging level",
        items = [('DEBUG','DEBUG','','',0), 
                 ('INFO','INFO','','',1),
                 ('WARNING','WARNING','','',2),
                 ('ERROR','ERROR','','',3)],
        default = 'INFO'
    )
    
    def draw(self, context):
        layout = self.layout
        
        layout.prop(self, "logging_level")


class FBXSKEL_export_menu(bpy.types.Menu):
    bl_label = "MH Wilds tools"
    bl_idname = "FBXSKEL_MT_menu_export"

    def draw(self, context):
        self.layout.operator(FBXSKEL_ExportFbxskel.bl_idname, text="WILDS skeleton files (.fbxskel.7)", icon="ARMATURE_DATA")

def FBXSKEL_menu_func_export(self, context):
    self.layout.menu(FBXSKEL_export_menu.bl_idname)

class FBXSKEL_import_menu(bpy.types.Menu):
    bl_label = "MH Wilds tools"
    bl_idname = "FBXSKEL_MT_menu_import"

    def draw(self, context):
        self.layout.operator(FBXSKEL_ImportFbxskel.bl_idname, text="WILDS skeleton files (.fbxskel.7)", icon="ARMATURE_DATA")

def FBXSKEL_menu_func_import(self, context):
    self.layout.menu(FBXSKEL_import_menu.bl_idname)

def register():
    bpy.utils.register_class(FBXSKEL_ImportFbxskel)
    bpy.utils.register_class(FBXSKEL_CustomAddonPreferences)
    bpy.utils.register_class(FBXSKEL_import_menu)
    bpy.types.TOPBAR_MT_file_import.append(FBXSKEL_menu_func_import)
    bpy.utils.register_class(FBXSKEL_ExportFbxskel)
    bpy.utils.register_class(FBXSKEL_export_menu)
    bpy.types.TOPBAR_MT_file_export.append(FBXSKEL_menu_func_export)
    pass

def unregister():
    bpy.utils.unregister_class(FBXSKEL_ImportFbxskel)
    bpy.utils.unregister_class(FBXSKEL_CustomAddonPreferences)
    bpy.utils.unregister_class(FBXSKEL_import_menu)
    bpy.types.TOPBAR_MT_file_import.remove(FBXSKEL_menu_func_import)
    bpy.utils.unregister_class(FBXSKEL_ExportFbxskel)
    bpy.utils.unregister_class(FBXSKEL_export_menu)
    bpy.types.TOPBAR_MT_file_export.remove(FBXSKEL_menu_func_export)
    pass

