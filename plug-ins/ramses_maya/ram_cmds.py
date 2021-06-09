import os, re
from datetime import datetime, timedelta

import maya.api.OpenMaya as om # pylint: disable=import-error
import maya.cmds as cmds # pylint: disable=import-error

from dumaf import getMayaWindow, getCreateGroup, hasParent
from .ui_settings import SettingsDialog # pylint: disable=import-error,no-name-in-module
from .ui_status import StatusDialog # pylint: disable=import-error,no-name-in-module
from .ui_versions import VersionDialog # pylint: disable=import-error,no-name-in-module
from .ui_publishtemplate import PublishTemplateDialog # pylint: disable=import-error,no-name-in-module
from .ui_comment import CommentDialog # pylint: disable=import-error,no-name-in-module
from .ui_import import ImportDialog # pylint: disable=import-error,no-name-in-module
from .ui_saveas import SaveAsDialog # pylint: disable=import-error,no-name-in-module

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
        return ''

    return saveFilePath

def getCurrentProject( filePath ):
    fileInfo = ram.RamFileManager.decomposeRamsesFilePath(filePath)
    # Set the project and step
    project = None
    if fileInfo is not None:
        project = ramses.project( fileInfo['project'] )
        ramses.setCurrentProject( project )
    # Try to get the current project
    if project is None:
        project = ramses.currentProject()

    return project

def getStep( filePath ):
    project = getCurrentProject( filePath )
    fileInfo = ram.RamFileManager.decomposeRamsesFilePath(filePath)
    if fileInfo is not None and project is not None:
        return project.step( fileInfo['step'] )

class RamSaveCmd( om.MPxCommand ):
    name = "ramSave"
    syntax = om.MSyntax()
    syntax.addFlag('-c', "-comment", om.MSyntax.kString )
    syntax.addFlag('-sc', "-setComment", om.MSyntax.kBoolean )

    def __init__(self):
        om.MPxCommand.__init__(self)
        self.newComment = ''
        self.setComment = False

    @staticmethod
    def createCommand():
        return RamSaveCmd()

    @staticmethod
    def createSyntax():
        return RamSaveCmd.syntax

    def parseArgs(self, args, saveFilePath):
        parser = om.MArgParser( RamSaveCmd.syntax, args)
        useDialog = False
        try:
            self.setComment = parser.flagArgumentBool('-sc', 0)
        except:
            self.setComment = False

        try:
            self.newComment = parser.flagArgumentString('-c', 0)
        except:
            useDialog = True

        # Get comment
        if self.setComment and useDialog:
            # Get current comment
            latestVersionFile = ram.RamFileManager.getLatestVersionFilePath( saveFilePath )
            currentComment = ram.RamMetaDataManager.getComment( latestVersionFile )
            # Ask for comment
            commentDialog = CommentDialog(getMayaWindow())
            commentDialog.setComment( currentComment )
            if not commentDialog.exec_():
                return False
            self.newComment = commentDialog.getComment()
        
        return True

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

        # Check if we need to set a comment
        if not self.parseArgs(args,saveFilePath):
            return

        # If the current Maya file is inside a preview/publish/version subfolder, we're going to increment
        # to be sure to not lose the previous working file.
        increment = False
        incrementReason = ''
        if ram.RamFileManager.inReservedFolder( currentFilePath ):
            increment = True
            incrementReason = "misplaced."
            cmds.warning( "Incremented and Saved as " + saveFilePath )

        # If the timeout has expired, we're also incrementing
        prevVersion = ram.RamFileManager.getLatestVersion( saveFilePath, previous=True )
        modified = prevVersion[2]
        now = datetime.today()
        timeout = timedelta(seconds = settings.autoIncrementTimeout * 60 )
        if  timeout < now - modified:
            incrementReason = "too old."
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

        # Write the comment
        if self.setComment:
            ram.RamMetaDataManager.setComment( backupFilePath, self.newComment )
            ram.log( "I've added this comment for you: " + self.newComment )
        elif increment:
            ram.RamMetaDataManager.setComment( backupFilePath, 'Auto-Increment because the previous version was ' + incrementReason )
            ram.log("I've incremented the version for you because it was " + incrementReason)

