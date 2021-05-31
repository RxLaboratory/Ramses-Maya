import sys
from PySide2.QtWidgets import (
    QApplication
)
import maya.cmds as cmds

def getCreateGroup( groupName ):
    n = '|' + groupName
    if cmds.objExists(n):
        return n
    cmds.group( name= groupName, em=True )
    return n

def getMayaWindow():
    app = QApplication.instance() #get the qApp instance if it exists.
    if not app:
        app = QApplication(sys.argv)

    try:
        mayaWin = next(w for w in app.topLevelWidgets() if w.objectName()=='MayaWindow')
        return mayaWin
    except:
        return None