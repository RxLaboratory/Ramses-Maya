import os
from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
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
    QRadioButton,
    QLineEdit,
    QAbstractItemView
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot,
)

import ramses as ram
ramses = ram.Ramses.instance()

class ImportDialog( QDialog ):

    def __init__(self, parent=None):
        super(ImportDialog,self).__init__(parent)

        self._currentProject = None
        self._currentItems = []
        self._currentSteps = []
        self._currentItem = None
        self._currentStep = None
        self._currentResource = ""
        self._currentFiles = []
        self._resourceFiles = []

        self.__setupUi()
        self.__loadProjects()
        self.__connectEvents()

    def __setupUi(self):
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
        self.assetButton = QRadioButton("Asset")
        typeLayout.addWidget(self.assetButton)
        self.shotButton = QRadioButton("Shot")
        typeLayout.addWidget(self.shotButton)
        self.templateButton = QRadioButton("Template")
        typeLayout.addWidget(self.templateButton)
        self.typeWidget.setLayout(typeLayout)
        self.typeWidget.setEnabled(False)
        topLayout.addRow( "Type:", self.typeWidget )

        self.actionWidget = QWidget()
        actionLayout = QVBoxLayout()
        actionLayout.setContentsMargins(0,0,0,0)
        self.openButton = QRadioButton("Open Item")
        self.openButton.setChecked(True)
        actionLayout.addWidget(self.openButton)
        self.importButton = QRadioButton("Import Item")
        actionLayout.addWidget(self.importButton)
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
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        self._openButton.setEnabled(False)
        self._importButton.setEnabled(False)

        mainLayout.addLayout( buttonsLayout )

        self.setLayout( mainLayout )

    def __connectEvents(self):
        self.projectBox.currentIndexChanged.connect( self.__projectChanged )
        self.assetButton.clicked.connect( self.__typeChanged )
        self.shotButton.clicked.connect( self.__typeChanged )
        self.templateButton.clicked.connect( self.__typeChanged )
        self.openButton.clicked.connect( self.__actionChanged )
        self.importButton.clicked.connect( self.__actionChanged )
        self._cancelButton.clicked.connect( self.reject )
        self._openButton.clicked.connect( self.accept )
        self._importButton.clicked.connect( self.__import )
        self.itemList.currentRowChanged.connect( self.__itemChanged )
        self.stepList.currentRowChanged.connect( self.__stepChanged )
        self.resourceList.currentRowChanged.connect( self.__resourceChanged )
        self.versionList.currentRowChanged.connect( self.__versionChanged )
        self.groupBox.currentIndexChanged.connect( self.__groupChanged )
        self.itemSearchField.textChanged.connect( self.__searchItem )
        self.versionSearchField.textChanged.connect( self.__searchVersion )

    def __loadProjects(self):
        # Load projects
        projects = ramses.projects()
        self.projectBox.clear()
        if projects is None:
            self.assetButton.setChecked(False)
            self.shotButton.setChecked(False)
            self.templateButton.setChecked(False)
            return
        for project in ramses.projects():
            n = project.name()
            if n == "":
                n = project.shortName()
            self.projectBox.addItem(n, project.shortName())
        self.projectBox.setCurrentIndex(-1)

    @Slot()
    def __projectChanged(self, index):
        self.assetButton.setChecked(False)
        self.shotButton.setChecked(False)
        self.templateButton.setChecked(False)
        self.typeWidget.setEnabled(index != -1)
        if index == -1:
            self._currentProject = None
            return
        self._currentProject = ramses.project( self.projectBox.currentData() )

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
    def __typeChanged( self ):
        shot = self.shotButton.isChecked()
        asset = self.assetButton.isChecked()
        template = self.templateButton.isChecked()
        # adjust UI
        if shot or asset:
            self.itemLabel.show()
            self.itemList.show()
            self.itemSearchField.show()
            if self.assetButton.isChecked():
                self.itemLabel.setText("Asset:")
                self.groupBox.show()
            else:
                self.itemLabel.setText("Shot:")
                self.groupBox.hide()
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
        self._currentItems = []
        self._currentSteps = []
        if not shot and not asset and not template:
            return
        # Load asset groups and asset steps
        if asset:
            if self._currentProject is None:
                return
            groups = self._currentProject.assetGroups()
            self.groupBox.blockSignals(True)
            self.groupBox.addItem("All", "")
            # Add groups
            for group in groups:
                self.groupBox.addItem(group, group)
            self.groupBox.setCurrentIndex(-1)
            self.groupBox.blockSignals(False)
            self._currentSteps = self._currentProject.steps( ram.StepType.ASSET_PRODUCTION )
        # Load shots and shot steps
        elif shot:
            if self._currentProject is None:
                return
            self._currentItems = self._currentProject.shots()
            self.__updateItems()
            self._currentSteps = self._currentProject.steps( ram.StepType.SHOT_PRODUCTION )
        # Load templates
        elif template:
            self._currentSteps = self._currentProject.steps()

        # Populate steps
        for step in self._currentSteps:
            n = step.name()
            if n == "":
                n = step.shortName()
            self.stepList.addItem(n)
        
    @Slot()
    def __actionChanged(self):
        if self.openButton.isChecked():
            self._importButton.hide()
            self._openButton.show()
            self.versionsLabel.setText("Version:")
            self.resourceList.show()
            self.resourcesLabel.show()
            self.versionList.setSelectionMode(QAbstractItemView.SingleSelection)
        else: # Import
            self._importButton.show()
            self._openButton.hide()
            self.versionsLabel.setText("File:")
            self.resourceList.hide()
            self.resourcesLabel.hide()
            self.versionList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__resourceChanged( self.resourceList.currentRow() )
        
    @Slot()
    def __groupChanged(self, index):
        # Load assets
        self._currentItems = self._currentProject.assets( self.groupBox.itemData( index ) )
        self.__updateItems()

    def __updateItems(self):
        self.itemList.clear()
        for item in self._currentItems:
            n = item.name()
            if n == "":
                n = item.shortName()
            self.itemList.addItem(n)

    @Slot()
    def __itemChanged(self, row ):
        if not row in range(0, len(self._currentItems) ):
            self._currentItem = None
            return
        self._currentItem = self._currentItems[row]
        self.__updateResources()

    @Slot()
    def __stepChanged(self, row):
        if not row in range(0, len(self._currentSteps)):
            self._currentStep = None
            return
        self._currentStep = self._currentSteps[row]
        self.__updateResources()

    def __updateResources(self):
        self.resourceList.clear()
        self._resourceFiles = []
        self.versionList.clear()
        self._currentFiles = []
        if self._currentStep is None:
            return

        # If open, list resources in wip folder
        if self.openButton.isChecked():
            # Shots and Assets
            if self.assetButton.isChecked() or self.shotButton.isChecked():
                if self._currentItem is None:
                    return
                # List resources
                resources = self._currentItem.stepFilePaths( self._currentStep )
                for resource in resources:
                    fileName = os.path.basename(resource)
                    fileInfo = ram.RamFileManager.decomposeRamsesFileName(fileName)
                    if fileInfo is None:
                        continue
                    res = fileInfo['resource']
                    self._resourceFiles.append( resource )
                    if res != "":
                        self.resourceList.addItem(res)
                    else:
                        self.resourceList.addItem("Main")
                        self._openButton.setEnabled(True)
                        self._currentResource = ""               
            # Templates
            else:
                # List resources
                folder = self._currentStep.templatesFolderPath()
                if folder == '':
                    return
                for f in os.listdir( folder ):
                    fileInfo = ram.RamFileManager.decomposeRamsesFileName(f)
                    if fileInfo is None:
                        continue
                    if fileInfo['project'] != self._currentStep.projectShortName():
                        continue
                    if fileInfo['step'] != self._currentStep.shortName():
                        continue 
                    res = fileInfo['object'] + ' | ' + fileInfo['resource']
                    self._resourceFiles.append( ram.RamFileManager.buildPath((
                        folder,
                        f
                    )) )
                    if res != '':
                        self.resourceList.addItem(res)
                    else:
                        self.resourceList.addItem("Main")
                        self._openButton.setEnabled(True)
                        self._currentResource = ""
        # If import, list all files in the publish folder
        else:
            files = []
            if self.assetButton.isChecked() or self.shotButton.isChecked():
                files = self._currentItem.publishFilePaths( None, self._currentStep )
            else:
                files = self._currentStep.templatesPublishFilePaths( )

            # Add an "Auto" field
            if len(files) > 0:
                i = QListWidgetItem( self.versionList )
                i.setText("Auto")
                i.setToolTip( "Automatically selects the files according to the current step." )
                self._importButton.setEnabled(True)

            for f in files:
                fileName = os.path.basename( f )
                fileInfo = ram.RamFileManager.decomposeRamsesFileName( fileName )
                if fileInfo is None:
                    continue
                self._currentFiles.append( f )
                n = fileInfo['resource']
                if n == '':
                    n = "Main"
                n = n + ' (' + fileInfo['extension'] + ')'
                i = QListWidgetItem( self.versionList )
                i.setText(n)
                i.setToolTip(f)

    @Slot()
    def __resourceChanged(self, row):
        if self.importButton.isChecked():
            self.__updateResources()
            return

        self._importButton.setEnabled(False)
        if row < 0:
            self._currentResource = ''
            self._openButton.setEnabled(False)
        else:
            self._openButton.setEnabled(True)
            self._currentResource = self.resourceList.item(row).text()

        if self._currentResource == "Main":
            self._currentResource = ""

        self.versionList.clear()
        self._currentFiles = []

        if self.templateButton.isChecked() and row in range(0, len(self._resourceFiles)):
            self._currentItem = ram.RamItem.fromPath( self._resourceFiles[ row ] )

        if self._currentItem is None:
            return
        if self._currentStep is None and ( self.assetButton.isChecked() or self.shotButton.isChecked() ):
            return

        # List versions
        if self.assetButton.isChecked() or self.shotButton.isChecked():
            self._currentFiles = self._currentItem.versionFilePaths(self._currentResource, self._currentStep)
        else:
            self._currentFiles = self._currentItem.versionFilePaths()
        self._currentFiles.reverse()
        # Add current
        self.versionList.addItem("Current Version")
        # Add other versions
        for f in self._currentFiles:
            fileName = os.path.basename( f )
            fileInfo = ram.RamFileManager.decomposeRamsesFileName( fileName )
            if fileInfo is None:
                continue
            comment = ram.RamMetaDataManager.getComment( f )
            itemText = fileInfo['state'] + ' | ' + str(fileInfo['version'])
            if comment != "":
                itemText = itemText + ' | ' + comment
            self.versionList.addItem(itemText)

    @Slot()
    def __versionChanged(self, row):
        self._importButton.setEnabled(row >= 0)

    @Slot()
    def __import(self):
        self.done(2)

    def setProject(self, project):
        if project is None:
            self.projectBox.setCurrentIndex(-1)
            return
        for i in range(self.projectBox.count()):
            if self.projectBox.itemData(i) == project.shortName():
                self.projectBox.setCurrentIndex(i)
                return
        n = project.name()
        if n == "":
            n = project.shortName()
        self.projectBox.addItem(n, project.shortName())
        self.projectBox.setCurrentIndex( self.projectBox.count() - 1)

    def getItem(self):
        return self._currentItem

    def getStep(self):
        return self._currentStep
    
    def getResource(self):
        resource = self._currentResource.replace(' | ', '_')
        if resource.endswith('_'):
            resource = resource[0:-1]
        return resource

    def _getFile(self, versionIndex):

        if self.importButton.isChecked() and versionIndex <= 0:
            return ""
            
        if versionIndex <= 0:
            if self.assetButton.isChecked() or self.shotButton.isChecked():
                file = self._currentItem.stepFilePath(self._currentResource, "ma", self._currentStep)
                if file != "":
                    return file
                file = self._currentItem.stepFilePath(self._currentResource, "mb", self._currentStep)
                if file != "":
                    return file
                return ""
            else:
                resourceRow = self.resourceList.currentRow()
                if resourceRow > 0:
                    return self._resourceFiles[ resourceRow ]

        return self._currentFiles[versionIndex-1]

    def getFile(self):
        row = self.versionList.currentRow()
        return self._getFile(row)
        
    def getFiles(self):
        items = self.versionList.selectedItems()
        if len(items) == 0:
            return [ self.getFile() ]
        
        files = []
        for i in range(0, self.versionList.count()):
            if self.versionList.item(i).isSelected():
                files.append( self._getFile(i) )
        return files


if __name__ == '__main__':
    importDialog = ImportDialog()
    ok = importDialog.exec_()

    item = importDialog.getItem()
    step = importDialog.getStep()
    filePath = importDialog.getFile()
    itemShortName = item.shortName()
    projectShortName = item.projectShortName()
    stepShortName = step.shortName()
    resource = importDialog.getResource()
    files = importDialog.getFiles()

    print(item)
    print(step)
    print(filePath)
    print(itemShortName)
    print(projectShortName)
    print(stepShortName)
    print(resource)
    print(ok)
    print(files)