# -*- coding: utf-8 -*-

import os

from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module disable=import-error
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QCheckBox,
    QPushButton,
    QAbstractItemView,
)

from PySide2.QtCore import ( # pylint: disable=no-name-in-module disable=import-error
    Slot,
    Qt,
)

from .utils_attributes import * # pylint: disable=import-error

class UpdateDialog( QDialog ):

    def __init__(self, parent = None):
        super(UpdateDialog, self).__init__(parent)
        self.__setupUi()
        self.__listItems()
        self.__connectEvents()

    def __setupUi(self):

        self.setWindowTitle("Update Items")

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        self.onlyNewButton = QCheckBox("Show only updated items.")
        self.onlyNewButton.setChecked(True)
        mainLayout.addWidget( self.onlyNewButton )

        self.itemList = QListWidget()
        self.itemList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        mainLayout.addWidget(self.itemList)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._updateButton = QPushButton("Update All")
        self._updateButton.setEnabled(False)
        buttonsLayout.addWidget( self._updateButton )
        self._updateSelectedButton = QPushButton("Update Selected")
        self._updateSelectedButton.setEnabled(False)
        buttonsLayout.addWidget( self._updateSelectedButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

        self.setLayout( mainLayout )

    def __connectEvents(self):
        self._updateButton.clicked.connect( self.accept )
        self._cancelButton.clicked.connect( self.reject )
        self.onlyNewButton.clicked.connect( self.showOnlyNew )
        self.itemList.itemSelectionChanged.connect( self.selectionChanged )
        self._updateSelectedButton.clicked.connect( self._updateSelected )

    Slot()
    def _updateSelected(self):
        self.done(2)

    Slot()
    def selectionChanged(self):
        items = self.itemList.selectedItems()
        self._updateSelectedButton.setEnabled(len(items) > 0)

    Slot()
    def showOnlyNew(self, checked = True):
        for i in range(0, self.itemList.count()):
            if not checked:
                self.itemList.item(i).setHidden(False)
            else:
                itemText = self.itemList.item(i).text()
                hidden =  not itemText.startswith('New: ')
                self.itemList.item(i).setHidden(hidden)
                if hidden:
                    self.itemList.item(i).setSelected(False)

    def __listItems(self):
        nodes = listRamsesNodes()
        if len(nodes) == 0:
            self._updateButton.setEnabled(False)
            self._updateSelectedButton.setEnabled(False)
            return
        self._updateButton.setEnabled(True)
        for node in nodes:
            name = getRamsesAttr(node, RamsesAttribute.ITEM )
            step = getRamsesAttr(node, RamsesAttribute.STEP )
            item = QListWidgetItem( self.itemList )
            item.setData(Qt.UserRole, node)
            item.setToolTip(node)

            itemText = name + ' (' + step + ') - ' + maf.getNodeBaseName( node )
            # Check timestamp
            geoFile = getRamsesAttr(node, RamsesAttribute.GEO_FILE)
            geoTime = getRamsesAttr(node, RamsesAttribute.GEO_TIME)
            shadingFile = getRamsesAttr(node, RamsesAttribute.SHADING_FILE)
            shadingTime = getRamsesAttr(node, RamsesAttribute.SHADING_TIME)
            updated = False
            if geoFile is not None:
                geoFTimeStamp = os.path.getmtime( geoFile )
                geoFTimeStamp = int(geoFTimeStamp)
                if geoFTimeStamp > geoTime:
                    updated = True
            # Shaders are referenced, they're always up-to-date
            # if shadingFile is not None:
            #     shadingFTimeStamp = os.path.getmtime( shadingFile )
            #     shadingFTimeStamp = int( shadingFTimeStamp )
            #     if shadingFTimeStamp > shadingTime:
            #         updated = True
            if updated:
                itemText = 'New: ' + itemText 
            elif self.onlyNewButton.isChecked():
                item.setHidden(True)
            item.setText(itemText)

    def getAllNodes(self):
        nodes = []
        for i in range(0, self.itemList.count()):
            item = self.itemList.item(i)
            if item.text().startswith('New: '):
                nodes.append( self.itemList.item(i).data(Qt.UserRole) )
        return nodes

    def getSelectedNodes(self):
        nodes = []
        for item in self.itemList.selectedItems():
            nodes.append( item.data(Qt.UserRole) )
        return nodes
