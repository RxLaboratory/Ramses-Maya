# -*- coding: utf-8 -*-

import re, os
import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_attributes import * # pylint: disable=import-error

def importStandard( item, filePath, step):
    step = ram.RamObject.getObjectShortName(step)

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Importing scene...")
    progressDialog.setMaximum(2)
    progressDialog.increment()

    # Get info
    itemShortName = item.shortName()
    itemType = item.itemType()
    # Get the file timestamp
    timestamp = os.path.getmtime( filePath )
    timestamp = int(timestamp)
    # Get version and state
    version = ram.RamMetaDataManager.getVersion( filePath )
    if version is None: version = -1
    state = ram.RamMetaDataManager.getState( filePath )
    if state is None: state = ''

    # Check if the short name is not made only of numbers
    regex = re.compile('^\\d+$')
    if re.match(regex, itemShortName):
        itemShortName = itemType + itemShortName

    # Import the file
    progressDialog.setText("Importing file...")
    progressDialog.increment()
    newNodes = cmds.file(filePath,
        i=True,
        ignoreVersion=True
        ,mergeNamespacesOnClash=True,
        returnNewNodes=True,
        ns=itemShortName,
        preserveReferences=True)

    # Get the root nodes

    progressDialog.setText("Tidying...")
    progressDialog.increment()
    progressDialog.setMaximum( len(newNodes) + 2 )

    rootCtrls = []

    for node in newNodes:
        progressDialog.increment()
        # When parenting the root, children won't exist anymore
        if not cmds.objExists(node):
            continue
        # only the root
        if maf.nodes.hasParent(node):
            continue
        if not cmds.nodeType(node) == 'transform':
            continue

        # Adjust root object
        cmds.setAttr(node+'.useOutlinerColor',1)
        cmds.setAttr(node+'.outlinerColor',165/255.0,38/255.0,255.0)

        # Store Ramses Data!
        if not cmds.referenceQuery( node, isNodeReferenced=True):
            setRamsesManaged( node )
            setRamsesAttr( node, RamsesAttribute.SOURCE_FILE, filePath, 'string' )
            setRamsesAttr( node, RamsesAttribute.SOURCE_TIME, timestamp, 'long' )
            setRamsesAttr( node, RamsesAttribute.STEP, step, 'string' )
            setRamsesAttr( node, RamsesAttribute.ITEM, item.shortName(), 'string' )
            setRamsesAttr( node, RamsesAttribute.ITEM_TYPE, itemType, 'string' )
            setRamsesAttr( node, RamsesAttribute.VERSION, version, 'long' )
            setRamsesAttr( node, RamsesAttribute.STATE, state, 'string' )

        rootCtrls.append( node )

    progressDialog.hide()
    return rootCtrls