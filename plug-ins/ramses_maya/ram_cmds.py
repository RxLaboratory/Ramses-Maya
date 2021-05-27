import sys, os
from datetime import datetime, timedelta

import maya.api.OpenMaya as om # pylint: disable=import-error
import maya.cmds as cmds # pylint: disable=import-error

from .dumaf import getMayaWindow # pylint: disable=import-error,no-name-in-module
from .ui_settings import SettingsDialog # pylint: disable=import-error,no-name-in-module
from .ui_status import StatusDialog # pylint: disable=import-error,no-name-in-module
from .ui_versions import VersionDialog # pylint: disable=import-error,no-name-in-module

import ramses as ram
# Keep the ramses and the settings instances at hand
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

class RamOpenCmd( om.MPxCommand ):
    name = "ramOpen"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamOpenCmd()

    def doIt(self, args):
        ram.log("Command 'open' is not implemented yet!")

class RamSaveCmd( om.MPxCommand ):
    name = "ramSave"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSaveCmd()

    def doIt(self, args):
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

class RamSaveVersionCmd( om.MPxCommand ):
    name = "ramSaveVersion"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSaveVersionCmd()

    def doIt(self, args):
        # The current maya file
        currentFilePath = cmds.file( q=True, sn=True )
        ram.log("Saving file: " + currentFilePath)
        
        # Check if the Daemon is available if Ramses is set to be used "online"
        if not checkDaemon():
            return

        # Get the save path 
        saveFilePath = getSaveFilePath( currentFilePath )
        if saveFilePath == "":
            return

        # Update status
        saveFileName = os.path.basename( saveFilePath )
        saveFileDict = ram.RamFileManager.decomposeRamsesFileName( saveFileName )
        currentStep = saveFileDict['ramStep']
        currentItem = ram.RamItem.fromPath( saveFilePath )
        currentStatus = currentItem.currentStatus( currentStep )
        # Show status dialog
        statusDialog = StatusDialog()
        statusDialog.setOffline(not settings.online)
        if currentStatus is not None:
            statusDialog.setStatus( currentStatus )
        update = statusDialog.exec_()
        if update == 0:
            return
        status = None
        publish = False
        if update == 1:
            status = ram.RamStatus(
                statusDialog.getState(),
                statusDialog.getComment(),
                statusDialog.getCompletionRatio()
            )
            publish = statusDialog.isPublished()

        # Set the save name and save
        cmds.file( rename = saveFilePath )
        cmds.file( save=True, options="v=1;" )
        # Backup / Increment
        state = settings.defaultState
        if status is not None:
            state = status.state
        elif currentStatus is not None:
            state = currentStatus.state

        backupFilePath = ram.RamFileManager.copyToVersion(
            saveFilePath,
            True,
            state.shortName()
            )
        backupFileName = os.path.basename( backupFilePath )
        decomposedFileName = ram.RamFileManager.decomposeRamsesFileName( backupFileName )
        newVersion = decomposedFileName['version']

        # Update status
        if status is not None:
            if settings.online:
                currentItem.setStatus(status, currentStep)
            ramses.updateStatus()

        # Publish
        if publish:
            ram.RamFileManager.copyToPublish( saveFilePath )
            ramses.publish()

        # Alert
        newVersionStr = str( newVersion )
        ram.log( "Incremental save, scene saved! New version is: " + newVersionStr )
        cmds.inViewMessage( msg='Incremental save! New version: <hl>v' + newVersionStr + '</hl>', pos='midCenter', fade=True )

class RamRetrieveVersionCmd( om.MPxCommand ):
    name = "ramRetrieveVersion"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamRetrieveVersionCmd()

    def doIt(self, args):
        # The current maya file
        currentFilePath = cmds.file( q=True, sn=True )

        # Get the save path 
        saveFilePath = getSaveFilePath( currentFilePath )
        if not saveFilePath:
            return

        # Get the version files
        versionFiles = ram.RamFileManager.getVersionFilePaths( saveFilePath )

        if len(versionFiles) == 0:
            cmds.inViewMessage( msg='No other version found.', pos='midBottom', fade=True )
            return

        versionDialog = VersionDialog()
        versionDialog.setVersions( versionFiles )
        if not versionDialog.exec_():
            return
        
        versionFile = ram.RamFileManager.restoreVersionFile( versionDialog.getVersion() )
        # open
        cmds.file(versionFile, open=True)

class RamPublishTemplateCmd( om.MPxCommand ):
    name = "ramPulbishTemplate"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamPublishTemplateCmd()

    def doIt(self, args):
        ram.log("Command 'publish as template' is not implemented yet!")

class RamOpenTemplateCmd( om.MPxCommand ):
    name = "ramOpenTemplate"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamOpenTemplateCmd()

    def doIt(self, args):
        ram.log("Command 'open template' is not implemented yet!")

class RamImportTemplateCmd( om.MPxCommand ):
    name = "ramImportTemplate"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamImportTemplateCmd()

    def doIt(self, args):
        ram.log("Command 'import template' is not implemented yet!")

class RamSettingsCmd( om.MPxCommand ):
    name = "ramSettings"
    settingsDialog = SettingsDialog( getMayaWindow() )

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSettingsCmd()

    def doIt(self, args):
        ram.log("Opening settings...")  
        self.settingsDialog.show()

class RamOpenRamsesCmd( om.MPxCommand ):
    name = "ramOpenRamses"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamOpenRamsesCmd()

    def doIt(self, args):
        ram.log("Opening the Ramses client...")
        ramses.showClient()
        
cmds_classes = (
    RamOpenCmd,
    RamSaveCmd,
    RamSaveVersionCmd,
    RamRetrieveVersionCmd,
    RamPublishTemplateCmd,
    RamOpenTemplateCmd,
    RamImportTemplateCmd,
    RamSettingsCmd,
    RamOpenRamsesCmd,
)

cmds_menuItems = []

def maya_useNewAPI():
    pass
