# Py
import os
from datetime import datetime, timedelta
# Maya
import maya.cmds as cmds
# PySide
from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QSlider,
    QSpinBox,
    QCheckBox,
    QTextEdit,
    QWidget,
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Qt,
    QLine,
    Slot,
)
# Ramses
import ramses as ram

ramses = ram.Ramses.instance()
settings = ram.RamSettings.instance()

class VersionDialog( QDialog ):
    def __init__(self, parent = None):
        super(VersionDialog,self).__init__(parent)
        self.__setupUi()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Retrieve Version" )
        self.setMinimumWidth(250)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        self._versionsBox = QComboBox()
        mainLayout.addWidget( self._versionsBox )

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._openButton = QPushButton("Retrieve")
        buttonsLayout.addWidget( self._openButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

        self.setLayout( mainLayout )

    def __connectEvents(self):
        self._openButton.clicked.connect( self.accept )
        self._cancelButton.clicked.connect( self.reject )

    def setVersions(self, fileList):
        self._versionsBox.clear()
        for f in fileList:
            fileName = os.path.basename( f )
            decomposedFileName = ram.RamFileManager.decomposeRamsesFileName( fileName )
            self._versionsBox.addItem( 
                decomposedFileName['state'] + ' | ' + str(decomposedFileName['version']),
                f
            )

    def getVersion(self):
        return self._versionsBox.currentData()

class StateBox( QComboBox ):
    def __init__(self, parent = None):
        super(StateBox,self).__init__(parent)

        # Populate states from Ramses
        for state in ramses.states():
            self.addItem( state.shortName(), state.color() )

        self.setState( ramses.defaultState )
        self.currentIndexChanged.connect( self.indexChanged )

    @Slot()
    def indexChanged(self, i):
        color = self.itemData(i)
        color = QColor.fromRgb( color[0], color[1], color[2] )
        pal = self.palette()
        pal.setColor(QPalette.Button, color)
        self.setPalette(pal)

    def setState(self, state):
        i = 0
        while i < self.count():
            if self.itemText( i ) == state.shortName():
                self.setCurrentIndex( i )
                return
            i = i+1

    def getState(self):
        return ramses.state( self.currentText() )

class StatusDialog( QDialog ):
    
    def __init__(self, parent = None):
        super(StatusDialog,self).__init__(parent)
        self.__setupUi()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Incremental Save: Update Status" )
        self.setMinimumWidth( 400 )

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        topLayout = QHBoxLayout()
        topLayout.setSpacing(3)

        self.stateBox = StateBox()
        topLayout.addWidget( self.stateBox )

        self.completionSlider = QSlider( Qt.Horizontal )
        self.completionSlider.setMaximum(100)
        topLayout.addWidget( self.completionSlider )
        self.completionBox = QSpinBox( )
        self.completionBox.setMinimum( 0 )
        self.completionBox.setMaximum( 100 )
        self.completionBox.setSuffix( "%" )
        topLayout.addWidget( self.completionBox )

        self.publishBox = QCheckBox("Publish the current scene.")
        topLayout.addWidget( self.publishBox )

        mainLayout.addLayout( topLayout )

        self.commentEdit = QTextEdit()
        mainLayout.addWidget( self.commentEdit )

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._saveButton = QPushButton("Update Status and Save")
        buttonsLayout.addWidget( self._saveButton )
        self._skipButton = QPushButton("Skip and Save")
        buttonsLayout.addWidget( self._skipButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

        self.setLayout( mainLayout )

    def __connectEvents(self):
        self.completionSlider.valueChanged.connect( self.completionBox.setValue )
        self.completionBox.valueChanged.connect( self.completionSlider.setValue )
        self.stateBox.currentTextChanged.connect(self.stateChanged )
        self._saveButton.clicked.connect( self.accept )
        self._cancelButton.clicked.connect( self.reject )
        self._skipButton.clicked.connect( self.skip )

    def stateChanged(self, s):
        state = ramses.state( s )
        self.completionBox.setValue( state.completionRatio() )

    def setStatus( self, status):
        self.stateBox.setState( status.state )
        self.completionBox.setValue( status.completionRatio )
        self.commentEdit.setPlainText( status.comment )

    def getState(self):
        return self.stateBox.getState()

    def getCompletionRatio(self):
        return self.completionBox.value()

    def getComment(self):
        return self.commentEdit.toPlainText()

    def isPublished(self):
        return self.publishBox.isChecked()

    def skip(self):
        self.done(2)

    def setOffline(self, offline):
        online = not offline
        self.completionSlider.setVisible(online)
        self.completionBox.setVisible(online)
        self.commentEdit.setVisible(online)

class PublishTemplateDialog( QDialog ):

    def __init__(self, parent=None):
        super(PublishTemplateDialog,self).__init__(parent)
        self.__setupUi()
        self.__loadProjects()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Publish Template" )

        self.setMinimumWidth(400)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        topLayout = QFormLayout()
        topLayout.setFieldGrowthPolicy( QFormLayout.AllNonFixedFieldsGrow )
        topLayout.setSpacing(3)

        self.projectBox = QComboBox()
        self.projectBox.setEditable(True)
        topLayout.addRow( "Project:", self.projectBox )

        self.stepBox = QComboBox()
        self.stepBox.setEditable(True)
        topLayout.addRow( "Step:", self.stepBox )

        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("Template")
        topLayout.addRow("Name:", self.nameEdit)

        self.extensionBox = QComboBox()
        self.extensionBox.addItem("Maya Binary (.mb)", "mb")
        self.extensionBox.addItem("Maya ASCII (.ma)", "ma")
        topLayout.addRow("File Type:", self.extensionBox)

        locationWidget = QWidget()
        locationLayout = QHBoxLayout()
        locationLayout.setSpacing(3)
        locationLayout.setContentsMargins(0,0,0,0)
        locationWidget.setLayout(locationLayout)

        self.locationEdit = QLineEdit()
        self.locationEdit.setEnabled(False)
        self.locationEdit.setPlaceholderText("Location...")
        locationLayout.addWidget( self.locationEdit )

        self.browseButton = QPushButton("Browse...")
        self.browseButton.setVisible( False )
        locationLayout.addWidget( self.browseButton )

        topLayout.addRow("Location:",locationWidget)

        self.fileNameLabel = QLabel()
        topLayout.addRow("Filename:", self.fileNameLabel)

        mainLayout.addLayout( topLayout )

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._publishButton = QPushButton("Publish Template")
        buttonsLayout.addWidget( self._publishButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

        self.setLayout( mainLayout )

    def __connectEvents(self):
        self.browseButton.clicked.connect( self.browse )
        self.projectBox.currentTextChanged.connect( self.__loadSteps )
        self.stepBox.currentTextChanged.connect( self.__buildPath )
        self._publishButton.clicked.connect( self.accept )
        self._cancelButton.clicked.connect( self.reject )
        self.extensionBox.currentIndexChanged.connect( self.__buildFileName )
        self.nameEdit.textEdited.connect( self.__buildFileName )

    def __loadProjects(self):
        # Load projects
        projects = ramses.projects()
        self.projectBox.clear()
        if projects is None:
            self.setOffline()
            self.__loadSteps( )
            return
        for project in ramses.projects():
            n = project.name()
            if n == "":
                n = project.shortName()
            self.projectBox.addItem(n, project.shortName())
        self.__loadSteps( )

    def __getCurrentShortName(self, comboBox):
        currentIndex = comboBox.currentIndex()
        currentText = comboBox.currentText()
        itemText = comboBox.itemText( currentIndex )
        if currentIndex == -1:
            return currentText
        if currentText == itemText:
            return comboBox.itemData( currentIndex )
        return currentText

    @Slot()
    def __loadSteps(self):
        projectShortName = self.__getCurrentShortName( self.projectBox )
        project = ramses.project( projectShortName )
        if project is not None:
            self.stepBox.clear()
            for step in project.steps():
                n = step.name()
                if n == "":
                    n = step.shortName()
                self.stepBox.addItem(n, step.shortName())
        self.__buildPath()

    @Slot()
    def __buildPath(self):
        self._publishButton.setEnabled(False)
        self.locationEdit.setText("")
        self.fileNameLabel.setText("")
        pShortName = self.__getCurrentShortName( self.projectBox )
        project = ramses.project( pShortName )
        if project is None:
            self.locationEdit.setPlaceholderText("Sorry, Invalid project...")
            return
        sShortName = self.__getCurrentShortName( self.stepBox )
        step = project.step(sShortName)
        if step is None:
            self.locationEdit.setPlaceholderText("Sorry, Invalid step...")
            return
        self.locationEdit.setPlaceholderText("Location")
        self.locationEdit.setText( step.templatesFolderPath() )
        self._publishButton.setEnabled(True)
        # build file name
        self.__buildFileName()

    @Slot()
    def __buildFileName(self):
        pShortName = self.__getCurrentShortName( self.projectBox )
        sShortName = self.__getCurrentShortName( self.stepBox )
        resource = self.nameEdit.text()
        if resource == "":
            resource = "Template"
        fileName = ram.RamFileManager.buildRamsesFileName(
            pShortName,
            sShortName,
            self.extensionBox.currentData(),
            ram.ItemType.GENERAL,
            '',
            resource
        )
        self.fileNameLabel.setText( fileName )

    @Slot()
    def browse(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Templates Directory",
            ramses.folderPath(),
            QFileDialog.ShowDirsOnly
            )
        self.locationEdit.setText("")
        # Try to extract info from the path
        if path != "":
            pathInfo = ram.RamFileManager.decomposeRamsesFilePath( path )
            project = pathInfo['project']
            step = pathInfo['step']
            if step == "" or project == "":
                cmds.confirmDialog(
                title="Invalid Ramses project or step",
                message="Sorry, this folder does not belong to a valid step in this project, I can't export the template there.",
                button=["OK"],
                icon="warning"
                )
            if project != "":
                self.projectBox.setEditText( project )
            if step != "":
                self.stepBox.setEditText( step )
            self.__buildPath() 

    def setProject(self, project):
        for i in range(self.projectBox.count()):
            if self.projectBox.itemData(i) == project.shortName():
                self.projectBox.setCurrentIndex(i)
                return
        n = project.name()
        if n == "":
            n = project.shortName()
        self.projectBox.addItem(n, project.shortName())
        self.projectBox.setCurrentIndex( self.projectBox.count() - 1)

    def setStep(self, step):
        for i in range( self.stepBox.count() ):
            if self.stepBox.itemData(i) == step.shortName():
                self.stepBox.setCurrentIndex(i)
                return
        n = step.name()
        if n == "":
            n = step.shortName()
        self.stepBox.addItem(n, step.shortName())
        self.stepBox.setCurrentIndex( self.projectBox.count() - 1)
        
    def setOffline(self, offline=True):
        online = not offline
        self.locationEdit.setEnabled(offline)
        self.browseButton.setVisible(offline)

    def getFolder(self):
        return self.locationEdit.text()

    def getFile(self):
        return self.fileNameLabel.text()

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
    print(saveFilePath)
    if saveFilePath == "": # Ramses may return an empty string if the current file name does not respect the Ramses Naming Scheme
        cmds.warning( ram.Log.MalformedName )
        # Set file to be renamed
        cmds.file( renameToSave = True )
        cmds.inViewMessage( msg='Malformed Ramses file name! <hl>Please save with a correct name first</hl>.', pos='midCenter', fade=True )
        return None

    return saveFilePath

def publishTemplate():
    ram.log("Publishing template...")

    # Check if the Daemon is available if Ramses is set to be used "online"
    if not checkDaemon():
        return

    # Get info from the current file
    currentFilePath = cmds.file( q=True, sn=True )
    fileInfo = ram.RamFileManager.decomposeRamsesFilePath( currentFilePath )

    # Prepare the dialog
    publishDialog = PublishTemplateDialog()
    # Set the project and step
    project = ramses.currentProject()
    step = None
    if project is None:
        # Try to get from current file
        project = ramses.project( fileInfo['project'] )
    if project is not None:
        publishDialog.setProject( project )
        step = project.step(fileInfo['step'])
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

def save():
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

def saveVersion():
    # The current maya file
    currentFilePath = cmds.file( q=True, sn=True )
    ram.log("Saving file: " + currentFilePath)
    
    # Check if the Daemon is available if Ramses is set to be used "online"
    if not checkDaemon():
        return

    # Get the save path 
    saveFilePath = getSaveFilePath( currentFilePath )
    print(saveFilePath)
    if not saveFilePath:
        return

    # Update status
    saveFileName = os.path.basename( saveFilePath )
    saveFileDict = ram.RamFileManager.decomposeRamsesFileName( saveFileName )
    currentStep = saveFileDict['step']
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
    newState = decomposedFileName['state']

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
    ram.log( "Incremental save, scene saved with state: " + newState + "! New version is: " + newVersionStr )
    cmds.inViewMessage( msg='Incremental save! New version: <hl>v' + newVersionStr + '</hl> | State: <hl>' + newState + '</hl>', pos='midCenter', fade=True )

def retrieveVersion():
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

publishTemplate()