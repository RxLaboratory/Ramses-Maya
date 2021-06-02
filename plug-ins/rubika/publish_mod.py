import tempfile, os

import maya.cmds as cmds # pylint: disable=import-error

import ramses as ram # pylint: disable=import-error

nonDeletableObjects = [
    '|frontShape',
    '|front',
    '|perspShape',
    '|persp',
    '|sideShape',
    '|side',
    '|topShape',
    '|top',
]

def safeLoadPlugin(pluginName):
    ok = cmds.pluginInfo(pluginName, loaded=True, q=True)
    if not ok:
        cmds.loadPlugin(pluginName)
        ram.log("I have loaded the plug-in " + pluginName + ", needed for the current task.")
        
def removeAllNamespaces():
    # Set the current namespace to the root
    cmds.namespace(setNamespace=':')

    # Remove namespaces containing nodes
    nodes = cmds.ls()
    namespaces = []
    for node in nodes:
        if ':' in node:
            nodeNamespaces = node.split(":")[0:-1]
            for nodeNamespace in nodeNamespaces:
                if not nodeNamespace in namespaces:
                    namespaces.append(nodeNamespace)
    for namespace in namespaces:
        try:
            cmds.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)
        except:
            pass

    # Remove remaining namespaces without merging with root
    namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
    for namespace in namespaces:
        try:
            cmds.namespace(removeNamespace=namespace)
        except:
            pass

def removeAllAnimCurves():
    keys = cmds.ls(type='animCurveTL') + cmds.ls(type='animCurveTA') + cmds.ls(type='animCurveTU')
    for key in keys:
        try:
            cmds.delete(key)
        except:
            pass

def createTempScene(name=''):
    # Rename the file because we're going to modify stuff in there
    tempDir = tempfile.gettempdir()
    fileName = 'RamsesWorkingFile' + name + '.mb'
    tempFile = ram.RamFileManager.buildPath((
        tempDir,
        fileName
    ))
    cmds.file(rename=tempFile)
    return tempFile

def cleanScene(removeAnimation=True):
    tempFile = createTempScene(name='')

    # Import all references
    for ref in cmds.ls(type='reference'):
        refFile = cmds.referenceQuery(ref, f=True)
        cmds.file(refFile, importReference=True)

    # Clean names
    removeAllNamespaces()

    # No animation in the mod step!
    if removeAnimation:
        removeAllAnimCurves()
    
    return tempFile

def hasParent(node):
    return cmds.listRelatives(node, p=True, f=True) is not None

def hasChildren(node):
    return cmds.listRelatives(node, c=True, f=True, type='transform') is not None

def isGroup(node):
    # A group is a transform node
    if cmds.objectType(node) != 'transform':
        return False
    # And it does not have any child shape
    return cmds.listRelatives(node,s=True,f=True) is None

def moveToZero(node):
    cmds.setAttr(node + '.tx',0)
    cmds.setAttr(node + '.ty',0)
    cmds.setAttr(node + '.tz',0)

def removeEmptyGroups(node=None):
    remove = True
    while remove:
        nodes = ()
        remove = False
        if node is None:
            nodes = cmds.ls(type='transform')
        else:
            nodes = cmds.listRelatives(node, ad=True, f=True, type='transform')
        if nodes is None:
            return
        for node in nodes:
            if not isGroup(node):
                continue
            if not hasChildren(node):
                cmds.delete(node)
                remove = True

def freezeTransform(shape):
        cmds.move(0, 0, 0, shape + ".rotatePivot", absolute=True)
        cmds.move(0, 0, 0, shape + ".scalePivot", absolute=True)
        cmds.makeIdentity(shape, apply=True, t=1, r=1, s=1, n=0)

# mode is 'vp' for viewport, 'rdr' for rendering
def exportShaders(node, mode, folderPath, fileNameBlocks): 
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

    # Set MetaData
    ram.RamMetaDataManager.setValue( filePath, 'shaderData', shaderData )

    return filePath

