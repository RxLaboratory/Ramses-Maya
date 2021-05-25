import sys
sys.path.append(
    'D:/DEV_SRC/RxOT/Ramses/Ramses-Py'
)

import maya.cmds as cmds
import ramses as ram

ramses = ram.Ramses.instance()
settings = ram.RamSettings.instance()

import os, sys, platform
from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    QLine,
    Slot,
)

import maya.cmds as cmds # pylint: disable=import-error

import ramses as ram
ramses = ram.Ramses.instance()

class PublishDialog( QDialog ):

    def __init__(self, parent=None):
        super(PublishDialog,self).__init__(parent)
        self.__setupUi()
        self.__loadProjects()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Publish Template" )

        self.setMinimumWidth(300)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        topLayout = QHBoxLayout()
        topLayout.setSpacing(3)

        self.projectBox = QComboBox()
        self.projectBox.setEditable(True)
        topLayout.addWidget( self.projectBox )

        self.stepBox = QComboBox()
        self.stepBox.setEditable(True)
        topLayout.addWidget( self.stepBox )

        middleLayout = QHBoxLayout()
        middleLayout.setSpacing(3)

        mainLayout.addLayout( topLayout )

        self.locationEdit = QLineEdit()
        self.locationEdit.setEnabled(False)
        self.locationEdit.setPlaceholderText("Location...")
        middleLayout.addWidget( self.locationEdit )

        self.browseButton = QPushButton("Browse...")
        self.browseButton.setVisible( False )
        middleLayout.addWidget( self.browseButton )

        mainLayout.addLayout( middleLayout )

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

def publishTemplate(): # TODO : template name & Extension as ma or mb
    ram.log("Publishing template...")

    # Check if the Daemon is available if Ramses is set to be used "online"
    if not checkDaemon():
        return

    # Get info from the current file
    currentFilePath = cmds.file( q=True, sn=True )
    fileInfo = ram.RamFileManager.decomposeRamsesFilePath( currentFilePath )

    # Prepare the dialog
    publishDialog = PublishDialog()
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
        if saveFolder == '':
            return
        if not os.path.isdir( saveFolder ):
            os.makedirs(saveFolder)
        saveInfo = ram.RamFileManager.decomposeRamsesFilePath( saveFolder )
        saveName = ram.RamFileManager.buildRamsesFileName(
            saveInfo['project'],
            saveInfo['step'],
            "mb",
            ram.ItemType.GENERAL,
            '',
            "Template"
        )
        saveFilePath = ram.RamFileManager.buildPath((
            saveFolder,
            saveName
        ))
        # save as
        cmds.file( rename = saveFilePath )
        cmds.file( save=True, options="v=1;" )
        # Message
        cmds.inViewMessage( msg='Template published as: <hl>' + saveName + '</hl> in ' + saveFolder , pos='midCenter', fade=True )


publishTemplate()