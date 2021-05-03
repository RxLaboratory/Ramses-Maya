import sys
import maya.api.OpenMaya as om # pylint: disable=import-error
from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QApplication
)

vendor = "RxLaboratory"
version = "0.0.1-dev"

def registerCommands( obj, classes ):
    plugin = om.MFnPlugin(obj, vendor, version)

    for c in classes:
        try:
            plugin.registerCommand( c.name, c.createCommand )
        except:
            sys.stderr.write( "Failed to register command: %s\n" % c.name )

    return plugin

def unregisterCommands( obj, classes ):
    plugin = om.MFnPlugin(obj, vendor, version)

    for c in reversed( classes ):
        try:
            plugin.deregisterCommand( c.name )
        except:
            sys.stderr.write( "Failed to unregister command: %s\n" % c.name )

    return plugin

def getMayaWindow():
    app = QApplication.instance() #get the qApp instance if it exists.
    if not app:
        app = QApplication(sys.argv)

    try:
        mayaWin = next(w for w in app.topLevelWidgets() if w.objectName()=='MayaWindow')
        return mayaWin
    except:
        return None