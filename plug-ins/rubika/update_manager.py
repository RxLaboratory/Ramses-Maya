# -*- coding: utf-8 -*-

from .ui_update import UpdateDialog
from .utils_attributes import * # pylint: disable=import-error
import dumaf as maf

from .update_geo import updateGeo

def updateRamsesItems():

    # We need to check if the scene has been correctly saved first
    # The current maya file
    currentFilePath = cmds.file( q=True, sn=True )
    saveFilePath = ram.RamFileManager.getSaveFilePath( currentFilePath )
    if saveFilePath == '': # Ramses may return None if the current file name does not respeect the Ramses Naming Scheme
        cmds.warning( ram.Log.MalformedName )
        cmds.inViewMessage( msg='Malformed Ramses file name! <hl>Please save with a correct name first</hl>.', pos='topCenter', fade=True )
        if not cmds.ramSaveAs():
            return ''
        newFilePath = cmds.file( q=True, sn=True )
        saveFilePath = ram.RamFileManager.getSaveFilePath( newFilePath )
    if saveFilePath == '': return

    updateDialog = UpdateDialog(maf.UI.getMayaWindow())
    result = updateDialog.exec_() 
    if result == 0:
        return
    nodes = []
    if result == 1:
        nodes = updateDialog.getAllNodes()
    else:
        nodes = updateDialog.getSelectedNodes()

    for node in nodes:
        geoFile = getRamsesAttr(node, RamsesAttribute.SOURCE_FILE)
        if geoFile:
            updateGeo( node )
