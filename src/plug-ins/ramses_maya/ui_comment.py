# -*- coding: utf-8 -*-

try:
    from PySide2 import QtWidgets as qw
except:  # pylint: disable=bare-except
    from PySide6 import QtWidgets as qw

from ramses_maya.ui_dialog import Dialog

class CommentDialog( Dialog ):
    def __init__(self, parent = None):
        super(CommentDialog,self).__init__(parent)
        self.__setupUi()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Add a comment to this version" )
        self.setMinimumWidth(400)

        mainLayout = qw.QVBoxLayout()
        mainLayout.setSpacing(3)
        self.main_layout.addLayout(mainLayout)

        self.textEdit = qw.QLineEdit()
        mainLayout.addWidget(self.textEdit)

        buttonsLayout = qw.QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._saveButton = qw.QPushButton("Add Comment and Save")
        buttonsLayout.addWidget( self._saveButton )
        self._cancelButton = qw.QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

    def __connectEvents(self):
        self._saveButton.clicked.connect( self.accept )
        self._cancelButton.clicked.connect( self.reject )

    def getComment(self):
        return self.textEdit.text()

    def setComment(self, comment):
        self.textEdit.setText(comment)

if __name__ == '__main__':
    dialog = CommentDialog()
    ok = dialog.exec_()
    print(ok)
