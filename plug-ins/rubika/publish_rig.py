# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=import-error
import maya.mel as mel # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_shaders import exportShaders
from .utils_nodes import getPublishNodes
from .utils_attributes import *
from .utils_constants import *
from .utils_general import *
from .utils_items import *
from .ui_publish_rig import PublishRigDialog
from .utils_publish import *

def publishRig( item, step, publishFileInfo, pipeFiles, vpShaders = True ):

    # Options
    publishDialog = PublishRigDialog(maf.UI.getMayaWindow())
    if not publishDialog.exec_():
        return

    hideJointsMode = publishDialog.hideJointsMode()
    lockHiddenVisibility = publishDialog.lockHidden()
    removeAnim = publishDialog.removeAnim()
    deformerSetsToDelete = publishDialog.getDeformerSets()
    renderingSetsToDelete = publishDialog.getRenderingSets()

    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Publishing rig")
    progressDialog.setMaximum(2)
    progressDialog.increment()

    # rename scene (cleanscene)
    tempData = maf.Scene.createTempScene()
    maf.Reference.importAll()
    maf.Namespace.removeAll()
    if removeAnim: maf.Animation.removeAll()
    if lockHiddenVisibility: maf.Node.lockHiddenVisibility()

    # get Nodes
    ns = getPublishNodes()
    nodes = []
    # move them to the root
    for node in ns:
        p = cmds.listRelatives(node, p=True)
        # already in the world
        if p is None:
            nodes.append('|' + node)
            continue
        n = maf.Node.parent(node, '|')
        nodes.append(n)

    # Delete the nodes we're not publishing
    allRootNodes = cmds.ls( '|*', r=True, long=True )
    for rootNode in reversed(allRootNodes):
        if rootNode in nodes:
            continue
        cmds.delete( rootNode )

    # Delete objects in sets if option
    for deformerSet in deformerSetsToDelete:
        objects = cmds.sets( deformerSet, q=True)
        if objects is None:
            continue
        for obj in objects:
            try:
                cmds.delete( obj )
            except:
                pass

    for renderingSet in renderingSetsToDelete:
        objects = cmds.sets( renderingSet, q=True)
        if objects is None:
            continue
        for obj in objects:
            if obj in maf.Node.nonDeletableObjects:
                continue
            try:
                cmds.delete( obj )
            except:
                pass

    # hide joints if option (using drawstyle or visibility)
    if hideJointsMode > 0:
        joints = cmds.ls(type='joint')
        if joints is not None:
            for joint in joints:
                if hideJointsMode == 1:
                    cmds.setAttr( joint + '.visibility', False )
                else:
                    cmds.setAttr( joint + '.drawStyle', 2 )

    progressDialog.setText("Exporting viewport shaders")
    progressDialog.increment()

    # export viewport shaders
    if vpShaders:
        for node in nodes:
            exportShaders( node, publishFileInfo, VPSHADERS_PIPE_NAME )
            # Assign initialshadinggroup to all geo
            cmds.sets(node,e=True,forceElement='initialShadingGroup')
            # delete all user shaders
            mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteShadingGroupsAndMaterials")')

    progressDialog.setText("Saving")
    progressDialog.increment()

    # export
    extension = getExtension( step, RIG_STEP, RIG_PIPE_FILE, pipeFiles, ['ma','mb'], 'ma' )
    publishNodesAsMayaScene( publishFileInfo, nodes, RIG_PIPE_NAME, extension)
   
    # reopen scene, etc
    endProcess(tempData, progressDialog)

    ram.log("I've published the rig.")
    cmds.inViewMessage(  msg="Rig published.", pos='midCenter', fade=True )

