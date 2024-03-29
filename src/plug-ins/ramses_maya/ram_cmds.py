# -*- coding: utf-8 -*-
"""Maya commands"""

import os
import platform
import subprocess
import tempfile
import shutil

import maya.api.OpenMaya as om # pylint: disable=import-error
import maya.cmds as cmds # pylint: disable=import-error
import maya.mel as mel # pylint: disable=import-error

import dumaf

from .ui_settings import SettingsDialog # pylint: disable=import-error,no-name-in-module
from .ui_status import StatusDialog # pylint: disable=import-error,no-name-in-module
from .ui_versions import VersionDialog # pylint: disable=import-error,no-name-in-module
from .ui_publishtemplate import PublishTemplateDialog # pylint: disable=import-error,no-name-in-module
from .ui_comment import CommentDialog # pylint: disable=import-error,no-name-in-module
from .ui_import import ImportDialog # pylint: disable=import-error,no-name-in-module
from .ui_saveas import SaveAsDialog # pylint: disable=import-error,no-name-in-module
from .ui_preview import PreviewDialog # pylint: disable=import-error,no-name-in-module
from .utils_attributes import get_item, get_step, set_import_attributes, list_ramses_nodes
from .ui_update import UpdateDialog
from .replace_manager import replacer
from .update_manager import get_update_file
from .ui_publish import PublishDialog
from .save_manager import setup_scene
from .utils import getVideoPlayer

import ramses as ram

# Keep the ramses and the SETTINGS instances at hand
RAMSES = ram.Ramses.instance()
SETTINGS = ram.RamSettings.instance()

def check_update():
    """Checks if an update is available"""
    from ramses_maya import TOOL_NAME, VERSION, IS_PRERELEASE
    dumaf.utils.checkUpdate( TOOL_NAME, VERSION, discreet=True, preRelease=IS_PRERELEASE )

def check_daemon():
    """Checks if the Daemon is available (if the SETTINGS tell we have to work with it)"""
    if not RAMSES.connect():
        cmds.confirmDialog(
            title="No User",
            message="You must log in Ramses first!",
            button=["OK"],
            icon="warning"
            )
        cmds.error( "User not available: You must log in Ramses first!" )
        return False

    return True

def get_save_filepath( filePath ):
    """Returns the file path for saving the given scene"""
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

def get_name_manager( filePath ):
    """Returns a RamFileInfo for the file"""
    nm = ram.RamFileInfo()
    nm.setFilePath( filePath )
    if nm.project == '':
        ram.log(ram.Log.MalformedName, ram.LogLevel.Fatal)
        cmds.inViewMessage( msg=ram.Log.MalformedName, pos='midCenter', fade=True )
        cmds.error( ram.Log.MalformedName )
        return None
    return nm

def get_preview_folder( item, step):
    """Returns the preview subfolder for the RamItem and the RamStep"""
    previewFolder = item.previewFolderPath( step )
    if previewFolder == '':
        ram.log("I can't find the publish folder for this item, maybe it does not respect the ramses naming scheme or it is out of place.", ram.LogLevel.Fatal)
        cmds.inViewMessage( msg="Can't find the publish folder for this scene, sorry. Check its name and location.", pos='midCenter', fade=True )
        cmds.error( "Can't find publish folder." )
        return ''
    return previewFolder

def get_temp_dir():
    """Creates and returns a tempdir. For some reason, sometimes the user folder is incorrect in TEMP on windows"""
    tempDir = tempfile.mkdtemp()
    if platform.system() == 'Windows':
        userDir = os.getenv('USERPROFILE')
        tempDir = userDir + '/AppData/Local/Temp/' + os.path.basename(tempDir)
    return tempDir

