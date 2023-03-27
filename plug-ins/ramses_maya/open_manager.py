# -*- coding: utf-8 -*-
"""The entry point for opening items"""

from maya import cmds # pylint: disable=import-error

def opener( item, file_path, step ):
    """Opens a scene"""
    # Open
    cmds.file(file_path, open=True, force=True)
