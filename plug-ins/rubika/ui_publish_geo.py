# -*- coding: utf-8 -*-

from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module disable=import-error
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QCheckBox,
    QLineEdit,
    QWidget,
    QPushButton,
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module disable=import-error
    Slot,
)

class PublishGeoDialog( QDialog ):

    def __init__(self, parent=None):
        super(PublishGeoDialog, self).__init__(parent)
        self.__setupUi()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Publish Geometry" )

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        topLayout = QFormLayout()
        topLayout.setFieldGrowthPolicy( QFormLayout.AllNonFixedFieldsGrow )
        topLayout.setSpacing(3)

        self.removeHiddenBox = QCheckBox("Remove.")
        self.removeHiddenBox.setChecked(True)
        topLayout.addRow("Hidden Nodes:", self.removeHiddenBox)

        self.removeLocatorsBox = QCheckBox("Remove.")
        self.removeLocatorsBox.setChecked(True)
        topLayout.addRow("Locators:", self.removeLocatorsBox)
        
        self.renameShapesBox = QCheckBox("Rename after the parent transform node.")
        self.renameShapesBox.setChecked(True)
        topLayout.addRow("Shape Nodes:", self.renameShapesBox)
        
        self.onlyRootGroupsBox = QCheckBox("Export only the groups (and their children) from the root of the scene.")
        self.onlyRootGroupsBox.setChecked(False)
        topLayout.addRow("Only Root Groups:", self.onlyRootGroupsBox)
        
        noFreezeWidget = QWidget()
        noFreezeLayout = QHBoxLayout()
        noFreezeLayout.setContentsMargins(0,0,0,0)
        self.noFreezeEdit = QLineEdit('_eye_, _eyes_')
        self.noFreezeCaseBox = QCheckBox("Case Sensitive")
        noFreezeLayout.addWidget(self.noFreezeEdit)
        noFreezeLayout.addWidget(self.noFreezeCaseBox)
        noFreezeWidget.setLayout(noFreezeLayout)
        topLayout.addRow("Don't freeze transformations for:", noFreezeWidget)

        self.keepCurvesBox = QCheckBox("Keep Curves (Bézier or NURBS)")
        topLayout.addRow("Curves:", self.keepCurvesBox)

        self.keepSurfacesBox = QCheckBox("Keep NURBS Surfaces")
        topLayout.addRow("Surfaces:", self.keepSurfacesBox)

        mainLayout.addLayout(topLayout)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._publishButton = QPushButton("Publish Geometry")
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

    def removeLocators(self):
        return self.removeLocatorsBox.isChecked()

    def renameShapes(self):
        return self.renameShapesBox.isChecked()

    def onlyRootGroups(self):
        return self.onlyRootGroupsBox.isChecked()

    def noFreeze(self):
        return self.noFreezeEdit.text()

    def noFreezeCaseSensitive(self):
        return self.noFreezeCaseBox.isChecked()

    def curves(self):
        return self.keepCurvesBox.isChecked()

    def surfaces(self):
        return self.keepSurfacesBox.isChecked()