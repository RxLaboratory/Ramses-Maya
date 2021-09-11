# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error


class RamsesAttribute():
    MANAGED = 'ramsesManaged'
    STEP = 'ramsesStep'
    ITEM = 'ramsesItem'
    ASSET_GROUP = 'ramsesAssetGroup'
    ITEM_TYPE = 'ramsesItemType'
    GEO_FILE = 'ramsesGeoFilePath'
    GEO_TIME = 'ramsesGeoTimeStamp'
    SHADING_TYPE = 'ramsesShadingType'
    SHADING_FILE = 'ramsesShadingFilePath'
    SHADING_TIME = 'ramsesShadingTimeStamp'
    SHADED_OBJECTS = 'ramsesShadedObjects'
    SOURCE_FILE = 'ramsesSourceFile'
    SOURCE_TIME = 'ramsesTimeStamp'
    RIG_FILE = 'ramsesRigFilePath'
    RIG_TIME = 'ramsesRigTimeStamp'
    DT_TYPES = ('string')
    AT_TYPES = ('long', 'bool')
    IS_PROXY = 'ramsesIsProxy'
    VERSION = 'ramsesVersion'
    STATE = 'ramsesState'
    ORIGIN_POS = 'ramsesOriginalPos'
    ORIGIN_ROT = 'ramsesOriginalRot'
    ORIGIN_SCA = 'ramsesOriginalSca'

def setRamsesAttr( node, attr, value, t):
    # Add if not already there
    if attr not in cmds.listAttr(node):
        if t in RamsesAttribute.DT_TYPES:
            cmds.addAttr( node, ln= attr, dt=t)
        else:
            cmds.addAttr( node, ln=attr, at=t)
    # Unlock
    cmds.setAttr( node + '.' + attr, lock=False )
    # Set
    if t in RamsesAttribute.DT_TYPES:
        cmds.setAttr( node + '.' + attr, value, type=t)
    else:
        cmds.setAttr( node + '.' + attr, value )    
    # Lock
    cmds.setAttr( node + '.' + attr, lock=True )

def getRamsesAttr( node, attr):
    if attr not in cmds.listAttr(node):
        return None
    return cmds.getAttr(node + '.' + attr)

def setRamsesManaged(node, managed=True):
    setRamsesAttr( node, RamsesAttribute.MANAGED, True, 'bool' )

def isRamsesManaged(node):
    return getRamsesAttr( node, RamsesAttribute.MANAGED )

def listRamsesNodes():
    # Scan all transform nodes
    transformNodes = cmds.ls(type='transform', long=True)
    nodes = []

    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Scanning Scene for Ramses Nodes")
    progressDialog.setMaximum(len(nodes))

    for node in transformNodes:
        progressDialog.increment()
        if isRamsesManaged(node):
            nodes.append(node)

    progressDialog.hide()
    return nodes
