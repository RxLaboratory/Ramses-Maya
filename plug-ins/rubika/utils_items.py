import ramses as ram # pylint: disable=import-error
import maya.cmds as cmds

def getFileInfo( filePath):
    fileInfo = ram.RamFileManager.decomposeRamsesFilePath( filePath )
    if fileInfo is None:
        ram.log(ram.Log.MalformedName, ram.LogLevel.Fatal)
        cmds.inViewMessage( msg=ram.Log.MalformedName, pos='midCenter', fade=True )
        cmds.error( ram.Log.MalformedName )
        return None
    return fileInfo

def getPublishFolder( item, step):
    publishFolder = item.publishFolderPath( step )
    if publishFolder == '':
        ram.log("I can't find the publish folder for this item, maybe it does not respect the ramses naming scheme or it is out of place.", ram.LogLevel.Fatal)
        cmds.inViewMessage( msg="Can't find the publish folder for this scene, sorry. Check its name and location.", pos='midCenter', fade=True )
        cmds.error( "Can't find publish folder." )
        return ''
    return publishFolder