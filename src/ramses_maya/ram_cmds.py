import sys
import maya.api.OpenMaya as om # pylint: disable=import-error

from ramses import Ramses # pylint: disable=no-name-in-module
from ramses.logger import log # pylint: disable=import-error,no-name-in-module
from dumaf import plugins # pylint: disable=import-error

class RamOpenCmd( om.MPxCommand ):
    name = "ramOpen"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamOpenCmd()

    def doIt(self, args):
        log("Command 'open' is not implemented yet!")

class RamSaveCmd( om.MPxCommand ):
    name = "ramSave"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSaveCmd()

    def doIt(self, args):
        log("Command 'save' is not implemented yet!")

class RamSaveVersionCmd( om.MPxCommand ):
    name = "ramSaveVersion"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSaveVersionCmd()

    def doIt(self, args):
        log("Command 'save new version' is not implemented yet!")

class RamPublish( om.MPxCommand ):
    name = "ramPublish"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamPublish()

    def doIt(self, args):
        log("Command 'publish' is not implemented yet!")

class RamRetrieveVersion( om.MPxCommand ):
    name = "ramRetriveVersion"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamRetrieveVersion()

    def doIt(self, args):
        log("Command 'retrieve version' is not implemented yet!")

class RamPublishAsTemplate( om.MPxCommand ):
    name = "ramPulbishAsTemplate"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamPublishAsTemplate()

    def doIt(self, args):
        log("Command 'publish as template' is not implemented yet!")

class RamOpenTemplate( om.MPxCommand ):
    name = "ramOpenTemplate"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamOpenTemplate()

    def doIt(self, args):
        log("Command 'open template' is not implemented yet!")

class RamImportTemplate( om.MPxCommand ):
    name = "ramImportTemplate"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamImportTemplate()

    def doIt(self, args):
        log("Command 'import template' is not implemented yet!")

class RamSettings( om.MPxCommand ):
    name = "ramSettings"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamSettings()

    def doIt(self, args):
        log("Command 'settings' is not implemented yet!")

class RamOpenRamses( om.MPxCommand ):
    name = "ramOpenRamses"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def createCommand():
        return RamOpenRamses()

    def doIt(self, args):
        # TODO implement settings
        ramses = Ramses.instance
        ramses.settings().ramsesClientPath = "D:/RAINBOX/LAB/DEV/02 - Applications/Ramses/Deploy/Ramses-Win/Ramses.exe"
        ramses.showClient()
        

cmds_classes = (
    RamOpenCmd,
    RamSaveCmd,
    RamSaveVersionCmd,
    RamPublish,
    RamRetrieveVersion,
    RamPublishAsTemplate,
    RamOpenTemplate,
    RamImportTemplate,
    RamSettings,
    RamOpenRamses,
)

def maya_useNewAPI():
    pass

def initializePlugin(obj):
    # Register all commands
    plugins.registerCommands( obj, cmds_classes )

def uninitializePlugin(obj):
    # Unregister all commands
    plugins.unregisterCommands( obj, cmds_classes )