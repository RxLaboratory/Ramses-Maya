import os
from datetime import datetime, timedelta

import ramses as ram
# Keep the ramses and the settings instances at hand
ramses = ram.Ramses.instance()
settings = ram.RamSettings.instance()

import maya.cmds as cmds # pylint: disable=import-error

import sys
from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QComboBox,
    QSlider,
    QSpinBox,
    QTextEdit,
    QPushButton,
    QCheckBox,
)
from PySide2.QtGui import (
    QColor,
    QPalette,
    )
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot,
    Qt
)

import ramses as ram
ramses = ram.Ramses.instance()

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

        self._saveButton = QPushButton("Update")
        buttonsLayout.addWidget( self._saveButton )
        self._skipButton = QPushButton("Skip")
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

def doIt():
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

doIt()