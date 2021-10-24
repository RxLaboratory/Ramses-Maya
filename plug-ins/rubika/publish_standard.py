# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_items import * # pylint: disable=import-error
from .utils_general import * # pylint: disable=import-error
from .utils_nodes import getPublishNodes
from .utils_publish import * # pylint: disable=import-error
from .utils_shaders import exportShaders

def publishStandard( item, step, publishFileInfo, pipeFiles ):
    
    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setMaximum(2)
    progressDialog.setText("Preparing...")
    progressDialog.increment()

    # Clean scene:
    # Remove empty groups from the scene
    # Prepare the scene
    tempData = maf.Scene.createTempScene()
    maf.Node.removeEmptyGroups()

    ram.log( "I'm publishing the scene in " + os.path.dirname( publishFileInfo.filePath() ) )

    progressDialog.setText( "Publishing scene..." )
    progressDialog.increment()

    # For all nodes in the publish set
    nodes = getPublishNodes()

    if len(nodes) == 0:
        endProcess(tempData, progressDialog)
        return

    numNodes = len(nodes)
    progressDialog.setMaximum( numNodes )
    progressDialog.setText("Preparing")
    progressDialog.increment()

    extension = getExtension( step, OTHER_STEP, STANDARD_PIPE_FILE, pipeFiles, ['ma', 'mb'], 'mb' )

     # Let's count how many objects are published
    publishedNodes = []

    for node in reversed(nodes):
        # Full path node
        node = maf.Path.absolutePath( node )
        nodeName = maf.Path.baseName( node )
        progressDialog.setText("Publishing: " + nodeName)
        progressDialog.increment()

        # Create a root controller
        r = maf.Node.createRootCtrl( node, nodeName + '_root_' + step.shortName() )
        node = r[0]
        controller = r[1]

        abcPaths = []

        if STANDARD_PIPE_FILE in pipeFiles:
            if hasExtension( STANDARD_PIPE_FILE, pipeFiles, 'abc'):
                frameIn = int(cmds.playbackOptions(q=True,ast=True))
                frameOut = int(cmds.playbackOptions(q=True,aet=True))
                abcPath = publishNodeAsABC( publishFileInfo, controller, nodeName.replace('_', ' ') + '-' + STANDARD_PIPE_NAME, (frameIn, frameOut))
                abcPaths.append(abcPath)

        if STANDARDREF_PIPE_FILE in pipeFiles:
            if hasExtension( STANDARDREF_PIPE_FILE, pipeFiles, 'abc'):
                frameIn = int(cmds.playbackOptions(q=True,ast=True))
                frameOut = int(cmds.playbackOptions(q=True,aet=True))
                abcPath = publishNodeAsABC( publishFileInfo, controller, nodeName.replace('_', ' ') + '-' + STANDARDREF_PIPE_NAME, (frameIn, frameOut))
                abcPaths.append(abcPath)
        
        # Export shaders
        shaderMode = ''
        if VPSHADERS_PIPE_FILE in pipeFiles:
            shaderMode = VPSHADERS_PIPE_NAME
        elif RDRSHADERS_PIPE_FILE in pipeFiles:
            shaderMode = RDRSHADERS_PIPE_NAME
        
        if shaderMode != '':
            shaderFilePath = exportShaders( node, publishFileInfo.copy(), shaderMode )
            # Update Ramses Metadata
            if shaderFilePath != "":
                for abcPath in abcPaths:
                    ram.RamMetaDataManager.setValue( abcPath, 'shaderFilePath', shaderFilePath )

        publishedNodes.append(controller)


    progressDialog.setText( "Cleaning" )
    progressDialog.increment()

    # Publish as ma/mb
    ext = extension
    if hasExtension( ANIM_PIPE_FILE, pipeFiles, 'ma'): ext = 'ma'
    if hasExtension( ANIM_PIPE_FILE, pipeFiles, 'mb'): ext = 'mb'

    if ext in ('ma', 'mb'):
        publishNodesAsMayaScene( publishFileInfo, publishedNodes, STANDARD_PIPE_NAME, ext)

    # End and log
    endProcess(tempData, progressDialog)

    ram.log("I've published the scene.")
    cmds.inViewMessage(  msg="Scene published!", pos='midCenterBot', fade=True )
