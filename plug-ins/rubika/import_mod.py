import re, os
import maya.cmds as cmds
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error

def lockTransform( node ):
    if cmds.nodeType(node) != 'transform':
        return
    for a in ['.tx','.ty','.tz','.rx','.ry','.rz','.sx','.sy','.sz']:
        cmds.setAttr(node + a, lock=True )

def getNodeBaseName( node ):
    nodeName = node.split('|')[-1]
    nodeName = nodeName.split(':')[-1]
    return nodeName

# mode is 'vp' for viewport, 'rdr' for rendering
def importShaders(node, mode, filePath, itemShortName=''):
    # Get shader data
    shaderData = ram.RamMetaDataManager.getValue(filePath,'shaderData')
    if shaderData is None:
        ram.log("I can't find any shader for this geometry, sorry.")
        return
    if 'shaderFilePath' not in shaderData:
        ram.log("I can't find any shader for this geometry, sorry.")
        return
    shaderFile = shaderData['shaderFilePath']
    if not os.path.isfile(shaderFile):
        ram.log("I can't find the shader file, sorry. It should be there: " + shaderFile)
        return 
    
    # For all mesh
    meshes = cmds.listRelatives( node, ad=True, type='mesh', f=True)
    if meshes is None:
        ram.log("I can't find any geometry to apply the shaders, sorry.")
        return

    # Reference the shader file
    cmds.file(shaderFile,r=True,mergeNamespacesOnClash=True,namespace=itemShortName)

    for mesh in meshes:
        # Get the transform node (which has the name we're looking for)
        transformNode = cmds.listRelatives(mesh, p=True, type='transform')[0]
        nodeName = getNodeBaseName( transformNode )
        if nodeName not in shaderData:
            continue
        meshShaderData = shaderData[nodeName]
        if not meshShaderData['hasShader']:
            continue
        # Apply
        cmds.select(mesh, r=True)
        shader = meshShaderData['shader']
        if shader != 'initialShadingGroup':
            shaderName = itemShortName + ':' + shader
            cmds.sets(e=True, forceElement = shaderName)
        else:
            cmds.sets(e=True,forceElement='initialShadingGroup')
        # Set opaque
        if meshShaderData['opaque']:
            cmds.setAttr(mesh + '.aiOpaque', 1)
        else:
            cmds.setAttr(mesh + '.aiOpaque', 0)

    cmds.select(clear=True)
        


def importMod(item, filePath, step):

    # Checks
    if step != 'MOD':
        return

    if item.itemType() != ram.ItemType.ASSET:
        ram.log("Sorry, this is not a valid Asset, I won't import it.")
        return

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Importing Geometry")
    progressDialog.setMaximum(2)

    # Get info
    itemShortName = item.shortName()
    itemType = ram.ItemType.ASSET
    assetGroupName = item.group()
    # Get the file timestamp
    timestamp = os.path.getmtime( filePath )
    timestamp = int(timestamp)

    # Get the Asset Group
    assetGroup = 'RamASSETS_' + assetGroupName
    assetGroup = maf.getCreateGroup( assetGroup )

    # Check if the short name is not made only of numbers
    regex = re.compile('^\\d+$')
    if re.match(regex, itemShortName):
        itemShortName = itemType + itemShortName

    # Get the Item Group
    itemGroup = maf.getCreateGroup( itemShortName, assetGroup )

    # Import the file
    progressDialog.setText("Importing file...")
    progressDialog.increment()
    newNodes = cmds.file(filePath,i=True,ignoreVersion=True,mergeNamespacesOnClash=True,returnNewNodes=True,ns=itemShortName)

    # Get the controler, and parent nodes to the group
    progressDialog.setText("Tidying...")
    progressDialog.increment()
    progressDialog.setMaximum( len(newNodes) + 2 )
    rootCtrl = ''
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
        rootCtrl = cmds.parent(node, itemGroup)[0]
        # get the full path please... Maya...
        rootCtrl = itemGroup + '|' + rootCtrl
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
        # Source file
        cmds.addAttr(rootCtrl,ln="ramSourceFilePath",dt="string")
        cmds.setAttr(rootCtrl+'.ramSourceFilePath',filePath,type='string')
        cmds.setAttr(rootCtrl+'.ramSourceFilePath', lock=True )
        cmds.addAttr(rootCtrl,ln='ramTimeStamp',at='long')
        cmds.setAttr(rootCtrl+'.ramTimeStamp', timestamp)
        cmds.setAttr(rootCtrl+'.ramTimeStamp', lock=True )
        # Shading
        cmds.addAttr(rootCtrl,ln="ramShading",dt="string")
        cmds.setAttr(rootCtrl+'.ramShading','vp',type='string')
        cmds.setAttr(rootCtrl+'.ramShading', lock=True )
        cmds.addAttr(rootCtrl,ln="ramShadingFilePath",dt="string")

        # Lock transform
        children = cmds.listRelatives(rootCtrl, ad=True, f=True, type='transform')
        for child in children:
            lockTransform(child)

        # Import shaders
        importShaders(rootCtrl, 'vp', filePath, itemShortName)


    progressDialog.hide()

item = ram.RamItem.fromPath('C:\\Users\\Duduf\\Ramses\\Projects\\FPE\\04-ASSETS\\Characters\\FPE_A_TRISTAN\\FPE_A_TRISTAN_MOD')
filePath = 'C:\\Users\\Duduf\\Ramses\\Projects\\FPE\\04-ASSETS\\Characters\\FPE_A_TRISTAN\\FPE_A_TRISTAN_MOD\\_published\\FPE_A_TRISTAN_MOD_Tristan.abc'
step = 'MOD'
importMod(item, filePath, step)