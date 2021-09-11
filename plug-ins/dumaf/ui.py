# -*- coding: utf-8 -*-

import sys
from PySide2.QtWidgets import ( # pylint: disable=import-error disable=no-name-in-module
    QApplication
)

def getMayaWindow():
    app = QApplication.instance() #get the qApp instance if it exists.
    if not app:
        app = QApplication(sys.argv)

    try:
        mayaWin = next(w for w in app.topLevelWidgets() if w.objectName()=='MayaWindow')
        return mayaWin
    except:
        return None
