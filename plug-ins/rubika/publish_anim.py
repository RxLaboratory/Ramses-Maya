# -*- coding: utf-8 -*-

from .ui_publish_anim import PublishAnimDialog
import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_nodes import getPublishNodes
from .utils_items import * # pylint: disable=import-error
from .utils_general import * # pylint: disable=import-error

def publishAnim( item, filePath, step ):
    
    # Options
    dialog = PublishAnimDialog(maf.getMayaWindow())
    if not dialog.exec_():
        return

    frameRange = dialog.getFrameRange()
    filterEuler = dialog.filterEuler()
    frameStep = dialog.getFrameStep()
    frameIn = frameRange[1] - frameRange[0]
    frameOut = frameRange[2] + frameRange[3]
    if filterEuler:
        filterEuler = '-eulerFilter'
    else:
        filterEuler = ''
    keepCurves = dialog.curves()
    keepSurfaces = dialog.surfaces()
    removeHidden = dialog.removeHidden()

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Publishing animation")
    progressDialog.setMaximum(2)
    progressDialog.increment()

    tempData = maf.cleanScene(False, False)

    # For all nodes in the publish set or proxy set
    nodes = getPublishNodes()

    if len(nodes) == 0:
        endProcess(tempData, progressDialog)
        return

    numNodes = len(nodes)
    progressDialog.setMaximum(numNodes + 2)
    progressDialog.setText("Preparing")
    progressDialog.increment()

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

    ram.log( "I'm publishing animation in " + publishFolder )
    
    # We need to use alembic
    if maf.safeLoadPlugin("AbcExport"):
        ram.log("I have loaded the Alembic Export plugin, needed for the current task.")

    # Let's count how many objects are published
    publishedNodes = []

    for node in nodes:
        # Full path node
        node = maf.getNodeAbsolutePath( node )
        nodeName = maf.getNodeBaseName( node )
        progressDialog.setText("Baking: " + nodeName)
        progressDialog.increment()

        # Get all children
        childNodes = cmds.listRelatives( node, ad=True, f=True, type='transform')
        if childNodes is None:
            childNodes = []
        childNodes.append(node)

        # Empty group, nothing to do
        if childNodes is None and maf.isGroup(node):
            cmds.delete(node)
            continue

        # Clean (remove what we don't want to publish)
        for childNode in childNodes:

            # Remove hidden
            if removeHidden and cmds.getAttr(childNode + '.v') == 0:
                cmds.delete(childNode)
                continue

            typesToKeep = ['mesh']
            if keepCurves:
                typesToKeep.append('bezierCurve')
                typesToKeep.append('nurbsCurve')
            if keepSurfaces:
                typesToKeep.append('nurbsSurface')

            maf.cleanNode(childNode, True, typesToKeep, False, False)

        # the main node may have been removed (if hidden for example)
        if not cmds.objExists(node):
            continue

        # Create a root controller
        r = maf.createRootCtrl( node, nodeName + '_' + ANIM_PIPE_NAME )
        node = r[0]
        controller = r[1]

        # Generate file path
        abcFileInfo = fileInfo.copy()
        # extension
        abcFileInfo['extension'] = 'abc'
        # Type
        pipeType = ANIM_PIPE_NAME
        # resource
        if abcFileInfo['resource'] != '':
            abcFileInfo['resource'] = abcFileInfo['resource'] + '-' + nodeName + '-' + pipeType
        else:
            abcFileInfo['resource'] = nodeName + '-' + pipeType
        # path
        abcFilePath = ram.RamFileManager.buildPath((
            publishFolder,
            ram.RamFileManager.composeRamsesFileName( abcFileInfo )
        ))

        # Build the ABC command
        abcOptions = ' '.join([
            '-frameRange ' + str(frameIn) + ' ' + str(frameOut),
            filterEuler,
            '-step ' + str(frameStep),
            '-root ' + controller,
            '-autoSubd', # crease
            '-uvWrite',
            '-writeUVSets',
            '-worldSpace',
            '-writeVisibility',
            '-dataFormat hdf',
            '-renderableOnly',
            '-file "' + abcFilePath + '"',
        ])
        print(abcFilePath)
        # Export
        cmds.AbcExport(j=abcOptions)
        # Update Ramses Metadata (version)
        ram.RamMetaDataManager.setPipeType( abcFilePath, pipeType )
        ram.RamMetaDataManager.setVersionFilePath( abcFilePath, versionFilePath )
        ram.RamMetaDataManager.setVersion( abcFilePath, version )

        publishedNodes.append(nodeName)

    progressDialog.setText("Cleaning...")
    progressDialog.increment()

    # Copy published scene to publish
    sceneFileInfo = fileInfo.copy()

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

    ram.log("I've published these animations:")
    for publishedNode in publishedNodes:
        ram.log(" > " + publishedNode)
    cmds.inViewMessage(  msg="Assets published: <hl>" + '</hl>,<hl>'.join(publishedNodes) + "</hl>.", pos='midCenterBot', fade=True )


