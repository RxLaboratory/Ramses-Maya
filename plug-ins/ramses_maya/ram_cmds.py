# -*- coding: utf-8 -*-
"""Maya commands"""

import os, re, platform, subprocess, tempfile, shutil
from datetime import datetime, timedelta

import maya.api.OpenMaya as om # pylint: disable=import-error
import maya.cmds as cmds # pylint: disable=import-error
import maya.mel as mel # pylint: disable=import-error

import dumaf as maf

from .ui_settings import SettingsDialog # pylint: disable=import-error,no-name-in-module
from .ui_status import StatusDialog # pylint: disable=import-error,no-name-in-module
from .ui_versions import VersionDialog # pylint: disable=import-error,no-name-in-module
from .ui_publishtemplate import PublishTemplateDialog # pylint: disable=import-error,no-name-in-module
from .ui_comment import CommentDialog # pylint: disable=import-error,no-name-in-module
from .ui_import import ImportDialog # pylint: disable=import-error,no-name-in-module
from .ui_saveas import SaveAsDialog # pylint: disable=import-error,no-name-in-module
from .ui_preview import PreviewDialog # pylint: disable=import-error,no-name-in-module

import ramses as ram
# Keep the ramses and the SETTINGS instances at hand
RAMSES = ram.Ramses.instance()
SETTINGS = ram.RamSettings.instance()

def checkDaemon():
    """Checks if the Daemon is available (if the SETTINGS tell we have to work with it)"""
    if SETTINGS.online:
        if not RAMSES.connect():
            cmds.confirmDialog(
                title="No User",
                message="You must log in Ramses first!",
                button=["OK"],
                icon="warning"
                )
            RAMSES.showClient()
            cmds.error( "User not available: You must log in Ramses first!" )
            return False

    return True

def getSaveFilePath( filePath ):
    # Ramses will check if the current file has to be renamed to respect the Ramses Tree and Naming Scheme
    saveFilePath = ram.RamFileManager.getSaveFilePath( filePath )
    if saveFilePath == '': # Ramses may return None if the current file name does not respeect the Ramses Naming Scheme
        cmds.warning( ram.Log.MalformedName )
        cmds.inViewMessage( msg='Malformed Ramses file name! <hl>Please save with a correct name first</hl>.', pos='topCenter', fade=True )
        if not cmds.ramSaveAs():
            return ''
        newFilePath = cmds.file( q=True, sn=True )
        saveFilePath = ram.RamFileManager.getSaveFilePath( newFilePath )
    if saveFilePath == '':
        cmds.warning( ram.Log.MalformedName )
        # Set file to be renamed
        # cmds.file( renameToSave = True )
        cmds.inViewMessage( msg='Some Problem occured, <hl>the file name is still invalid for Ramses</hl>, sorry.', pos='midCenter', fade=True )
        return ''

    return saveFilePath

def getCurrentProject( filePath ):
    nm = ram.RamFileInfo()
    nm.setFilePath( filePath )
    # Set the project and step
    project = None
    if nm.project != '':
        project = RAMSES.project( nm.project )
        RAMSES.setCurrentProject( project )
    # Try to get the current project
    if project is None:
        project = RAMSES.currentProject()

    return project

def getStep( filePath ):
    project = getCurrentProject( filePath )
    nm = ram.RamFileInfo()
    nm.setFilePath( filePath )
    if nm.step != '':
        return project.step( nm.step )
    return None

def getNameManager( filePath ):
    nm = ram.RamFileInfo()
    nm.setFilePath( filePath )
    if nm.project == '':
        ram.log(ram.Log.MalformedName, ram.LogLevel.Fatal)
        cmds.inViewMessage( msg=ram.Log.MalformedName, pos='midCenter', fade=True )
        cmds.error( ram.Log.MalformedName )
        return None
    return nm

def getPreviewFolder( item, step):
    previewFolder = item.previewFolderPath( step )
    if previewFolder == '':
        ram.log("I can't find the publish folder for this item, maybe it does not respect the ramses naming scheme or it is out of place.", ram.LogLevel.Fatal)
        cmds.inViewMessage( msg="Can't find the publish folder for this scene, sorry. Check its name and location.", pos='midCenter', fade=True )
        cmds.error( "Can't find publish folder." )
        return ''
    return previewFolder

