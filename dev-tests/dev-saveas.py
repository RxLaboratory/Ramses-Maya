import os

from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QDialog,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
    QFormLayout,
    QWidget,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot,
)

import maya.cmds as cmds

import ramses as ram
ramses = ram.Ramses.instance()

class SaveAsDialog( QDialog ):

    def __init__(self, parent=None):
        super(SaveAsDialog, self).__init__(parent)

        self.__currentProject = None
        self.__currentStep = None
        self.__currentItem = None

        self.__setupUi()
        self.__loadProjects()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Save Scene As..." )

        self.setMinimumWidth(400)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        topLayout = QFormLayout()
        topLayout.setFieldGrowthPolicy( QFormLayout.AllNonFixedFieldsGrow )
        topLayout.setSpacing(3)

        self.projectBox = QComboBox()
        self.projectBox.setEditable(True)
        topLayout.addRow( "Project:", self.projectBox )

        typeWidget = QWidget()
        typeLayout = QVBoxLayout()
        typeLayout.setContentsMargins(0,0,0,0)
        typeLayout.setSpacing(3)
        self.assetButton = QRadioButton("Asset")
        self.assetButton.setChecked(True)
        typeLayout.addWidget(self.assetButton)
        self.shotButton = QRadioButton("Shot")
        typeLayout.addWidget(self.shotButton)
        self.otherButton = QRadioButton("Other")
        typeLayout.addWidget(self.otherButton)
        typeWidget.setLayout(typeLayout)
        topLayout.addRow("Type:", typeWidget)

        self.stepBox = QComboBox()
        self.stepBox.setEditable(True)
        topLayout.addRow( "Step:", self.stepBox )

        self.assetGroupBox = QComboBox()
        self.assetGroupBox.setEditable(True)
        self.assetGroupLabel = QLabel("Asset Group:")
        topLayout.addRow( self.assetGroupLabel, self.assetGroupBox )

        self.itemBox = QComboBox()
        self.itemBox.setEditable(True)
        self.itemLabel = QLabel("Item:")
        topLayout.addRow( self.itemLabel, self.itemBox )

        self.resourceEdit = QLineEdit()
        topLayout.addRow( "Resource:", self.resourceEdit)

        self.extensionBox = QComboBox()
        self.extensionBox.addItem("Maya Binary (.mb)", "mb")
        self.extensionBox.addItem("Maya ASCII (.ma)", "ma")
        topLayout.addRow("File Type:", self.extensionBox)

        locationWidget = QWidget()
        locationLayout = QHBoxLayout()
        locationLayout.setSpacing(3)
        locationLayout.setContentsMargins(0,0,0,0)
        locationWidget.setLayout(locationLayout)

        self.locationEdit = QLineEdit()
        self.locationEdit.setEnabled(False)
        self.locationEdit.setPlaceholderText("Location...")
        locationLayout.addWidget( self.locationEdit )

        self.browseButton = QPushButton("Browse...")
        self.browseButton.setVisible( False )
        locationLayout.addWidget( self.browseButton )

        topLayout.addRow("Location:",locationWidget)

        self.fileNameLabel = QLabel()
        topLayout.addRow("Filename:", self.fileNameLabel)

        mainLayout.addLayout(topLayout)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)
        self._saveButton = QPushButton("Save")
        buttonsLayout.addWidget( self._saveButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )
        mainLayout.addLayout( buttonsLayout )

        self.setLayout(mainLayout)

    def __connectEvents(self):
        self._saveButton.clicked.connect( self.accept )
        self._cancelButton.clicked.connect( self.reject )
        self.projectBox.currentTextChanged.connect( self.__loadSteps )
        self.stepBox.currentIndexChanged.connect( self.__loadItems )
        self.assetButton.clicked.connect( self.__typeChanged )
        self.shotButton.clicked.connect( self.__typeChanged )
        self.otherButton.clicked.connect( self.__typeChanged )
        self.assetGroupBox.currentIndexChanged.connect( self.__loadAssets )
        self.itemBox.currentTextChanged.connect( self.__buildPath )
        self.resourceEdit.textChanged.connect( self.__buildPath )
        self.extensionBox.currentIndexChanged.connect( self.__buildPath )

    def __loadProjects(self):
        # Load projects
        projects = ramses.projects()
        self.projectBox.clear()
        if len(projects) == 0:
            self.setOffline()
            self.__loadSteps( )
            return
        for project in ramses.projects():
            n = project.name()
            if n == "":
                n = project.shortName()
            self.projectBox.addItem(n, project.shortName())
        self.__loadSteps( )

    def __getCurrentShortName(self, comboBox):
        currentIndex = comboBox.currentIndex()
        currentText = comboBox.currentText()
        itemText = comboBox.itemText( currentIndex )
        if currentIndex == -1:
            return currentText
        if currentText == itemText:
            return comboBox.itemData( currentIndex )
        return currentText

    @Slot()
    def __loadSteps(self):
        projectShortName = self.__getCurrentShortName( self.projectBox )
        self.__currentProject = ramses.project( projectShortName )
        self.stepBox.clear()
        if self.__currentProject is None:
            return
        steps = []
        if self.assetButton.isChecked():
            steps = self.__currentProject.steps( ram.StepType.ASSET_PRODUCTION )
        elif self.shotButton.isChecked():
            steps = self.__currentProject.steps( ram.StepType.SHOT_PRODUCTION )
        else:
            steps = self.__currentProject.steps( )
        for step in steps:
            n = step.name()
            if n == "":
                n = step.shortName()
            self.stepBox.addItem(n, step.shortName())
        self.__loadItems()

    def __buildPath(self):
        self.locationEdit.setText('')
        self.fileNameLabel.setText('')
        self._saveButton.setEnabled(False)
        if self.__currentProject is None:
            self.locationEdit.setPlaceholderText('Sorry, invalid project...')
            return
        if self.__currentStep is None:
            self.locationEdit.setPlaceholderText('Sorry, invalid step...')
            return
        
        if self.assetButton.isChecked():

            # Get the group
            assetGroup = self.assetGroupBox.currentText()
            if assetGroup == '':
                self.locationEdit.setText('Sorry, invalid asset group...')
                return

            # Let's get the step/asset location
            assetShortName = self.__getCurrentShortName( self.itemBox )
            if assetShortName == '':
                self.locationEdit.setPlaceholderText("Sorry, invalid asset...")
                return

            assetsPath = self.__currentProject.assetsPath( assetGroup )

            assetFolderName = ram.RamFileManager.buildRamsesFileName(
                self.__currentProject.shortName(),
                '',
                '',
                ram.ItemType.ASSET,
                assetShortName
            )
            assetStepFolderName = ram.RamFileManager.buildRamsesFileName(
                self.__currentProject.shortName(),
                self.__currentStep.shortName(),
                '',
                ram.ItemType.ASSET,
                assetShortName
            )
            # The folder
            assetFolder = ram.RamFileManager.buildPath((
                assetsPath,
                assetFolderName,
                assetStepFolderName
            ))

            self.locationEdit.setText(assetFolder)

            # The filename
            assetFileName = ram.RamFileManager.buildRamsesFileName(
                self.__currentProject.shortName(),
                self.__currentStep.shortName(),
                self.extensionBox.currentData(),
                ram.ItemType.ASSET,
                assetShortName,
                self.resourceEdit.text()
            )

            self.fileNameLabel.setText(assetFileName)
                
        elif self.shotButton.isChecked():
            shotShortName = self.__getCurrentShortName( self.itemBox )
            if shotShortName == '':
                self.locationEdit.setPlaceholderText("Sorry, invalid shot...")
                return

            shotsPath = self.__currentProject.shotsPath()
            shotFolderName = ram.RamFileManager.buildRamsesFileName(
                self.__currentProject.shortName(),
                '',
                '',
                ram.ItemType.SHOT,
                shotShortName
            )

            shotStepFolderName = ram.RamFileManager.buildRamsesFileName(
                self.__currentProject.shortName(),
                self.__currentStep.shortName(),
                '',
                ram.ItemType.SHOT,
                shotShortName
            )

            shotFolder = ram.RamFileManager.buildPath((
                shotsPath,
                shotFolderName,
                shotStepFolderName
            ))

            self.locationEdit.setText(shotFolder)

            # The filename
            shotFileName = ram.RamFileManager.buildRamsesFileName(
                self.__currentProject.shortName(),
                self.__currentStep.shortName(),
                self.extensionBox.currentData(),
                ram.ItemType.SHOT,
                shotShortName,
                self.resourceEdit.text()
            )

            self.fileNameLabel.setText(shotFileName)
        
        else:
            itemShortName = self.__getCurrentShortName( self.itemBox )

            stepPath = self.__currentStep.folderPath()

            self.locationEdit.setText(stepPath)

            # The filename
            itemFileName = ram.RamFileManager.buildRamsesFileName(
                self.__currentProject.shortName(),
                self.__currentStep.shortName(),
                self.extensionBox.currentData(),
                ram.ItemType.GENERAL,
                itemShortName,
                self.resourceEdit.text()
            )

            self.fileNameLabel.setText( itemFileName )

        self._saveButton.setEnabled(True)

    @Slot()
    def __typeChanged(self):
        if self.assetButton.isChecked():
            self.assetGroupBox.show()
            self.assetGroupLabel.show()
        else:
            self.assetGroupBox.hide()
            self.assetGroupLabel.hide()

        self.__loadSteps()

    @Slot()
    def __loadItems(self):
        self.itemBox.clear()
        self.assetGroupBox.clear()
        print(self.__currentProject)
        if self.__currentProject is None:
            return
        stepShortName = self.__getCurrentShortName( self.stepBox )
        self.__currentStep = self.__currentProject.step( stepShortName )
        print(self.__currentStep)
        if self.__currentStep is None:
            return

        if self.assetButton.isChecked():
            # Load asset groups
            for ag in self.__currentProject.assetGroups():
                self.assetGroupBox.addItem(ag)
            self.__loadAssets()
        elif self.shotButton.isChecked():
            # Load shots
            print( self.__currentProject.shots() )
            for shot in self.__currentProject.shots():
                print(shot)
                n = shot.name()
                if n == "":
                    n = shot.shortName()
                self.itemBox.addItem(n, shot.shortName())

        self.__buildPath()

    @Slot()
    def __loadAssets(self):
        self.itemBox.clear()
        if self.__currentProject is None:
            return
        ag = self.assetGroupBox.currentText() 
        for asset in self.__currentProject.assets( ag ):
            n = asset.name()
            if n == "":
                n = asset.shortName()
            self.itemBox.addItem(n, asset.shortName())

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

    def setStep(self, step):
        for i in range( self.stepBox.count() ):
            if self.stepBox.itemData(i) == step.shortName():
                self.stepBox.setCurrentIndex(i)
                return
        n = step.name()
        if n == "":
            n = step.shortName()
        self.stepBox.addItem(n, step.shortName())
        self.stepBox.setCurrentIndex( self.stepBox.count() - 1)

    def setItem(self, item):
        if item.itemType() == ram.ItemType.ASSET:
            self.assetButton.setChecked(True)
        elif item.itemType() == ram.ItemType.SHOT:
            self.shotButton.setChecked(True)
        else:
            self.otherButton.setChecked(True)

        self.__typeChanged()

        for i in range( self.itemBox.count() ):
            if self.itemBox.itemData(i) == item.shortName():
                self.itemBox.setCurrentIndex(i)
                return
        n = item.name()
        if n == "":
            n = item.shortName()
        self.itemBox.addItem(n, item.shortName())
        self.itemBox.setCurrentIndex( self.itemBox.count() - 1)

    def setItemShortName(self, itemShortName):
        for i in range( self.itemBox.count() ):
            if self.itemBox.itemData(i) == itemShortName:
                self.itemBox.setCurrentIndex(i)
                return
        self.itemBox.addItem(itemShortName, itemShortName)
        self.itemBox.setCurrentIndex( self.itemBox.count() - 1)

    def getFilePath(self):
        path = self.locationEdit.text()
        if path == '':
            return ''
        fileName = self.fileNameLabel.text()
        return ram.RamFileManager.buildPath((
            path,
            fileName
        ))

