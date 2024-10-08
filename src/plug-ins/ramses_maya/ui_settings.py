# -*- coding: utf-8 -*-

import sys
import platform
import os

try:
    from PySide2 import QtWidgets as qw
    from PySide2 import QtGui as qg
    from PySide2 import QtCore as qc
except:  # pylint: disable=bare-except
    from PySide6 import QtWidgets as qw
    from PySide6 import QtGui as qg
    from PySide6 import QtCore as qc

import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram
import dumaf as maf
from ramses_maya.ui_dialog import Dialog

# Keep the settings at hand
SETTINGS = ram.RamSettings.instance()

saveCmd = """
import maya.cmds as cmds
ok = cmds.pluginInfo('Ramses', loaded=True, q=True)
if not ok:
    cmds.loadPlugin('Ramses')
cmds.ramSave()
"""

openCmd = """
import maya.cmds as cmds
ok = cmds.pluginInfo('Ramses', loaded=True, q=True)
if not ok:
    cmds.loadPlugin('Ramses')
cmds.ramOpen()
"""

saveAsCmd = """
import maya.cmds as cmds
ok = cmds.pluginInfo('Ramses', loaded=True, q=True)
if not ok:
    cmds.loadPlugin('Ramses')
cmds.ramSaveAs()
"""