def getTempDir():
    """Creates and returns a tempdir. For some reason, sometimes the user folder is incorrect in TEMP on windows"""
    tempDir = tempfile.mkdtemp()
    if platform.system() == 'Windows':
        userDir = os.getenv('USERPROFILE')
        tempDir = userDir + '/AppData/Local/Temp/' + os.path.basename(tempDir)
    return tempDir

def createPlayblast(filePath, size):

    # Warning, That's for win only ! Needs work on MAC/Linux
    # TODO MAC: open playblast at the end
    # TODO MAC/LINUX: video (audio) playblast format must not be avi
    # TODO MAC/LINUX: call to ffmpeg without .exe
    if platform.system() != 'Windows':
        return

    # Get bin dir
    ramsesFoler = cmds.getModulePath(moduleName='Ramses')
    ffmpegFile = ramsesFoler + '/bin/ffmpeg.exe'
    ffplayFile = ramsesFoler + '/bin/ffplay.exe'

    # Get a temp dir for rendering the playblast
    tempDir = getTempDir()
    # The tempDir may not exist
    if not os.path.isdir(tempDir):
        os.makedirs(tempDir)
    imageFile = tempDir + '/' + 'blast'
    
    # Create jpg frame sequence
    w = cmds.getAttr("defaultResolution.width") * size
    h = cmds.getAttr("defaultResolution.height") * size
    w = w - w % 4
    h = h - h % 4
    imageFile = cmds.playblast( filename=imageFile,
        format='image',
        clearCache=True,
        framePadding= 5,
        viewer=False,
        showOrnaments=True,
        percent=100,
        compression="jpg",
        quality=50, 
        width = w,
        height = h )

    # if there's sound, create a sound file
    soundFile = ''
    sounds = cmds.ls(type='audio')
    # If there are sounds in the scene
    if sounds:
        timeCtrl = mel.eval('$tmpVar=$gPlayBackSlider')
        # And sounds are used by the timeline
        if cmds.timeControl(timeCtrl, displaySound=True, query=True):
            soundFile = tempDir + '/' + 'blast.avi'
            soundFile = cmds.playblast(filename=soundFile, format='avi', clearCache=True, useTraxSounds=True, framePadding= 5, viewer=False, showOrnaments=False, percent=10,compression="none", quality=10)

    # Get framerate
    framerate = mel.eval('float $fps = `currentTimeUnitToFPS`') # It's not in cmds!!

    # Transcode using ffmpeg
    ffmpegArgs = [
        ffmpegFile,
        '-loglevel', 'error', # limit output to errors
        '-y', # overwrite
        '-start_number', str(cmds.playbackOptions(q=True,minTime=True)),
        '-framerate', str(framerate),
        '-i', imageFile.replace('####', "%5d"), # Image file
    ]
    if soundFile != '':
        ffmpegArgs = ffmpegArgs + [
            '-i', soundFile,
            '-map', '0:0', # map video to video
            '-map', '1:1', # map audio to audio
            '-b:a', '131072', # "Bad" quality
        ]
    ffmpegArgs = ffmpegArgs + [
        '-f', 'mp4', # Codec
        '-c:v', 'h264', # Codec
        '-level', '3.0', # Compatibility
        '-crf', '25', # "Bad" quality
        '-preset', 'ultrafast', # We're in a hurry to playblast!
        '-tune', 'fastdecode', # It needs to be easy to play
        '-profile:v', 'baseline', # Compatibility
        '-x264opts', 'b_pyramid=0', # Needed to decoded in Adobe Apps
        '-pix_fmt', 'yuv420p', # Because ffmpeg does 422 by default, which causes compatibility issues
        '-intra', # Intra frame for frame by frame playback
        filePath # Output file
    ]

    #ram.log('FFmpeg args: ' + ' | '.join(ffmpegArgs), ram.LogLevel.Debug)

    ffmpegProcess = subprocess.Popen(ffmpegArgs,shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE) # Launch!

    output = ffmpegProcess.communicate()
    #ram.log('FFmpeg output: ' + str(output[1]), ram.LogLevel.Debug)

    # Remove temp files
    shutil.rmtree(tempDir)
    subprocess.Popen([ffplayFile, '-seek_interval', '0.1', filePath])
    return
    # Open playblast
    if platform.system() == "Windows":
        os.startfile(filePath)
    elif platform.system() == "Linux":
        subprocess.call(["xdg-open", filePath])

