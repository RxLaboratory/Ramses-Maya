# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=no-name-in-module disable=import-error

from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module disable=import-error
    QDialog,
    QHBoxLayout,
    QListWidget,
    QVBoxLayout,
    QFormLayout,
    QCheckBox,
    QAbstractItemView,
    QPushButton,
    QWidget,
    QRadioButton,
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module disable=import-error
    Slot,
    Qt
)

class PublishRigDialog( QDialog ):

    def __init__(self, parent=None):
        super(PublishRigDialog, self).__init__(parent)
        self.__setupUi()
        self.__loadSets()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Publish Rig" )

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        topLayout = QFormLayout()
        topLayout.setFieldGrowthPolicy( QFormLayout.AllNonFixedFieldsGrow )
        topLayout.setSpacing(3)

        hideJointsWidget = QWidget()
        hideJointsLayout = QVBoxLayout()
        hideJointsLayout.setContentsMargins(0,0,0,0)
        hideJointsLayout.setSpacing(3)
        self.hideJointsBox = QRadioButton("Hide.")
        self.hideJointsBox.setChecked(True)
        hideJointsLayout.addWidget(self.hideJointsBox)
        self.drawJointsBox = QRadioButton("Disbale draw.")
        hideJointsLayout.addWidget(self.drawJointsBox)
        self.keepJointsBox = QRadioButton("Keep as is.")
        hideJointsLayout.addWidget(self.keepJointsBox)
        hideJointsWidget.setLayout(hideJointsLayout)
        topLayout.addRow("Joints:", hideJointsWidget)

        self.lockHiddenBox = QCheckBox( "Lock visibility of hidden nodes." )
        self.lockHiddenBox.setChecked(True)
        topLayout.addRow("Node Visibility:", self.lockHiddenBox)

        self.deleteKeyframesBox = QCheckBox( "Delete animation keyframes." )
        self.deleteKeyframesBox.setChecked(True)
        topLayout.addRow("Animation:", self.deleteKeyframesBox)

        self.deformerSetList = QListWidget()
        self.deformerSetList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        topLayout.addRow("Deformer Sets to remove:", self.deformerSetList)

        self.renderingSetList = QListWidget()
        self.renderingSetList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        topLayout.addRow("Rendering Sets to remove:", self.renderingSetList)

        mainLayout.addLayout(topLayout)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._publishButton = QPushButton("Publish Rig")
        buttonsLayout.addWidget( self._publishButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

        self.setLayout( mainLayout )

    def __connectEvents(self):
        self._publishButton.clicked.connect( self.accept )
        self._cancelButton.clicked.connect( self.reject )

    def __loadSets(self):
        renderingSets = cmds.listSets(t=1)
        deformerSets = cmds.listSets(t=2)

        if renderingSets is not None:
            self.renderingSetList.addItem("None")
            for set in renderingSets:
                self.renderingSetList.addItem( set )

        if deformerSets is not None:
            self.deformerSetList.addItem("None")
            for set in deformerSets:
                self.deformerSetList.addItem( set )

    def hideJointsMode(self):
        if self.keepJointsBox.isChecked():
            return 0
        elif self.hideJointsBox.isChecked():
            return 1
        return 2

    def lockHidden(self):
        return self.lockHiddenBox.isChecked()

    def removeAnim(self):
        return self.deleteKeyframesBox.isChecked()

    def getDeformerSets(self):
        sets = []
        if self.deformerSetList.count() == 0:
            return sets
        if self.deformerSetList.item(0).isSelected():
            return sets
        for i in range(0, self.deformerSetList.count() ):
            item = self.deformerSetList.item(i)
            if item.isSelected():
                sets.append(item.data(Qt.UserRole))
        return sets

    def getRenderingSets(self):
        sets = []
        if self.renderingSetList.count() == 0:
            return sets
        if self.renderingSetList.item(0).isSelected():
            return sets
        for i in range(0, self.renderingSetList.count() ):
            item = self.renderingSetList.item(i)
            if item.isSelected():
                sets.append(item.data(Qt.UserRole))
        return sets