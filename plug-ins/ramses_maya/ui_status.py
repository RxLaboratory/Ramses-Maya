# -*- coding: utf-8 -*-

import sys
from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QApplication,
    QLabel,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QComboBox,
    QSlider,
    QSpinBox,
    QTextEdit,
    QPushButton,
    QCheckBox,
)
from PySide2.QtGui import (  # pylint: disable=no-name-in-module
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

        mainLayout.addLayout( topLayout )

        optionsLayout = QFormLayout()
        optionsLayout.setFieldGrowthPolicy( QFormLayout.AllNonFixedFieldsGrow )
        optionsLayout.setSpacing(3)

        self.publishBox = QCheckBox("Publish the current scene.")
        optionsLayout.addRow( "Publication:", self.publishBox )

        self.previewBox = QCheckBox("Create preview files (thumbnail or playblast).")
        optionsLayout.addRow( "Preview:", self.previewBox )

        self.commentLabel = QLabel("Comment:")
        self.commentEdit = QTextEdit()
        optionsLayout.addRow( self.commentLabel, self.commentEdit )

        mainLayout.addLayout( optionsLayout )

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._saveButton = QPushButton("Update Status and Save")
        buttonsLayout.addWidget( self._saveButton )
        self._skipButton = QPushButton("Skip and just Save")
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
        self.commentLabel.setVisible(online)

    def setPublish(self, pub=True):
        self.publishBox.setChecked(pub)

    def preview(self):
        return self.previewBox.isChecked()

if __name__ == '__main__':
    statusDialog = StatusDialog()
    ok = statusDialog.exec_()
    print(ok)
