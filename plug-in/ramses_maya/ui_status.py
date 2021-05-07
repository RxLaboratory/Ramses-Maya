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
)
from PySide2.QtGui import (
    QColor,
    QPalette,
    )
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot,
    Qt
)

# In Dev Mode, Ramses lives in its repo
sys.path.append( 'D:/DEV_SRC/RxOT/Ramses/Ramses-Py' )

import ramses as ram
ramses = ram.Ramses.instance()

class StateBox( QComboBox ):
    def __init__(self, parent = None):
        super(StateBox,self).__init__(parent)

        # Populate states from Ramses
        for state in ramses.states():
            self.addItem( state.shortName(), state.color() )

        self.indexChanged(0)
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
        return ramses.state( self.currentText )

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

    def skip(self):
        self.done(2)

if __name__ == '__main__':
    statusDialog = StatusDialog()
    ok = statusDialog.exec_()
    print(ok)