def getCurrentProject( filePath ):
    fileInfo = ram.RamFileManager.decomposeRamsesFilePath(filePath)
    # Set the project and step
    project = None
    if fileInfo is not None:
        project = ramses.project( fileInfo['project'] )
        ramses.setCurrentProject( project )
    # Try to get the current project
    if project is None:
        project = ramses.currentProject()

    return project

def getStep( filePath ):
    project = getCurrentProject( filePath )
    fileInfo = ram.RamFileManager.decomposeRamsesFilePath(filePath)
    if fileInfo is not None and project is not None:
        return project.step( fileInfo['step'] )

def saveAs():
    # Get current info
    currentFilePath = cmds.file( q=True, sn=True )

    # Info
    project = getCurrentProject( currentFilePath )
    step = getStep( currentFilePath )
    item = ram.RamItem.fromPath( currentFilePath )

    saveAsDialog = SaveAsDialog()
    if project is not None:
        saveAsDialog.setProject( project )
    if item is not None:
        saveAsDialog.setItem(item)
    if step is not None:
        saveAsDialog.setStep( step )
    if not saveAsDialog.exec_():
        return

    filePath = saveAsDialog.getFilePath()
    if filePath == '':
        return
    # Create folder
    folder = os.path.dirname(filePath)
    fileName = os.path.basename(filePath)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    # Check if file exists
    if os.path.isfile( filePath ):
        result = cmds.confirmDialog( message="The corresponding file already exits. Do you want to overwrite it?", button=("Overwrite and Save", "Cancel") )
        if result == 'Cancel':
            return

    cmds.file(rename = filePath )
    cmds.file( save=True, options="v=1;", f=True )

    ram.log( "Scene saved as: " + filePath )
    cmds.inViewMessage( msg='Scene saved as: <hl>' + fileName + '</hl>.', pos='midCenter', fade=True )


saveAs()