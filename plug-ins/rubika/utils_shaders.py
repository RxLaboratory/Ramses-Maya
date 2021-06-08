import os
from re import A
import maya.cmds as cmds # pylint: disable=import-error
import dumaf as maf
import ramses as ram # pylint: disable=import-error
from .utils_attributes import * # pylint: disable=import-error

# mode is 'vp' for viewport, 'rdr' for rendering
def exportShadersBak(node, mode, folderPath, fileNameBlocks, associatedGeometryFilePath=''): 
    # List all nodes containing shaders
    nodes = cmds.listRelatives(node, ad=True, f=True, type='mesh')
    # If there are Yeti nodes
    try:
        nodes = nodes + cmds.listRelatives(node, ad=True, f=True, type='pgYetiMaya')
    except:
        pass

    # Prepare the data info we're exporting
    shaderData = {}
    allShadingEngines = []

    # Get shading info
    for meshNode in nodes:
        nodeHistory = cmds.listHistory( meshNode, f=True )
        shadingEngines = cmds.listConnections( nodeHistory, type='shadingEngine')
        shadingEngine = 'initialShadingGroup'

        # Get the name from parent (transform node for this mesh)
        objectName = cmds.listRelatives(meshNode, p=True)[0]
        # Remove namespace if any
        objectName = objectName.split(':')[-1]

        objectShaderData = {}

        if shadingEngines is not None:
            objectShaderData['hasShader'] = True
            shadingEngine = shadingEngines[0]
            
            # Get the first surface shader to rename the engine
            surfaceShaders = cmds.listConnections(shadingEngine + '.surfaceShader')
            if surfaceShaders is not None:
                surfaceShader = surfaceShaders[0]
                surfaceShaderName = surfaceShader.split(':')[-1]
                # Remove all what's before the first '_'
                i = surfaceShaderName.find('_')
                if i >= 0:
                    surfaceShaderName = surfaceShaderName[i+1:]
                # And rename
                if shadingEngine != 'initialShadingGroup':
                    shadingEngine = cmds.rename( shadingEngine, mode + '_' + surfaceShaderName)
            
            objectShaderData['shader'] = shadingEngine

            # Check if the node is opaque
            objectShaderData['opaque'] = False
            try:
                objectShaderData['opaque'] = cmds.getAttr(meshNode + '.aiOpaque')
            except:
                pass
        else:
            objectShaderData['hasShader'] = False
        
        shaderData[objectName] = objectShaderData
        allShadingEngines.append(shadingEngine)

    # Select and export shadingEngines
    cmds.select(allShadingEngines, noExpand=True, r=True)
    nodeName = node.split('|')[-1].split(':')[-1]

    # extension
    fileNameBlocks['extension'] = 'mb'
    # resource
    if fileNameBlocks['resource'] != '':
        fileNameBlocks['resource'] = fileNameBlocks['resource'] + '-' + nodeName + '-' + mode + 'Shaders'
    else:
        fileNameBlocks['resource'] = nodeName + '-' + mode + 'Shaders'
    # path
    filePath = ram.RamFileManager.buildPath((
        folderPath,
        ram.RamFileManager.composeRamsesFileName(fileNameBlocks)
    ))
    cmds.file( filePath, exportSelected=True, type='mayaBinary', force=True )
    cmds.select(cl=True)
    shaderData['shaderFilePath'] = filePath
    shaderData['shaderType'] = mode

    # Set MetaData
    if associatedGeometryFilePath == '':
        associatedGeometryFilePath = filePath
    ram.RamMetaDataManager.setValue( associatedGeometryFilePath, 'shaderData', shaderData )

    return filePath

