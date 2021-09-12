# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=import-error
from .utils_update import update
from .import_anim import importAnim

def updateAnim( node, filePath, item, step):

    # Re-import
    newRootCtrls = importAnim( item, filePath, step, showDialog=False )

    # Snap and re-apply sets
    newRootCtrls = update(node, newRootCtrls)

    # Delete the old hierarchy and the locator
    cmds.delete( node )

    return newRootCtrls