def createThumbnail(filePath):
    cmds.refresh(cv=True, fn = filePath)

class RamSaveCmd( om.MPxCommand ):
    name = "ramSave"
    
    def __init__(self):
        om.MPxCommand.__init__(self)
        self.newComment = ''
        self.setComment = False

    @staticmethod
    def createCommand():
        return RamSaveCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        syntax.addFlag('-c', "-comment", om.MSyntax.kString )
        syntax.addFlag('-sc', "-setComment", om.MSyntax.kBoolean )
        return syntax

    def parseArgs(self, args, saveFilePath):
        parser = om.MArgParser( self.syntax(), args)
        useDialog = False
        if parser.isFlagSet( '-sc' ):
            self.setComment = parser.flagArgumentBool('-sc', 0)
        else:
            self.setComment = False

        if parser.isFlagSet( '-c' ):
            self.newComment = parser.flagArgumentString('-c', 0)
        else:
            useDialog = True

        # Get comment
        if self.setComment and useDialog:
            # Get current comment
            latestVersionFile = ram.RamFileManager.getLatestVersionFilePath( saveFilePath )
            currentComment = ram.RamMetaDataManager.getComment( latestVersionFile )
            # Ask for comment
            commentDialog = CommentDialog(maf.UI.getMayaWindow())
            commentDialog.setComment( currentComment )
            if not commentDialog.exec_():
                return False
            self.newComment = commentDialog.getComment()
        
        return True

    def doIt(self, args):
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        ram.log("Saving file...")

        # The current maya file
        currentFilePath = cmds.file( q=True, sn=True )
        ram.log("Saving file: " + currentFilePath)

        # We don't need the daemon to just save a file
        # if not checkDaemon():
        #     return

        # Get the save path 
        saveFilePath = getSaveFilePath( currentFilePath )
        if saveFilePath == '':
            return

        # Parse arguments
        if not self.parseArgs(args,saveFilePath):
            return

        increment = False
        incrementReason = ''
        # It it's a restored version, we need to increment
        nm = ram.RamFileInfo()
        nm.setFilePath( currentFilePath )
        if nm.isRestoredVersion:
            increment = True
            incrementReason = "we're restoring the older version " + str(nm.restoredVersion) + "."
            cmds.warning( "Incremented and Saved as " + saveFilePath )

        # If the current Maya file is inside a preview/publish/version subfolder, we're going to increment
        # to be sure to not lose the previous working file.
        
        if ram.RamFileManager.inReservedFolder( currentFilePath ) and not increment:
            increment = True
            incrementReason = "the file was misplaced."
            cmds.warning( "Incremented and Saved as " + saveFilePath )

        # If the timeout has expired, we're also incrementing
        prevVersionInfo = ram.RamFileManager.getLatestVersionInfo( saveFilePath, previous=True )
        modified = prevVersionInfo.date
        now = datetime.today()
        timeout = timedelta(seconds = SETTINGS.autoIncrementTimeout * 60 )
        if  timeout < now - modified and not increment:
            incrementReason = "the file was too old."
            increment = True

        # Set the save name and save
        cmds.file( rename = saveFilePath )
        cmds.file( save=True, options="v=1;" )
        # Backup / Increment
        backupFilePath = ram.RamFileManager.copyToVersion( saveFilePath, increment=increment )
        backupFileName = os.path.basename( backupFilePath )
        nm = ram.RamFileInfo()
        nm.setFileName( backupFileName )
        newVersion = str( nm.version )
        ram.log( "Scene saved! Current version is: " + newVersion )
        cmds.inViewMessage( msg='Scene saved! <hl>v' + newVersion + '</hl>', pos='midCenter', fade=True )

        # Write the comment
        if self.setComment:
            ram.RamMetaDataManager.setComment( backupFilePath, self.newComment )
            ram.log( "I've added this comment for you: " + self.newComment )
        elif increment:
            ram.RamMetaDataManager.setComment( backupFilePath, 'Auto-Increment because ' + incrementReason )
            ram.log("I've incremented the version for you because it was " + incrementReason)

