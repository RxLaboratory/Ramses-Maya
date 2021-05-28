import os
from datetime import datetime, timedelta

import ramses as ram
# Keep the ramses and the settings instances at hand
ramses = ram.Ramses.instance()
settings = ram.RamSettings.instance()

import maya.cmds as cmds # pylint: disable=import-error

def getSaveFilePath( filePath ):
    # Ramses will check if the current file has to be renamed to respect the Ramses Tree and Naming Scheme
    saveFilePath = ram.RamFileManager.getSaveFilePath( filePath )
    if not saveFilePath: # Ramses may return None if the current file name does not respeect the Ramses Naming Scheme
        cmds.warning( ram.Log.MalformedName )
        # Set file to be renamed
        cmds.file( renameToSave = True )
        cmds.inViewMessage( msg='Malformed Ramses file name! <hl>Please save with a correct name first</hl>.', pos='midCenter', fade=True )
        return None

    return saveFilePath

def doIt():
    ram.log("Saving file...")

    # The current maya file
    currentFilePath = cmds.file( q=True, sn=True )
    ram.log("Saving file: " + currentFilePath)
    
    # We don't need the daemon to just save a file
    # if not checkDaemon():
    #     return

    # Get the save path 
    saveFilePath = getSaveFilePath( currentFilePath )
    if not saveFilePath:
        return

    # If the current Maya file is inside a preview/publish/version subfolder, we're going to increment
    # to be sure to not lose the previous working file.
    increment = False
    if ram.RamFileManager.inReservedFolder( currentFilePath ):
        increment = True
        cmds.warning( "Incremented and Saved as " + saveFilePath )

    # If the timeout has expired, we're also incrementing
    prevVersion = ram.RamFileManager.getLatestVersion( saveFilePath, previous=True )
    modified = prevVersion[2]
    now = datetime.today()
    timeout = timedelta(seconds = settings.autoIncrementTimeout * 60 )
    if  timeout < now - modified:
        increment = True

    # Set the save name and save
    cmds.file( rename = saveFilePath )
    cmds.file( save=True, options="v=1;" )
    # Backup / Increment
    backupFilePath = ram.RamFileManager.copyToVersion( saveFilePath, increment=increment )
    backupFileName = os.path.basename( backupFilePath )
    decomposedFileName = ram.RamFileManager.decomposeRamsesFileName( backupFileName )
    newVersion = str( decomposedFileName['version'] )
    ram.log( "Scene saved! Current version is: " + newVersion )
    cmds.inViewMessage( msg='Scene saved! <hl>v' + newVersion + '</hl>', pos='midCenter', fade=True )

doIt()