# -*- coding: utf-8 -*-

import os
from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module,import-error
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QWidget,
    QLineEdit,
    QAbstractItemView
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module,import-error
    Slot,
    Qt
)

import ramses as ram

from .utils import icon

RAMSES = ram.Ramses.instance()

class ImportDialog( QDialog ):

    # <== CONSTRUCTOR ==>

    def __init__(self, parent=None):
        super(ImportDialog,self).__init__(parent)

        self.__setupUi()
        self.__loadProjects()
        self.__connectEvents()

    # <== PRIVATE METHODS ==>

    def __setupUi(self):
        """Creates the dialog UI"""

        checkableButtonCSS = """
            QPushButton {
                background-color: rgba(0,0,0,0);
                border:none;
                padding: 5px;
                color: #eeeeee;
            }
            QPushButton:hover {
                background-color: #707070;
            }
            QPushButton:checked {
                background-color: #2b2b2b;
            }"""

        self.setWindowTitle( "Open / Import Item" )

        self.setMinimumWidth(500)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        midLayout = QHBoxLayout()
        midLayout.setSpacing(3)

        topLayout = QFormLayout()
        topLayout.setFieldGrowthPolicy( QFormLayout.AllNonFixedFieldsGrow )
        topLayout.setSpacing(3)

        topLayout.addRow(QLabel("Info:"))

        self.projectBox = QComboBox()
        topLayout.addRow( "Project:", self.projectBox )

        self.typeWidget = QWidget()
        typeLayout = QVBoxLayout()
        typeLayout.setContentsMargins(0,0,0,0)
        typeLayout.setSpacing(3)
        self.assetButton = QPushButton()
        self.assetButton.setText("Asset")
        self.assetButton.setIcon(icon("ramasset"))
        self.assetButton.setCheckable(True)
        self.assetButton.setStyleSheet(checkableButtonCSS)
        typeLayout.addWidget(self.assetButton)
        self.shotButton = QPushButton()
        self.shotButton.setText("Shot")
        self.shotButton.setIcon(icon("ramshot"))
        self.shotButton.setCheckable(True)
        self.shotButton.setStyleSheet(checkableButtonCSS)
        typeLayout.addWidget(self.shotButton)
        self.templateButton = QPushButton()
        self.templateButton.setText("Template")
        self.templateButton.setIcon(icon("ramtemplateitem"))
        self.templateButton.setCheckable(True)
        self.templateButton.setStyleSheet(checkableButtonCSS)
        typeLayout.addWidget(self.templateButton)
        self.typeWidget.setLayout(typeLayout)
        self.typeWidget.setEnabled(False)
        topLayout.addRow( "Type:", self.typeWidget )

        self.actionWidget = QWidget()
        actionLayout = QVBoxLayout()
        actionLayout.setContentsMargins(0,0,0,0)
        actionLayout.setSpacing(3)
        self.openButton = QPushButton()
        self.openButton.setText("Open item")
        self.openButton.setIcon(icon("ramopenscene"))
        self.openButton.setCheckable(True)
        self.openButton.setChecked(True)
        self.openButton.setStyleSheet(checkableButtonCSS)
        actionLayout.addWidget(self.openButton)
        self.importButton = QPushButton()
        self.importButton.setText("Import item")
        self.importButton.setIcon(icon("ramimportitem"))
        self.importButton.setCheckable(True)
        self.importButton.setStyleSheet(checkableButtonCSS)
        actionLayout.addWidget(self.importButton)
        self.replaceButton = QPushButton()
        self.replaceButton.setText("Replace selected items")
        self.replaceButton.setIcon(icon("ramreplaceitem"))
        self.replaceButton.setCheckable(True)
        self.replaceButton.setStyleSheet(checkableButtonCSS)
        self.replaceButton.hide() # Not available yet
        actionLayout.addWidget(self.replaceButton)
        self.actionWidget.setLayout(actionLayout)
        topLayout.addRow( "Action:", self.actionWidget )

        midLayout.addLayout( topLayout )

        itemLayout = QVBoxLayout()
        itemLayout.setSpacing(3)
        self.itemLabel = QLabel("Item")
        self.itemLabel.hide()
        itemLayout.addWidget(self.itemLabel)
        self.groupBox = QComboBox()
        self.groupBox.hide()
        itemLayout.addWidget(self.groupBox)
        self.itemSearchField = QLineEdit()
        self.itemSearchField.setPlaceholderText('Search...')
        self.itemSearchField.setClearButtonEnabled(True)
        itemLayout.addWidget(self.itemSearchField)
        self.itemSearchField.hide()
        self.itemList = QListWidget()
        self.itemList.hide()
        itemLayout.addWidget(self.itemList)
        midLayout.addLayout(itemLayout)

        stepLayout = QVBoxLayout()
        stepLayout.setSpacing(3)
        stepLabel = QLabel("Step:")
        stepLayout.addWidget(stepLabel)
        self.stepList = QListWidget()
        stepLayout.addWidget(self.stepList)
        midLayout.addLayout(stepLayout)

        resourcesLayout = QVBoxLayout()
        resourcesLayout.setSpacing(3)
        self.resourcesLabel = QLabel("Resource:")
        resourcesLayout.addWidget(self.resourcesLabel)
        self.resourceList = QListWidget()
        resourcesLayout.addWidget(self.resourceList)
        midLayout.addLayout(resourcesLayout)

        versionsLayout = QVBoxLayout()
        versionsLayout.setSpacing(3)
        self.versionsLabel = QLabel("Version:")
        versionsLayout.addWidget(self.versionsLabel)
        self.publishVersionBox = QComboBox()
        versionsLayout.addWidget(self.publishVersionBox)
        self.publishVersionBox.setVisible(False)
        self.versionSearchField = QLineEdit()
        self.versionSearchField.setPlaceholderText('Search...')
        self.versionSearchField.setClearButtonEnabled(True)
        versionsLayout.addWidget(self.versionSearchField)
        self.versionList = QListWidget()
        versionsLayout.addWidget(self.versionList)
        midLayout.addLayout(versionsLayout)

        mainLayout.addLayout( midLayout )

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)
        self._openButton = QPushButton("Open")
        buttonsLayout.addWidget( self._openButton )
        self._importButton = QPushButton("Import")
        self._importButton.hide()
        buttonsLayout.addWidget( self._importButton )
        self._replaceButton = QPushButton("Replace")
        self._replaceButton.hide()
        buttonsLayout.addWidget( self._replaceButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        self._openButton.setEnabled(False)
        self._replaceButton.setEnabled(False)
        self._importButton.setEnabled(False)

        mainLayout.addLayout( buttonsLayout )

        self.setLayout( mainLayout )

    def __connectEvents(self):
        self.projectBox.currentIndexChanged.connect( self.__projectChanged )

        self.assetButton.clicked.connect( self.__assetButtonClicked )
        self.shotButton.clicked.connect( self.__shotButtonClicked )
        self.templateButton.clicked.connect( self.__templateButtonClicked )
        self.assetButton.clicked.connect( self.__typeChanged )
        self.shotButton.clicked.connect( self.__typeChanged )
        self.templateButton.clicked.connect( self.__typeChanged )

        self.openButton.clicked.connect( self.__openButtonClicked )
        self.importButton.clicked.connect( self.__importButtonClicked )
        self.replaceButton.clicked.connect( self.__replaceButtonClicked )
        self.openButton.clicked.connect( self.__actionChanged )
        self.importButton.clicked.connect( self.__actionChanged )
        self.replaceButton.clicked.connect( self.__actionChanged )

        self._cancelButton.clicked.connect( self.reject )
        self._openButton.clicked.connect( self.accept )
        self._importButton.clicked.connect( self.__import )
        self._replaceButton.clicked.connect( self.__replace )
        self.itemList.currentRowChanged.connect( self.__updateResources )
        self.stepList.currentRowChanged.connect( self.__updateResources )
        self.resourceList.currentRowChanged.connect( self.__resourceChanged )
        self.versionList.currentRowChanged.connect( self.__versionChanged )
        self.groupBox.currentIndexChanged.connect( self.__updateItems )
        self.itemSearchField.textChanged.connect( self.__searchItem )
        self.versionSearchField.textChanged.connect( self.__searchVersion )
        self.publishVersionBox.currentIndexChanged.connect( self.__updatePublishedFiles )

    @Slot()
    def __assetButtonClicked(self):
        self.assetButton.setChecked(True)
        self.shotButton.setChecked(False)
        self.templateButton.setChecked(False)

    @Slot()
    def __shotButtonClicked(self):
        self.assetButton.setChecked(False)
        self.shotButton.setChecked(True)
        self.templateButton.setChecked(False)

    @Slot()
    def __templateButtonClicked(self):
        self.assetButton.setChecked(False)
        self.shotButton.setChecked(False)
        self.templateButton.setChecked(True)

    @Slot()
    def __openButtonClicked(self):
        self.openButton.setChecked(True)
        self.importButton.setChecked(False)
        self.replaceButton.setChecked(False)

    @Slot()
    def __importButtonClicked(self):
        self.openButton.setChecked(False)
        self.importButton.setChecked(True)
        self.replaceButton.setChecked(False)

    @Slot()
    def __replaceButtonClicked(self):
        self.openButton.setChecked(False)
        self.importButton.setChecked(False)
        self.replaceButton.setChecked(True)

    def __loadProjects(self):
        # Load projects
        projects = RAMSES.projects()
        self.projectBox.clear()

        if projects is None:
            self.assetButton.setChecked(False)
            self.shotButton.setChecked(False)
            self.templateButton.setChecked(False)
            return

        for project in RAMSES.projects():
            self.projectBox.addItem(str(project), project)

        self.projectBox.setCurrentIndex(-1)

    @Slot()
    def __projectChanged(self, index):
        self.assetButton.setChecked(False)
        self.shotButton.setChecked(False)
        self.templateButton.setChecked(False)
        self.typeWidget.setEnabled(index != -1)
        if index == -1: return

    @Slot()
    def __typeChanged( self ):
        shot = self.shotButton.isChecked()
        asset = self.assetButton.isChecked()
        template = self.templateButton.isChecked()

        # adjust UI
        if shot or asset:
            self.itemLabel.show()
            self.itemList.show()
            self.itemSearchField.show()
            self.groupBox.show()
            if asset: self.itemLabel.setText("Asset:")
            else: self.itemLabel.setText("Shot:")
        else:
            self.itemLabel.hide()
            self.itemList.hide()
            self.groupBox.hide()
            self.itemSearchField.hide()

        # reinit lists
        self.itemList.clear()
        self.stepList.clear()
        self.resourceList.clear()
        self.versionList.clear()
        self.groupBox.clear()

        if not shot and not asset and not template: return

        project = self.projectBox.currentData()
        if not project: return

        steps = ()

        # Load asset groups and asset steps
        if asset:
            groups = project.assetGroups()
            self.groupBox.blockSignals(True)
            self.groupBox.addItem("All", "")
            # Add groups
            for group in groups:
                self.groupBox.addItem(group, group)
            self.groupBox.setCurrentIndex(-1)
            self.groupBox.blockSignals(False)
            steps = project.steps( ram.StepType.ASSET_PRODUCTION )
        # Load sequences, shots and shot steps
        elif shot:
            groups = project.sequences()
            self.groupBox.blockSignals(True)
            self.groupBox.addItem("All", "")
            # Add sequences
            for group in groups:
                self.groupBox.addItem(group, group)
            self.groupBox.setCurrentIndex(-1)
            self.groupBox.blockSignals(False)
            steps = project.steps( ram.StepType.SHOT_PRODUCTION )
        # Load steps for templates
        elif template:
            steps = project.steps()

        # Populate steps
        for step in steps:
            n = str(step)
            item = QListWidgetItem( n )
            item.setData( Qt.UserRole, step )
            self.stepList.addItem( item )
        
    @Slot()
    def __updateItems(self):

        project = self.projectBox.currentData()
        if not project: return

        items = ()
        if self.shotButton.isChecked(): items = project.shots( sequence = self.groupBox.currentData() )
        elif self.assetButton.isChecked(): items = project.assets( self.groupBox.currentData() )
        else: return

        self.itemList.clear()
        for item in items:
            n = str(item)
            listItem = QListWidgetItem( n )
            listItem.setData( Qt.UserRole, item )
            self.itemList.addItem( listItem )

    @Slot()
    def __searchItem(self, text):
        text = text.lower()
        for i in range(0, self.itemList.count()):
            item = self.itemList.item(i)
            item.setHidden(
                text != '' and text not in item.text().lower()
                )

    @Slot()
    def __searchVersion(self, text):
        text = text.lower()
        for i in range(0, self.versionList.count()):
            item = self.versionList.item(i)
            item.setHidden(
                text != '' and text not in item.text().lower()
                )
    
    @Slot()
    def __actionChanged(self):
        if self.openButton.isChecked():
            self._importButton.hide()
            self._replaceButton.hide()
            self._openButton.show()
            self.versionsLabel.setText("Version:")
            self.versionList.setSelectionMode(QAbstractItemView.SingleSelection)
            self.publishVersionBox.setVisible(False)
        else: # Import or replace
            if self.replaceButton.isChecked():
                self._replaceButton.show()
                self._importButton.hide()
                self.versionList.setSelectionMode(QAbstractItemView.SingleSelection)
            else:
                self._replaceButton.hide()
                self._importButton.show()
                self.versionList.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self._openButton.hide()
            self.versionsLabel.setText("File:")
            self.publishVersionBox.setVisible(True)
        self.__updateResources()
        self.__resourceChanged( self.resourceList.currentRow() )
    
    @Slot()
    def __updateResources(self):

        def listTemplateResources(step):
            folder = step.templatesFolderPath()
            if folder == '': return

            for f in os.listdir( folder ):
                # Template must be a folder
                fPath = ram.RamFileManager.buildPath((
                    folder,
                    f
                ))
                if not os.path.isdir(fPath):
                    continue

                nm = ram.RamFileInfo()
                if not nm.setFileName( f ):
                    continue

                if nm.project != step.projectShortName():
                    continue

                if nm.step != step.shortName():
                    continue
                
                for t in os.listdir( fPath ):
                    # Resource must be a file
                    resource = ram.RamFileManager.buildPath((
                        fPath,
                        t
                    ))
                    if not os.path.isfile(resource):
                        continue

                    if not nm.setFileName( t ):
                        continue
                    
                    res = nm.resource

                    if nm.isRestoredVersion:
                        if res != '': res = res + " | "
                        res = res + "v" + str(nm.restoredVersion) + " (restored)"

                    if res == "":
                        res = "Main (" + nm.extension + ")"
                        self._openButton.setEnabled(True)

                    item = QListWidgetItem( nm.shortName + " | " + res )
                    item.setData( Qt.UserRole, resource )
                    item.setToolTip(t)
                    self.resourceList.addItem( item )

        self.resourceList.hide()
        self.resourcesLabel.hide()

        self.resourceList.clear()
        self.versionList.clear()
        
        stepItem = self.stepList.currentItem()
        if not stepItem: return
        step = stepItem.data(Qt.UserRole)

        currentItem = self.getItem()

        # If open, list resources in wip folder
        if self.openButton.isChecked():
            self.resourceList.show()
            self.resourcesLabel.show()
            # Shots and Assets
            if self.assetButton.isChecked() or self.shotButton.isChecked():
                if not currentItem: return
                # List resources
                resources = currentItem.stepFilePaths( step )

                for resource in resources:
                    nm = ram.RamFileInfo()
                    nm.setFilePath(resource)
                    if nm.project == '': continue

                    res = nm.resource

                    if nm.isRestoredVersion:
                        if res != '': res = res + " | "
                        res = res + "v" + str(nm.restoredVersion) + " (restored)"

                    if res == "":
                        res = "Main (" + nm.extension + ")"
                        self._openButton.setEnabled(True)
                                       
                    item = QListWidgetItem( res )
                    item.setData( Qt.UserRole, resource )
                    self.resourceList.addItem( item )

            # Templates
            else:
                # List resources
                listTemplateResources(step)

        # If import asset or shot, list all subfolders
        elif self.assetButton.isChecked() or self.shotButton.isChecked():
            self.__listPublishedVersions()
        # If import template, list resources
        else:
            self.resourceList.show()
            self.resourcesLabel.show()
            listTemplateResources(step)
        
    def __listPublishedVersions(self):
        self.publishVersionBox.clear()
        folders = []
        currentItem = self.getItem()
        if not currentItem: return
        step = self.getStep()
        if not step: return
        folders = currentItem.publishedVersionFolderPaths( step )

        for f in reversed(folders): # list more recent first
            folderName = os.path.basename( f )
            folderName = folderName.split("_")
            title = ""

            # Test length to know what we've got
            if len(folderName) == 3: # resource, version, state
                title = folderName[0] + " | v" + folderName[1] + " | " + folderName[2]
            elif len(folderName) < 3: # version (state)
                if int(folderName[0]) != 0:
                    title = "v" + " | ".join(folderName)
            else:
                title = " | ".join(folderName)

            self.publishVersionBox.addItem(title, f)
            self.__updatePublishedFiles()

    @Slot()
    def __updatePublishedFiles(self):
        self.versionList.clear()
        # List available files
        folder = self.publishVersionBox.currentData()
        files = ram.RamFileManager.getRamsesFiles( folder )
        for f in files:
            nm = ram.RamFileInfo()
            fileName = os.path.basename(f)
            if not nm.setFileName(fileName): continue
            resource = nm.resource
            if resource == "": resource = "Main"
            title = resource + " (" + nm.extension + ")"
            item = QListWidgetItem( title )
            item.setData(Qt.UserRole, f)
            item.setToolTip(fileName)
            self.versionList.addItem(item)

    @Slot()
    def __resourceChanged(self, row):

        # Import, list publish files for templates
        if self.importButton.isChecked():
            if self.assetButton.isChecked() or self.shotButton.isChecked():
                return
            self.__listPublishedVersions()
            return

        # Open, list versions
        if row < 0:
            self._openButton.setEnabled(False)
        else:
            self._openButton.setEnabled(True)

        self.versionList.clear()

        currentItem = self.getItem()
        if not currentItem: return
        
        # List versions
        versionFiles = ()
        versionFiles = currentItem.versionFilePaths( self.getResource(), self.getStep() )

        if len(versionFiles) == 0: return

        versionFiles.reverse()    

        # Add current
        item = QListWidgetItem("Current version")
        item.setData(Qt.UserRole, versionFiles[0])
        self.versionList.addItem(item)

        # Add other versions
        for v in versionFiles:
            fileName = os.path.basename( v )
            nm = ram.RamFileInfo()
            if not nm.setFileName( fileName ):
                continue
            comment = ram.RamMetaDataManager.getComment( v )
            itemText = nm.state + ' | ' + str( nm.version )
            if comment != "":
                itemText = itemText + ' | ' + comment
            item = QListWidgetItem( itemText )
            item.setData(Qt.UserRole, v)
            self.versionList.addItem(item)

    @Slot()
    def __versionChanged(self, row):
        self._importButton.setEnabled(row >= 0)
        self._replaceButton.setEnabled(row >= 0)

    @Slot()
    def __import(self):
        self.done(2)

    @Slot()
    def __replace(self):
        self.done(3)

    # <== PUBLIC METHODS ==>

    def setMode(self, mode="open"):
        """Sets the mode of the window, either open, import or replace"""
        if mode == "import":
            self.__importButtonClicked()
        elif mode == "replace":
            self.__replaceButtonClicked()
        else:
            self.__openButtonClicked()
        self.__actionChanged()

    def setProject(self, project):
        
        if project is None:
            self.projectBox.setCurrentIndex(-1)
            return
        for i in range(self.projectBox.count()):
            testProject = self.projectBox.itemData(i)
            if not testProject: continue
            if testProject == project:
                self.projectBox.setCurrentIndex(i)
                return

        self.projectBox.addItem( str(project), project )
        self.projectBox.setCurrentIndex( self.projectBox.count() - 1)

    def setType( self, itemType):
        if itemType == ram.ItemType.ASSET:
            self.assetButton.setChecked(True)
        elif itemType == ram.ItemType.SHOT:
            self.shotButton.setChecked(True)
        self.__typeChanged()

    def setItem(self, itemShortName ):
        self.groupBox.setCurrentIndex(0)
        for i in range( 0, self.itemList.count()):
            listItem = self.itemList.item(i)
            if listItem.data(Qt.UserRole).shortName() == itemShortName:
                self.itemList.setCurrentItem(listItem)
                self.__updateResources()
                return

    def setStep(self, stepShortName):
        for i in range(0, self.stepList.count()):
            listItem = self.stepList.item(i)
            if listItem.data(Qt.UserRole).shortName == stepShortName:
                self.stepList.setCurrentItem(listItem)
                self.__updateResources()
                return

    def getProject(self):
        return self.projectBox.currentData()

    def getItem(self):
        """Returns the Item (RamAsset, RamShot or RamItem if template) currently selected."""
        
        # if it's an asset or a shot, get from itemList
        if self.shotButton.isChecked() or self.assetButton.isChecked():
            item = self.itemList.currentItem()
            if not item: return None
            return item.data(Qt.UserRole)

        # if it's a template, get the item from the path of the selected resource (or version if import)        
        item = self.resourceList.currentItem()
        if not item: return None
        return ram.RamItem.fromPath( item.data(Qt.UserRole) )

    def getStep(self):
        item = self.stepList.currentItem()
        if not item: return None
        return item.data(Qt.UserRole)
    
    def getResource(self):

        item = self.resourceList.currentItem()
        if not item: return ""

        nm = ram.RamFileInfo()
        nm.setFilePath( item.data(Qt.UserRole) )
        return nm.resource

    def getFile(self):

        # return the selected version if it's not  the current
        rowForCurrent = -1
        if self.openButton.isChecked(): rowForCurrent = 0
        if self.versionList.currentRow() > rowForCurrent:
            return self.versionList.currentItem().data(Qt.UserRole)

        # no version selected, return the resource file
        # We can't import if no version file selected
        if self.importButton.isChecked(): return ""

        # return the selected resource if any
        item = self.resourceList.currentItem()
        if item: return item.data(Qt.UserRole)

        # If it's an asset or a shot which is selected, return the default (no resource)
        if self.assetButton.isChecked() or self.shotButton.isChecked():

            currentItem = self.getItem()
            if not currentItem: return ""
            step = self.getStep()
            if not step: return ""

            file = currentItem.stepFilePath("", "ma", step) # Try MA first
            if file != "": return file
            file = currentItem.stepFilePath("", "mb", step) # or MB
            return file
       
    def getFiles(self):
        if self.versionList.count() == 0: return ( self.getFiles )

        # De-select the item 0, which is basically "no version"
        if self.openButton.isChecked(): self.versionList.item(0).setSelected(False)
        items = self.versionList.selectedItems()
        if len(items) == 0:
            return ( self.getFile() )
        
        files = []
        for item in items:
            files.append( item.data(Qt.UserRole) )
        return files

if __name__ == '__main__':
    importDialog = ImportDialog()
    ok = importDialog.exec_()

    print( importDialog.getItem() )
    print( importDialog.getStep() )
    print( importDialog.getFile() )
    print( importDialog.getResource() )
    print( importDialog.getFiles() )