class RamSaveAsCmd( om.MPxCommand ): #TODO Set offline if offline and implement browse button
    name = "ramSaveAs"
    syntax = om.MSyntax()

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSaveAsCmd()

    @staticmethod
    def createSyntax():
        return RamSaveAsCmd.syntax

    def doIt(self, args):
        # Get current info
        currentFilePath = cmds.file( q=True, sn=True )

        # Info
        project = getCurrentProject( currentFilePath )
        step = getStep( currentFilePath )
        item = ram.RamItem.fromPath( currentFilePath )

        saveAsDialog = SaveAsDialog(getMayaWindow())
        if project is not None:
            saveAsDialog.setProject( project )
        if item is not None:
            saveAsDialog.setItem(item)
        if step is not None:
            saveAsDialog.setStep( step )
        if not saveAsDialog.exec_():
            return

        filePath = saveAsDialog.getFilePath()
        if filePath == '':
            return
        # Create folder
        folder = os.path.dirname(filePath)
        fileName = os.path.basename(filePath)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        # Check if file exists
        if os.path.isfile( filePath ):
            result = cmds.confirmDialog( message="The corresponding file already exits. Do you want to overwrite it?", button=("Overwrite and Save", "Cancel") )
            if result == 'Cancel':
                return

        cmds.file(rename = filePath )
        cmds.file( save=True, options="v=1;", f=True )

        ram.log( "Scene saved as: " + filePath )
        cmds.inViewMessage( msg='Scene saved as: <hl>' + fileName + '</hl>.', pos='midCenter', fade=True )

class RamSaveVersionCmd( om.MPxCommand ):
    name = "ramSaveVersion"
    syntax = om.MSyntax()
    syntax.addFlag('-us', "-updateStatus", om.MSyntax.kBoolean )
    syntax.addFlag('-p', "-publish", om.MSyntax.kBoolean )

    # Defaults
    updateSatus = True
    publish = False

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSaveVersionCmd()

    @staticmethod
    def createSyntax():
        return RamSaveVersionCmd.syntax

    def parseArgs(self, args):
        parser = om.MArgParser( RamSaveVersionCmd.syntax, args)

        try:
            self.updateSatus = parser.flagArgumentBool('-us', 0)
        except:
            self.updateSatus = True

        try:
            self.publish = parser.flagArgumentBool('-p', 0)
        except:
            self.publish = False

    def doIt(self, args):
        # The current maya file
        currentFilePath = cmds.file( q=True, sn=True )
        ram.log("Saving file: " + currentFilePath)
        
        # Check if the Daemon is available if Ramses is set to be used "online"
        if not checkDaemon():
            return

        # Get the save path 
        saveFilePath = getSaveFilePath( currentFilePath )
        if saveFilePath == '':
            return

        self.parseArgs(args)

        # Update status
        saveFileName = os.path.basename( saveFilePath )
        saveFileDict = ram.RamFileManager.decomposeRamsesFileName( saveFileName )
        currentStep = saveFileDict['step']
        currentItem = ram.RamItem.fromPath( saveFilePath )
        if currentItem is None:
            cmds.warning( ram.Log.NotAnItem )
            cmds.inViewMessage( msg='Invalid item, <hl>this does not seem to be a valid Ramses Item</hl>', pos='midCenter', fade=True )
        currentStatus = currentItem.currentStatus( currentStep )
        status = None

        if self.updateSatus:
            # Show status dialog
            statusDialog = StatusDialog(getMayaWindow())
            statusDialog.setOffline(not settings.online)
            statusDialog.setPublish( self.publish )
            if currentStatus is not None:
                statusDialog.setStatus( currentStatus )
            update = statusDialog.exec_()
            if update == 0:
                return
            if update == 1:
                status = ram.RamStatus(
                    statusDialog.getState(),
                    statusDialog.getComment(),
                    statusDialog.getCompletionRatio()
                )
                self.publish = statusDialog.isPublished()

        # Set the save name and save
        cmds.file( rename = saveFilePath )
        cmds.file( save=True, options="v=1;" )
        # Backup / Increment
        state = ramses.defaultState
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
            # We need the RamStep, get it from the project
            project = currentItem.project()
            step = None
            if project is not None:
                step = project.step(currentStep)
                ramses.setCurrentProject(project)
                
            if step is not None:
                currentItem.setStatus(status, step)
                ramses.updateStatus(currentItem, status, step)

        # Alert
        newVersionStr = str( newVersion )
        ram.log( "Incremental save, scene saved! New version is: " + newVersionStr )
        cmds.inViewMessage( msg='Incremental save! New version: <hl>v' + newVersionStr + '</hl>', pos='midCenterBot', fade=True )

        # Publish
        if self.publish:
            publishedFilePath = ram.RamFileManager.copyToPublish( saveFilePath )
            ram.RamMetaDataManager.setVersion( publishedFilePath, newVersion )
            ram.RamMetaDataManager.setVersionFilePath( publishedFilePath, backupFilePath )
            # We need the RamStep, get it from the project
            project = currentItem.project()
            step = None
            if project is not None:
                step = project.step(currentStep)
                ramses.setCurrentProject(project)
            if step is not None:
                ramses.publish( currentItem, saveFilePath, step)