class RamSaveAsCmd( om.MPxCommand ): #TODO Set offline if offline and implement browse button
    name = "ramSaveAs"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSaveAsCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        return syntax

    def doIt(self, args):
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):

        # We need the daemon
        if not checkDaemon():
            return

        # Get current info
        currentFilePath = cmds.file( q=True, sn=True )

        # Info
        project = getCurrentProject( currentFilePath )
        step = getStep( currentFilePath )
        item = ram.RamItem.fromPath( currentFilePath )

        saveAsDialog = SaveAsDialog(maf.UI.getMayaWindow())
        if project is not None:
            saveAsDialog.setProject( project )
        if step is not None:
            saveAsDialog.setStep( step )
        if item is not None:
            saveAsDialog.setItem(item)
            
        if not saveAsDialog.exec_():
            self.setResult( False )
            return

        filePath = saveAsDialog.getFilePath()
        extension = saveAsDialog.getExtension()
        if filePath == '':
            self.setResult( False )
            return
        # Create folder
        folder = os.path.dirname(filePath)
        fileName = os.path.basename(filePath)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        # Check if file exists
        if os.path.isfile( filePath ):
            # Backup
            backupFilePath = ram.RamFileManager.copyToVersion( filePath, increment=True )
            # Be kind, set a comment
            ram.RamMetaDataManager.setComment( backupFilePath, "Overwritten by an external file." )
            ram.log( 'I\'ve added this comment for you: "Overwritten by an external file."' )

        mayaType = 'mayaBinary'
        if extension == 'ma':
            mayaType = 'mayaAscii'
        cmds.file(rename = filePath )
        cmds.file( save=True, options="v=1;", f=True, typ=mayaType )

        # Create the first version ( or increment existing )
        ram.RamFileManager.copyToVersion( filePath, increment=True )

        ram.log( "Scene saved as: " + filePath )
        cmds.inViewMessage( msg='Scene saved as: <hl>' + fileName + '</hl>.', pos='midCenter', fade=True )

        self.setResult( True )

class RamSaveVersionCmd( om.MPxCommand ):
    name = "ramSaveVersion"

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
        syntax = om.MSyntax()
        syntax.addFlag('-us', "-updateStatus", om.MSyntax.kBoolean )
        syntax.addFlag('-p', "-publish", om.MSyntax.kBoolean )
        syntax.addFlag('-pv', "-preview", om.MSyntax.kBoolean )
        return syntax

    def parseArgs(self, args):
        parser = om.MArgParser( self.syntax(), args)

        if parser.isFlagSet( '-us' ):
            self.updateSatus = parser.flagArgumentBool('-us', 0)
        else:
            self.updateSatus = True

        if parser.isFlagSet( '-p' ):
            self.publish = parser.flagArgumentBool('-p', 0)
        else:
            self.publish = False

        if parser.isFlagSet( '-pv' ):
            self.preview = parser.flagArgumentBool('-pv', 0)
        else:
            self.preview = False

    def doIt(self, args):
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
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
        nm = ram.RamFileInfo()
        nm.setFileName( saveFileName )
        currentStep = nm.step
        currentItem = ram.RamItem.fromPath( saveFilePath )
        if currentItem is None:
            cmds.warning( ram.Log.NotAnItem )
            cmds.inViewMessage( msg='Invalid item, <hl>this does not seem to be a valid Ramses Item</hl>', pos='midCenter', fade=True )
        currentStatus = currentItem.currentStatus( currentStep )
        status = None

        if self.updateSatus:
            # Show status dialog
            statusDialog = StatusDialog(maf.UI.getMayaWindow())
            if not SETTINGS.online or currentItem.itemType() == ram.ItemType.GENERAL:
                statusDialog.setOffline(True)
            else:
                statusDialog.setOffline(False)
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
                status.published = statusDialog.isPublished()
                self.publish = statusDialog.isPublished()
                self.preview = statusDialog.preview()

        # Set the save name and save
        cmds.file( rename = saveFilePath )
        cmds.file( save=True, options="v=1;" )
        # Backup / Increment
        state = RAMSES.defaultState
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
        nm = ram.RamFileInfo()
        nm.setFileName( backupFileName )
        newVersion = nm.version

        # Update status
        if status is not None:
            status.version = newVersion
            # We need the RamStep, get it from the project
            project = currentItem.project()
            step = None
            if project is not None:
                step = project.step(currentStep)
                RAMSES.setCurrentProject(project)
                
            if step is not None:
                currentItem.setStatus(status, step)
                RAMSES.updateStatus(currentItem, status, step)

        # Alert
        newVersionStr = str( newVersion )
        ram.log( "Incremental save, scene saved! New version is: " + newVersionStr )
        cmds.inViewMessage( msg='Incremental save! New version: <hl>v' + newVersionStr + '</hl>', pos='midCenterBot', fade=True )

        # Publish
        if self.publish:
            publishedFileInfo = ram.RamFileManager.getPublishInfo( saveFilePath )
            # Prepare the file for backup in the published folder
            backupInfo = publishedFileInfo.copy()
            backupInfo.version = -1
            backupInfo.state = ''
            # Save
            publishedFilePath = backupInfo.filePath()
            cmds.file( rename = publishedFilePath )
            cmds.file( save=True, options="v=1;" )
            ram.RamMetaDataManager.appendHistoryDate( publishedFilePath )
            # Reopen initial file
            cmds.file(saveFilePath,o=True,f=True)
            ram.RamMetaDataManager.setVersion( publishedFilePath, newVersion )
            ram.RamMetaDataManager.setVersionFilePath( publishedFilePath, backupFilePath )
            # We need the RamStep, get it from the project
            project = currentItem.project()
            step = None
            if project is not None:
                step = project.step(currentStep)
                RAMSES.setCurrentProject(project)
            if step is not None:
                RAMSES.publish( currentItem, step, publishedFileInfo.copy() )

        if self.preview:
            cmds.ramPreview()

