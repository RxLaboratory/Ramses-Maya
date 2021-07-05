# -*- coding: utf-8 -*-

from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module disable=import-error
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QCheckBox,
    QPushButton,
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module disable=import-error
    Slot,
)

class PublishShaderDialog( QDialog ):

    def __init__( self, parent=None ):
        super(PublishShaderDialog, self).__init__(parent)
        self.__setupUi()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Publish Shaders" )

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        topLayout = QFormLayout()
        topLayout.setFieldGrowthPolicy( QFormLayout.AllNonFixedFieldsGrow )
        topLayout.setSpacing(3)

        self.removeHiddenBox = QCheckBox("Remove.")
        self.removeHiddenBox.setChecked(True)
        topLayout.addRow("Hidden Nodes:", self.removeHiddenBox)

        mainLayout.addLayout(topLayout)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._publishButton = QPushButton("Publish Shaders")
        buttonsLayout.addWidget( self._publishButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

        self.setLayout( mainLayout )

    def __connectEvents(self):
        self._publishButton.clicked.connect( self.accept )
        self._cancelButton.clicked.connect( self.reject )

    def removeHidden(self):
        return self.removeHiddenBox.isChecked()