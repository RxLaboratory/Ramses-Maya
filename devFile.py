import sys
sys.path.append(
    'D:/DEV_SRC/RxOT/Ramses/Ramses-Py'
)

import maya.cmds as cmds
import ramses as ram

ramses = ram.Ramses.instance()
settings = ram.RamSettings.instance()

def checkDaemon():
    """Checks if the Daemon is available (if the settings tell we have to work with it)"""
    if settings.online:
        if not ramses.connect():
            cmds.confirmDialog(
                title="No User",
                message="You must log in Ramses first!",
                button=["OK"],
                icon="warning"
                )
            ramses.showClient()
            cmds.error( "User not available: You must log in Ramses first!" )
            return False

    return True

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

    
def ramSaveIncremental():
    # The current maya file
    currentFilePath = cmds.file( q=True, sn=True )
    ram.log("Saving file: " + currentFilePath)
       
    # Check if the Daemon is available if Ramses is set to be used "online"
    if not checkDaemon():
        return

    # Get the save path 
    saveFilePath = getSaveFilePath( currentFilePath )
    if not saveFilePath:
        return

    # Set the save name and save
    cmds.file( rename = saveFilePath )
    cmds.file( save=True, options="v=1;" )
    # Backup / Increment
    backupFilePath = ram.RamFileManager.copyToVersion( saveFilePath, increment=True )
    backupFileName = os.path.basename( backupFilePath )
    decomposedFileName = ram.RamFileManager.decomposeRamsesFileName( backupFileName )
    newVersion = str( decomposedFileName['version'] )
    ram.log( "Incremental save, scene saved! New version is: " + newVersion )
    cmds.inViewMessage( msg='Incremental save! New version: <hl>v' + newVersion + '</hl>', pos='midCenter', fade=True )
    
ramSaveIncremental()