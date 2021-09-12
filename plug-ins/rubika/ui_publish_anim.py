# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=import-error

from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module disable=import-error
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QSpinBox,
    QVBoxLayout,
    QFormLayout,
    QCheckBox,
    QWidget,
    QPushButton,
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module disable=import-error
    Slot,
)

class PublishAnimDialog( QDialog ):
    def __init__(self, parent=None):
        super(PublishAnimDialog, self).__init__(parent)
        self.__setupUi()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Publish Animation" )

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        topLayout = QFormLayout()
        topLayout.setFieldGrowthPolicy( QFormLayout.AllNonFixedFieldsGrow )
        topLayout.setSpacing(3)

        frameRangeWidget = QWidget()
        frameRangeLayout = QHBoxLayout()
        frameRangeLayout.setContentsMargins(0,0,0,0)
        frameRangeLayout.setSpacing(3)
        self.rangeInEdit = QSpinBox()
        self.rangeInEdit.setMinimum(-10000)
        self.rangeInEdit.setMaximum(10000)
        inFrame = int(cmds.playbackOptions(q=True,ast=True))
        self.rangeInEdit.setValue( inFrame )
        frameRangeLayout.addWidget( self.rangeInEdit )
        self.rangeOutEdit = QSpinBox()
        self.rangeOutEdit.setMinimum(-10000)
        self.rangeOutEdit.setMaximum(10000)
        outFrame = int(cmds.playbackOptions(q=True,aet=True))
        self.rangeOutEdit.setValue(outFrame)
        frameRangeLayout.addWidget( self.rangeOutEdit )
        frameRangeWidget.setLayout( frameRangeLayout )
        topLayout.addRow( "Frame Range:", frameRangeWidget )

        handlesWidget = QWidget()
        handlesLayout = QHBoxLayout()
        handlesLayout.setContentsMargins(0,0,0,0)
        handlesLayout.setSpacing(3)
        self.handlesInEdit = QSpinBox()
        self.handlesInEdit.setMinimum(0)
        self.handlesInEdit.setMaximum(10000)
        self.handlesInEdit.setPrefix('-')
        handlesLayout.addWidget( self.handlesInEdit )
        self.handlesOutEdit = QSpinBox()
        self.handlesOutEdit.setMinimum(0)
        self.handlesOutEdit.setMaximum(10000)
        self.handlesOutEdit.setValue(0)
        self.handlesOutEdit.setPrefix('+')
        handlesLayout.addWidget( self.handlesOutEdit )
        handlesWidget.setLayout( handlesLayout )
        topLayout.addRow( "Handles:", handlesWidget )

        self.frameStepEdit = QDoubleSpinBox()
        self.frameStepEdit.setMinimum(0.1)
        self.frameStepEdit.setMaximum( 100 )
        self.frameStepEdit.setDecimals(1)
        self.frameStepEdit.setValue(1.0)
        topLayout.addRow("Frame Step:", self.frameStepEdit )

        self.filterEulerBox = QCheckBox("Filter Euler Rotations")
        topLayout.addRow("Rotations:", self.filterEulerBox )

        self.removeHiddenBox = QCheckBox("Remove Hidden Nodes")
        topLayout.addRow("Visibility:", self.removeHiddenBox)

        self.keepCurvesBox = QCheckBox("Keep Curves (Bézier or NURBS)")
        topLayout.addRow("Curves:", self.keepCurvesBox)

        self.keepSurfacesBox = QCheckBox("Keep NURBS Surfaces")
        topLayout.addRow("Surfaces:", self.keepSurfacesBox)

        self.keepDeformersBox = QCheckBox("Keep Deformers animation")
        topLayout.addRow("Deformers:", self.keepDeformersBox)
        self.keepDeformersBox.setChecked(True)

        mainLayout.addLayout(topLayout)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._publishButton = QPushButton("Publish Animation")
        buttonsLayout.addWidget( self._publishButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

        self.setLayout( mainLayout )

    def __connectEvents(self):
        self._publishButton.clicked.connect( self.accept )
        self._cancelButton.clicked.connect( self.reject )

    def getFrameRange(self):
        return (
            self.handlesInEdit.value(),
            self.rangeInEdit.value(),
            self.rangeOutEdit.value(),
            self.handlesOutEdit.value()
        )

    def filterEuler(self):
        return self.filterEulerBox.isChecked()

    def getFrameStep(self):
        return self.frameStepEdit.value()

    def curves(self):
        return self.keepCurvesBox.isChecked()

    def surfaces(self):
        return self.keepSurfacesBox.isChecked()

    def deformers(self):
        return self.keepDeformersBox.isChecked()

    def removeHidden(self):
        return self.removeHiddenBox.isChecked()