class RamRetrieveVersionCmd( om.MPxCommand ):
    name = "ramRetrieveVersion"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamRetrieveVersionCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        return syntax

    def doIt(self, args):
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
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

        versionDialog = VersionDialog(maf.UI.getMayaWindow())
        versionDialog.setVersions( versionFiles )
        if not versionDialog.exec_():
            return

         # If the current file needs to be saved
        if not maf.Scene.checkSaveState():
            return
        
        versionFile = ram.RamFileManager.restoreVersionFile( versionDialog.getVersion() )
        # We need to wait for the file to be correctly written before opening
        ram.RamFileManager.waitFiles()
        # open
        cmds.file(versionFile, open=True, force=True)

class RamPublishTemplateCmd( om.MPxCommand ):
    name = "ramPublishTemplate"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamPublishTemplateCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        return syntax

    def doIt(self, args):
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        ram.log("Saving as template...")

        # Check if the Daemon is available if Ramses is set to be used "online"
        if not checkDaemon():
            return

        # Get info from the current file
        currentFilePath = cmds.file( q=True, sn=True )

        # Prepare the dialog
        publishDialog = PublishTemplateDialog(maf.UI.getMayaWindow())
        if not SETTINGS.online:
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
            cmds.inViewMessage( msg='Template saved as: <hl>' + saveName + '</hl> in ' + saveFolder , pos='midCenter', fade=True )
            ram.log('Template saved as: ' + saveName + ' in ' + saveFolder)

