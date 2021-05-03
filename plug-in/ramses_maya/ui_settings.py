from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QApplication,
    QFileDialog,
    QWidget,
    QMainWindow,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QSpinBox,
    QCheckBox,
    QLabel,
    QPushButton,
    QComboBox
)
from PySide2.QtGui import QDesktopServices # pylint: disable=no-name-in-module
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot,
    QUrl,
    Qt
)
import platform
import sys

# In Dev Mode, Ramses lives in its repo
sys.path.append( 'D:/DEV_SRC/RxOT/Ramses/Ramses-Py' )

import ramses as ram
# Keep the settings at hand
settings = ram.RamSettings.instance()

class SettingsDialog( QMainWindow ):

    def __init__( self, parent=None ):
        super(SettingsDialog, self).__init__(parent)
        self._setupUi()
        self._setupMenu()
        self._connectEvents()
        self.revert()

    def _setupUi(self):
        self.setWindowTitle("Ramses Add-ons settings")
        self.setMinimumWidth( 500 )

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(12)

        formLayout = QGridLayout()
        formLayout.setSpacing(3)

        connectLabel = QLabel("Use the Ramses Application:")
        connectLabel.setAlignment( Qt.AlignRight|Qt.AlignVCenter )
        formLayout.addWidget( connectLabel, 0, 0)

        self._onlineBox = QCheckBox("Connected")
        formLayout.addWidget( self._onlineBox, 0, 1 )

        pathLabel = QLabel("Ramses Application path:")
        pathLabel.setAlignment( Qt.AlignRight|Qt.AlignVCenter )
        formLayout.addWidget( pathLabel, 1, 0)
        
        pathLayout = QHBoxLayout()
        self._clientPathEdit = QLineEdit( )
        pathLayout.addWidget( self._clientPathEdit )
        self._clientPathButton = QPushButton(text="Browse...")
        pathLayout.addWidget( self._clientPathButton )
        formLayout.addLayout( pathLayout, 1, 1)

        portLabel = QLabel("Ramses Daemon port:")
        portLabel.setAlignment( Qt.AlignRight|Qt.AlignVCenter )
        formLayout.addWidget( portLabel, 2, 0)

        self._clientPortBox = QSpinBox()
        self._clientPortBox.setMinimum( 1024 )
        self._clientPortBox.setMaximum( 49151 )
        formLayout.addWidget( self._clientPortBox, 2, 1 )

        mainLayout.addLayout( formLayout )

        formLayout.addWidget( QLabel("Developper Options:"), 3, 0)
        formLayout.setRowMinimumHeight( 3, 30 )

        logLabel = QLabel("Log Level:")
        logLabel.setAlignment( Qt.AlignRight|Qt.AlignVCenter )
        formLayout.addWidget( logLabel, 4, 0 )

        self._logLevelBox = QComboBox()
        self._logLevelBox.addItem( "Data Received", ram.LogLevel.DataReceived )
        self._logLevelBox.addItem( "Data Sent", ram.LogLevel.DataSent )
        self._logLevelBox.addItem( "Debug", ram.LogLevel.Debug )
        self._logLevelBox.addItem( "Information", ram.LogLevel.Info )
        self._logLevelBox.addItem( "Critical", ram.LogLevel.Critical )
        self._logLevelBox.addItem( "Fatal", ram.LogLevel.Fatal )
        formLayout.addWidget( self._logLevelBox, 4, 1 )

        mainLayout.addLayout( formLayout )

        mainLayout.addStretch()

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

    def _setupMenu(self):
        editMenu = self.menuBar().addMenu("Edit")
        self._revertToSavedAction = editMenu.addAction("Revert to Saved")
        self._restoreDefaultsAction = editMenu.addAction("Restore Default Settings")

        helpMenu = self.menuBar().addMenu("Help")
        self._helpAction = helpMenu.addAction("Help on Ramses Add-ons...")

    def _connectEvents(self):
        self._clientPathButton.clicked.connect( self.browseClientPath )
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
        settings.save()
        self.close()

    @Slot()
    def revert(self):
        self._clientPathEdit.setText( settings.ramsesClientPath )
        self._clientPortBox.setValue( settings.ramsesClientPort )
        self._onlineBox.setChecked( settings.online )
        i = 0
        while i < self._logLevelBox.count():
            if self._logLevelBox.itemData( i ) == settings.logLevel:
                self._logLevelBox.setCurrentIndex( i )
                break
            i=i+1

    @Slot()
    def restoreDefaults(self):
        self._clientPathEdit.setText( settings.defaultRamsesClientPath )
        self._clientPortBox.setValue( settings.defaultRamsesClientPort )
        self._onlineBox.setChecked( settings.defaultOnline )
        i=0
        while i < self._logLevelBox.count():
            if self._logLevelBox.itemData( i ) == settings.defaultLogLevel:
                self._logLevelBox.setCurrentIndex( i )
                break
            i=i+1

    @Slot()
    def help(self):
        QDesktopServices.openUrl( QUrl( settings.addonsHelpUrl ) )
    
    @Slot()
    def browseClientPath(self):
        filter = ""
        system = platform.system()
        if system == "Windows": filter = "Executable Files (*.exe *.bat)"
        file = QFileDialog.getOpenFileName(self, "Select the path to the Ramses Client", "", filter)
        if file[0] != "": self._clientPathEdit.setText( file[0] )

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