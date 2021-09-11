# -*- coding: utf-8 -*-

import os
import maya.cmds as cmds # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
import ramses as ram

class RamsesAttribute():
    MANAGED = 'ramsesManaged'
    STEP = 'ramsesStep'
    ITEM = 'ramsesItem'
    ASSET_GROUP = 'ramsesAssetGroup'
    ITEM_TYPE = 'ramsesItemType'
    SOURCE_FILE = 'ramsesSourceFile'
    SOURCE_TIME = 'ramsesTimeStamp'
    SHADING_TYPE = 'ramsesShadingType'
    SHADED_OBJECTS = 'ramsesShadedObjects'
    DT_TYPES = ('string','float2','float3')
    AT_TYPES = ('long', 'bool')
    IS_PROXY = 'ramsesIsProxy'
    VERSION = 'ramsesVersion'
    STATE = 'ramsesState'
    ORIGIN_POS = 'ramsesOriginalPos'
    ORIGIN_ROT = 'ramsesOriginalRot'
    ORIGIN_SCA = 'ramsesOriginalSca'
    RESOURCE = 'ramsesResource'

def setImportAttributes( node, item, step, filePath ):
    timestamp = os.path.getmtime( filePath )
    timestamp = int(timestamp)
    
    version = ram.RamMetaDataManager.getVersion( filePath )
    state = ram.RamMetaDataManager.getState( filePath )
    resource = ram.RamMetaDataManager.getResource(filePath)

    setRamsesManaged( node )
    setRamsesAttr( node, RamsesAttribute.SOURCE_FILE, filePath, 'string' )
    setRamsesAttr( node, RamsesAttribute.SOURCE_TIME, timestamp, 'long' )
    setRamsesAttr( node, RamsesAttribute.VERSION, version, 'long' )
    setRamsesAttr( node, RamsesAttribute.STATE, state, 'string' )
    setRamsesAttr( node, RamsesAttribute.STEP, step, 'string' )
    setRamsesAttr( node, RamsesAttribute.ITEM, item.shortName(), 'string' )
    setRamsesAttr( node, RamsesAttribute.ITEM_TYPE, item.itemType(), 'string' )
    setRamsesAttr( node, RamsesAttribute.ASSET_GROUP, item.group(), 'string' )
    setRamsesAttr( node, RamsesAttribute.RESOURCE, resource, 'string' )

def setRamsesAttr3( node, attr, x, y, z, t):
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
        cmds.setAttr( node + '.' + attr, x, y, z, type=t)
    else:
        cmds.setAttr( node + '.' + attr, x, y, z )
    # Lock
    cmds.setAttr( node + '.' + attr, lock=True )

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

def listRamsesNodes(t='transform'):
    # Scan all transform nodes
    sceneNodes = ()
    if t == '': sceneNodes = cmds.ls( long=True )
    else: sceneNodes = cmds.ls( type=t, long=True )

    nodes = []

    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Scanning Scene for Ramses Nodes")
    progressDialog.setMaximum(len(sceneNodes))

    for node in sceneNodes:
        progressDialog.increment()
        if isRamsesManaged(node):
            nodes.append(node)

    progressDialog.hide()
    return nodes
