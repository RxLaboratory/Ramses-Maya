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
    QPushButton
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
from ramses import Ramses

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
        settings = Ramses.instance.settings()
        settings.ramsesClientPath = self._clientPathEdit.text()
        settings.ramsesClientPort = self._clientPortBox.value()
        settings.autoConnect = self._autoConnectBox.isChecked()
        settings.save()
        self.close()

    @Slot()
    def revert(self):
        settings = Ramses.instance.settings()
        self._clientPathEdit.setText( settings.ramsesClientPath )
        self._clientPortBox.setValue( settings.ramsesClientPort )
        self._autoConnectBox.setChecked( settings.autoConnect )

    @Slot()
    def restoreDefaults(self):
        self._clientPathEdit.setText("")
        self._clientPortBox.setValue(18185)
        self._autoConnectBox.setChecked(True)

    @Slot()
    def help(self):
        QDesktopServices.openUrl( QUrl( Ramses.addonsHelpUrl ) )
    
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