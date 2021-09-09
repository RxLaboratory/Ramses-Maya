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


def publishProxyShaders( item, filePath, step ):
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

    # Item info
    nm = ram.RamNameManager()
    nm.setFilePath( filePath )
    if nm.project == '':
        endProcess(tempData, progressDialog)
        return
    version = item.latestVersion( nm.resource, '', step )
    versionFilePath = item.latestVersionFilePath( nm.resource, '', step )

    # Publish folder
    publishFolder = getPublishFolder(item, step)
    if publishFolder == '':
        endProcess(tempData, progressDialog)
        return
    ram.log( "I'm publishing the shaders in " + publishFolder )

    # We need Arnold, of course
    maf.safeLoadPlugin('mtoa')

    for node in nodes:
        progressDialog.setText("Publishing proxy: " + node)
        progressDialog.increment()

        cmds.select(node,r=True)
        nodeName = maf.getNodeBaseName( node )
        if nodeName.lower().startswith( 'proxy_' ):
            nodeName = nodeName[6:]
        # extension
        nm.extension = 'ass'
        # resource
        if nm.resource != '':
            nm.resource = nm.resource + '-' + nodeName + '-proxyShade'
        else:
            nm.resource = nodeName + '-proxyShade'
        # path
        assFilePath = ram.RamFileManager.buildPath((
            publishFolder,
            nm.fileName()
        ))

        cmds.arnoldExportAss(f=assFilePath, s=True, mask=223, lightLinks=0, shadowLinks=0, cam="perspShape" )
        ram.RamMetaDataManager.setPipeType( assFilePath, PROXYSHADE_PIPE_NAME )
        ram.RamMetaDataManager.setVersionFilePath( assFilePath, versionFilePath )
        ram.RamMetaDataManager.setVersion( assFilePath, version )

    progressDialog.setText( "Cleaning" )
    progressDialog.increment()

    endProcess(tempData, progressDialog)

def publishShaders( item, filePath, step, mode):
    
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

    # Item info
    nm = ram.RamNameManager()
    nm.setFilePath( filePath )
    if nm.project == '':
        progressDialog.hide()
        return
    version = item.latestVersion( nm.resource, '', step )
    versionFilePath = item.latestVersionFilePath( nm.resource, '', step )

    # Publish folder
    publishFolder = getPublishFolder(item, step)
    if publishFolder == '':
        progressDialog.hide()
        return
    ram.log( "I'm publishing the shaders in " + publishFolder )

    for node in nodes:
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
        for childNode in childNodes:

            # Remove hidden
            if removeHidden and cmds.getAttr(childNode + '.v') == 0:
                cmds.delete(childNode)
                continue

            maf.cleanNode( childNode, True, ('mesh'), False, False)
        
        # Remove remaining empty groups
        maf.removeEmptyGroups(node)

        # Export
        shaderFilePath = exportShaders(node, publishFolder, nm.copy(), mode )
        # Update Ramses Metadata (version)
        ram.RamMetaDataManager.setPipeType( shaderFilePath, mode )
        ram.RamMetaDataManager.setVersionFilePath( shaderFilePath, versionFilePath )
        ram.RamMetaDataManager.setVersion( shaderFilePath, version )

    progressDialog.setText("Cleaning...")

    endProcess(tempData, progressDialog)

    progressDialog.hide()