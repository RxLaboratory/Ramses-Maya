# -*- coding: utf-8 -*-
"""The entry point for saving items"""

from maya import cmds # pylint: disable=import-error

import os
import dumaf
from ramses import RamItem

from .ui_scene_setup import SceneSetupDialog # pylint: disable=import-error,no-name-in-module

def setup_scene_save_handler( filePath, item, step=None, version=1, comment='', incremented=False): # pylint: disable=unused-argument
    """Setup scene before saving"""
    return setup_scene(item, step)

def setup_scene_template_handler( filePath, item, step, templateName=''): # pylint: disable=unused-argument
    """Setup scene before saving template"""
    return setup_scene(item, step)

def setup_scene_save_as_handler( filePath, item, step, resource ): # pylint: disable=unused-argument
    """Setup scene before saving as new scene"""
    return setup_scene(item, step)

def setup_scene(item, step=None): # pylint: disable=unused-argument
    """Setup the current scene according to the given item.
    Returns False if the user cancelled the operation."""

    dumaf.sets.create_if_not_exists("Ramses_Publish")
    dumaf.sets.create_if_not_exists("Ramses_DelOnPublish")

    if not item:
        return True

    dlg = SceneSetupDialog( dumaf.ui.getMayaWindow() )
    ok = dlg.setItem( item, step )
    if not ok:
        if not dlg.exec_():
            return False

    return True

def saver(filePath, item, step, version, comment, incremented): # pylint: disable=unused-argument
    """Saves the scene"""

    # Set the save name and save
    cmds.file( rename = filePath )
    cmds.file( save=True, options="v=1;" )

    if incremented:
        cmds.warning( "Incremented and Saved as " + filePath )

    cmds.inViewMessage( msg='Scene saved! <hl>v' + str(version) + '</hl>', pos='midCenter', fade=True )

    return True

def saveAs( filePath, item, step, resource ):
    """Saves as new scene"""
    cmds.file(rename = filePath )
    cmds.file( save=True, options="v=1;", f=True)
    cmds.inViewMessage( msg='Scene saved as: <hl>' + os.path.basename(filePath) + '</hl>.', pos='midCenter', fade=True )

def templateSaver( filePath, item, step, templateName ): # pylint: disable=unused-argument
    """Saves the template"""

    # save as
    cmds.file( rename = filePath )
    cmds.file( save=True, options="v=1;" )
    # Message
    cmds.inViewMessage( msg='Template saved as: <hl>' + os.path.basename(filePath) + '</hl> in ' + os.path.dirname(filePath) , pos='midCenter', fade=True )
