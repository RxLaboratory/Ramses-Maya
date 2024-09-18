# -*- coding: utf-8 -*-
"""The about dialog of the addon"""

try:
    from PySide2 import QtWidgets as qw
except:  # pylint: disable=bare-except
    from PySide6 import QtWidgets as qw

from ramses_maya.constants import VERSION, VENDOR, TOOL_NAME
from ramses_maya.utils import donate

class AboutDialog(qw.QDialog):
    """The about dialog"""

    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)

        self.setWindowTitle("About " + TOOL_NAME)

        l = qw.QVBoxLayout()
        l.setContentsMargins(6,6,6,6)
        l.setSpacing(6)
        self.setLayout(l)

        l.addWidget(qw.QLabel( "<strong>About " + TOOL_NAME + "</strong> by " + VENDOR + "<br />"
            "<i>v" + VERSION + "</i>"
        ))
        
        l.addWidget(qw.QLabel("<p>Licensed under the GNU General Public License v3</p>"
                          "<p>Please make a donation if you like this!</p>" ))

        self.donateButton = qw.QPushButton("💟 Donate ")
        l.addWidget(self.donateButton)

        self.donateButton.clicked.connect(donate)

if __name__ == "__main__":
    app = qw.QApplication.instance() or qw.QApplication()
    d = AboutDialog()
    d.exec_()
