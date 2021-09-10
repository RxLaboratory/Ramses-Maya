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

def publishRig( item, step, publishFileInfo, vpShaders = True ):

    # Options
    publishDialog = PublishRigDialog(maf.getMayaWindow())
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
    tempData = maf.cleanScene( removeAnim, lockHiddenVisibility )

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
        n = maf.parentNodeTo(node, '|')
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
            if obj in maf.nonDeletableObjects:
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
                    cmds.setAttr( joint + '.drawStyle', 0 )

    progressDialog.setText("Exporting viewport shaders")
    progressDialog.increment()

    # export viewport shaders
    if vpShaders:
        for node in nodes:
            shaderFilePath = exportShaders( node, publishFileInfo, VPSHADERS_PIPE_NAME )
            # Update Ramses Metadata (version)
            ram.RamMetaDataManager.setPipeType( shaderFilePath, VPSHADERS_PIPE_NAME )
            ram.RamMetaDataManager.setVersion( shaderFilePath, publishFileInfo.version )
            ram.RamMetaDataManager.setState( shaderFilePath, publishFileInfo.state )
            # Assign initialshadinggroup to all geo
            cmds.sets(node,e=True,forceElement='initialShadingGroup')

    # delete all user shaders
    mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteShadingGroupsAndMaterials")')

    progressDialog.setText("Saving")
    progressDialog.increment()

    # We need to build the future file path where we'll save the scene
    sceneInfo = publishFileInfo.copy()
    sceneInfo.version = -1
    sceneInfo.state = ''
    sceneInfo.extension = getExtension( step, RIG_STEP, RIG_PIPE_FILE, ['ma','mb'], 'ma' )
    # resource
    if sceneInfo.resource != '':
        sceneInfo.resource = sceneInfo.resource + '-' + RIG_PIPE_NAME
    else:
        sceneInfo.resource = RIG_PIPE_NAME
    # path
    sceneFilePath = sceneInfo.filePath()
    
    # save as publish
    cmds.file( rename=sceneFilePath )
    cmds.file( save=True, options="v=1;" )
    # Update Ramses Metadata (version)
    ram.RamMetaDataManager.setPipeType( sceneFilePath, RIG_PIPE_NAME )
    ram.RamMetaDataManager.setVersion( sceneFilePath, publishFileInfo.version )
    ram.RamMetaDataManager.setState( sceneFilePath, publishFileInfo.state )

    # reopen scene, etc
    endProcess(tempData, progressDialog)

    ram.log("I've published the rig.")
    cmds.inViewMessage(  msg="Rig published.", pos='midCenter', fade=True )

