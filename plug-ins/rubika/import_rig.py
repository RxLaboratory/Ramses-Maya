# -*- coding: utf-8 -*-

import re, os
import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_attributes import * # pylint: disable=import-error

def importRig( item, rigFile, step):

    step = ram.RamObject.getObjectShortName(step)

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Importing Rig")
    progressDialog.setMaximum(2)

    # Get info
    itemShortName = item.shortName()
    itemType = ram.ItemType.ASSET
    assetGroupName = item.group()
    # Get the file timestamp
    timestamp = os.path.getmtime( rigFile )
    timestamp = int(timestamp)
    # Get version and state
    version = ram.RamMetaDataManager.getVersion( rigFile )
    if version is None: version = -1
    state = ram.RamMetaDataManager.getState( rigFile )
    if state is None: state = ''

    # Get the Asset Group
    assetGroup = 'RamASSETS_' + assetGroupName
    assetGroup = maf.Node.getCreateGroup( assetGroup )

    # Check if the short name is not made only of numbers
    regex = re.compile('^\\d+$')
    if re.match(regex, itemShortName):
        itemShortName = itemType + itemShortName

    # Get the Item Group
    itemGroup = maf.Node.getCreateGroup( itemShortName, assetGroup )

    # Generate the namespace
    rigNameSpace = itemShortName + '_Rig_001'
    i = 1
    while cmds.namespace( exists=rigNameSpace ):
        i = i+1
        it = str(i)
        while len(it) < 3:
            it = '0' + it
        rigNameSpace = itemShortName + '_Rig_' + it

    # Import the file
    progressDialog.setText("Importing file...")
    progressDialog.increment()
    # Import as reference
    newNodes = cmds.file(rigFile,r=True,ignoreVersion=True,mergeNamespacesOnClash=False,returnNewNodes=True,ns=rigNameSpace)

    progressDialog.setText("Tidying...")
    progressDialog.increment()
    progressDialog.setMaximum( len(newNodes) + 2 )

    # Get the root nodes and tidy
    rootNodes = []
    for node in newNodes:
        progressDialog.increment()
        # When parenting the root, children won't exist anymore
        if not cmds.objExists(node):
            continue
        # only the root
        if maf.Node.hasParent(node):
            continue
        if not cmds.nodeType(node) == 'transform':
            continue

        # group the root
        rootGroup = cmds.group( node, name = itemShortName + '_Rig' )

        # set the color and the attr on the group (it acts as the root)
        cmds.setAttr(rootGroup+'.useOutlinerColor',1)
        cmds.setAttr(rootGroup+'.outlinerColor',168/255.0,138/255.0,244/255.0)
        # Store Ramses Data!
        setRamsesManaged( rootGroup )
        setRamsesAttr( rootGroup, RamsesAttribute.RIG_FILE, rigFile, 'string' )
        setRamsesAttr( rootGroup, RamsesAttribute.RIG_TIME, timestamp, 'long' )
        setRamsesAttr( rootGroup, RamsesAttribute.STEP, step, 'string' )
        setRamsesAttr( rootGroup, RamsesAttribute.ITEM, item.shortName(), 'string' )
        setRamsesAttr( rootGroup, RamsesAttribute.ITEM_TYPE, itemType, 'string' )
        setRamsesAttr( rootGroup, RamsesAttribute.ASSET_GROUP, item.group(), 'string' )
        setRamsesAttr( rootGroup, RamsesAttribute.VERSION, version, 'long' )
        setRamsesAttr( rootGroup, RamsesAttribute.STATE, state, 'string' )

        # lock transform of the root group
        maf.Node.lockTransform( rootGroup )

        # move it to its category
        rootGroup = maf.Node.parent(rootGroup, itemGroup)
        rootNodes.append(rootGroup) 

    progressDialog.hide()
    return rootNodes