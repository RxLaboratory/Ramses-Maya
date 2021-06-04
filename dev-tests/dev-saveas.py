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

        self.stepBox = QComboBox()
        self.stepBox.setEditable(True)
        topLayout.addRow( "Step:", self.stepBox )

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

    def __loadProjects(self):
        # Load projects
        projects = ramses.projects()
        self.projectBox.clear()
        if projects is None:
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
        project = ramses.project( projectShortName )
        if project is not None:
            self.stepBox.clear()
            for step in project.steps():
                n = step.name()
                if n == "":
                    n = step.shortName()
                self.stepBox.addItem(n, step.shortName())
        self.__buildPath()

    def __buildPath(self):
        pass

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
    if not saveAsDialog.exec_():
        return

saveAs()