class RamOpenCmd( om.MPxCommand ):
    """Shows the UI to open, import or replace an item"""
    name = "ramOpen"

    def __init__(self):
        om.MPxCommand.__init__(self)
        self.importMode = False

    @staticmethod
    def createCommand():
        return RamOpenCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        syntax.addFlag('-i', "-import", om.MSyntax.kBoolean )
        syntax.addFlag('-r', "-replace", om.MSyntax.kBoolean )
        return syntax

    def parseArgs(self, args):
        parser = om.MArgParser( self.syntax(), args)
        if parser.isFlagSet( '-i' ):
            self.mode = "import"
        elif parser.isFlagSet( '-r' ):
            self.mode = "replace"
        else:
            self.mode = "open"

    def doIt(self, args):
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        # Check if the Daemon is available if Ramses is set to be used "online"
        if not checkDaemon():
            return

        self.parseArgs(args)

        # Let's show the dialog
        importDialog = ImportDialog(maf.UI.getMayaWindow())
        importDialog.setMode( self.mode )
        # Get some info from current scene
        currentFilePath = cmds.file( q=True, sn=True )
        if currentFilePath != '':
            nm = ram.RamFileInfo()
            nm.setFilePath( currentFilePath )
            if nm.project != '':
                project = RAMSES.project( nm.project )
                if project is not None:
                    RAMSES.setCurrentProject( project )
                    importDialog.setProject( project )
                    importDialog.setType( nm.ramType )
                    importDialog.setItem( nm.shortName )
                    # importDialog.setStep( nm.step )
        else:
            # Try to get project from RAMSES
            project = RAMSES.currentProject()
            if project is not None:
                importDialog.setProject( project )
        result = importDialog.exec_()

        if result == 1: # open
            # If the current file needs to be saved
            if not maf.Scene.checkSaveState():
                return
            # Get the file, check if it's a version
            file = importDialog.getFile()
            if ram.RamFileManager.inVersionsFolder( file ):
                file = ram.RamFileManager.restoreVersionFile( file )
            # Open
            cmds.file(file, open=True, force=True)
        elif result == 2: # import
            # Get Data
            item = importDialog.getItem()
            if item is None:
                return
            step = importDialog.getStep()
            filePaths = importDialog.getFiles()
            itemShortName = item.shortName()
            resource = importDialog.getResource()

            # Let's import only if there's no user-defined import scripts
            if len( RAMSES.importScripts ) > 0:
                RAMSES.importItem(
                    item,
                    filePaths,
                    step                
                )
                return

            for filePath in filePaths:

                # If file path is empty, let's import the default
                if filePath == "":
                    publishFolder = item.publishFolderPath( step )
                    nm = ram.RamFileInfo()
                    nm.project = item.projectShortName()
                    nm.step = step.shortName()
                    nm.ramType = item.itemType()
                    nm.shortName = item.shortName()
                    publishFileName = nm.fileName()
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
                    groupName = 'RamITEMS'
                    if re.match(regex, itemShortName):
                        itemShortName = ram.ItemType.GENERAL + itemShortName

                group = maf.DuMaNode.getCreateGroup(groupName)

                # Import the file
                newNodes = maf.Scene.importFile(filePath, itemShortName)
                
                # Add a group for the imported asset
                itemGroup = maf.DuMaNode.getCreateGroup( itemShortName, group)
                # Parent the imported nodes
                for node in newNodes:
                    # only the root transform nodes
                    if node.isTransform() and not node.hasParent():
                        node.parentTo(itemGroup)
        elif result == 3: # replace
            # Get Data
            item = importDialog.getItem()
            if item is None:
                return
            step = importDialog.getStep()
            filePath = importDialog.getFile()
            itemShortName = item.shortName()
            resource = importDialog.getResource()

            # Let's import only if there's no user-defined import scripts
            if len( RAMSES.replaceScripts ) > 0:
                RAMSES.replaceItem(
                    item,
                    filePath,
                    step
                )
                return

            #TODO Implement default replacement method when the publish/import has been updated

