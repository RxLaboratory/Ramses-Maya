# -*- coding: utf-8 -*-
"""The entry point for saving items"""

from maya import cmds # pylint: disable=import-error

import dumaf

from .ui_scene_setup import SceneSetupDialog # pylint: disable=import-error,no-name-in-module

def setup_scene(item, filePath='', step=None, version=1, comment='', incremented=False): # pylint: disable=unused-argument
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


def saver(item, filePath, step, version, comment, incremented): # pylint: disable=unused-argument
    """Saves the scene"""

    # Set the save name and save
    cmds.file( rename = filePath )
    cmds.file( save=True, options="v=1;" )

    if incremented:
        cmds.warning( "Incremented and Saved as " + filePath )

    cmds.inViewMessage( msg='Scene saved! <hl>v' + str(version) + '</hl>', pos='midCenter', fade=True )

    return True