# mode is 'vp' for viewport, 'rdr' for rendering
def exportShaders(node, mode, folderPath, fileNameBlocks, associatedGeometryFilePath=''): 
    # List all nodes containing shaders
    nodes = cmds.listRelatives(node, ad=True, f=True, type='mesh')
    # If there are Yeti nodes
    try:
        nodes = nodes + cmds.listRelatives(node, ad=True, f=True, type='pgYetiMaya')
    except:
        pass

    # Prepare the data info we're exporting
    allShadingEngines = []

    # Get shading info
    for meshNode in nodes:
        nodeHistory = cmds.listHistory( meshNode, f=True )
        shadingEngines = cmds.listConnections( nodeHistory, type='shadingEngine')
        shadingEngine = 'initialShadingGroup'

        # Get the name from parent (transform node for this mesh)
        objectName = cmds.listRelatives(meshNode, p=True)[0]
        # Remove namespace if any
        objectName = objectName.split(':')[-1]

        if shadingEngines is not None:
            for shadingEngine in shadingEngines:

                # Get the first surface shader to rename the engine
                surfaceShaders = cmds.listConnections(shadingEngine + '.surfaceShader')
                if surfaceShaders is not None:
                    surfaceShader = surfaceShaders[0]
                    surfaceShaderName = surfaceShader.split(':')[-1]
                    # Remove all what's before the first '_'
                    i = surfaceShaderName.find('_')
                    if i >= 0:
                        surfaceShaderName = surfaceShaderName[i+1:]
                    # And rename
                    if shadingEngine != 'initialShadingGroup':
                        shadingEngine = cmds.rename( shadingEngine, mode + '_' + surfaceShaderName)
            
                    # List the objects this engine is shading
                    setRamsesManaged( shadingEngine )
                    objectNames = getRamsesAttr( shadingEngine, RamsesAttribute.SHADED_OBJECTS )
                    if objectNames is None:
                        objectNames = ''
                    else:
                        objectNames = objectNames + ','
                    objectNames = objectNames + objectName
                    setRamsesAttr( shadingEngine, RamsesAttribute.SHADED_OBJECTS, objectNames, 'string')
        
        allShadingEngines.append(shadingEngine)

    # Select and export shadingEngines
    cmds.select(allShadingEngines, noExpand=True, r=True)
    nodeName = node.split('|')[-1].split(':')[-1]

    # extension
    fileNameBlocks['extension'] = 'mb'
    # resource
    if fileNameBlocks['resource'] != '':
        fileNameBlocks['resource'] = fileNameBlocks['resource'] + '-' + nodeName + '-' + mode + 'Shaders'
    else:
        fileNameBlocks['resource'] = nodeName + '-' + mode + 'Shaders'
    # path
    filePath = ram.RamFileManager.buildPath((
        folderPath,
        ram.RamFileManager.composeRamsesFileName(fileNameBlocks)
    ))
    cmds.file( filePath, exportSelected=True, type='mayaBinary', force=True )
    cmds.select(cl=True)

    # Set MetaData
    if associatedGeometryFilePath == '':
        associatedGeometryFilePath = filePath
    ram.RamMetaDataManager.setValue( associatedGeometryFilePath, 'shaderFilePath', filePath )

    return filePath

# mode is 'vp' for viewport, 'rdr' for rendering
def referenceShaders(nodes, mode, filePath, itemShortName=''):
    
    # If already referenced, get the existing reference and clean it
    shaderNodes = []
    isAlreadyReferenced = False
    try:
        shaderNodes = cmds.referenceQuery( filePath, nodes=True )
        isAlreadyReferenced = True
    except:
        pass

    if not isAlreadyReferenced:
        # Reference the shader file
        shaderNodes = cmds.file(filePath,r=True,mergeNamespacesOnClash=True,namespace=itemShortName, returnNewNodes = True)

    if shaderNodes is None or len(shaderNodes) == 0:
        ram.log( "I did not find any shader to import, sorry." )
        return

    # For all mesh
    meshes = cmds.listRelatives( nodes, ad=True, type='mesh', f=True)
    if meshes is None:
        ram.log("I can't find any geometry to apply the shaders, sorry.")
        return

    for mesh in meshes:
        # Get the transform node (which has the name we're looking for)
        transformNode = cmds.listRelatives(mesh, p=True, type='transform')[0]
        nodeName = maf.getNodeBaseName( transformNode )
        # Apply
        cmds.select(mesh, r=True)
        found = False
        for shaderNode in shaderNodes:
            shadedObjects = getRamsesAttr( shaderNode, RamsesAttribute.SHADED_OBJECTS )
            if shadedObjects is None:
                continue
            shadedObjects = shadedObjects.split(',')
            if nodeName in shadedObjects:
                cmds.sets(e=True, forceElement = shaderNode)
                found = True

    cmds.select(clear=True)

    # Shading Data
    timestamp = os.path.getmtime( filePath )

    for node in nodes:
        setRamsesManaged( node )
        setRamsesAttr( node, RamsesAttribute.SHADING_TYPE, mode, 'string')
        setRamsesAttr( node, RamsesAttribute.SHADING_FILE, filePath, 'string')
        setRamsesAttr( node, RamsesAttribute.SHADING_TIME, timestamp, 'long')

