# -*- coding: utf-8 -*-

from .ui_update import UpdateDialog
from .utils_attributes import * # pylint: disable=import-error
import dumaf as maf
from .utils_constants import *
from .update_standard import updateStandard
from .update_set import updateSet
from .update_geo import updateGeo
from .update_anim import updateAnim
from .utils_attributes import *

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

    progressDialog = maf.ProgressDialog()
    progressDialog.setText("Updating items...")
    progressDialog.setMaximum(len(nodes))
    progressDialog.show()

    print(nodes)

    for n in nodes:

        node = n[0]
        updateFile = n[1]

        progressDialog.setText("Updating: " + maf.Path.baseName(node) )
        progressDialog.increment()

        # Let's update!

        # A node may have been updated twice
        if not cmds.objExists( node ): continue

        # Check if this is a reference, in which case, just replace it
        if cmds.referenceQuery(node, isNodeReferenced=True):
            # Get the reference node
            rNode = cmds.referenceQuery( node, referenceNode=True)
            # Reload new file
            cmds.file( updateFile, loadReference=rNode )
            continue

        # Get the item and step
        ramItem = getItem( node )
        ramStep = getStep( node )

        # Check the pipe and update
        if GEO_PIPE_FILE.check( updateFile ):
            updateGeo( node, updateFile, ramItem, ramStep )
            continue
        if PROXYGEO_PIPE_FILE.check(updateFile):
            updateGeo( node, updateFile, ramItem, ramStep )
            continue
        if ANIM_PIPE_FILE.check( updateFile ):
            updateAnim( node, updateFile, ramItem, ramStep )
            continue
        if SET_PIPE_FILE.check( updateFile ):
            updateSet( node, updateFile, ramItem, ramStep )
            continue
        
        updateStandard( node, updateFile, ramItem, ramStep )

    progressDialog.close()
