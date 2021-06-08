from .ui_update import UpdateDialog
from .utils_attributes import * # pylint: disable=import-error
from .import_geo import importGeo
import dumaf as maf
import ramses as ram # pylint: disable=import-error

def updateMod( rootCtrl ):
    # Create a locator to keep current transform
    rootLocator = cmds.spaceLocator(name='_ramsesTempLocator_')
    # Snap!
    rootLocator = maf.snapNodeTo( rootLocator, rootCtrl )

    # We need to transfer the deformers to the new geo
    currentNodes = cmds.listRelatives(rootCtrl, ad = True, f=True)
    if currentNodes is None:
        return
    deformerSets = {}
    for node in currentNodes:
        sets = cmds.listSets(object=node, ets= True, type=2) # Type 2 is for deformers, 1 is for rendering sets
        if sets is not None:
            nodeName = node.split('|')[-1]
            deformerSets[nodeName] = sets

    # Re-Import
    itemShortName = getRamsesAttr( rootCtrl, RamsesAttribute.ITEM )
    assetGroup = getRamsesAttr( rootCtrl, RamsesAttribute.ASSET_GROUP )
    filePath = getRamsesAttr( rootCtrl, RamsesAttribute.GEO_FILE )
    item = ram.RamAsset('', itemShortName, '', assetGroup)
    newRootCtrl = importGeo( item, filePath, 'MOD')

    # Move to the locator
    newRootCtrl = maf.snapNodeTo( newRootCtrl, rootLocator )

    # Re-set deformers
    newNodes = cmds.listRelatives( newRootCtrl, ad = True, f = True)
    if newNodes is not None:
        for newNode in newNodes:
            newName = newNode.split('|')[-1]
            if newName in deformerSets:
                cmds.sets( newNode, include=deformerSets[newName])

    # Delete
    cmds.delete( rootCtrl )
    cmds.delete( rootLocator )

def updateRamsesItems():
    updateDialog = UpdateDialog(maf.getMayaWindow())
    result = updateDialog.exec_() 
    if result == 0:
        return
    nodes = []
    if result == 1:
        nodes = updateDialog.getAllNodes()
    else:
        nodes = updateDialog.getSelectedNodes()

    for node in nodes:
        step = getRamsesAttr(node, RamsesAttribute.STEP)
        if step == 'MOD':
            updateMod( node )
