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
    QPushButton
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

        self.typeBox = QComboBox()
        self.typeBox.addItem("Asset")
        self.typeBox.addItem("Shot")
        self.typeBox.addItem("Template")
        self.typeBox.setCurrentIndex(-1)
        self.typeBox.setEnabled(False)
        topLayout.addRow( "Type:", self.typeBox )

        self.actionBox = QComboBox()
        self.actionBox.addItem("Open Item")
        self.actionBox.addItem("Import Item")
        topLayout.addRow( "Action:", self.actionBox )

        midLayout.addLayout( topLayout )

        itemLayout = QVBoxLayout()
        itemLayout.setSpacing(3)
        self.itemLabel = QLabel("Item")
        self.itemLabel.hide()
        itemLayout.addWidget(self.itemLabel)
        self.groupBox = QComboBox()
        self.groupBox.hide()
        itemLayout.addWidget(self.groupBox)
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
        resourcesLabel = QLabel("Resource:")
        resourcesLayout.addWidget(resourcesLabel)
        self.resourceList = QListWidget()
        resourcesLayout.addWidget(self.resourceList)
        midLayout.addLayout(resourcesLayout)

        versionsLayout = QVBoxLayout()
        versionsLayout.setSpacing(3)
        self.versionsLabel = QLabel("Version:")
        versionsLayout.addWidget(self.versionsLabel)
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
        self.typeBox.currentIndexChanged.connect( self.__typeChanged )
        self.actionBox.currentIndexChanged.connect( self.__actionChanged )
        self._cancelButton.clicked.connect( self.reject )
        self._openButton.clicked.connect( self.accept )
        self._importButton.clicked.connect( self.__import )
        self.itemList.currentRowChanged.connect( self.__itemChanged )
        self.stepList.currentRowChanged.connect( self.__stepChanged )
        self.resourceList.currentRowChanged.connect( self.__resourceChanged )
        self.versionList.currentRowChanged.connect( self.__versionChanged )
        self.groupBox.currentIndexChanged.connect( self.__groupChanged )

    def __loadProjects(self):
        # Load projects
        projects = ramses.projects()
        self.projectBox.clear()
        if projects is None:
            self.typeBox.setCurrentIndex(-1)
            return
        for project in ramses.projects():
            n = project.name()
            if n == "":
                n = project.shortName()
            self.projectBox.addItem(n, project.shortName())
        self.projectBox.setCurrentIndex(-1)

    @Slot()
    def __projectChanged(self, index):
        self.typeBox.setCurrentIndex(-1)
        self.typeBox.setEnabled(index != -1)
        if index == -1:
            self._currentProject = None
            return
        self._currentProject = ramses.project( self.projectBox.currentData() )

    @Slot()
    def __typeChanged( self, index ):
        # adjust UI
        if index in (0, 1):
            self.itemLabel.show()
            self.itemList.show()
            if index == 0:
                self.itemLabel.setText("Asset:")
                self.groupBox.show()
            else:
                self.itemLabel.setText("Shot:")
                self.groupBox.hide()
        else:
            self.itemLabel.hide()
            self.itemList.hide()
            self.groupBox.hide()
        # reinit lists
        self.itemList.clear()
        self.stepList.clear()
        self.resourceList.clear()
        self.versionList.clear()
        self.groupBox.clear()
        self._currentItems = []
        self._currentSteps = []
        if index == -1:
            return
        # Load asset groups and asset steps
        if index == 0:
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
        elif index == 1:
            if self._currentProject is None:
                return
            self._currentItems = self._currentProject.shots()
            self.__updateItems()
            self._currentSteps = self._currentProject.steps( ram.StepType.SHOT_PRODUCTION )
        # Load templates
        elif index == 2:
            self._currentSteps = self._currentProject.steps()

        # Populate steps
        for step in self._currentSteps:
            n = step.name()
            if n == "":
                n = step.shortName()
            self.stepList.addItem(n)
        
    @Slot()
    def __actionChanged(self, index):
        if index == 0:
            self._importButton.hide()
            self._openButton.show()
            self.versionsLabel.setText("Version:")
        else:
            self._importButton.show()
            self._openButton.hide()
            self.versionsLabel.setText("File:")
        self.__resourceChanged( self.resourceList.currentRow() )

    @Slot()
    def __groupChanged(self, index):
        # Load assets
        self._currentItems = self._currentProject.assets( self.groupBox.currentData() )
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
        if self._currentStep is None:
            return
        # Shots and Assets
        if self.typeBox.currentIndex() in (0,1):
            if self._currentItem is None:
                return
            # List resources
            for resource in self._currentItem.stepFilePaths( self._currentStep ):
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

    @Slot()
    def __resourceChanged(self, row):
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

        if self.typeBox.currentIndex() == 2 and row in range(0, len(self._resourceFiles)):
            self._currentItem = ram.RamItem.fromPath( self._resourceFiles[ row ] )

        if self._currentItem is None:
            return
        if self._currentStep is None and self.typeBox.currentIndex() in (0,1):
            return

        # List versions or published files
        if self.actionBox.currentIndex() == 0: # Open action, list versions
            if self.typeBox.currentIndex() in (0,1):
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
        else: # Import Action, list published files
            if self.typeBox.currentIndex() in (0,1):
                self._currentFiles = self._currentItem.publishFilePaths( self._currentResource, self._currentStep )
            else:
                self._currentFiles = self._currentItem.publishFilePaths( )
            for f in self._currentFiles:
                fileName = os.path.basename( f )
                self.versionList.addItem(fileName)

    @Slot()
    def __versionChanged(self, row):
        self._importButton.setEnabled(row >= 0)

    @Slot()
    def __import(self):
        self.done(2)

    def setProject(self, project):
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

    def getFile(self):
        row = self.versionList.currentRow()
        # if open (index 0), there's an extra item on top of the list
        l = - self.actionBox.currentIndex()
        if row <= l:
            if self.typeBox.currentIndex() in (0,1):
                file = self._currentItem.stepFilePath(self._currentResource, "ma", self._currentStep)
                if file != "":
                    return file
                file = self._currentItem.stepFilePath(self._currentResource, "mb", self._currentStep)
                if file != "":
                    return file
                return ""
            else:
                resourceRow = self.resourceList.currentRow()
                if resourceRow >= 0:
                    return self._resourceFiles[ resourceRow ]
        # if open (index 0), there's an extra item on top of the list
        r = 1-self.actionBox.currentIndex()
        return self._currentFiles[row-r]

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

    print(item)
    print(step)
    print(filePath)
    print(itemShortName)
    print(projectShortName)
    print(stepShortName)
    print(resource)
    print(ok)
