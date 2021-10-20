# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=import-error
import dumaf as maf
from .utils_attributes import isRamsesManaged

def update( node, newNodes ):
    # Get a locator for the current node
    rootLocator = createUpdateLocator( node )

    # Keep current deformer and rendering sets
    nodeSets = getNodeSets( node )

    # Get ramses locators
    nodeLocators = getNodeLocators( node )

    newRootCtrls = updateNodes( node, newNodes, rootLocator, nodeSets, nodeLocators )

    cmds.delete(rootLocator)
    for loc in nodeLocators:
        cmds.delete(loc)

    return newRootCtrls

def createUpdateLocator( node ):

    # Create a locator to keep current transform
    rootLocator = cmds.spaceLocator(name='_ramsesTempLocator_')
    # Snap!
    rootLocator = maf.Node.snap( rootLocator, node )

    return rootLocator

def getNodeSets( rootNode ):

    # We need to transfer the deformers and rendering sets to the new geo
    currentNodes = cmds.listRelatives(rootNode, ad = True, f=True)
    if currentNodes is None:
        return {}
    nodeSets = {}
    for node in currentNodes:
        sets = cmds.listSets(object=node, ets= True)
        if sets is not None:
            nodeName = maf.Path.baseName(node, True)
            nodeSets[nodeName] = sets

    return nodeSets

def getNodeLocators( rootNode ):
    currentNodes = cmds.listRelatives(rootNode, ad = True, f=True)
    if currentNodes is None:
        return []
    locators = []
    for node in currentNodes:
        if isRamsesManaged( node ):
            nodeName = maf.Path.baseName(node, True)
            loc = cmds.spaceLocator(name=nodeName + '_ramsesTempLocator_')
            loc = maf.Node.snap( loc, node )
            locators.append(loc)
    return locators

def updateNodes( oldNode, newNodes, rootLocator, nodeSets, nodeLocators ):
    rootCtrls = []
    for newNode in newNodes:

        # Move to the locator
        newRootCtrl = maf.Node.snap( newNode, rootLocator )

        # Re-set deformers and rendering sets
        children = cmds.listRelatives( newRootCtrl, ad = True, f = True)
        if children is not None:
            children.append(newRootCtrl)
            for child in children:
                newName = maf.Path.baseName(child, True)
                # Reset deformers and shaders
                if newName in nodeSets:
                    newSets = nodeSets[newName]
                    for newSet in newSets:
                        try:
                            cmds.sets( child, add=newSet )
                        except: # Shaders have to be forced as an object can't be in two shader sets at once
                            try: # There may still be special sets
                                cmds.sets( child, forceElement=newSet )
                            except:
                                pass
                # Snap to locator
                if isRamsesManaged( child ):
                    for loc in nodeLocators:
                        locName = maf.Path.baseName(loc, True)
                        locName = locName.split('_ramsesTempLocator_')[0]
                        if locName == newName:
                            maf.Node.snap( child, loc )

        # Re-parent the root to the previous parent
        rootParent = cmds.listRelatives( oldNode, parent=True, f=True, type='transform')
        if rootParent is not None:
            rootParent = rootParent[0]
        else:
            rootParent = '|'
        newRootCtrl = maf.Node.parent( newRootCtrl, rootParent )

        rootCtrls.append(newRootCtrl)

    return rootCtrls