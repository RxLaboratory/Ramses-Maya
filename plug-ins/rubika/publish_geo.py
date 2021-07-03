import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .ui_publish_geo import PublishGeoDialog
from .utils_shaders import exportShaders
from .utils_nodes import getPublishNodes, getProxyNodes
from .utils_attributes import * # pylint: disable=import-error
from .utils_constants import * # pylint: disable=import-error
from .utils_general import * # pylint: disable=import-error
from .utils_items import * # pylint: disable=import-error

ONLY_PROXY = 0
ALL = 1
ONLY_GEO = 2

def publishGeo(item, filePath, step, pipeFiles = [GEO_PIPE_FILE]):

    # Options
    removeHidden = True
    removeLocators = True
    renameShapes = True
    onlyRootGroups = False
    noFreeze = ''
    noFreezeCaseSensitive = False
    keepCurves = False
    keepSurfaces = False

    if GEO_PIPE_FILE in pipeFiles or SET_PIPE_FILE in pipeFiles:
        # Show dialog
        publishGeoDialog = PublishGeoDialog( maf.getMayaWindow() )
        if not publishGeoDialog.exec_():
            return

        # Options
        removeHidden = publishGeoDialog.removeHidden()
        removeLocators = publishGeoDialog.removeLocators()
        renameShapes = publishGeoDialog.renameShapes()
        onlyRootGroups = publishGeoDialog.onlyRootGroups()
        noFreeze = publishGeoDialog.noFreeze()
        noFreezeCaseSensitive = publishGeoDialog.noFreezeCaseSensitive()
        keepCurves = publishGeoDialog.curves()
        keepSurfaces = publishGeoDialog.surfaces()

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Publishing geometry")

    tempData = maf.cleanScene()

    # For all nodes in the publish set or proxy set
    nodes = []
    if GEO_PIPE_FILE in pipeFiles or SET_PIPE_FILE in pipeFiles or VPSHADERS_PIPE_FILE in pipeFiles or RDRSHADERS_PIPE_FILE in pipeFiles:
        nodes = getPublishNodes()
    if PROXYGEO_PIPE_FILE in pipeFiles:
        showAlert = GEO_PIPE_FILE not in pipeFiles
        nodes = nodes + getProxyNodes( showAlert )
    
    if len(nodes) == 0:
        endProcess(tempData, progressDialog)
        return

    numNodes = len(nodes)
    progressDialog.setMaximum(numNodes + 2)
    progressDialog.setText("Preparing")
    progressDialog.increment()
    
    # Prepare options
    # Freeze transform & center pivot
    if not noFreezeCaseSensitive:
        noFreeze = noFreeze.lower()
    # noFreeze contains a comma-separated list
    noFreeze = noFreeze.replace(' ','')
    noFreeze = noFreeze.split(',')

    # Item info
    fileInfo = getFileInfo( filePath )
    if fileInfo is None:
        endProcess(tempData, progressDialog)
        return
    version = item.latestVersion( fileInfo['resource'], '', step )
    versionFilePath = item.latestVersionFilePath( fileInfo['resource'], '', step )

    # Publish folder
    publishFolder = getPublishFolder(item, step)
    if publishFolder == '':
        endProcess(tempData, progressDialog)
        return
    ram.log( "I'm publishing geometry in " + publishFolder )

    # Extension
    extension = ''
    if SET_PIPE_FILE in pipeFiles:
        extension = getExtension( step, SET_STEP, SET_PIPE_FILE, ['ma','mb', 'abc'], 'mb' )
    else:
        extension = getExtension( step, MOD_STEP, GEO_PIPE_FILE, ['ma','mb', 'abc'], 'abc' )
    if extension == 'abc':
        # We need to use alembic
        if maf.safeLoadPlugin("AbcExport"):
            ram.log("I have loaded the Alembic Export plugin, needed for the current task.")

    # Let's count how many objects are published
    publishedNodes = []

    for node in nodes:
        progressDialog.setText("Publishing: " + node)
        progressDialog.increment()

        if onlyRootGroups:
            # MOD to publish must be in a group
            # The node must be a root
            if maf.hasParent(node):
                continue
            # It must be a group
            if not maf.isGroup(node):
                continue 
            # It must have children to publish
            if not maf.hasChildren(node):
                continue

        # Get all children
        childNodes = cmds.listRelatives( node, ad=True, f=True, type='transform')
        if childNodes is None:
            childNodes = []
        childNodes.append(node)

        # Empty group, nothing to do
        if childNodes is None and maf.isGroup(node):
            cmds.delete(node)
            continue

        maf.moveToZero(node)

        # Clean (remove what we don't want to publish)
        for childNode in childNodes:

            # Remove hidden
            if removeHidden and cmds.getAttr(childNode + '.v') == 0:
                cmds.delete(childNode)
                continue

            typesToKeep = ['mesh']
            if not removeLocators:
                typesToKeep.append('locator')
            if keepCurves:
                typesToKeep.append('bezierCurve')
                typesToKeep.append('nurbsCurve')
            if keepSurfaces:
                typesToKeep.append('nurbsSurface')

            freeze = True
            childName = childNode.lower()
            for no in noFreeze:
                if no in childName:
                    freeze = False
                    break

            maf.cleanNode( childNode, True, typesToKeep, renameShapes, freeze)

        # the main node may have been removed (if hidden for example)
        if not cmds.objExists(node):
            continue

        # Last steps
        nodeName = maf.getNodeBaseName(node, True)
        if nodeName.lower().startswith('proxy_'):
            nodeName = nodeName[6:]

        # Remove remaining empty groups
        maf.removeEmptyGroups(node)

        # Type
        pType = ''
        if getRamsesAttr( node, RamsesAttribute.IS_PROXY ):
            pType = PROXYGEO_PIPE_NAME
        elif SET_PIPE_FILE in pipeFiles:
            pType = SET_PIPE_NAME
        else:
            pType = GEO_PIPE_NAME

        # Create a root controller
        r = maf.createRootCtrl( node, nodeName + '_' + pType )
        node = r[0]
        controller = r[1]

        if extension == 'abc':
            # Save and create Abc
            # Generate file path
            abcFileInfo = fileInfo.copy()
            # extension
            abcFileInfo['extension'] = 'abc'
            # resource
            if abcFileInfo['resource'] != '':
                abcFileInfo['resource'] = abcFileInfo['resource'] + '-' + nodeName + '-' + pType
            else:
                abcFileInfo['resource'] = nodeName + '-' + pType
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
                '-file "' + abcFilePath + '"'
            ])
            cmds.AbcExport(j=abcOptions)
            # Update Ramses Metadata (version)
            ram.RamMetaDataManager.setPipeType( abcFilePath, pType )
            ram.RamMetaDataManager.setVersionFilePath( abcFilePath, versionFilePath )
            ram.RamMetaDataManager.setVersion( abcFilePath, version )

        # Export viewport shaders
        shaderMode = ''
        if VPSHADERS_PIPE_FILE in pipeFiles:
            shaderMode = VPSHADERS_PIPE_NAME
        elif RDRSHADERS_PIPE_FILE in pipeFiles:
            shaderMode = RDRSHADERS_PIPE_NAME
        if shaderMode != '' and not getRamsesAttr( node, RamsesAttribute.IS_PROXY ):
            shaderFilePath = exportShaders( node, publishFolder, fileInfo.copy(), shaderMode )
            # Update Ramses Metadata (version)
            ram.RamMetaDataManager.setValue( abcFilePath, 'shaderFilePath', shaderFilePath )
            ram.RamMetaDataManager.setPipeType( shaderFilePath, shaderMode )
            ram.RamMetaDataManager.setVersionFilePath( shaderFilePath, versionFilePath )
            ram.RamMetaDataManager.setVersion( shaderFilePath, version )

        publishedNodes.append(node)

    progressDialog.setText( "Cleaning" )
    progressDialog.increment()

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
    for transformNode in reversed(allTransformNodes):
        if transformNode in allPublishedNodes:
            continue
        if transformNode in maf.nonDeletableObjects:
            continue
        try:
            cmds.delete(transformNode)
        except:
            pass

    # Clean scene:
    # Remove empty groups from the scene
    maf.removeEmptyGroups()

    # Copy published scene to publish
    sceneFileInfo = fileInfo.copy()

    # Get Type
    pipeType = GEO_PIPE_NAME
    if SET_PIPE_FILE in pipeFiles:
        pipeType = SET_PIPE_NAME

    if PROXYGEO_PIPE_FILE in pipeFiles and not GEO_PIPE_FILE in pipeFiles and not SET_PIPE_FILE in pipeFiles:
        pipeType = PROXYGEO_PIPE_NAME

    if SET_PIPE_FILE in pipeFiles:
        sceneFileInfo['extension'] = getExtension( step, SET_STEP, SET_PIPE_FILE, ['ma','mb'], 'mb' )
    else:
        sceneFileInfo['extension'] = 'mb'
    # resource
    if sceneFileInfo['resource'] != '':
        sceneFileInfo['resource'] = sceneFileInfo['resource'] + '-' + pipeType
    else:
        sceneFileInfo['resource'] = pipeType
    # path
    sceneFilePath = ram.RamFileManager.buildPath((
        publishFolder,
        ram.RamFileManager.composeRamsesFileName( sceneFileInfo )
    ))
    # Save
    cmds.file( rename=sceneFilePath )
    cmds.file( save=True, options="v=1;" )
    ram.RamMetaDataManager.setPipeType( sceneFilePath, pipeType )
    ram.RamMetaDataManager.setVersionFilePath( sceneFilePath, versionFilePath )
    ram.RamMetaDataManager.setVersion( sceneFilePath, version )

    endProcess(tempData, progressDialog)

    ram.log("I've published these assets:")
    for publishedNode in publishedNodes:
        publishedNode = maf.getNodeBaseName( publishedNode )
        ram.log(" > " + publishedNode)
    cmds.inViewMessage(  msg="Assets published: <hl>" + '</hl>,<hl>'.join(publishedNodes) + "</hl>.", pos='midCenterBot', fade=True )

