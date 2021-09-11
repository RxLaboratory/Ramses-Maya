# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_items import * # pylint: disable=import-error
from .utils_general import * # pylint: disable=import-error

def publishStandard( item, step, publishFileInfo, pipeFiles ):
    
    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setMaximum(2)
    progressDialog.setText("Preparing...")
    progressDialog.increment()

    # Clean scene:
    # Remove empty groups from the scene
    maf.Node.removeEmptyGroups()

    ram.log( "I'm publishing geometry in " + os.path.dirname( publishFileInfo.filePath() ) )

    progressDialog.setText( "Publishing..." )
    progressDialog.increment()

    extension = getExtension( step, OTHER_STEP, STANDARD_PIPE_FILE, pipeFiles, ['ma', 'mb'], 'mb' )

    # Copy published scene to publish
    sceneInfo = publishFileInfo.copy()
    sceneInfo.version = -1
    sceneInfo.state = ''
    sceneInfo.extension = extension
    # resource
    if sceneInfo.resource != '':
        sceneInfo.resource = sceneInfo.resource + '-' + STANDARD_PIPE_NAME
    else:
        sceneInfo.resource = STANDARD_PIPE_NAME
    # path
    sceneFilePath = sceneInfo.filePath()

    # Save
    prevScene = cmds.file( q=True, sn=True )
    cmds.file( rename=sceneFilePath )
    cmds.file( save=True, options="v=1;" )
    ram.RamMetaDataManager.setPipeType( sceneFilePath, STANDARD_PIPE_NAME )
    ram.RamMetaDataManager.setVersion( sceneFilePath, publishFileInfo.version )
    ram.RamMetaDataManager.setState( sceneFilePath, publishFileInfo.state )
    ram.RamMetaDataManager.setResource( sceneFilePath, publishFileInfo.resource )
    # Reopen
    cmds.file(prevScene,o=True,f=True)

    progressDialog.hide()

    ram.log("I've published the scene.")
    cmds.inViewMessage(  msg="Scene published!", pos='midCenterBot', fade=True )