class SettingsDialog( Dialog ):
    """The dialog to change the module settings"""

    def __init__( self, parent=None ):
        super(SettingsDialog, self).__init__(parent)
        self.__setupUi()
        self.__setupMenu()
        self.__connectEvents()
        self.revert()

    def __setupUi(self):
        self.setWindowTitle("Ramses Add-ons settings")
        self.setMinimumWidth( 500 )

        secondaryLayout = qw.QHBoxLayout()
        secondaryLayout.setSpacing(3)

        self.sectionsBox = qw.QListWidget()
        self.sectionsBox.addItem("Versionning")
        self.sectionsBox.addItem("Ramses Application")
        self.sectionsBox.addItem("Scripts")
        self.sectionsBox.addItem("Development")
        self.sectionsBox.setMaximumWidth( 150 )
        secondaryLayout.addWidget(self.sectionsBox)

        self.stackedLayout = qw.QStackedLayout()

        versionningWidget = qw.QWidget()
        vL = qw.QVBoxLayout()
        versionningWidget.setLayout(vL)
        self.stackedLayout.addWidget( versionningWidget )
        versionningLayout = qw.QFormLayout()
        versionningLayout.setSpacing(3)
        vL.addLayout(versionningLayout)
        vL.addStretch()

        self._autoIncrementBox = qw.QSpinBox()
        self._autoIncrementBox.setMinimum(1)
        self._autoIncrementBox.setMaximum(1440) #24h
        self._autoIncrementBox.setSuffix(" minutes.")
        versionningLayout.addRow( "Auto-increment version every:", self._autoIncrementBox )

        self._saveHotkeyBox = qw.QCheckBox("Replace with the \"ramSave\" command.")
        versionningLayout.addRow( "\"Save\" hotkey (Ctrl+S):", self._saveHotkeyBox )

        self._saveAsHotkeyBox = qw.QCheckBox("Replace with the \"ramSaveAs\" command.")
        versionningLayout.addRow( "\"Save As\" hotkey (Ctrl+Shift+S):", self._saveAsHotkeyBox )

        self._openHotkeyBox = qw.QCheckBox("Replace with the \"ramOpen\" command.")
        versionningLayout.addRow( "\"Open\" hotkey (Ctrl+O):", self._openHotkeyBox )

        appWidget = qw.QWidget()
        aL = qw.QVBoxLayout()
        appWidget.setLayout(aL)
        self.stackedLayout.addWidget( appWidget )
        appLayout = qw.QFormLayout()
        appLayout.setSpacing(3)
        aL.addLayout(appLayout)
        aL.addStretch()

        pathLabel = qw.QLabel("Ramses Application path:")       
        pathLayout = qw.QHBoxLayout()
        self._clientPathEdit = qw.QLineEdit( )
        pathLayout.addWidget( self._clientPathEdit )
        self._clientPathButton = qw.QPushButton(text="Browse...")
        pathLayout.addWidget( self._clientPathButton )
        appLayout.setWidget( 1, qw.QFormLayout.LabelRole, pathLabel)
        appLayout.setLayout( 1, qw.QFormLayout.FieldRole, pathLayout)

        portLabel = qw.QLabel("Ramses Daemon port:")
        self._clientPortBox = qw.QSpinBox()
        self._clientPortBox.setMinimum( 1024 )
        self._clientPortBox.setMaximum( 49151 )
        appLayout.addRow( portLabel, self._clientPortBox )

        scriptsWidget = qw.QWidget()
        sLH = qw.QHBoxLayout()
        scriptsWidget.setLayout(sLH)
        sLV = qw.QVBoxLayout()
        sLV.setSpacing(2)
        sLH.addLayout(sLV)
        self.stackedLayout.addWidget( scriptsWidget )
        self.scriptsList = qw.QListWidget()
        self.scriptsList.setSelectionMode(qw.QAbstractItemView.ExtendedSelection)
        sLV.addWidget(self.scriptsList)
        scriptsButtonsLayout = qw.QHBoxLayout()
        scriptsButtonsLayout.setSpacing(2)
        sLV.addLayout(scriptsButtonsLayout)
        self.scriptsRemoveButton = qw.QPushButton("Remove")
        scriptsButtonsLayout.addWidget( self.scriptsRemoveButton )
        self.scriptsAddButton = qw.QPushButton("Add...")
        scriptsButtonsLayout.addWidget( self.scriptsAddButton )
        scriptsHelpLabel = qw.QLabel( """Custom scripts can define event functions
to be run automatically on specific tasks:

    - on_open( ... )
    - on_update_status( ... )
    - on_publish( ... )
    - on_replace_item( ... )
    - on_import_item( ... )

Read the Maya add-on documentation
and the Ramses API reference
for more information and details about
the available arguments for each function"""
        )
        sLH.addWidget( scriptsHelpLabel )

        devWidget = qw.QWidget()
        dL = qw.QVBoxLayout()
        devWidget.setLayout(dL)
        self.stackedLayout.addWidget( devWidget )
        devLayout = qw.QFormLayout()
        devLayout.setSpacing(3)
        dL.addLayout(devLayout)
        dL.addStretch()

        debugModeLabel = qw.QLabel("Debug Mode:")
        self._debugModeBox = qw.QCheckBox("Enabled")
        devLayout.addRow( debugModeLabel, self._debugModeBox )

        logLabel = qw.QLabel("Log Level:")

        self._logLevelBox = qw.QComboBox()
        self._logLevelBox.addItem( "Data Received", ram.LogLevel.DataReceived )
        self._logLevelBox.addItem( "Data Sent", ram.LogLevel.DataSent )
        self._logLevelBox.addItem( "Debug", ram.LogLevel.Debug )
        self._logLevelBox.addItem( "Information", ram.LogLevel.Info )
        self._logLevelBox.addItem( "Critical", ram.LogLevel.Critical )
        self._logLevelBox.addItem( "Fatal", ram.LogLevel.Fatal )
        
        devLayout.addRow( logLabel, self._logLevelBox )

        secondaryLayout.addLayout(self.stackedLayout)

        self.main_layout.addLayout( secondaryLayout )
        secondaryLayout.setStretch(0, 0)
        secondaryLayout.setStretch(1, 100)

        buttonsLayout = qw.QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._saveButton = qw.QPushButton("Save")
        buttonsLayout.addWidget( self._saveButton )
        self._cancelButton = qw.QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        self.main_layout.addLayout( buttonsLayout )

    def __setupMenu(self):
        self._revertToSavedAction = self.edit_menu.addAction("Revert to Saved")
        self._restoreDefaultsAction = self.edit_menu.addAction("Restore Default Settings")

    def __connectEvents(self):
        self.sectionsBox.currentRowChanged.connect(self.stackedLayout.setCurrentIndex)
        self._clientPathButton.clicked.connect( self.browseClientPath )
        self._saveButton.clicked.connect( self.save )
        self._cancelButton.clicked.connect( self.cancel )
        self._revertToSavedAction.triggered.connect( self.revert )
        self._restoreDefaultsAction.triggered.connect( self.restoreDefaults )
        self.scriptsAddButton.clicked.connect( self.addScript )
        self.scriptsRemoveButton.clicked.connect( self.removeScript )

    @qc.Slot()
    def cancel(self):
        """Cancels"""
        self.close()

    @qc.Slot()
    def save(self):
        """Saves the settings"""
        SETTINGS.ramsesClientPath = self._clientPathEdit.text()
        SETTINGS.ramsesClientPort = self._clientPortBox.value()
        SETTINGS.logLevel = self._logLevelBox.currentData()
        SETTINGS.autoIncrementTimeout = self._autoIncrementBox.value()
        SETTINGS.debugMode = self._debugModeBox.isChecked()
        SETTINGS.userSettings['useRamSaveSceneHotkey'] = self._saveHotkeyBox.isChecked()
        SETTINGS.userSettings['useRamOpenceneHotkey'] = self._openHotkeyBox.isChecked()
        SETTINGS.userSettings['useRamSaveAsHotkey'] = self._saveAsHotkeyBox.isChecked()
        SETTINGS.userScripts = []
        for i in range(self.scriptsList.count()):
            SETTINGS.userScripts.append(self.scriptsList.item(i).toolTip())
        SETTINGS.save()

        # Update the hotkeys
        if self._saveHotkeyBox.isChecked():
            maf.HotKey.createHotkey(saveCmd, 'ctrl+s', 'RamSaveScene', "Ramses Save Scene", "Ramses" )
        else:
            maf.HotKey.restoreSaveSceneHotkey()

        if self._openHotkeyBox.isChecked():
            maf.HotKey.createHotkey(openCmd, 'ctrl+o', 'RamOpenScene', "Ramses Open Scene", "Ramses" )
        else:
            maf.HotKey.restoreOpenSceneHotkey()

        if self._saveAsHotkeyBox.isChecked():
            maf.HotKey.createHotkey(saveAsCmd, 'ctrl+shift+s', 'RamSaveSceneAs', "Ramses Save Scene As", "Ramses" )
        else:
            maf.HotKey.restoreSaveSceneAsHotkey()

        self.close()

    @qc.Slot()
    def revert(self):
        """Reloads the settings"""
        self._clientPathEdit.setText( SETTINGS.ramsesClientPath )
        self._clientPortBox.setValue( SETTINGS.ramsesClientPort )
        self._autoIncrementBox.setValue( SETTINGS.autoIncrementTimeout )
        self._debugModeBox.setChecked( SETTINGS.debugMode )
        save = True
        saveas = True
        open = True
        if 'useRamSaveSceneHotkey' in SETTINGS.userSettings:
            save = SETTINGS.userSettings['useRamSaveSceneHotkey']
        if 'useRamSaveAsHotkey' in SETTINGS.userSettings:
            saveas = SETTINGS.userSettings['useRamSaveAsHotkey']
        if 'useRamOpenceneHotkey' in SETTINGS.userSettings:
            open = SETTINGS.userSettings['useRamOpenceneHotkey']
        self._saveHotkeyBox.setChecked(save)
        self._saveAsHotkeyBox.setChecked(saveas)
        self._openHotkeyBox.setChecked(open)
        i = 0
        while i < self._logLevelBox.count():
            if self._logLevelBox.itemData( i ) == SETTINGS.logLevel:
                self._logLevelBox.setCurrentIndex( i )
                break
            i=i+1
        self.scriptsList.clear()
        for s in SETTINGS.userScripts:
            self.__addScriptToList(s)

    @qc.Slot()
    def restoreDefaults(self):
        """Restores the default settings"""
        self._clientPathEdit.setText( SETTINGS.defaultRamsesClientPath )
        self._clientPortBox.setValue( SETTINGS.defaultRamsesClientPort )
        self._autoIncrementBox.setValue( SETTINGS.defaultAutoIncrementTimeout )
        self._debugModeBox.setChecked( SETTINGS.defaultDebugMode )
        self.scriptsList.clear()
        i=0
        while i < self._logLevelBox.count():
            if self._logLevelBox.itemData( i ) == SETTINGS.defaultLogLevel:
                self._logLevelBox.setCurrentIndex( i )
                break
            i=i+1

    @qc.Slot()
    def help(self):
        """Shows the addon help"""
        qg.QDesktopServices.openUrl( qc.QUrl( SETTINGS.addonsHelpUrl ) )

    @qc.Slot()
    def browseClientPath(self):
        """Opens a file browser to select the Ramses Application path"""
        file_filter = ""
        system = platform.system()
        if system == "Windows":
            file_filter = "Executable Files (*.exe *.bat)"
        file = qw.QFileDialog.getOpenFileName(self,
            "Select the path to the Ramses Application",
            self._clientPathEdit.text(),
            file_filter)
        if file[0] != "":
            self._clientPathEdit.setText( file[0] )

    @qc.Slot()
    def addScript(self):
        """Adds a new custom script"""

        file_filter = "Python Script Files (*.py);;All Files (*.*)"
        file = qw.QFileDialog.getOpenFileName(self,
            "Select the Python script to add",
            "",
            file_filter)
        script_path = file[0]

        if script_path != "":
            self.__addScriptToList(script_path)

    def __addScriptToList(self, script_path):
        item = qw.QListWidgetItem( os.path.basename(script_path), self.scriptsList )
        item.setToolTip( script_path )

    @qc.Slot()
    def removeScript(self):
        """Removes the selected scripts"""
        for item in reversed(self.scriptsList.selectedItems()):
            item = self.scriptsList.takeItem(self.scriptsList.row(item))
            del item

if __name__ == '__main__':
    app = qw.QApplication(sys.argv)
    settingsDialog = SettingsDialog()
    settingsDialog.show()
    sys.exit(app.exec_())