def create_playblast(filePath, size):
    """Creates a playblast"""
    # Warning, That's for win only ! Needs work on MAC/Linux
    # TODO MAC: open playblast at the end
    # TODO MAC/LINUX: video (audio) playblast format must not be avi
    # TODO MAC/LINUX: call to ffmpeg without .exe
    if platform.system() != 'Windows':
        return

    # Get bin dir
    ramsesFoler = cmds.getModulePath(moduleName='Ramses')
    ffmpegFile = ramsesFoler + '/bin/ffmpeg.exe'

    # Get a temp dir for rendering the playblast
    tempDir = get_temp_dir()
    # The tempDir may not exist
    if not os.path.isdir(tempDir):
        os.makedirs(tempDir)
    imageFile = tempDir + '/' + 'blast'

    # Create jpg frame sequence
    w = cmds.getAttr("defaultResolution.width") * size
    h = cmds.getAttr("defaultResolution.height") * size
    w = w - w % 4
    h = h - h % 4
    imageFile = cmds.playblast(
        filename=imageFile,
        format='image',
        clearCache=True,
        framePadding=5,
        viewer=False,
        showOrnaments=True,
        percent=100,
        compression="jpg",
        quality=50,
        width = w,
        height = h
        )

    # if there's sound, create a sound file
    soundFile = ''
    sounds = cmds.ls(type='audio')
    # If there are sounds in the scene
    if sounds:
        timeCtrl = mel.eval('$tmpVar=$gPlayBackSlider')
        # And sounds are used by the timeline
        if cmds.timeControl(timeCtrl, displaySound=True, query=True):
            soundFile = tempDir + '/' + 'blast.avi'
            soundFile = cmds.playblast(
                filename=soundFile,
                format='avi',
                clearCache=True,
                useTraxSounds=True,
                framePadding= 5,
                viewer=False,
                showOrnaments=False,
                percent=10,
                compression="none",
                quality=10
                )

    # Get framerate
    framerate = mel.eval('float $fps = `currentTimeUnitToFPS`') # It's not in cmds!!

    # We the number of # may be wrong, because maya....
    ffmpegImageFile = imageFile.replace('.#', ".%5d")
    ffmpegImageFile = ffmpegImageFile.replace('#',"")

    # Transcode using ffmpeg
    ffmpegArgs = [
        ffmpegFile,
        '-loglevel', 'error', # limit output to errors
        '-y', # overwrite
        '-start_number', str(cmds.playbackOptions(q=True,minTime=True)),
        '-framerate', str(framerate),
        '-i', ffmpegImageFile, # Image file
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
    ram.log('FFmpeg output: ' + str(output[1]), ram.LogLevel.Debug)

    # Remove temp files
    shutil.rmtree(tempDir)
    player = getVideoPlayer()
    if player.endswith('ffplay.exe'):
        subprocess.Popen([player, '-seek_interval', '0.1', filePath])
    else:
        subprocess.Popen([player, filePath])
    return

def create_thumbnail(filePath):
    """Saves a thumbnail for the current viewport at filepath"""
    cmds.refresh(cv=True, fn = filePath)

class RamSaveCmd( om.MPxCommand ):
    """ramSave Maya cmd"""
    name = "ramSave"

    def __init__(self):
        om.MPxCommand.__init__(self)
        self.newComment = ''
        self.setComment = False

    @staticmethod
    def createCommand():
        """Creates the Maya command"""
        return RamSaveCmd()

    @staticmethod
    def createSyntax():
        """Creates the syntax of the command"""
        syntax = om.MSyntax()
        syntax.addFlag('-c', "-comment", om.MSyntax.kString )
        syntax.addFlag('-sc', "-setComment", om.MSyntax.kBoolean )
        return syntax

    def parseArgs(self, args, saveFilePath):
        """Parses the arguments of the maya command"""
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
            commentDialog = CommentDialog(dumaf.ui.getMayaWindow())
            commentDialog.setComment( currentComment )
            if not commentDialog.exec_():
                return False
            self.newComment = commentDialog.getComment()

        return True

    def doIt(self, args):
        """The Maya command entry point"""
        check_update()
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        """Runs the save command"""
        ram.log("Saving file...")

        # The current maya file
        currentFilePath = cmds.file( q=True, sn=True )
        ram.log("Saving file: " + currentFilePath)

        # We don't need the daemon to just save a file
        # if not checkDaemon():
        #     return

        # Get the save path
        saveFilePath = get_save_filepath( currentFilePath )
        if saveFilePath == '':
            return

        # Parse arguments
        if not self.parseArgs(args,saveFilePath):
            return

        RAMSES.saveFile( currentFilePath, comment=self.newComment )

class RamSaveAsCmd( om.MPxCommand ):
    """ramSaveAs Maya cmd"""

    name = "ramSaveAs"

    def __init__(self): # pylint: disable=invalid-name
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand(): # pylint: disable=invalid-name
        """Creates and returns the command"""
        return RamSaveAsCmd()

    @staticmethod
    def createSyntax(): # pylint: disable=invalid-name
        """Creates and returns the Mel syntax"""
        syntax = om.MSyntax()
        return syntax

    def doIt(self, args): # pylint: disable=invalid-name
        """Runs the command or throw an error if it fails"""
        check_update()
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        """Runs the command"""
        # We need the daemon
        if not check_daemon():
            return

        # Get current info
        currentFilePath = cmds.file( q=True, sn=True )

        # Info
        project = ram.RamProject.fromPath( currentFilePath )
        step = ram.RamStep.fromPath( currentFilePath )
        item = ram.RamItem.fromPath( currentFilePath )

        saveAsDialog = SaveAsDialog(dumaf.ui.getMayaWindow())
        if project is not None:
            saveAsDialog.setProject( project )
        if step is not None:
            saveAsDialog.setStep( step )
        if item is not None:
            saveAsDialog.setItem(item)

        if not saveAsDialog.exec_():
            self.setResult( False )
            return

        item = saveAsDialog.getItem()
        step = saveAsDialog.getStep()
        resource = saveAsDialog.getResource()
        ext = saveAsDialog.getExtension()

        if not item or not step:
            self.setResult( False )
            return

        RAMSES.saveFileAs( currentFilePath, ext, item, step, resource)
        self.setResult( True )

class RamSaveVersionCmd( om.MPxCommand ):
    """ramSaveVersion Maya commnand: saves a new version, sets the status, publishes"""
    name = "ramSaveVersion"

    # Defaults
    updateSatus = True
    publish = False
    preview = False
    edit_publish_settings = False

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        """Creates the command"""
        return RamSaveVersionCmd()

    @staticmethod
    def createSyntax():
        """Creates the Mel Syntax"""
        syntax = om.MSyntax()
        syntax.addFlag('-us', "-updateStatus", om.MSyntax.kBoolean )
        syntax.addFlag('-p', "-publish", om.MSyntax.kBoolean )
        syntax.addFlag('-pv', "-preview", om.MSyntax.kBoolean )
        syntax.addFlag('-eps', "-editPublishSettings", om.MSyntax.kBoolean )
        return syntax

    def parseArgs(self, args):
        """Parses the Mel args"""
        parser = om.MArgParser( self.syntax(), args)

        if parser.isFlagSet( '-us' ):
            self.updateSatus = parser.flagArgumentBool('-us', 0)
        else:
            self.updateSatus = True

        if parser.isFlagSet( '-p' ):
            self.publish = parser.flagArgumentBool('-p', 0)
            if parser.isFlagSet( '-eps' ):
                self.edit_publish_settings = parser.flagArgumentBool('-eps', 0)
        else:
            self.publish = False

        if parser.isFlagSet( '-pv' ):
            self.preview = parser.flagArgumentBool('-pv', 0)
        else:
            self.preview = False

    def doIt(self, args):
        """Runs the command or raise an error"""
        check_update()
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        """Runs the command"""
        # The current maya file
        currentFilePath = cmds.file( q=True, sn=True )
        ram.log("Saving file: " + currentFilePath)

        # Check if the Daemon is available
        if not check_daemon():
            return

        # Get the save path
        save_filepath = get_save_filepath( currentFilePath )
        if save_filepath == '':
            return

        self.parseArgs(args)

        # Update status
        currentStep = ram.RamStep.fromPath( save_filepath )
        currentItem = ram.RamItem.fromPath( save_filepath, True )

        if currentItem is None or currentStep is None:
            cmds.warning( ram.Log.NotAnItem )
            cmds.inViewMessage( msg='Invalid item, <hl>this does not seem to be a valid Ramses Item</hl>', pos='midCenter', fade=True )
            return

        currentStatus = currentItem.currentStatus( currentStep )
        status = None

        if self.updateSatus:
            # Show status dialog
            status_dialog = StatusDialog(dumaf.ui.getMayaWindow())
            if currentItem.virtual():
                status_dialog.setVirtual()
            status_dialog.setPublish( self.publish )
            status_dialog.setStatus( currentStatus )
            update = status_dialog.exec_()
            if update == 0:
                return
            if update == 1:
                currentStatus.setState( status_dialog.getState() )
                currentStatus.setComment( status_dialog.getComment() )
                currentStatus.setCompletionRatio( status_dialog.getCompletionRatio() )
                currentStatus.setPublished( status_dialog.publish() )
                currentStatus.setUser()

                status = currentStatus

                self.publish = status_dialog.publish()
                self.preview = status_dialog.preview()
                self.edit_publish_settings = status_dialog.edit_publish_settings()

        # Get the state
        state = RAMSES.defaultState
        if status is not None:
            state = status.state()
        elif currentStatus is not None:
            state = currentStatus.state()

        stateShortName = 'v'
        if state:
            stateShortName = state.shortName()

        RAMSES.saveFile(
            save_filepath,
            incrementVersion=True,
            comment="",
            newStateShortName=stateShortName
            )

        # Get the new version
        versionInfo = ram.RamFileManager.getLatestVersionInfo( save_filepath )
        newVersion = versionInfo.version

        # Update status
        if status is not None:
            status.setVersion(newVersion)
            RAMSES.updateStatus(currentItem, status, currentStep)

        # Alert
        newVersionStr = str( newVersion )
        cmds.inViewMessage( msg='Incremental save! New version: <hl>v' + newVersionStr + '</hl>', pos='midCenterBot', fade=True )

        # Publish
        if self.publish:
            if currentStep is not None:
                RAMSES.publish( save_filepath, publishOptions=None, showPublishOptions=self.edit_publish_settings )
            else:
                ram.log( "I can't publish this item, I don't know which step it is.", ram.LogLevel.Critical )
                cmds.inViewMessage( msg="Can't publish: unknown step.", pos='midCenterBot', fade=True )

        if self.preview:
            cmds.ramPreview()

class RamRetrieveVersionCmd( om.MPxCommand ):
    """ramRetrieveVersion Maya cmd"""
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
        check_update()
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
        saveFilePath = get_save_filepath( currentFilePath )
        if not saveFilePath:
            return

        # Get the version files
        versionFiles = ram.RamFileManager.getVersionFilePaths( saveFilePath )

        if len(versionFiles) == 0:
            cmds.inViewMessage( msg='No other version found.', pos='midBottom', fade=True )
            return

        versionDialog = VersionDialog(dumaf.ui.getMayaWindow())
        versionDialog.setVersions( versionFiles )
        if not versionDialog.exec_():
            return

         # If the current file needs to be saved
        if not dumaf.Scene.checkSaveState():
            return
        
        versionFile = ram.RamFileManager.restoreVersionFile( versionDialog.getVersion() )
        # We need to wait for the file to be correctly written before opening
        ram.RamFileManager.waitFiles()
        # open
        cmds.file(versionFile, open=True, force=True)

class RamPublishTemplateCmd( om.MPxCommand ):
    """ramPublishTemplate Maya commnand: saves a new template"""
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
        check_update()
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        """Runs the command"""

        # Check if the Daemon is available if Ramses is set to be used "online"
        if not check_daemon():
            return

        # Get info from the current file
        currentFilePath = cmds.file( q=True, sn=True )

        # Prepare the dialog
        publishDialog = PublishTemplateDialog(dumaf.ui.getMayaWindow())

        # Set the project and step
        project = ram.RamProject.fromPath( currentFilePath )
        step = ram.RamStep.fromPath( currentFilePath )
        # Set
        if project is not None:
            publishDialog.setProject( project )
        if step is not None:
            publishDialog.setStep( step )

        if publishDialog.exec_():
            # save as template
            step = publishDialog.getStep()
            ext = publishDialog.getExtension()
            templateName = publishDialog.getTemplateName()
            RAMSES.saveTemplate( ext, step, templateName)

class RamOpenCmd( om.MPxCommand ):
    """Shows the UI to open, import or replace an item"""
    name = "ramOpen"

    def __init__(self):
        om.MPxCommand.__init__(self)
        self.importMode = False

    @staticmethod
    def createCommand():
        """Creates the command"""
        return RamOpenCmd()

    @staticmethod
    def createSyntax():
        """Creates the Mel Syntax"""
        syntax = om.MSyntax()
        syntax.addFlag('-i', "-import", om.MSyntax.kBoolean )
        syntax.addFlag('-r', "-replace", om.MSyntax.kBoolean )
        return syntax

    def parseArgs(self, args):
        """Parses Mel arguments"""
        parser = om.MArgParser( self.syntax(), args)
        if parser.isFlagSet( '-i' ):
            self.mode = "import"
        elif parser.isFlagSet( '-r' ):
            self.mode = "replace"
        else:
            self.mode = "open"

    def doIt(self, args):
        """Runs or raise the error"""
        check_update()
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        """Runs the command"""
        # Check if the Daemon is available if Ramses is set to be used "online"
        if not check_daemon():
            return

        self.parseArgs(args)

        # Let's show the dialog
        importDialog = ImportDialog(dumaf.ui.getMayaWindow())
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
            if not dumaf.Scene.checkSaveState():
                return
            # Get the file and open
            file = importDialog.getFile()
            RAMSES.openFile( file )
        else:
            # Get Data
            item = importDialog.getItem()
            if item is None:
                return
            step = importDialog.getStep()
            show_options = importDialog.show_import_options()

            if result == 2: # import
                filePaths = importDialog.getFiles()
                RAMSES.importItem(
                    cmds.file( q=True, sn=True ),
                    filePaths,
                    item,
                    step,
                    importOptions=None,
                    showImportOptions=show_options
                )
                return

            if result == 3: # replace
                filePath = importDialog.getFile()

                RAMSES.replaceItem(
                    cmds.file( q=True, sn=True ),
                    filePath,
                    item,
                    step,
                    importOptions=None,
                    showImportOptions=show_options
                )
                return

class RamPreviewCmd( om.MPxCommand ):
    """The command to generate a playblast or a thumbnail"""
    name = "ramPreview"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        """Creates the command"""
        return RamPreviewCmd()

    @staticmethod
    def createSyntax():
        """Creates the Mel Syntax"""
        syntax = om.MSyntax()
        return syntax

    def doIt(self, args):
        """Runs or raises an error if debug mode"""
        check_update()
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        """Runs the command"""
        currentFilePath = cmds.file( q=True, sn=True )

        # Get the save path
        saveFilePath = get_save_filepath( currentFilePath )
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
        nm = get_name_manager( saveFilePath )
        if nm is None:
            return
        version = currentItem.latestVersion( nm.resource, '', currentStep )
        versionFilePath = currentItem.latestVersionFilePath( nm.resource, '', currentStep )

        # Preview folder
        previewFolder = get_preview_folder(currentItem, currentStep)
        if previewFolder == '':
            return
        ram.log( "I'm previewing in " + previewFolder )

        # Keep current SETTINGS
        currentAA = cmds.getAttr('hardwareRenderingGlobals.multiSampleEnable')
        currentAO = cmds.getAttr('hardwareRenderingGlobals.ssaoEnable')
        prevCam = cmds.lookThru( q=True )
        # Because the first call seems to be ignored...
        cmds.lookThru( prevCam )

        # show UI
        dialog = PreviewDialog( dumaf.ui.getMayaWindow() )
        result = dialog.exec_()
        if not result:
            return

        # Options
        comment = dialog.comment()
        cam = dialog.camera()
        size = dialog.getSize()
        hud = dialog.showHUD()
        thumbnail = dialog.thumbnail()
        pb = dialog.playblast()

        # Set the cam
        cmds.lookThru( cam )

        # Remove all current HUD
        currentHuds = cmds.headsUpDisplay(listHeadsUpDisplays=True)
        if currentHuds:
            for hud in currentHuds:
                cmds.headsUpDisplay(hud, remove=True)
        # Add ours
        if hud:
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
            camName = dumaf.paths.baseName(cam)
            focalLength = str(round(cmds.getAttr(cam + '.focalLength'))) + ' mm'
            if cmds.keyframe(cam, at='focalLength', query=True, keyframeCount=True):
                focalLength = 'Animated'

            cmds.headsUpDisplay(
                'RamItem',
                section=2,
                block=0,
                ba='center',
                blockSize='large',
                label=itemName,
                labelFontSize='large'
                )
            cmds.headsUpDisplay(
                'RamStep',
                section=2,
                block=1,
                ba='center',
                blockSize='small',
                label='Step: ' + currentStep,
                labelFontSize='small'
                )
            if comment != '':
                cmds.headsUpDisplay(
                    'RamComment',
                    section=5,
                    block=0,
                    blockSize='small',
                    ba='left',
                    label='Comment : ' + comment,
                    labelFontSize='small'
                    )
            cmds.headsUpDisplay(
                'RamCurrentFrame',
                section=0,
                block=0,
                blockSize='large',
                label='Frame ',
                pre='currentFrame',
                labelFontSize='large',
                dfs='large'
                )
            cmds.headsUpDisplay(
                'RamCam',
                section=7,
                block=0,
                blockSize='large',
                label='Camera: ' + camName,
                labelFontSize='large'
                )
            cmds.headsUpDisplay(
                'RamFocalLength',
                section=9,
                block=0,
                blockSize='large',
                label='Focal Length: ' + focalLength,
                labelFontSize='large'
                )

        # Save path
        pbNM = nm.copy()
        # resource
        if pbNM.resource != '':
            pbNM.resource = pbNM.resource + '-' + comment
        else:
            pbNM.resource = comment

        # Save path
        pbFolderPath = dialog.folder()
        if pbFolderPath == '':
            pbFolderPath = previewFolder
        pbFileName = dialog.fileName()
        if pbFileName == '':
            pbFileName = pbNM.fileName()

        pbFileName = pbFileName.split('.')[0:-1]
        pbFileName = ".".join(pbFileName)
        pbFilePath = ''

        if thumbnail:
            # path
            pbFilePath = ram.RamFileManager.buildPath((
                pbFolderPath,
                pbFileName + '.' + 'png'
            ))
            # Attempt to set window size
            dialog.setWindowSize()
            create_thumbnail(pbFilePath)

        if pb:
            # Extension
            # path
            pbFilePath = ram.RamFileManager.buildPath((
                pbFolderPath,
                pbFileName + '.' + 'mp4'
            ))
            cmds.refresh()
            create_playblast(pbFilePath, size)

        # Hide window
        dialog.hideRenderer()

        # Set back render SETTINGS
        cmds.setAttr('hardwareRenderingGlobals.multiSampleEnable',currentAA)
        cmds.setAttr('hardwareRenderingGlobals.ssaoEnable',currentAO)
        cmds.lookThru( prevCam )
        mel.eval("lookThroughModelPanel " + prevCam + " modelPanel4;")

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

    settingsDialog = SettingsDialog( dumaf.ui.getMayaWindow() )

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
        check_update()
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
        check_update()
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        ram.log("Opening the Ramses client...")
        RAMSES.showClient()

class RamSetupSceneCmd( om.MPxCommand ):
    """Sets the scene up to be Ramses friendly,
    and respect the project/shot settings (resolution, duration...)"""
    name = "ramSetupScene"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSetupSceneCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        return syntax

    def doIt(self, args):
        check_update()
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        """Runs the command"""
        # The current maya file
        currentFilePath = cmds.file( q=True, sn=True )

        # Check if the Daemon is available if Ramses is set to be used "online"
        if not check_daemon():
            return

        # Get the save path 
        save_filepath = get_save_filepath( currentFilePath )
        if save_filepath == '':
            return

        currentItem = ram.RamItem.fromPath( save_filepath )
        currentStep = ram.RamStep.fromPath( save_filepath )

        ok = setup_scene(currentItem, currentStep)

        if ok:
            cmds.inViewMessage( msg='Scene ready!', pos='midCenter', fade=True )

class RamUpdateCmd( om.MPxCommand ):
    """The command to update Ramses nodes in the scene with other versions"""
    name = "ramUpdate"

    # Defaults
    updateAll = False
    updateSelection = False

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        """"Creates the command"""
        return RamUpdateCmd()

    @staticmethod
    def createSyntax():
        """Creates the Mel Syntax"""
        syntax = om.MSyntax()
        syntax.addFlag('-a', "-updateAll", om.MSyntax.kBoolean )
        syntax.addFlag('-s', "-updateSelection", om.MSyntax.kBoolean )
        return syntax

    def parseArgs(self, args):
        """Parses the Mel args"""
        parser = om.MArgParser( self.syntax(), args)

        if parser.isFlagSet( '-a' ):
            self.updateAll = parser.flagArgumentBool('-a', 0)
        else:
            self.updateAll = False

        if parser.isFlagSet( '-s' ):
            self.updateSelection = parser.flagArgumentBool('-s', 0)
        else:
            self.updateSelection = False

    def doIt(self, args):
        """Runs the command or raise an error in debug mode"""
        check_update()
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        """Runs the command"""
        # The current maya file
        currentFilePath = cmds.file( q=True, sn=True )

        # Check if the Daemon is available if Ramses is set to be used "online"
        if not check_daemon():
            return

        # Get the save path 
        save_filepath = get_save_filepath( currentFilePath )
        if save_filepath == '':
            return

        # Parse arguments
        self.parseArgs(args)

        # The list of nodes to be updated
        # An list of tuples ( mayaNode, updateFile )
        nodes = []

        if not self.updateAll and not self.updateSelection:
            updateDialog = UpdateDialog(dumaf.ui.getMayaWindow())
            result = updateDialog.exec_()
            if result == 0:
                return
            if result == 1:
                nodes = updateDialog.getAllNodes()
            else:
                nodes = updateDialog.getSelectedNodes()
        else:
            # List all the ramses nodes in the scene
            ram_nodes = list_ramses_nodes(
                node_type='',
                selected_only=self.updateSelection
                )

            # Check if there are updates
            for ram_node in ram_nodes:
                update_file = get_update_file( ram_node )
                if update_file != '':
                    nodes.append( (ram_node, update_file) )

        if len(nodes) == 0:
            return

        progressDialog = dumaf.ProgressDialog()
        progressDialog.setText("Updating items...")
        progressDialog.setMaximum(len(nodes))
        progressDialog.show()

        for n in nodes:
            node = n[0]
            updateFile = n[1]

            # Get the item and step
            ram_item = get_item( node )
            ram_step = get_step( node )

            progressDialog.setText("Updating: " + dumaf.paths.baseName(node) )
            ram.log("Updating: " + dumaf.paths.baseName(node) + "\nwith: " + updateFile )
            progressDialog.increment()

            # Let's update!
            # Replace
            # the replacer replaces selected nodes: select it!
            cmds.select(node, replace=True)
            replacer(updateFile, ram_item, ram_step, import_options=None, show_import_options=False)

        progressDialog.close()

class RamPublishSettings( om.MPxCommand ):
    """Sets the publish settings"""
    name = "ramPublishSettings"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamPublishSettings()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        return syntax

    def doIt(self, args):
        check_update()
        try:
            self.run(args)
        except:
            ram.printException()
            if SETTINGS.debugMode:
                raise

    def run(self, args):
        # The current maya file
        current_file_path = cmds.file( q=True, sn=True )
        
        # Check if the Daemon is available if Ramses is set to be used "online"
        if not check_daemon():
            return

        # Get current info
        step = ram.RamStep.fromPath( current_file_path )

        publish_dialog = PublishDialog()
        project = ram.RamProject.fromPath(current_file_path)
        if project:
            publish_dialog.set_steps( project.steps() )
        if step:
            publish_dialog.set_step(step)
        if not publish_dialog.exec_():
            return

        settings = publish_dialog.get_preset()
        step = publish_dialog.get_step()

        ram.log("Saving settings for: " + str(step) + "\n" + settings)

        step.setPublishSettings(settings)

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
    RamSetupSceneCmd,
    RamUpdateCmd,
    RamPublishSettings,
)

cmds_menuItems = []

def maya_useNewAPI():
    pass
