# -*- coding: utf-8 -*-
"""The entry point for opening items"""

from maya import cmds # pylint: disable=import-error
from .utils_files import add_to_recent_files

def opener( item, file_path, step ):
    """Opens a scene"""
    # Open
    cmds.file(file_path, open=True, force=True)
    add_to_recent_files( file_path )
