from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module disable=import-error
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QPushButton,
    QAbstractItemView,
    QLabel,
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module disable=import-error
    Slot,
    Qt,
)

from .utils_constants import *
import ramses as ram

class PipeDialog( QDialog ):

    def __init__(self, parent = None, mode='Publish'):
        super(PipeDialog, self).__init__(parent)
        self.__setupUi(mode)
        self.__connectEvents()

    def __setupUi(self, mode='Publish' ):

        self.setWindowTitle( "Select Publish Types" )

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        helpLabel = QLabel("Select the types you need to publish:")
        mainLayout.addWidget( helpLabel )

        self.pipeList = QListWidget()
        self.pipeList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for pipeFile in PIPE_FILES:
            i = QListWidgetItem( self.pipeList )
            i.setText( pipeFile.shortName() + pipeFile.fileType().extensions()[0] + ' | ' + pipeFile.fileType().name() )
            i.setData(Qt.UserRole, pipeFile.shortName() )
        mainLayout.addWidget(self.pipeList)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._publishButton = QPushButton(mode)
        self._publishButton.setEnabled(False)
        buttonsLayout.addWidget( self._publishButton )  
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

        self.setLayout( mainLayout )


    def __connectEvents(self):
        self._publishButton.clicked.connect( self.accept ) 
        self._cancelButton.clicked.connect( self.reject )
        self.pipeList.itemSelectionChanged.connect( self.__itemChanged )

    Slot()
    def __itemChanged(self):
        self._publishButton.setEnabled(True)

    def getPipes(self):
        pipeFiles = []
        for i in range( 0, self.pipeList.count()):
            if self.pipeList.item(i).isSelected():
                pipeFiles.append( PIPE_FILES[i] )

        return [ ram.RamPipe( '', '', pipeFiles ) ]