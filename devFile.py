import sys
sys.path.append(
    'D:/DEV_SRC/RxOT/Ramses/Ramses-Py'
)

import maya.cmds as cmds
import ramses as ram

import sys
from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QComboBox,
    QPushButton,
)
   
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot,
    Qt
)

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

retrieveVersion()