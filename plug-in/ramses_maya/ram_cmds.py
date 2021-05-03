import sys

import maya.api.OpenMaya as om # pylint: disable=import-error
import maya.cmds as cmds # pylint: disable=import-error

from dumaf import ( # pylint: disable=import-error,no-name-in-module
    registerCommands,
    unregisterCommands,
    getMayaWindow
)

from ui_settings import SettingsDialog # pylint: disable=import-error,no-name-in-module

import ramses as ram
# Keep the ramses instance at hand
ramses = ram.Ramses.instance()

class RamOpenCmd( om.MPxCommand ):
    name = "ramOpen"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamOpenCmd()

    def doIt(self, args):
        ram.log("Command 'open' is not implemented yet!")

class RamSaveCmd( om.MPxCommand ):
    name = "ramSave"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSaveCmd()

    def doIt(self, args):
        ram.log("Command 'save' is not implemented yet!")

class RamSaveVersionCmd( om.MPxCommand ):
    name = "ramSaveVersion"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSaveVersionCmd()

    def doIt(self, args):
        ram.log("Command 'save new version' is not implemented yet!")

class RamPublishCmd( om.MPxCommand ):
    name = "ramPublish"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamPublishCmd()

    def doIt(self, args):
        ram.log("Command 'publish' is not implemented yet!")

class RamRetrieveVersionCmd( om.MPxCommand ):
    name = "ramRetriveVersion"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamRetrieveVersionCmd()

    def doIt(self, args):
        ram.log("Command 'retrieve version' is not implemented yet!")

class RamPublishTemplateCmd( om.MPxCommand ):
    name = "ramPulbishTemplate"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamPublishTemplateCmd()

    def doIt(self, args):
        ram.log("Command 'publish as template' is not implemented yet!")

class RamOpenTemplateCmd( om.MPxCommand ):
    name = "ramOpenTemplate"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamOpenTemplateCmd()

    def doIt(self, args):
        ram.log("Command 'open template' is not implemented yet!")

class RamImportTemplateCmd( om.MPxCommand ):
    name = "ramImportTemplate"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamImportTemplateCmd()

    def doIt(self, args):
        ram.log("Command 'import template' is not implemented yet!")

class RamSettingsCmd( om.MPxCommand ):
    name = "ramSettings"
    settingsDialog = SettingsDialog( getMayaWindow() )

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSettingsCmd()

    def doIt(self, args):
        ram.log("Opening settings...")  
        self.settingsDialog.show()

class RamOpenRamsesCmd( om.MPxCommand ):
    name = "ramOpenRamses"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamOpenRamsesCmd()

    def doIt(self, args):
        ram.log("Opening the Ramses client...")
        ramses.showClient()
        
cmds_classes = (
    RamOpenCmd,
    RamSaveCmd,
    RamSaveVersionCmd,
    RamPublishCmd,
    RamRetrieveVersionCmd,
    RamPublishTemplateCmd,
    RamOpenTemplateCmd,
    RamImportTemplateCmd,
    RamSettingsCmd,
    RamOpenRamsesCmd,
)

cmds_menuItems = []

def maya_useNewAPI():
    pass

def initializePlugin(obj):
    # Register all commands
    registerCommands( obj, cmds_classes )

    # Add Menu Items
    cmds_menuItems.append( [
        cmds.menuItem(
            parent='MayaWindow|mainWindowMenu',
            divider=True
            ),
        cmds.menuItem(
            parent='MayaWindow|mainWindowMenu',
            label='Ramses Settings',
            command=cmds.ramSettings
            ) ]
    )

def uninitializePlugin(obj):
    # Unregister all commands
    unregisterCommands( obj, cmds_classes )

    # Remove menu items
    for menuItem in cmds_menuItems:
        cmds.deleteUI( menuItem, menuItem = True )