class RamPreviewCmd( om.MPxCommand ):
    name = "ramPreview"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamPreviewCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        return syntax

    def doIt(self, args):
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        currentFilePath = cmds.file( q=True, sn=True )

        # Get the save path 
        saveFilePath = getSaveFilePath( currentFilePath )
        if saveFilePath == '':
            return

        currentItem = ram.RamItem.fromPath( saveFilePath )
        if currentItem is None:
            cmds.warning( ram.Log.NotAnItem )
            cmds.inViewMessage( msg='Invalid item, <hl>this does not seem to be a valid Ramses Item</hl>', pos='midCenter', fade=True )

        nm = ram.RamFileInfo()
        nm.setFilePath( saveFilePath )
        currentStep = nm.step
        
        # Item info
        nm = getNameManager( saveFilePath )
        if nm is None:
            return
        version = currentItem.latestVersion( nm.resource, '', currentStep )
        versionFilePath = currentItem.latestVersionFilePath( nm.resource, '', currentStep )

        # Preview folder
        previewFolder = getPreviewFolder(currentItem, currentStep)
        if previewFolder == '':
            return
        ram.log( "I'm previewing in " + previewFolder )

        # Keep current SETTINGS
        currentAA = cmds.getAttr('hardwareRenderingGlobals.multiSampleEnable')
        currentAO = cmds.getAttr('hardwareRenderingGlobals.ssaoEnable')

        # show UI
        dialog = PreviewDialog( maf.UI.getMayaWindow() )
        result = dialog.exec_()
        if not result:
            return

        # Options
        comment = dialog.comment()
        cam = dialog.camera()
        size = dialog.getSize()

        # Remove all current HUD
        currentHuds = cmds.headsUpDisplay(listHeadsUpDisplays=True)
        if currentHuds:
            for hud in currentHuds:
                cmds.headsUpDisplay(hud, remove=True)
        # Add ours
        # Collect info
        itemName = currentItem.name()
        if itemName == '':
            itemName = currentItem.shortName()
        if currentItem.itemType() == ram.ItemType.SHOT:
            itemName = 'Shot: ' + itemName 
        elif currentItem.itemType() == ram.ItemType.ASSET:
            itemName = 'Asset: ' + itemName
        else:
            itemName = 'Item: ' + itemName
        camName = maf.Path.baseName(cam)
        focalLength = str(round(cmds.getAttr(cam + '.focalLength'))) + ' mm'
        if cmds.keyframe(cam, at='focalLength', query=True, keyframeCount=True):
            focalLength = 'Animated'

        cmds.headsUpDisplay('RamItem',section=2, block=0,ba='center', blockSize='large', label=itemName, labelFontSize='large')
        cmds.headsUpDisplay('RamStep',section=2, block=1,ba='center',blockSize='small', label='Step: ' + currentStep, labelFontSize='small')
        if comment != '':
            cmds.headsUpDisplay('RamComment',section=5, block=0, blockSize='small', ba='left', label='Comment : ' + comment, labelFontSize='small')
        cmds.headsUpDisplay('RamCurrentFrame',section=0, block=0, blockSize='large', label='Frame ',pre='currentFrame', labelFontSize='large',dfs='large')
        cmds.headsUpDisplay('RamCam',section=7, block=0, blockSize='large', label='Camera: ' + camName, labelFontSize='large')
        cmds.headsUpDisplay('RamFocalLength',section=9, block=0, blockSize='large', label='Focal Length: ' + focalLength,labelFontSize='large')

        # Save path
        pbNM = nm.copy()
        # resource
        if pbNM.resource != '':
            pbNM.resource = pbNM.resource + '-' + comment
        else:
            pbNM.resource = comment

        pbFilePath = ''

        if result == 1:
            # Extension
            pbNM.extension = 'mp4'
            # path
            pbFilePath = ram.RamFileManager.buildPath((
                previewFolder,
                pbNM.fileName()
            ))
            createPlayblast(pbFilePath, size)
        else:
            pbNM.extension = 'png'
            # path
            pbFilePath = ram.RamFileManager.buildPath((
                previewFolder,
                pbNM.fileName()
            ))
            # Attempt to set window size
            dialog.setWindowSize()
            createThumbnail(pbFilePath)

        # Hide window
        dialog.hideRenderer()
        
        # Set back render SETTINGS
        cmds.setAttr('hardwareRenderingGlobals.multiSampleEnable',currentAA)
        cmds.setAttr('hardwareRenderingGlobals.ssaoEnable',currentAO)

        # Remove all current HUD
        currentHuds = cmds.headsUpDisplay(listHeadsUpDisplays=True)
        if currentHuds:
            for hud in currentHuds:
                cmds.headsUpDisplay(hud, remove=True)

        # Set Metadata
        ram.RamMetaDataManager.setVersion(pbFilePath, version)
        ram.RamMetaDataManager.setVersionFilePath(pbFilePath, versionFilePath)
        ram.RamMetaDataManager.setComment(pbFilePath, comment)

class RamSettingsCmd( om.MPxCommand ):
    name = "ramSettings"

    settingsDialog = SettingsDialog( maf.UI.getMayaWindow() )

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSettingsCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        return syntax

    def doIt(self, args):
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        ram.log("Opening SETTINGS...")  
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
        syntax = om.MSyntax()
        return syntax

    def doIt(self, args):
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        ram.log("Opening the Ramses client...")
        RAMSES.showClient()
        
cmds_classes = (
    RamSaveCmd,
    RamSaveAsCmd,
    RamSaveVersionCmd,
    RamRetrieveVersionCmd,
    RamPublishTemplateCmd,
    RamOpenCmd,
    RamPreviewCmd,
    RamSettingsCmd,
    RamOpenRamsesCmd,
)

cmds_menuItems = []

def maya_useNewAPI():
    pass
