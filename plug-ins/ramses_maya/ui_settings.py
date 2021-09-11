# -*- coding: utf-8 -*-

import sys, platform
from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QApplication,
    QFileDialog,
    QFormLayout,
    QStackedLayout,
    QWidget,
    QMainWindow,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QSpinBox,
    QCheckBox,
    QLabel,
    QPushButton,
    QComboBox,
    QListWidget,
    QWidget,
    QSizePolicy,
)
from PySide2.QtGui import QDesktopServices # pylint: disable=no-name-in-module
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot,
    QUrl,
    Qt
)

import ramses as ram
import dumaf as maf
import maya.cmds as cmds # pylint: disable=import-error
# Keep the settings at hand
settings = ram.RamSettings.instance()

class SettingsDialog( QMainWindow ):

    def __init__( self, parent=None ):
        super(SettingsDialog, self).__init__(parent)
        self.__setupUi()
        self.__setupMenu()
        self.__connectEvents()
        self.revert()

    def __setupUi(self):
        self.setWindowTitle("Ramses Add-ons settings")
        self.setMinimumWidth( 500 )

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(12)

        secondaryLayout = QHBoxLayout()
        secondaryLayout.setSpacing(3)

        self.sectionsBox = QListWidget()
        self.sectionsBox.addItem("Versionning")
        self.sectionsBox.addItem("Folders")
        self.sectionsBox.addItem("Ramses Application")
        self.sectionsBox.addItem("Development")
        self.sectionsBox.setMaximumWidth( 150 )
        secondaryLayout.addWidget(self.sectionsBox)

        self.stackedLayout = QStackedLayout()

        versionningWidget = QWidget()
        vL = QVBoxLayout()
        versionningWidget.setLayout(vL)
        self.stackedLayout.addWidget( versionningWidget )
        versionningLayout = QFormLayout()
        versionningLayout.setSpacing(3)
        vL.addLayout(versionningLayout)
        vL.addStretch()

        self._autoIncrementBox = QSpinBox()
        self._autoIncrementBox.setMinimum(1)
        self._autoIncrementBox.setMaximum(1440) #24h
        self._autoIncrementBox.setSuffix(" minutes.")
        versionningLayout.addRow( "Auto-increment version every:", self._autoIncrementBox )

        self._saveHotkeyBox = QCheckBox("Replace with the \"ramSave\" command.")
        versionningLayout.addRow( "\"Save\" hotkey (Ctrl+S):", self._saveHotkeyBox )

        self._saveAsHotkeyBox = QCheckBox("Replace with the \"ramSaveAs\" command.")
        versionningLayout.addRow( "\"Save As\" hotkey (Ctrl+Shift+S):", self._saveAsHotkeyBox )

        self._openHotkeyBox = QCheckBox("Replace with the \"ramOpen\" command.")
        versionningLayout.addRow( "\"Open\" hotkey (Ctrl+O):", self._openHotkeyBox )

        foldersWidget = QWidget()
        fL = QVBoxLayout()
        foldersWidget.setLayout(fL)
        self.stackedLayout.addWidget( foldersWidget )
        foldersLayout = QFormLayout()
        foldersLayout.setSpacing(3)
        fL.addLayout(foldersLayout)
        fL.addStretch()

        pathLabel = QLabel("Ramses data path:")       
        pathLayout = QHBoxLayout()
        self._ramsesPathEdit = QLineEdit( )
        pathLayout.addWidget( self._ramsesPathEdit )
        self._ramsesPathButton = QPushButton(text="Browse...")
        pathLayout.addWidget( self._ramsesPathButton )
        foldersLayout.setWidget( 1, QFormLayout.LabelRole, pathLabel)
        foldersLayout.setLayout( 1, QFormLayout.FieldRole, pathLayout)

        appWidget = QWidget()
        aL = QVBoxLayout()
        appWidget.setLayout(aL)
        self.stackedLayout.addWidget( appWidget )
        appLayout = QFormLayout()
        appLayout.setSpacing(3)
        aL.addLayout(appLayout)
        aL.addStretch()

        connectLabel = QLabel("Use the Ramses Application:")
        self._onlineBox = QCheckBox("Connected")
        appLayout.addRow( connectLabel, self._onlineBox )

        pathLabel = QLabel("Ramses Application path:")       
        pathLayout = QHBoxLayout()
        self._clientPathEdit = QLineEdit( )
        pathLayout.addWidget( self._clientPathEdit )
        self._clientPathButton = QPushButton(text="Browse...")
        pathLayout.addWidget( self._clientPathButton )
        appLayout.setWidget( 1, QFormLayout.LabelRole, pathLabel)
        appLayout.setLayout( 1, QFormLayout.FieldRole, pathLayout)

        portLabel = QLabel("Ramses Daemon port:")
        self._clientPortBox = QSpinBox()
        self._clientPortBox.setMinimum( 1024 )
        self._clientPortBox.setMaximum( 49151 )
        appLayout.addRow( portLabel, self._clientPortBox )

        devWidget = QWidget()
        dL = QVBoxLayout()
        devWidget.setLayout(dL)
        self.stackedLayout.addWidget( devWidget )
        devLayout = QFormLayout()
        devLayout.setSpacing(3)
        dL.addLayout(devLayout)
        dL.addStretch()

        logLabel = QLabel("Log Level:")

        self._logLevelBox = QComboBox()
        self._logLevelBox.addItem( "Data Received", ram.LogLevel.DataReceived )
        self._logLevelBox.addItem( "Data Sent", ram.LogLevel.DataSent )
        self._logLevelBox.addItem( "Debug", ram.LogLevel.Debug )
        self._logLevelBox.addItem( "Information", ram.LogLevel.Info )
        self._logLevelBox.addItem( "Critical", ram.LogLevel.Critical )
        self._logLevelBox.addItem( "Fatal", ram.LogLevel.Fatal )
        
        devLayout.addRow( logLabel, self._logLevelBox )

        secondaryLayout.addLayout(self.stackedLayout)

        mainLayout.addLayout( secondaryLayout )
        secondaryLayout.setStretch(0, 0)
        secondaryLayout.setStretch(1, 100)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._saveButton = QPushButton("Save")
        buttonsLayout.addWidget( self._saveButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

        mainWidget = QWidget()
        mainWidget.setLayout( mainLayout )
        self.setCentralWidget( mainWidget )

    def __setupMenu(self):
        editMenu = self.menuBar().addMenu("Edit")
        self._revertToSavedAction = editMenu.addAction("Revert to Saved")
        self._restoreDefaultsAction = editMenu.addAction("Restore Default Settings")

        helpMenu = self.menuBar().addMenu("Help")
        self._helpAction = helpMenu.addAction("Help on Ramses Add-ons...")

    def __connectEvents(self):
        self.sectionsBox.currentRowChanged.connect(self.stackedLayout.setCurrentIndex)
        self._clientPathButton.clicked.connect( self.browseClientPath )
        self._ramsesPathButton.clicked.connect( self.browseRamsesPath )
        self._saveButton.clicked.connect( self.save )
        self._cancelButton.clicked.connect( self.cancel )
        self._revertToSavedAction.triggered.connect( self.revert )
        self._restoreDefaultsAction.triggered.connect( self.restoreDefaults )
        self._helpAction.triggered.connect( self.help )
        self._onlineBox.clicked.connect( self.switchConnected )

    @Slot()
    def cancel(self):
        self.close()

    @Slot()
    def save(self):
        settings.ramsesClientPath = self._clientPathEdit.text()
        settings.ramsesClientPort = self._clientPortBox.value()
        settings.online = self._onlineBox.isChecked()
        settings.logLevel = self._logLevelBox.currentData()
        settings.autoIncrementTimeout = self._autoIncrementBox.value()
        settings.ramsesFolderPath = self._ramsesPathEdit.text()
        settings.userSettings['useRamSaveSceneHotkey'] = self._saveHotkeyBox.isChecked()
        settings.userSettings['useRamOpenceneHotkey'] = self._openHotkeyBox.isChecked()
        settings.userSettings['useRamSaveAsHotkey'] = self._saveAsHotkeyBox.isChecked()
        settings.save()

        # Update the hotkeys
        if self._saveHotkeyBox.isChecked():
            pyCommand="""
import maya.cmds as cmds
ok = cmds.pluginInfo('Ramses', loaded=True, q=True)\nif not ok:
    cmds.loadPlugin('Ramses')
cmds.ramSave()
"""
            cm = maf.NameCmd.createNameCommand('RamSaveScene', "Ramses Save Scene", pyCommand)
            cmds.hotkey(keyShortcut='s', ctrlModifier = True, name=cm)
            cmds.savePrefs(hotkeys=True)
        else:
            maf.NameCmd.restoreSaveSceneHotkey()

        if self._openHotkeyBox.isChecked():
            pyCommand="""
import maya.cmds as cmds
ok = cmds.pluginInfo('Ramses', loaded=True, q=True)
if not ok:
    cmds.loadPlugin('Ramses')
cmds.ramOpen()
"""
            cm = maf.NameCmd.createNameCommand('RamOpenScene', "Ramses Open Scene", pyCommand)
            cmds.hotkey(keyShortcut='o', ctrlModifier = True, name=cm)
            cmds.savePrefs(hotkeys=True)
        else:
            maf.NameCmd.restoreOpenSceneHotkey()

        if self._saveAsHotkeyBox.isChecked():
            pyCommand="""
import maya.cmds as cmds
ok = cmds.pluginInfo('Ramses', loaded=True, q=True)
if not ok:
    cmds.loadPlugin('Ramses')
cmds.ramSaveAs()
"""
            cm = maf.NameCmd.createNameCommand('RamSaveSceneAsma', "Ramses Save Scene As", pyCommand)
            cmds.hotkey(keyShortcut='s', ctrlModifier = True, shiftModifier=True, name=cm)
            cmds.savePrefs(hotkeys=True)
        else:
            maf.NameCmd.restoreSaveSceneAsHotkey()

        self.close()

    @Slot()
    def revert(self):
        self._clientPathEdit.setText( settings.ramsesClientPath )
        self._clientPortBox.setValue( settings.ramsesClientPort )
        self._onlineBox.setChecked( settings.online )
        self._autoIncrementBox.setValue( settings.autoIncrementTimeout )
        self._ramsesPathEdit.setText( settings.ramsesFolderPath )
        save = True
        saveas = True
        open = True
        if 'useRamSaveSceneHotkey' in settings.userSettings:
            save = settings.userSettings['useRamSaveSceneHotkey']
        if 'useRamSaveAsHotkey' in settings.userSettings:
            saveas = settings.userSettings['useRamSaveAsHotkey']
        if 'useRamOpenceneHotkey' in settings.userSettings:
            open = settings.userSettings['useRamOpenceneHotkey']
        self._saveHotkeyBox.setChecked(save)
        self._saveAsHotkeyBox.setChecked(saveas)
        self._openHotkeyBox.setChecked(open)
        i = 0
        while i < self._logLevelBox.count():
            if self._logLevelBox.itemData( i ) == settings.logLevel:
                self._logLevelBox.setCurrentIndex( i )
                break
            i=i+1
        self.switchConnected( settings.online )

    @Slot()
    def restoreDefaults(self):
        self._clientPathEdit.setText( settings.defaultRamsesClientPath )
        self._clientPortBox.setValue( settings.defaultRamsesClientPort )
        self._onlineBox.setChecked( settings.defaultOnline )
        self._autoIncrementBox.setValue( settings.defaultAutoIncrementTimeout )
        self._ramsesPathEdit.setText( settings.defaultRamsesFolderPath )
        i=0
        while i < self._logLevelBox.count():
            if self._logLevelBox.itemData( i ) == settings.defaultLogLevel:
                self._logLevelBox.setCurrentIndex( i )
                break
            i=i+1
        self.switchConnected( settings.defaultOnline )

    @Slot()
    def help(self):
        QDesktopServices.openUrl( QUrl( settings.addonsHelpUrl ) )
    
    @Slot()
    def browseClientPath(self):
        filter = ""
        system = platform.system()
        if system == "Windows": filter = "Executable Files (*.exe *.bat)"
        file = QFileDialog.getOpenFileName(self,
            "Select the path to the Ramses Client",
            self._clientPathEdit.text(),
            filter)
        if file[0] != "": self._clientPathEdit.setText( file[0] )
    
    @Slot()
    def browseRamsesPath(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select the path to the Ramses Folder",
            self._ramsesPathEdit.text(),
            QFileDialog.ShowDirsOnly
            )
        if folder != "": self._ramsesPathEdit.setText(folder )

    @Slot()
    def switchConnected(self, checked):
        self._clientPathEdit.setEnabled(checked)
        self._clientPortBox.setEnabled(checked)
        self._clientPathButton.setEnabled(checked)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    settingsDialog = SettingsDialog()
    settingsDialog.show()
    sys.exit(app.exec_())