class RamRetrieveVersionCmd( om.MPxCommand ):
    name = "ramRetrieveVersion"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamRetrieveVersionCmd()

    @staticmethod
    def createSyntax():
        syntaxCreator = om.MSyntax()
        return syntaxCreator

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

        versionDialog = VersionDialog(getMayaWindow())
        versionDialog.setVersions( versionFiles )
        if not versionDialog.exec_():
            return
        
        versionFile = ram.RamFileManager.restoreVersionFile( versionDialog.getVersion() )
        # open
        cmds.file(versionFile, open=True)

class RamPublishTemplateCmd( om.MPxCommand ):
    name = "ramPublishTemplate"
    syntax = om.MSyntax()

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamPublishTemplateCmd()

    @staticmethod
    def createSyntax():
        return RamPublishTemplateCmd.syntax

    def doIt(self, args):
        ram.log("Publishing template...")

        # Check if the Daemon is available if Ramses is set to be used "online"
        if not checkDaemon():
            return

        # Get info from the current file
        currentFilePath = cmds.file( q=True, sn=True )

        # Prepare the dialog
        publishDialog = PublishTemplateDialog(getMayaWindow())
        if not settings.online:
            publishDialog.setOffline()

        # Set the project and step
        project = getCurrentProject( currentFilePath )
        step = getStep( currentFilePath )
        # Set
        if project is not None:
            publishDialog.setProject( project )
        if step is not None:
            publishDialog.setStep( step )
        
        if publishDialog.exec_():
            # save as template
            saveFolder = publishDialog.getFolder()
            saveName = publishDialog.getFile()
            if saveFolder == '':
                return
            if not os.path.isdir( saveFolder ):
                os.makedirs(saveFolder)
            saveFilePath = ram.RamFileManager.buildPath((
                saveFolder,
                saveName
            ))
            # save as
            cmds.file( rename = saveFilePath )
            cmds.file( save=True, options="v=1;" )
            # Message
            cmds.inViewMessage( msg='Template published as: <hl>' + saveName + '</hl> in ' + saveFolder , pos='midCenter', fade=True )
            ram.log('Template published as: ' + saveName + ' in ' + saveFolder)

