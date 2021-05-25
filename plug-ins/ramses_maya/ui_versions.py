import os, sys

from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QComboBox,
    QPushButton,
)

import ramses as ram

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