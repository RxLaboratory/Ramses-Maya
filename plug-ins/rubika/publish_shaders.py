from .utils_shaders import exportShaders
from .utils_nodes import getPublishNodes
from .utils_items import getFileInfo, getPublishFolder
from .ui_publish_shaders import PublishShaderDialog
import dumaf as maf # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import maya.cmds as cmds # pylint: disable=import-error


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

    tempFile = maf.cleanScene()

    # For all nodes in the publish set
    nodes = getPublishNodes()
    if len(nodes) == 0:
        return

    numNodes = len(nodes)
    progressDialog.setMaximum(numNodes + 2)
    progressDialog.setText("Preparing")
    progressDialog.increment()

    # Item info
    fileInfo = getFileInfo( filePath )
    if fileInfo is None:
        return
    version = item.latestVersion( fileInfo['resource'], '', step )
    versionFilePath = item.latestVersionFilePath( fileInfo['resource'], '', step )

    # Publish folder
    publishFolder = getPublishFolder(item, step)
    if publishFolder == '':
        return
    ram.log( "I'm publishing geometry in " + publishFolder )

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
        shaderFilePath = exportShaders(node, mode, publishFolder, fileInfo.copy() )
        # Update Ramses Metadata (version)
        ram.RamMetaDataManager.setVersionFilePath( shaderFilePath, versionFilePath )
        ram.RamMetaDataManager.setVersion( shaderFilePath, version )

        