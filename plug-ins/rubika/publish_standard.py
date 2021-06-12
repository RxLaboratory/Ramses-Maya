import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_items import * # pylint: disable=import-error
from .utils_general import * # pylint: disable=import-error

def publishStandard( item, filePath, step, extension ):
    
    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setMaximum(2)
    progressDialog.setText("Preparing...")
    progressDialog.increment()

    # Clean scene:
    # Remove empty groups from the scene
    maf.removeEmptyGroups()

    # Item info
    fileInfo = getFileInfo( filePath )
    if fileInfo is None:
        progressDialog.hide()
        return
    version = item.latestVersion( fileInfo['resource'], '', step )
    versionFilePath = item.latestVersionFilePath( fileInfo['resource'], '', step )

    # Publish folder
    publishFolder = getPublishFolder(item, step)
    if publishFolder == '':
        progressDialog.hide()
        return
    ram.log( "I'm publishing geometry in " + publishFolder )

    progressDialog.setText( "Publishing..." )
    progressDialog.increment()

    # Copy published scene to publish
    sceneFileInfo = fileInfo.copy()
    sceneFileInfo['extension'] = extension
    # resource
    if sceneFileInfo['resource'] != '':
        sceneFileInfo['resource'] = sceneFileInfo['resource'] + '-Published'
    else:
        sceneFileInfo['resource'] = 'Published'
    # path
    sceneFilePath = ram.RamFileManager.buildPath((
        publishFolder,
        ram.RamFileManager.composeRamsesFileName( sceneFileInfo )
    ))

    # Save
    cmds.file( rename=sceneFilePath )
    cmds.file( save=True, options="v=1;" )
    if extension == 'ma':
        ram.RamMetaDataManager.setPipeType( sceneFilePath, STANDARDA_PIPE_NAME )
    else:
        ram.RamMetaDataManager.setPipeType( sceneFilePath, STANDARDB_PIPE_NAME )
    ram.RamMetaDataManager.setVersionFilePath( sceneFilePath, versionFilePath )
    ram.RamMetaDataManager.setVersion( sceneFilePath, version )

    progressDialog.hide()

    ram.log("I've published the scene.")
    cmds.inViewMessage(  msg="Scene published!", pos='midCenterBot', fade=True )
