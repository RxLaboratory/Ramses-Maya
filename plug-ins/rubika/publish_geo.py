# -*- coding: utf-8 -*-

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
from .utils_publish import *

ONLY_PROXY = 0
ALL = 1
ONLY_GEO = 2

def publishGeo(item, step, publishFileInfo, pipeFiles = [GEO_PIPE_FILE]):

    # Options
    removeHidden = True
    removeLocators = True
    renameShapes = True
    keepAnimation = False
    keepAnimatedDeformers = False
    noFreeze = ''
    noFreezeCaseSensitive = False
    keepCurves = False
    keepSurfaces = False

    if GEO_PIPE_FILE in pipeFiles:
        # Show dialog
        publishGeoDialog = PublishGeoDialog( maf.UI.getMayaWindow() )
        if not publishGeoDialog.exec_():
            return

        # Options
        removeHidden = publishGeoDialog.removeHidden()
        removeLocators = publishGeoDialog.removeLocators()
        renameShapes = publishGeoDialog.renameShapes()
        noFreeze = publishGeoDialog.noFreeze()
        noFreezeCaseSensitive = publishGeoDialog.noFreezeCaseSensitive()
        keepCurves = publishGeoDialog.curves()
        keepSurfaces = publishGeoDialog.surfaces()
        keepAnimation = publishGeoDialog.animation()
        keepAnimatedDeformers = publishGeoDialog.animatedDeformers()

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Publishing geometry")
    tempData = maf.Scene.createTempScene()
    maf.Reference.importAll()
    maf.Namespace.removeAll()
    if not keepAnimation: maf.Animation.removeAll()
    maf.Node.lockHiddenVisibility()

    # For all nodes in the publish set or proxy set
    nodes = []
    if GEO_PIPE_FILE in pipeFiles or VPSHADERS_PIPE_FILE in pipeFiles or RDRSHADERS_PIPE_FILE in pipeFiles:
        nodes = getPublishNodes()
    if PROXYGEO_PIPE_FILE in pipeFiles:
        showAlert = GEO_PIPE_FILE not in pipeFiles
        nodes = nodes + getProxyNodes( showAlert )
    
    if len(nodes) == 0:
        endProcess(tempData, progressDialog)
        return

    numNodes = len(nodes)
    progressDialog.setMaximum(numNodes)
    progressDialog.setText("Preparing")
    progressDialog.increment()
    
    # Prepare options
    # Freeze transform & center pivot
    if not noFreezeCaseSensitive:
        noFreeze = noFreeze.lower()
    # noFreeze contains a comma-separated list
    noFreeze = noFreeze.replace(' ','')
    noFreeze = noFreeze.split(',')

    # Publish folder
    ram.log( "I'm publishing geometry in " + os.path.dirname( publishFileInfo.filePath() ) )

    # Let's count how many objects are published
    publishedNodes = []

    for node in reversed(nodes):
        # Full path node
        node = maf.Path.absolutePath( node )
        nodeName = maf.Path.baseName( node )
        progressDialog.setText("Publishing: " + nodeName)
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

        maf.Node.lockTransform( node, False, recursive=True )
        maf.Node.moveToZero(node)

        # Clean (freeze transform, rename shapes, etc)
        for childNode in reversed(childNodes):

            # Remove hidden
            if removeHidden and cmds.getAttr(childNode + '.v') == 0:
                cmds.delete(childNode)
                continue

            typesToKeep = ()
            if not keepAnimatedDeformers:
                typesToKeep = ['mesh']
                if not removeLocators:
                    typesToKeep.append('locator')
                if keepCurves:
                    typesToKeep.append('bezierCurve')
                    typesToKeep.append('nurbsCurve')
                if keepSurfaces:
                    typesToKeep.append('nurbsSurface')

            if not maf.Node.check( childNode, True, typesToKeep ):
                continue
            
            if not keepAnimatedDeformers:
                maf.Node.removeExtraShapes( childNode )
                if renameShapes: maf.Node.renameShapes( childNode )
                maf.Node.deleteHistory( childNode )

            freeze = True
            childName = childNode
            if not noFreezeCaseSensitive: childName = childNode.lower()
            for no in noFreeze:
                if no in childName:
                    freeze = False
                    break

            if not keepAnimation and freeze:
                maf.Node.freezeTransform( childNode )
                maf.Node.lockTransform( childNode )

        # the main node may have been removed (if hidden for example)
        if not cmds.objExists(node):
            continue

        # Remove remaining empty groups
        maf.Node.removeEmptyGroups(node)

        # Type and extension
        pType = ''
        extension = ''
        if getRamsesAttr( node, RamsesAttribute.IS_PROXY ):
            pType = PROXYGEO_PIPE_NAME
            if hasExtension( PROXYGEO_PIPE_FILE, pipeFiles, 'abc'):
                extension = 'abc'
            else:
                extension = getExtension( step, MOD_STEP, PROXYGEO_PIPE_FILE, pipeFiles, ['ma', 'mb', 'abc'], 'abc' )
        else:
            pType = GEO_PIPE_NAME
            if hasExtension( GEO_PIPE_FILE, pipeFiles, 'abc'):
                extension = 'abc'
            else:
                extension = getExtension( step, MOD_STEP, GEO_PIPE_FILE, pipeFiles, ['ma', 'mb', 'abc'], 'abc' )

        # Create a root controller
        r = maf.Node.createRootCtrl( node, nodeName + '_root_' + pType )
        node = r[0]
        controller = r[1]

        if extension == 'abc':

            frameIn = 1
            frameOut = 1
            if keepAnimation:
                frameIn = int(cmds.playbackOptions(q=True,ast=True))
                frameOut = int(cmds.playbackOptions(q=True,aet=True))

            abcPath = publishNodeAsABC( publishFileInfo, controller, pType, (frameIn, frameOut))

        # Export shaders
        shaderMode = ''
        if VPSHADERS_PIPE_FILE in pipeFiles:
            shaderMode = VPSHADERS_PIPE_NAME
        elif RDRSHADERS_PIPE_FILE in pipeFiles:
            shaderMode = RDRSHADERS_PIPE_NAME
        
        if shaderMode != '' and not getRamsesAttr( node, RamsesAttribute.IS_PROXY ):
            shaderFilePath = exportShaders( node, publishFileInfo.copy(), shaderMode )
            # Update Ramses Metadata
            if extension == 'abc':
                ram.RamMetaDataManager.setValue( abcPath, 'shaderFilePath', shaderFilePath )

        publishedNodes.append(controller)

    progressDialog.setText( "Cleaning" )
    progressDialog.increment()

    # Publish ma or mb

    # Get Type
    pipeType = GEO_PIPE_NAME
    pipe = GEO_PIPE_FILE
    if PROXYGEO_PIPE_FILE in pipeFiles and not GEO_PIPE_FILE in pipeFiles:
        pipeType = PROXYGEO_PIPE_NAME
        pipe = PROXYGEO_PIPE_FILE
    # Get extension
    if hasExtension( pipe, pipeFiles, 'ma'): extension = 'ma'
    elif hasExtension( pipe, pipeFiles, 'mb'): extension = 'mb'
    else: extension = getExtension( step, MOD_STEP, pipe, pipeFiles, ['ma', 'mb', 'abc'], 'abc' )

    if extension in ('ma', 'mb'):
        publishNodesAsMayaScene( publishFileInfo, publishedNodes, pipeType, extension)

    # End and log
    endProcess(tempData, progressDialog)

    ram.log("I've published the geometry.")
    cmds.inViewMessage(  msg="Geometry has been published.", pos='midCenterBot', fade=True )