def publishMod(item, filePath, step): # TODO build UI, Add progress window in Ramses-Maya passed as an arg to the scripts

    # OPTIONS (build UI)
    removeHidden = True
    removeLocators = True
    renameShapes = True
    onlyRootGroups = False
    noFreeze = 'Sphere, Torus'
    noFreezeCaseSensitive = False

    # Checks
    if step.shortName() != 'MOD':
        return

    tempFile = cleanScene()

    # We need to use alembic
    safeLoadPlugin("AbcExport")

    # For all nodes in the publish set
    nodes = ()
    try:
        nodes = cmds.sets( 'Ramses_Publish', nodesOnly=True, q=True )
    except ValueError:
        ram.log("Nothing to publish! The asset you need to publish must be listed in a 'Ramses_Publish' set.")
        cmds.inViewMessage( msg='Nothing to publish! The asset you need to publish must be listed in a <hl>Ramses_Pulbish</hl> set.', pos='midCenter', fade=True )
        return
    
    if nodes is None or len(nodes) == 0:
        ram.log("The 'Ramses_Publish' set is empty, there's nothing to publish!")
        cmds.inViewMessage( msg="The <hl>Ramses_Publish</hl> set is empty, there's nothing to publish!", pos='midCenter', fade=True )
        return

    # Prepare options
    # Freeze transform & center pivot
    if not noFreezeCaseSensitive:
        noFreeze = noFreeze.lower()
    # noFreeze contains a comma-separated list
    noFreeze = noFreeze.replace(' ','')
    noFreeze = noFreeze.split(',')

    # Item info
    fileInfo = ram.RamFileManager.decomposeRamsesFilePath( filePath )
    if fileInfo is None:
        ram.log(ram.Log.MalformedName, ram.LogLevel.Fatal)
        cmds.inViewMessage( msg=ram.Log.MalformedName, pos='midCenter', fade=True )
        cmds.error( ram.Log.MalformedName )
        return
    version = item.latestVersion()
    versionFilePath = item.latestVersionFilePath()

    publishFolder = item.publishFolderPath( step )
    if publishFolder == '':
        ram.log("I can't find the publish folder for this item, maybe it does not respect the ramses naming scheme or it is out of place.", ram.LogLevel.Fatal)
        cmds.inViewMessage( msg="Can't find the publish folder for this scene, sorry. Check its name and location.", pos='midCenter', fade=True )
        cmds.error( "Can't find publish folder." )
        return
    ram.log( "I'm publishing in " + publishFolder )

    # Let's count how many objects are published
    publishedNodes = []

    for node in nodes:
        if onlyRootGroups:
            # MOD to publish must be in a group
            # The node must be a root
            if hasParent(node):
                continue
            # It must be a group
            if not isGroup(node):
                continue 
            # It must have children to publish
            if not hasChildren(node):
                continue

        # Absolute path to be sure
        # node = '|' + node

        # Get all children
        childNodes = cmds.listRelatives( node, ad=True, f=True, type='transform')
        if childNodes is None:
            childNodes = []
        childNodes.append(node)

        # Empty group, nothing to do
        if childNodes is None and isGroup(node):
            cmds.delete(node)
            continue

        moveToZero(node)

        # Clean (remove what we don't want to publish)
        for childNode in childNodes:

            # Remove hidden
            if removeHidden and cmds.getAttr(childNode + '.v') == 0:
                cmds.delete(childNode)
                continue

            # The shape(s) of this child
            shapes = cmds.listRelatives(childNode,s=True,f=True)

            if shapes is None:
                # No shapes, no child: empty group to remove
                if not hasChildren(childNode):
                    cmds.delete(childNode)
                # Nothing else to check for groups
                continue

            # Remove supplementary shapes
            # (Maya may store more than a single shape in transform nodes because of the dependency graph)
            if len(shapes) > 1:
                cmds.delete(shapes[1:])

            # The single remaining shape for this child
            shape = shapes[0]

            # Check type
            shapeType = cmds.nodeType( shape )
            typesToKeep = ['mesh']
            if not removeLocators:
                typesToKeep.append('locator')
                
            if shapeType not in typesToKeep:
                cmds.delete(shape)
                if not hasChildren( childNode ):
                    cmds.delete(childNode)
                continue

            # Delete history
            cmds.delete(shape, constructionHistory=True)

            # Rename shapes after transform nodes
            if renameShapes:
                cmds.rename(shape, childNode.split('|')[-1] + 'Shape')

            # Freeze transform & center pivot
            freeze = True
            childName = childNode.lower()
            for no in noFreeze:
                if no in childName:
                    freeze = False
                    break
            if freeze and shapeType == 'mesh':
                freezeTransform(childNode)            

        # Last steps
        nodeName = node.split('|')[-1]

        # Remove remaining empty groups
        removeEmptyGroups(node)

        # Create a root controller
        # Get the bounding box
        boundingBox = cmds.exactWorldBoundingBox( node )
        xmax = boundingBox[3]
        xmin = boundingBox[0]
        zmax = boundingBox[5]
        zmin = boundingBox[2]
        # Get the 2D Projection on the floor (XZ) lengths
        boundingWidth = xmax - xmin
        boundingLength = zmax - zmin
        # Compute a margin relative to mean of these lengths
        margin = ( boundingWidth + boundingLength ) / 2.0
        # Make it small
        margin = margin / 20.0
        # Create a shape using this margin and coordinates
        cv1 = ( xmin - margin, 0, zmin - margin)
        cv2 = ( xmax + margin, 0, zmin - margin)
        cv3 = ( xmax + margin, 0, zmax + margin)
        cv4 = ( xmin - margin, 0, zmax + margin)
        cv5 = cv1
        controller = cmds.curve( d=1, p=[cv1, cv2, cv3, cv4, cv5], k=(0,1,2,3,4), name=nodeName + '_root')
        # Parent the node
        cmds.parent(node, controller)

        # Export viewport shaders
        shaderFilePath = exportShaders(node, 'vp', publishFolder, fileInfo.copy())
        # Update Ramses Metadata (version)
        ram.RamMetaDataManager.setVersionFilePath( shaderFilePath, versionFilePath )
        ram.RamMetaDataManager.setVersion( shaderFilePath, version )

        # Save and create Abc
        # Generate file path
        abcFileInfo = fileInfo.copy()
        # extension
        abcFileInfo['extension'] = 'abc'
        # resource
        if abcFileInfo['resource'] != '':
            abcFileInfo['resource'] = abcFileInfo['resource'] + '-' + nodeName
        else:
            abcFileInfo['resource'] = nodeName
        # path
        abcFilePath = ram.RamFileManager.buildPath((
            publishFolder,
            ram.RamFileManager.composeRamsesFileName( abcFileInfo )
        ))
        # Save
        abcOptions = ' '.join([
            '-frameRange 1 1',
            '-autoSubd', # Crease info
            '-uvWrite',
            '-worldSpace',
            '-writeUVSets',
            '-dataFormat hdf',
            '-root |' + controller,
            '-file ' + abcFilePath
        ])
        cmds.AbcExport(j=abcOptions)
        # Update Ramses Metadata (version)
        ram.RamMetaDataManager.setVersionFilePath( abcFilePath, versionFilePath )
        ram.RamMetaDataManager.setVersion( abcFilePath, version )

        publishedNodes.append(node)

    # remove all nodes not children or parent of publishedNodes
    allTransformNodes = cmds.ls(transforms=True, long=True)
    allPublishedNodes = []
    for publishedNode in publishedNodes:
        # Children
        published = cmds.listRelatives(publishedNode, ad=True, f=True, type='transform')
        if published is not None:
            allPublishedNodes = allPublishedNodes + published
        # Parents
        published = cmds.listRelatives(publishedNode, ap=True, f=True, type='transform')
        if published is not None:
            allPublishedNodes = allPublishedNodes + published
        # And Self
        published = cmds.ls(publishedNode, transforms=True, long=True)
        if published is not None:
            allPublishedNodes = allPublishedNodes + published
    for transformNode in allTransformNodes:
        if transformNode in allPublishedNodes:
            continue
        if transformNode in nonDeletableObjects:
            continue
        cmds.delete(transformNode)

    # Clean scene:
    # Remove empty groups from the scene
    removeEmptyGroups()

    # Copy published scene to publish
    sceneFileInfo = fileInfo.copy()
    sceneFileInfo['extension'] = 'mb'
    # resource
    if sceneFileInfo['resource'] != '':
        sceneFileInfo['resource'] = sceneFileInfo['resource'] + '-CleanPub'
    else:
        sceneFileInfo['resource'] = 'CleanPub'
    # path
    sceneFilePath = ram.RamFileManager.buildPath((
        publishFolder,
        ram.RamFileManager.composeRamsesFileName( sceneFileInfo )
    ))
    # Save
    cmds.file( rename=sceneFilePath )
    cmds.file( save=True, options="v=1;" )
    # Update Ramses Metadata (version)
    ram.RamMetaDataManager.setVersionFilePath( sceneFilePath, versionFilePath )
    ram.RamMetaDataManager.setVersion( sceneFilePath, version )

    # Re-Open initial scene
    cmds.file(filePath,o=True,f=True)

    # Remove temp file
    if os.path.isfile(tempFile):
        os.remove(tempFile)

    ram.log("I've published these nodes:")
    for publishedNode in publishedNodes:
        ram.log(" > " + publishedNode)
    
currentScene = cmds.file( q=True, sn=True )
item = ram.RamItem.fromPath(currentScene)
publishMod(item, currentScene, ram.RamStep('MOD','MOD'))