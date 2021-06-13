import re, os
import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_attributes import * # pylint: disable=import-error

def importGeo(item, filePath, step):

    # Checks
    step = ram.RamObject.getObjectShortName(step)

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Importing Geometry")
    progressDialog.setMaximum(2)

    # Get info
    itemShortName = item.shortName()
    itemType = item.itemType()
    itemGroupName = item.group()
    # Get the file timestamp
    timestamp = os.path.getmtime( filePath )
    timestamp = int(timestamp)

    # Get the Asset Group
    itemsGroup = ''
    if itemType == ram.ItemType.ASSET:
        itemsGroup = 'RamASSETS_' + itemGroupName
    elif itemType == ram.ItemType.SHOT:
        itemsGroup = 'RamSHOTS'
    else:
        itemsGroup = 'RamITEMS'

    itemsGroup = maf.getCreateGroup( itemsGroup )

    # Check if the short name is not made only of numbers
    regex = re.compile('^\\d+$')
    if re.match(regex, itemShortName):
        itemShortName = itemType + itemShortName

    # Get the Item Group
    itemGroup = maf.getCreateGroup( itemShortName + ':' + itemShortName, itemsGroup )

    # We may need to use alembic
    if maf.safeLoadPlugin("AbcImport"):
        ram.log("I have loaded the Alembic Export plugin, needed for the current task.")

    # Import the file
    progressDialog.setText("Importing file...")
    progressDialog.increment()
    newNodes = cmds.file(filePath,i=True,ignoreVersion=True,mergeNamespacesOnClash=True,returnNewNodes=True,ns=itemShortName)

    # Get the controler, and parent nodes to the group
    progressDialog.setText("Tidying...")
    progressDialog.increment()
    progressDialog.setMaximum( len(newNodes) + 2 )
    rootCtrls = []
    rootCtrlShape = ''
    for node in newNodes:
        progressDialog.increment()
        # When parenting the root, children won't exist anymore
        if not cmds.objExists(node):
            continue
        # only the root
        if maf.hasParent(node):
            continue
        if not cmds.nodeType(node) == 'transform':
            continue
        # Parent to the item group
        rootCtrl = maf.parentNodeTo(node, itemGroup)
        if '_root' in node:
            # Get the shape
            nodeShapes = cmds.listRelatives(rootCtrl, shapes=True, f=True, type='nurbsCurve')
            if nodeShapes is None:
                continue
            rootCtrlShape = nodeShapes[0]
            # Adjust root appearance
            cmds.setAttr(rootCtrlShape+'.overrideEnabled', 1)
            cmds.setAttr(rootCtrlShape+'.overrideColor', 18)
            cmds.rename(rootCtrlShape,rootCtrl + 'Shape')

        # Adjust root object
        cmds.setAttr(rootCtrl+'.useOutlinerColor',1)
        cmds.setAttr(rootCtrl+'.outlinerColor',0.392,0.863,1)

        # Store Ramses Data!
        setRamsesManaged( rootCtrl )
        setRamsesAttr( rootCtrl, RamsesAttribute.GEO_FILE, filePath, 'string' )
        setRamsesAttr( rootCtrl, RamsesAttribute.GEO_TIME, timestamp, 'long' )
        setRamsesAttr( rootCtrl, RamsesAttribute.STEP, step, 'string' )
        setRamsesAttr( rootCtrl, RamsesAttribute.ITEM, item.shortName(), 'string' )
        setRamsesAttr( rootCtrl, RamsesAttribute.ITEM_TYPE, itemType, 'string' )
        setRamsesAttr( rootCtrl, RamsesAttribute.ASSET_GROUP, item.group(), 'string' )

        # Lock transform
        children = cmds.listRelatives(rootCtrl, ad=True, f=True, type='transform')
        for child in children:
            maf.lockTransform(child)

        rootCtrls.append( rootCtrl )

    progressDialog.hide()
    return rootCtrls