class RamOpenCmd( om.MPxCommand ):
    name = "ramOpen"
    syntax = om.MSyntax()

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamOpenCmd()

    @staticmethod
    def createSyntax():
        return RamOpenCmd.syntax

    def doIt(self, args):
        # Check if the Daemon is available if Ramses is set to be used "online"
        if not checkDaemon():
            return

        # Let's show the dialog
        importDialog = ImportDialog(getMayaWindow())
        # Get some info from current scene
        currentFilePath = cmds.file( q=True, sn=True )
        if currentFilePath != '':
            fileInfo = ram.RamFileManager.decomposeRamsesFilePath( currentFilePath )
            if fileInfo is not None:
                project = ramses.project( fileInfo['project'] )
                ramses.setCurrentProject(project)
                importDialog.setProject( project )
        else:
            # Try to get project from ramses
            project = ramses.currentProject()
            if project is not None:
                importDialog.setProject( project )
        result = importDialog.exec_()

        if result == 1: # open
            # If the current file needs to be saved
            if cmds.file(q=True, modified=True):
                sceneName = os.path.basename(currentFilePath)
                if sceneName == '':
                    sceneName = 'untitled scene'
                result = cmds.confirmDialog( message="Save changes to " + sceneName + "?", button=("Save", "Don't Save", "Cancel") )
                if result == 'Cancel':
                    return
                if result == 'Save':
                    cmds.file( save=True, options="v=1;" )
            # Get the file, check if it's a version
            file = importDialog.getFile()
            if ram.RamFileManager.inVersionsFolder( file ):
                file = ram.RamFileManager.restoreVersionFile( file )
            # Open
            cmds.file(file, open=True, force=True)
        elif result == 2: # import
            # Get Data
            item = importDialog.getItem()
            step = importDialog.getStep()
            filePaths = importDialog.getFiles()
            itemShortName = item.shortName()
            resource = importDialog.getResource()

            # Let's import only if there's no user-defined import scripts
            if len( ramses.importScripts ) > 0:
                ramses.importItem(
                    item,
                    filePaths,
                    step                
                )
                return

            for filePath in filePaths:

                # If file path is empty, let's import the default
                if filePath == "":
                    publishFolder = item.publishFolderPath( step )
                    publishFileName = ram.RamFileManager.buildRamsesFileName(
                        item.projectShortName(),
                        step.shortName(),
                        '',
                        item.itemType(),
                        item.shortName()
                    )
                    filePath = ram.RamFileManager.buildPath((
                        publishFolder,
                        publishFileName
                    ))
                    testFilePath = filePath + '.ma'
                    if not os.path.isfile(testFilePath):
                        testFilePath = filePath + '.mb'
                        if not os.path.isfile(testFilePath):
                            ram.log("Sorry, I can't find anything to import...")
                            return
                    filePath = testFilePath

                # We're going to import in a group
                groupName = ''

                # Prepare names
                # Check if the short name is not made only of numbers
                regex = re.compile('^\\d+$')
                # If it's an asset, let's get the asset group
                itemType = item.itemType()
                if itemType == ram.ItemType.ASSET:
                    groupName = 'RamASSETS_' + item.group()
                    if re.match(regex, itemShortName):
                        itemShortName = ram.ItemType.ASSET + itemShortName
                # If it's a shot, let's store in the shots group
                elif itemType == ram.ItemType.SHOT:
                    groupName = 'RamSHOTS'
                    if re.match(regex, itemShortName):
                        itemShortName = ram.ItemType.SHOT + itemShortName
                # If it's a general item, store in a group named after the step
                else:
                    itemShortName = resource
                    groupName = 'RamITEMS'
                    if re.match(regex, itemShortName):
                        itemShortName = ram.ItemType.GENERAL + itemShortName

                groupName = getCreateGroup(groupName)
                # Import the file
                newNodes = cmds.file(filePath,i=True,ignoreVersion=True,mergeNamespacesOnClash=True,returnNewNodes=True,ns=itemShortName)
                # Add a group for the imported asset
                itemGroupName = getCreateGroup( itemShortName, groupName)
                for node in newNodes:
                    # When parenting the root, children won't exist anymore
                    if not cmds.objExists(node):
                        continue
                    # only the root transform nodes
                    if cmds.nodeType(node) == 'transform' and not hasParent(node):
                        cmds.parent(node, itemGroupName)

class RamSettingsCmd( om.MPxCommand ):
    name = "ramSettings"

    settingsDialog = SettingsDialog( getMayaWindow() )

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSettingsCmd()

    @staticmethod
    def createSyntax():
        syntaxCreator = om.MSyntax()
        return syntaxCreator

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

    @staticmethod
    def createSyntax():
        syntaxCreator = om.MSyntax()
        return syntaxCreator

    def doIt(self, args):
        ram.log("Opening the Ramses client...")
        ramses.showClient()
        
cmds_classes = (
    RamSaveCmd,
    RamSaveAsCmd,
    RamSaveVersionCmd,
    RamRetrieveVersionCmd,
    RamPublishTemplateCmd,
    RamOpenCmd,
    RamSettingsCmd,
    RamOpenRamsesCmd,
)

cmds_menuItems = []

def maya_useNewAPI():
    pass
