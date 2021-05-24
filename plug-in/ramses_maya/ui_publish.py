import os, sys, platform
from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    QLine,
    Slot,
)

# In Dev Mode, Ramses lives in its repo
sys.path.append( 'D:/DEV_SRC/RxOT/Ramses/Ramses-Py' )

import ramses as ram
ramses = ram.Ramses.instance()

class PublishDialog( QDialog ):

    def __init__(self, parent=None):
        super(PublishDialog,self).__init__(parent)
        self.__setupUi()
        self.__populateUi()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Publish Template" )

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        topLayout = QHBoxLayout()
        topLayout.setSpacing(3)

        self.projectLabel = QLabel()
        topLayout.addWidget( self.projectLabel )

        self.stepBox = QComboBox()
        topLayout.addWidget( self.stepBox )

        self.stepLabel = QLabel()
        self.stepLabel.setVisible( False )
        topLayout.addWidget( self.stepLabel )

        middleLayout = QHBoxLayout()
        middleLayout.setSpacing(3)

        mainLayout.addLayout( topLayout )

        self.locationEdit = QLineEdit()
        self.locationEdit.setEnabled(False)
        self.locationEdit.setPlaceholderText("Location...")
        middleLayout.addWidget( self.locationEdit )

        self.browseButton = QPushButton("Browse...")
        self.browseButton.setVisible( False )
        middleLayout.addWidget( self.browseButton )

        mainLayout.addLayout( middleLayout )

        self.setLayout( mainLayout )

    def __connectEvents(self):
        self.browseButton.clicked.connect( self.browse )

    def __populateUi(self):
        project = ramses.currentProject()
        if project is None:
            self.setOffline()
            return
        self.projectLabel.setText( project.shortName() )
        steps = project.steps()
        for step in steps:
            self.stepBox.addItem( step.name(), step.shortName() )

    @Slot()
    def browse(self):
        path = QFileDialog.getExistingDirectory(self,
            "Select Templates Directory",
            ramses.folderPath(),
            QFileDialog.ShowDirsOnly)
        self.locationEdit.setText(path)
        # Try to extract info from the path
        if path != "":
            

    def setProjectShortName(self, projectShortName):
        self.projectLabel.setText( projectShortName )

    def setOffline(self, offline=True):
        online = not offline
        self.projectLabel.setEnabled(offline)
        self.stepBox.setVisible(online)
        self.stepLabel.setVisible(offline)
        self.locationEdit.setEnabled(offline)
        self.browseButton.setVisible(offline)

if __name__ == '__main__':
    publishDialog = PublishDialog()
    ok = publishDialog.exec_()
    print(ok)
