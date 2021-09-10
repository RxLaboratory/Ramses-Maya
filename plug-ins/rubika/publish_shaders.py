# -*- coding: utf-8 -*-

import os

from .utils_shaders import exportShaders
from .utils_nodes import getPublishNodes, getProxyNodes
from .utils_items import getPublishFolder
from .ui_publish_shaders import PublishShaderDialog
from .utils_general import *
import dumaf as maf # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import maya.cmds as cmds # pylint: disable=import-error
from .utils_constants import *


def publishProxyShaders( item, step, publishFileInfo ):
    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Publishing Arnold Scene Source")

    tempData = maf.cleanScene()

    # For all nodes in the proxy set
    nodes = getProxyNodes( False )
    if len(nodes) == 0:
        endProcess(tempData, progressDialog)
        return

    numNodes = len(nodes)
    progressDialog.setMaximum(numNodes + 1)
    progressDialog.setText("Preparing")
    progressDialog.increment()

    ram.log( "I'm publishing the shaders in " + os.path.dirname( publishFileInfo.filePath() ) )

    # We need Arnold, of course
    maf.safeLoadPlugin('mtoa')

    for node in nodes:
        progressDialog.setText("Publishing proxy: " + node)
        progressDialog.increment()

        cmds.select(node,r=True)
        nodeName = maf.getNodeBaseName( node )
        if nodeName.lower().startswith( 'proxy_' ):
            nodeName = nodeName[6:]

        saveInfo = publishFileInfo.copy()
        saveInfo.version = -1
        saveInfo.state  =''
        # extension
        saveInfo.extension = 'ass'
        # resource
        if saveInfo.resource != '':
            saveInfo.resource = saveInfo.resource + '-' + nodeName + '-proxyShade'
        else:
            saveInfo.resource = nodeName + '-proxyShade'
        # path
        assFilePath = saveInfo.filePath()

        cmds.arnoldExportAss(f=assFilePath, s=True, mask=223, lightLinks=0, shadowLinks=0, cam="perspShape" )
        ram.RamMetaDataManager.setPipeType( assFilePath, PROXYSHADE_PIPE_NAME )
        ram.RamMetaDataManager.setVersion( assFilePath, publishFileInfo.version )
        ram.RamMetaDataManager.setState( assFilePath, publishFileInfo.state )

    progressDialog.setText( "Cleaning" )
    progressDialog.increment()

    endProcess(tempData, progressDialog)

def publishShaders( item, step, publishFileInfo, mode):
    
    # Show dialog
    publishShaderDialog = PublishShaderDialog( maf.getMayaWindow() )
    if not publishShaderDialog.exec_():
        return

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Publishing shaders")

    # Options
    removeHidden = publishShaderDialog.removeHidden()

    tempData = maf.cleanScene()

    # For all nodes in the publish set
    nodes = getPublishNodes()
    if len(nodes) == 0:
        progressDialog.hide()
        return

    numNodes = len(nodes)
    progressDialog.setMaximum(numNodes + 1)
    progressDialog.setText("Preparing")
    progressDialog.increment()

    # Publish folder
    ram.log( "I'm publishing the shaders in " + os.path.dirname( publishFileInfo.filePath() ) )

    for node in reversed(nodes):
        progressDialog.setText("Publishing: " + node)
        progressDialog.increment()

        # If there's no mesh, nothing to do
        meshes = cmds.listRelatives( node, ad=True, f=True, type='mesh')
        if meshes is None:
            continue

        # Get all children
        childNodes = cmds.listRelatives( node, ad=True, f=True, type='transform')
        if childNodes is None:
            childNodes = []
        childNodes.append(node)

        # Clean (remove what we don't want to publish)
        for childNode in reversed(childNodes):

            # Remove hidden
            if removeHidden and cmds.getAttr(childNode + '.v') == 0:
                cmds.delete(childNode)
                continue

            maf.cleanNode( childNode, True, False, False)
            maf.checkNode( childNode, True, ('mesh'))
        
        # Remove remaining empty groups
        maf.removeEmptyGroups(node)

        # Export
        shaderFilePath = exportShaders(node, publishFileInfo, mode )
        # Update Ramses Metadata (version)
        ram.RamMetaDataManager.setPipeType( shaderFilePath, mode )
        ram.RamMetaDataManager.setVersion( shaderFilePath, publishFileInfo.version )
        ram.RamMetaDataManager.setState( shaderFilePath, publishFileInfo.state )

    progressDialog.setText("Cleaning...")

    endProcess(tempData, progressDialog)

    progressDialog.hide()