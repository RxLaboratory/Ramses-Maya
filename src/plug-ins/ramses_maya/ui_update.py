# -*- coding: utf-8 -*-

import os

try:
    from PySide2 import QtWidgets as qw
    from PySide2 import QtCore as qc
except:  # pylint: disable=bare-except
    from PySide6 import QtWidgets as qw
    from PySide6 import QtCore as qc

from maya import cmds # pylint: disable=import-error
from ramses_maya.utils_attributes import list_ramses_nodes, get_item, get_state, get_step, get_ramses_attr, RamsesAttribute
from ramses_maya.ui_dialog import Dialog
import ramses
import dumaf

RAMSES = ramses.Ramses.instance()

class UpdateDialog( Dialog ):
    """The Dialog to update items in the scene"""

    def __init__(self, parent = None):
        super(UpdateDialog, self).__init__(parent)
        self.__setupUi()
        self.__listItems()
        self.__connectEvents()

    def __setupUi(self):

        self.setWindowTitle("Update Items")

        mainLayout = qw.QVBoxLayout()
        mainLayout.setSpacing(3)
        self.main_layout.addLayout(mainLayout)

        columnLayout = qw.QHBoxLayout()
        columnLayout.setContentsMargins(0,0,0,0)
        columnLayout.setSpacing(6)

        currentLayout = qw.QVBoxLayout()
        currentLayout.setContentsMargins(0,0,0,0)
        currentLayout.setSpacing(3)

        self.onlyNewButton = qw.QCheckBox("Show only updated items.")
        self.onlyNewButton.setChecked(True)
        currentLayout.addWidget( self.onlyNewButton )

        self.onlySelectedButton = qw.QCheckBox("Show only selected nodes.")
        self.onlySelectedButton.setChecked(False)
        currentLayout.addWidget( self.onlySelectedButton )

        self.itemList = qw.QListWidget()
        self.itemList.setSelectionMode(qw.QAbstractItemView.ExtendedSelection)
        currentLayout.addWidget(self.itemList)

        self.currentDetailsLabel = qw.QLabel("")
        currentLayout.addWidget(self.currentDetailsLabel)

        columnLayout.addLayout(currentLayout)

        updateLayout = qw.QVBoxLayout()
        updateLayout.setContentsMargins(0,0,0,0)
        updateLayout.setSpacing(3)

        updateLabel = qw.QLabel("Published versions:")
        updateLayout.addWidget(updateLabel)

        self.updateList = qw.QListWidget()
        self.updateList.setSelectionMode(qw.QAbstractItemView.SingleSelection)
        updateLayout.addWidget(self.updateList)

        self.updateDetailsLabel = qw.QLabel("")
        updateLayout.addWidget(self.updateDetailsLabel)
        
        columnLayout.addLayout(updateLayout)

        mainLayout.addLayout(columnLayout)

        buttonsLayout = qw.QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._updateButton = qw.QPushButton("Update All")
        self._updateButton.setEnabled(False)
        buttonsLayout.addWidget( self._updateButton )
        self._updateSelectedButton = qw.QPushButton("Update Selected")
        self._updateSelectedButton.setEnabled(False)
        buttonsLayout.addWidget( self._updateSelectedButton )
        self._cancelButton = qw.QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

    def __connectEvents(self):
        self._updateButton.clicked.connect( self.accept )
        self._cancelButton.clicked.connect( self.reject )
        self.onlyNewButton.clicked.connect( self.showOnlyNew )
        self.onlySelectedButton.clicked.connect( self.showOnlySelected )
        self.itemList.itemSelectionChanged.connect( self.selectionChanged )
        self._updateSelectedButton.clicked.connect( self._updateSelected )

    qc.Slot()
    def _updateSelected(self):
        self.done(2)

    qc.Slot()
    def selectionChanged(self):
        """Updates displayed info according to the selection"""
        items = self.itemList.selectedItems()
        self._updateSelectedButton.setEnabled(len(items) > 0)
        self.updateList.clear()

        currentItem = self.itemList.currentItem()
        if currentItem is not None and len(items) == 1:

            # Details

            currentDetails = '\n'.join((
                "Current version: " + str( currentItem.data(qc.Qt.UserRole + 4) ),
                "Current state: " + currentItem.data(qc.Qt.UserRole + 3).name()
            ))
            self.currentDetailsLabel.setText( currentDetails )

            state = currentItem.data(qc.Qt.UserRole + 8)
            stateName = "- Not Found -"
            if state:
                stateName = state.name()

            updateDetails = '\n'.join((
                "Latest version: " + str( currentItem.data(qc.Qt.UserRole + 7) ),
                "Latest state: " + stateName
            ))
            self.updateDetailsLabel.setText( updateDetails )

            # List available versions
            ramItem = currentItem.data(qc.Qt.UserRole + 1)
            ramStep = currentItem.data(qc.Qt.UserRole + 2)
            sourceFile = currentItem.data(qc.Qt.UserRole + 5)
            resource = currentItem.data(qc.Qt.UserRole + 6)
            sourceFileName = os.path.basename(sourceFile)
            publishedFolders = ramItem.publishedVersionFolderPaths( ramStep, sourceFileName, resource )
            for f in reversed(publishedFolders):
                updateItem = qw.QListWidgetItem(self.updateList)

                splitName = os.path.basename(f).split('_')
                if len(splitName) == 3:
                    splitName[1] = 'v' + str(int(splitName[1]))
                    splitName[2] = str( ramses.Ramses.instance().state(splitName[2]).name() )
                elif len(splitName) == 2:
                    splitName[0] = 'v' + str(int(splitName[0]))
                    splitName[1] = str( ramses.Ramses.instance().state(splitName[1]).name() )

                itemName = ' | '.join(splitName)
                updateItem.setText( itemName )
                updateFile = ramses.RamFileManager.buildPath((f, sourceFileName))
                updateItem.setData(qc.Qt.UserRole, updateFile)

            self.updateList.setCurrentItem( self.updateList.item(0) )
                            
        else:
            self.currentDetailsLabel.setText("")
    qc.Slot()
    def showOnlyNew(self, checked = True):
        self.__filterList()

    qc.Slot()
    def showOnlySelected(self, checked = True):
        self.__filterList()

    def __filterList(self):
        selection = cmds.ls( long=True, selection=True )
        if selection is None: selection = []

        onlySelected = self.onlySelectedButton.isChecked()
        onlyUpdated = self.onlyNewButton.isChecked()
    
        for i in range(0, self.itemList.count()):
            listItem = self.itemList.item( i )
            if not onlySelected and not onlyUpdated:
                listItem.setHidden(False)
                continue

            node = listItem.data(qc.Qt.UserRole)
            updated = listItem.text().startswith('New: ')
            selected = node in selection

            if onlyUpdated and not updated:
                listItem.setHidden(True)
                continue
            if onlySelected and not selected:
                listItem.setHidden(True)
                continue

            listItem.setHidden(False)

    def __listItems(self):
        """List the items found in the scene"""
        nodes = list_ramses_nodes('')
        if len(nodes) == 0:
            self._updateButton.setEnabled(False)
            self._updateSelectedButton.setEnabled(False)
            return
        self._updateButton.setEnabled(True)
        for node in nodes:
            nodeName = dumaf.paths.baseName(node)

            ramItem = get_item( node )
            ramStep = get_step( node )
            ramState = get_state( node )

            if ramItem is None or ramStep is None: continue

            # Check source info
            sourceFile = get_ramses_attr( node, RamsesAttribute.SOURCE_FILE )
            version = get_ramses_attr( node, RamsesAttribute.VERSION )
            resource = get_ramses_attr(node, RamsesAttribute.RESOURCE )

            listItem = qw.QListWidgetItem( self.itemList )
            listItem.setData(qc.Qt.UserRole, node)
            listItem.setData(qc.Qt.UserRole + 1, ramItem )
            listItem.setData(qc.Qt.UserRole + 2, ramStep )
            listItem.setData(qc.Qt.UserRole + 3, ramState )
            listItem.setData(qc.Qt.UserRole + 4, version )
            listItem.setData(qc.Qt.UserRole + 5, sourceFile )
            listItem.setData(qc.Qt.UserRole + 6, resource )
            listItem.setData(qc.Qt.UserRole + 7, '-Not found-')
            listItem.setData(qc.Qt.UserRole + 8, None )
            listItem.setToolTip( node )

            itemText = ramItem.name() + ' | ' + ramStep.name()
            if resource != '':
                itemText = itemText + ' | ' + resource
            itemText = itemText + ' (' + nodeName + ')'

            updated = False

            if sourceFile is not None:
                # Get the latest one and check its version and state
                fileName = os.path.basename( sourceFile )
                latestFolder = ramItem.latestPublishedVersionFolderPath( ramStep, fileName, resource )
                latestFile = ramses.RamFileManager.buildPath((latestFolder, fileName))
                if latestFile != sourceFile and latestFile != '':
                    updated = True
                updateVersion = ramses.RamMetaDataManager.getVersion(latestFile)
                updateState = ramses.RamMetaDataManager.getState( latestFile )
                updateState = ramses.Ramses.instance().state(updateState)
                listItem.setData(qc.Qt.UserRole + 7, updateVersion)
                listItem.setData(qc.Qt.UserRole + 8, updateState)
                listItem.setData(qc.Qt.UserRole + 9, latestFile )
            if updated:
                itemText = 'New: ' + itemText 

            elif self.onlyNewButton.isChecked():
                listItem.setHidden(True)

            listItem.setText(itemText)

    def getAllNodes(self):
        nodes = []
        for i in range(0, self.itemList.count()):
            item = self.itemList.item(i)
            if item.text().startswith('New: '):
                nodes.append( ( item.data(qc.Qt.UserRole), item.data(qc.Qt.UserRole + 9)) )
        return nodes

    def getSelectedNodes(self):
        nodes = []

        updateItem = self.updateList.currentItem()
        currentItem = self.itemList.currentItem()

        if updateItem is not None and currentItem is not None:
            nodes.append( ( currentItem.data(qc.Qt.UserRole), updateItem.data(qc.Qt.UserRole) ) )
            return nodes

        for item in self.itemList.selectedItems():
            nodes.append( ( item.data(qc.Qt.UserRole), item.data(qc.Qt.UserRole + 9) ) )
        return nodes

if __name__ == '__main__':
    updateDialog = UpdateDialog()
    ok = updateDialog.exec_()
    print(ok)
    if ok == 1:
        print( updateDialog.getAllNodes() )
    elif ok == 2:
        print( updateDialog.getSelectedNodes() )
