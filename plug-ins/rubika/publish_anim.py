# -*- coding: utf-8 -*-

from .ui_publish_anim import PublishAnimDialog
import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_nodes import getPublishNodes
from .utils_items import * # pylint: disable=import-error
from .utils_general import * # pylint: disable=import-error

def publishAnim( item, step, publishFileInfo ):
    
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
    keepDeformers = dialog.deformers()
    removeHidden = dialog.removeHidden()

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Publishing animation")
    progressDialog.setMaximum(2)
    progressDialog.increment()

    # Prepare the scene
    tempData = maf.Scene.createTempScene()
    maf.Reference.importAll()
    maf.Namespace.removeAll()

    # For all nodes in the publish set or proxy set
    nodes = getPublishNodes()

    if len(nodes) == 0:
        endProcess(tempData, progressDialog)
        return

    numNodes = len(nodes)
    progressDialog.setMaximum(numNodes + 2)
    progressDialog.setText("Preparing")
    progressDialog.increment()

    ram.log( "I'm publishing animation in " + os.path.dirname( publishFileInfo.filePath() ) )
    
    # We need to use alembic
    if maf.Plugin.load("AbcExport"):
        ram.log("I have loaded the Alembic Export plugin, needed for the current task.")

    # Let's count how many objects are published
    publishedNodes = []

    for node in reversed(nodes):
        # Full path node
        node = maf.Path.absolutePath( node )
        nodeName = maf.Path.baseName( node )
        progressDialog.setText("Baking: " + nodeName)
        progressDialog.increment()

        # Get all children
        childNodes = cmds.listRelatives( node, ad=True, f=True, type='transform')
        if childNodes is None:
            childNodes = []
        childNodes.append(node)

        # Empty group, nothing to do
        if childNodes is None and maf.Node.isGroup(node):
            cmds.delete(node)
            continue

        # Clean (remove what we don't want to publish)
        for childNode in reversed(childNodes):

            # Remove hidden
            if removeHidden and cmds.getAttr(childNode + '.v') == 0:
                cmds.delete(childNode)
                continue

            # Check and clean

            typesToKeep = []
            if not keepDeformers:
                typesToKeep = ['mesh']
                if keepCurves:
                    typesToKeep.append('bezierCurve')
                    typesToKeep.append('nurbsCurve')
                if keepSurfaces:
                    typesToKeep.append('nurbsSurface')
            
            if not maf.Node.check( childNode, True, typesToKeep ):
                continue
            
            if not keepDeformers:
                maf.Node.removeExtraShapes( childNode )
                maf.Node.deleteHistory( childNode )
                maf.Node.renameShapes( childNode )        

        # the main node may have been removed (if hidden for example)
        if not cmds.objExists(node):
            continue

        # Create a root controller
        r = maf.Node.createRootCtrl( node, nodeName + '_' + ANIM_PIPE_NAME )
        node = r[0]
        controller = r[1]

        # Generate file path
        abcInfo = publishFileInfo.copy()
        abcInfo.version = -1
        abcInfo.state = ''
        # extension
        abcInfo.extension = 'abc'
        # Type
        pipeType = ANIM_PIPE_NAME
        # resource
        if abcInfo.resource != '':
            abcInfo.resource = abcInfo.resource + '-' + nodeName + '-' + pipeType
        else:
            abcInfo.resource = nodeName + '-' + pipeType
        # path
        abcFilePath = abcInfo.filePath()

        # Build the ABC command
        abcOptions = ' '.join([
            '-frameRange ' + str(frameIn) + ' ' + str(frameOut),
            filterEuler,
            '-step ' + str(frameStep),
            '-autoSubd', # crease
            '-uvWrite',
            '-writeUVSets',
            '-worldSpace',
            '-writeVisibility',
            '-dataFormat hdf',
            '-renderableOnly',
            '-root ' + controller,
            '-file "' + abcFilePath + '"',
        ])
        ram.log("These are the alembic options:\n" + abcOptions, ram.LogLevel.Debug)
        # Export
        cmds.AbcExport(j=abcOptions)
        # Update Ramses Metadata (version)
        ram.RamMetaDataManager.setPipeType( abcFilePath, pipeType )
        ram.RamMetaDataManager.setVersion( abcFilePath, publishFileInfo.version )
        ram.RamMetaDataManager.setState( abcFilePath, publishFileInfo.state )

        publishedNodes.append(nodeName)

    progressDialog.setText("Cleaning...")
    progressDialog.increment()

    # Copy published scene to publish
    sceneInfo = publishFileInfo.copy()

    sceneInfo.extension = 'mb'
    # resource
    if sceneInfo.resource != '':
        sceneInfo.resource = sceneInfo.resource + '-' + pipeType
    else:
        sceneInfo.resource = pipeType
    # path
    sceneFilePath = sceneInfo.filePath()
    # Save
    cmds.file( rename=sceneFilePath )
    cmds.file( save=True, options="v=1;" )
    ram.RamMetaDataManager.setPipeType( sceneFilePath, pipeType )
    ram.RamMetaDataManager.setVersion( sceneFilePath, publishFileInfo.version )
    ram.RamMetaDataManager.setState( sceneFilePath, publishFileInfo.state )

    endProcess(tempData, progressDialog)

    ram.log("I've published these animations:")
    for publishedNode in publishedNodes:
        ram.log(" > " + publishedNode)
    cmds.inViewMessage(  msg="Assets published: <hl>" + '</hl>,<hl>'.join(publishedNodes) + "</hl>.", pos='midCenterBot', fade=True )


