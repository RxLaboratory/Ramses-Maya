from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QApplication,
    QFileDialog,
    QWidget,
    QMainWindow,
    QFormLayout,
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
    QUrl
)
import platform
import sys

# In Dev Mode, Ramses lives in its repo
sys.path.append( 'D:/DEV_SRC/RxOT/Ramses/Ramses-Py' )

from ramses import ( # pylint: disable=import-error,no-name-in-module
    RamSettings,
    LogLevel
)
# Keep the settings at hand
settings = RamSettings.instance()

class SettingsDialog( QMainWindow ):

    def __init__( self, parent=None ):
        super(SettingsDialog, self).__init__(parent)
        self._setupUi()
        self._setupMenu()
        self._connectEvents()
        self.revert()

    def _setupUi(self):
        self.setWindowTitle("Ramses Add-ons settings")

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
 
        formLayout = QFormLayout()
        formLayout.setSpacing(3)

        formLayout.setWidget( 0, QFormLayout.LabelRole, QLabel("Ramses Application path:"))
        
        pathLayout = QHBoxLayout()
        self._clientPathEdit = QLineEdit( )
        pathLayout.addWidget( self._clientPathEdit )
        self._clientPathButton = QPushButton(text="Browse...")
        pathLayout.addWidget( self._clientPathButton )
        formLayout.setLayout( 0, QFormLayout.FieldRole, pathLayout)

        formLayout.setWidget( 1, QFormLayout.LabelRole, QLabel("Ramses Daemon port:"))

        self._clientPortBox = QSpinBox()
        self._clientPortBox.setMinimum( 1024 )
        self._clientPortBox.setMaximum( 49151 )
        formLayout.setWidget( 1, QFormLayout.FieldRole, self._clientPortBox )

        formLayout.setWidget( 2, QFormLayout.LabelRole, QLabel("Auto-connect to the App:"))

        self._autoConnectBox = QCheckBox("Auto-connection")
        formLayout.setWidget( 2, QFormLayout.FieldRole, self._autoConnectBox )

        formLayout.setWidget( 3, QFormLayout.LabelRole, QLabel("Developper Options:"))

        formLayout.setWidget(4,  QFormLayout.LabelRole, QLabel("Log Level:") )

        self._logLevelBox = QComboBox()
        self._logLevelBox.addItem( "Data Received", LogLevel.DataReceived )
        self._logLevelBox.addItem( "Data Sent", LogLevel.DataSent )
        self._logLevelBox.addItem( "Debug", LogLevel.Debug )
        self._logLevelBox.addItem( "Information", LogLevel.Info )
        self._logLevelBox.addItem( "Critical", LogLevel.Critical )
        self._logLevelBox.addItem( "Fatal", LogLevel.Fatal )
        formLayout.setWidget( 4, QFormLayout.FieldRole, self._logLevelBox )

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

    @Slot()
    def cancel(self):
        self.close()

    @Slot()
    def save(self):
        settings.ramsesClientPath = self._clientPathEdit.text()
        settings.ramsesClientPort = self._clientPortBox.value()
        settings.autoConnect = self._autoConnectBox.isChecked()
        settings.logLevel = self._logLevelBox.currentData()
        settings.save()
        self.close()

    @Slot()
    def revert(self):
        self._clientPathEdit.setText( settings.ramsesClientPath )
        self._clientPortBox.setValue( settings.ramsesClientPort )
        self._autoConnectBox.setChecked( settings.autoConnect )
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
        self._autoConnectBox.setChecked( settings.defaultAutoConnect )
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    settingsDialog = SettingsDialog()
    settingsDialog.show()
    sys.exit(app.exec_())