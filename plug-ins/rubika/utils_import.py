# -*- coding: utf-8 -*-

import re
import maya.cmds as cmds # pylint: disable=import-error
import dumaf as maf
import ramses as ram
from .utils_attributes import * # pylint: disable=import-error

def getImportGroup( item ):
    # Get info
    itemShortName = item.shortName()
    itemName = item.name()
    itemType = item.itemType()
    itemGroupName = item.group()

    # Get the Asset Group
    itemsGroup = ''
    if itemType == ram.ItemType.ASSET:
        itemsGroup = 'RamASSETS_' + itemGroupName
    elif itemType == ram.ItemType.SHOT:
        itemsGroup = 'RamSHOTS'
    else:
        itemsGroup = 'RamITEMS'

    itemsGroup = maf.Node.getCreateGroup( itemsGroup )

    # Check if the short name is not made only of numbers
    regex = re.compile('^\\d+$')
    if re.match(regex, itemShortName):
        itemShortName = itemType + itemShortName

    # Get the Item Group
    return maf.Node.getCreateGroup( itemShortName + ':' + itemName, itemsGroup )

def importCmd( filePath, namespace ):
    return cmds.file (
        filePath,
        i=True,
        ignoreVersion=True,
        mergeNamespacesOnClash=True,
        returnNewNodes=True,
        ns=namespace,
        preserveReferences=True
        )

def referenceCmd( filePath, namespace ):
    return cmds.file(
        filePath,
        r=True,
        ignoreVersion=True,
        mergeNamespacesOnClash=False,
        returnNewNodes=True,
        ns=namespace
        )  

def importFile(item, filePath, step, progressDialog=maf.ProgressDialog(), reference=False, lockTransform=True ):

    progressDialog.show()

    if reference: lockTransform = False

    itemGroup = getImportGroup( item )

    # Check the extension
    ext = filePath.split('.')[-1]
    # Load alembic
    if ext == 'abc':
        # We may need to use alembic
        if maf.Plugin.load("AbcImport"):
            ram.log("I have loaded the Alembic Export plugin, needed for the current task.")

    # Get/Generate the namespace
    itemShortName = item.shortName()
    itemType = item.itemType()
    # Check if the short name is not made only of numbers
    regex = re.compile('^\\d+$')
    if re.match(regex, itemShortName):
        itemShortName = itemType + itemShortName
    # And the namespace + its number
    importNamespace = itemShortName + '_001'
    i = 1
    while cmds.namespace( exists=importNamespace ):
        i = i+1
        it = str(i)
        while len(it) < 3:
            it = '0' + it
        importNamespace = itemShortName + '_'  + it

    if reference:
        newNodes = referenceCmd( filePath, item.shortName())
    else:
        newNodes = importCmd( filePath, item.shortName())

    progressDialog.setText("Tidying...")
    progressDialog.increment()
    progressDialog.setMaximum( len(newNodes) + 2 )

    # Get the controller, and parent nodes to the group
    rootNodes = []
    for node in reversed(newNodes):
        progressDialog.increment()
        # When parenting the roots, children won't exist anymore
        if not cmds.objExists(node):
            continue
        # If it's not a root, and this is referenced, it can't be ramses managed (unless the reference is imported)
        if isRamsesManaged( node ) and reference:
            setRamsesManaged( node, False )
        # only the root
        if maf.Node.hasParent(node):
            continue
        if not cmds.nodeType(node) == 'transform':
            continue

        # Parent to the item group
        rootCtrl = maf.Node.parent(node, itemGroup)

        if '_root' in node:
            # Get the shape
            nodeShapes = cmds.listRelatives(rootCtrl, shapes=True, f=True, type='nurbsCurve')
            if nodeShapes is None:
                continue
            rootCtrlShape = nodeShapes[0]
            # Adjust root appearance
            cmds.setAttr(rootCtrlShape+'.overrideEnabled', 1)
            cmds.setAttr(rootCtrlShape+'.overrideColor', 18)

        # Adjust root object
        cmds.setAttr(rootCtrl+'.useOutlinerColor',1)
        color = step.color()
        cmds.setAttr( rootCtrl+'.outlinerColor', color[0], color[1], color[2] )

        # Store Ramses Data!
        setImportAttributes( rootCtrl, item, step, filePath )

        # Lock transform except ramses managed children
        if lockTransform:
            children = cmds.listRelatives(rootCtrl, ad=True, f=True, type='transform')
            if children:
                for child in children:
                    if not isRamsesManaged(child):
                        maf.Node.lockTransform(child)

        rootNodes.append( rootCtrl )

    return rootNodes