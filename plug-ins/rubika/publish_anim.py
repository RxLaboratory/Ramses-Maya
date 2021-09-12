# -*- coding: utf-8 -*-

from .ui_publish_anim import PublishAnimDialog
import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_nodes import getPublishNodes
from .utils_items import * # pylint: disable=import-error
from .utils_general import * # pylint: disable=import-error
from .utils_publish import * # pylint: disable=import-error

def publishAnim( item, step, publishFileInfo, pipeFiles ):
    
    # Options
    dialog = PublishAnimDialog(maf.UI.getMayaWindow())
    if not dialog.exec_():
        return

    frameRange = dialog.getFrameRange()
    filterEuler = dialog.filterEuler()
    frameStep = dialog.getFrameStep()
    frameIn = frameRange[1] - frameRange[0]
    frameOut = frameRange[2] + frameRange[3]
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

    # For all nodes in the publish set
    nodes = getPublishNodes()

    if len(nodes) == 0:
        endProcess(tempData, progressDialog)
        return

    numNodes = len(nodes)
    progressDialog.setMaximum( numNodes )
    progressDialog.setText("Preparing")
    progressDialog.increment()

    ram.log( "I'm publishing animation in " + os.path.dirname( publishFileInfo.filePath() ) )

    extension = getExtension( step, ANIM_STEP, ANIM_PIPE_FILE, pipeFiles, ['ma', 'mb', 'abc'], 'abc')
    
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
        r = maf.Node.createRootCtrl( node, nodeName + '_root_' + ANIM_PIPE_NAME )
        node = r[0]
        controller = r[1]

        ext = extension
        if hasExtension( ANIM_PIPE_FILE, pipeFiles, 'abc'): ext = 'abc'

        if ext == 'abc':
            publishNodeAsABC( publishFileInfo, controller, ANIM_PIPE_NAME, (frameIn, frameOut), frameStep, filterEuler)

        publishedNodes.append(controller)

    progressDialog.setText("Cleaning...")
    progressDialog.increment()

    # Publish as ma/mb
    ext = extension
    if hasExtension( ANIM_PIPE_FILE, pipeFiles, 'ma'): ext = 'ma'
    if hasExtension( ANIM_PIPE_FILE, pipeFiles, 'mb'): ext = 'mb'

    if ext in ('ma', 'mb'):
        publishNodesAsMayaScene( publishFileInfo, publishedNodes, ANIM_PIPE_NAME, ext)

    # End and log
    endProcess(tempData, progressDialog)

    ram.log("I've published the animation.")
    cmds.inViewMessage(  msg="Animation has been published.", pos='midCenterBot', fade=True )


