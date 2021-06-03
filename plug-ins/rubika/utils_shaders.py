import maya.cmds as cmds # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error

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

    # Set MetaData
    if associatedGeometryFilePath == '':
        associatedGeometryFilePath = filePath
    ram.RamMetaDataManager.setValue( associatedGeometryFilePath, 'shaderData', shaderData )

    return filePath
