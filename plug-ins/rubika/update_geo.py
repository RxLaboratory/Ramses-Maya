# -*- coding: utf-8 -*-

from .utils_attributes import * # pylint: disable=import-error
from .import_geo import importGeo
from .utils_shaders import referenceShaders
import dumaf as maf
import ramses as ram # pylint: disable=import-error

def updateGeo( rootCtrl ):
    # Create a locator to keep current transform
    rootLocator = cmds.spaceLocator(name='_ramsesTempLocator_')
    # Snap!
    rootLocator = maf.snapNodeTo( rootLocator, rootCtrl )

    # We need to transfer the deformers and rendering sets to the new geo
    currentNodes = cmds.listRelatives(rootCtrl, ad = True, f=True)
    if currentNodes is None:
        return
    nodeSets = {}
    for node in currentNodes:
        sets = cmds.listSets(object=node, ets= True)
        if sets is not None:
            nodeName = maf.getNodeBaseName(node, True)
            nodeSets[nodeName] = sets

    # Re-Import
    itemShortName = getRamsesAttr( rootCtrl, RamsesAttribute.ITEM )
    assetGroup = getRamsesAttr( rootCtrl, RamsesAttribute.ASSET_GROUP )
    filePath = getRamsesAttr( rootCtrl, RamsesAttribute.GEO_FILE )
    step = getRamsesAttr( rootCtrl, RamsesAttribute.STEP )
    # Shading too
    shadingMode = getRamsesAttr( rootCtrl, RamsesAttribute.SHADING_TYPE )
    shadingFile = getRamsesAttr( rootCtrl, RamsesAttribute.SHADING_FILE )

    item = ram.RamAsset('', itemShortName, '', assetGroup)
    newRootCtrls = importGeo( item, filePath, step )

    rootCtrls = []

    for newRootCtrl in newRootCtrls:
        # Move to the locator
        newRootCtrl = maf.snapNodeTo( newRootCtrl, rootLocator )

        # Re-set deformers
        newNodes = cmds.listRelatives( newRootCtrl, ad = True, f = True)
        if newNodes is not None:
            for newNode in newNodes:
                newName = maf.getNodeBaseName(newNode, True)
                if newName in nodeSets:
                    cmds.sets( newNode, include=nodeSets[newName])
                
        # Re-parent the root to the previous parent
        rootParent = cmds.listRelatives( rootCtrl, parent=True, f=True, type='transform')
        if rootParent is not None:
            rootParent = rootParent[0]
        else:
            rootParent = '|'

        newRootCtrl = maf.parentNodeTo( newRootCtrl, rootParent )
        rootCtrls.append(newRootCtrl)

    # Re-set shader
    if shadingMode and shadingFile:
        referenceShaders( rootCtrls, shadingMode, shadingFile, itemShortName)

    # Delete
    cmds.delete( rootCtrl )
    cmds.delete( rootLocator )

