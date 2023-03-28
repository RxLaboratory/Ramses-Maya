# -*- coding: utf-8 -*-
"""The entry point for opening items"""

from maya import cmds # pylint: disable=import-error

def opener( file_path, item, step ):
    """Opens a scene"""
    # Open
    cmds.file(file_path, open=True, force=True)