# mode is 'vp' for viewport, 'rdr' for rendering
def referenceShadersBak(node, mode, filePath, itemShortName=''):
    # Get shader data
    shaderData = ram.RamMetaDataManager.getValue(filePath,'shaderData')
    if shaderData is None:
        ram.log("I can't find any shader data, sorry.")
        return
    if 'shaderFilePath' not in shaderData:
        ram.log("I can't find any shader data, sorry.")
        return
    shaderFile = shaderData['shaderFilePath']
    if not os.path.isfile(shaderFile):
        ram.log("I can't find the shader file, sorry. It should be there: " + shaderFile)
        return
    
    # If already referenced, get the existing reference and clean it
    shaderNodes = []
    isAlreadyReferenced = False
    try:
        shaderNodes = cmds.referenceQuery( shaderFile, nodes=True )
        isAlreadyReferenced = True
    except:
        pass

    if not isAlreadyReferenced:
        # Reference the shader file
        shaderNodes = cmds.file(shaderFile,r=True,mergeNamespacesOnClash=True,namespace=itemShortName, returnNewNodes = True)

    if shaderNodes is None or len(shaderNodes) == 0:
        ram.log( "I did not find any shader to import, sorry." )
        return

    # For all mesh
    meshes = cmds.listRelatives( node, ad=True, type='mesh', f=True)
    if meshes is None:
        ram.log("I can't find any geometry to apply the shaders, sorry.")
        return

    # Reinit the shaders on everything (in case we're just reloading the shaders)
    cmds.select(node,r=True)
    cmds.sets(e=True,forceElement='initialShadingGroup')

    for mesh in meshes:
        # Get the transform node (which has the name we're looking for)
        transformNode = cmds.listRelatives(mesh, p=True, type='transform')[0]
        nodeName = maf.getNodeBaseName( transformNode )
        if nodeName not in shaderData:
            continue
        meshShaderData = shaderData[nodeName]
        if not meshShaderData['hasShader']:
            continue
        # Apply
        cmds.select(mesh, r=True)
        shader = meshShaderData['shader']
        if shader != 'initialShadingGroup':
            # Get the "real" shader name from the shaderNodes
            shaderName = ''
            for shaderNode in shaderNodes:
                if shaderNode.endswith(shader):
                    shaderName = shaderNode
                    break
            if shaderName != '':
                cmds.sets(e=True, forceElement = shaderName)
        else:
            cmds.sets(e=True,forceElement='initialShadingGroup')
        # Set opaque
        try:
            if meshShaderData['opaque']:
                cmds.setAttr(mesh + '.aiOpaque', 1)
            else:
                cmds.setAttr(mesh + '.aiOpaque', 0)
        except:
            pass

    cmds.select(clear=True)

    # Shading Data
    timestamp = os.path.getmtime( shaderFile )

    setRamsesManaged( node )
    setRamsesAttr( node, RamsesAttribute.SHADING_TYPE, mode, 'string')
    setRamsesAttr( node, RamsesAttribute.SHADING_FILE, shaderFile, 'string')
    setRamsesAttr( node, RamsesAttribute.SHADING_TIME, timestamp, 'long')
