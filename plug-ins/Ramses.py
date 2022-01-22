import ramses_maya as ram
import maya.cmds as cmds # pylint: disable=import-error
import maya.api.OpenMaya as om # pylint: disable=import-error

vendor = "RxLaboratory"
version = "0.2.10-alpha"

def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass

saveCmd = """
import maya.cmds as cmds
ok = cmds.pluginInfo('Ramses', loaded=True, q=True)
if not ok:
    cmds.loadPlugin('Ramses')
cmds.ramSave()
"""

openCmd = """
import maya.cmds as cmds
ok = cmds.pluginInfo('Ramses', loaded=True, q=True)
if not ok:
    cmds.loadPlugin('Ramses')
cmds.ramOpen()
"""

saveAsCmd = """
import maya.cmds as cmds
ok = cmds.pluginInfo('Ramses', loaded=True, q=True)
if not ok:
    cmds.loadPlugin('Ramses')
cmds.ramSaveAs()
"""

def installHotkeys():
    # Register hotkeys
    settings = ram.RamSettings.instance()
    save = True
    if 'useRamSaveSceneHotkey' in settings.userSettings:
        save = settings.userSettings['useRamSaveSceneHotkey']
    open = True
    if 'useRamOpenceneHotkey' in settings.userSettings:
        open = settings.userSettings['useRamOpenceneHotkey']
    saveas = True
    if 'useRamSaveAsHotkey' in settings.userSettings:
        saveas = settings.userSettings['useRamSaveAsHotkey']
       
    if save:
        ram.maf.HotKey.createHotkey(saveCmd, 'ctrl+s', 'RamSaveScene', "Ramses Save Scene", "Ramses" )

    if open:
        ram.maf.HotKey.createHotkey(openCmd, 'ctrl+o', 'RamOpenScene', "Ramses Open Scene", "Ramses" )

    if saveas:
        ram.maf.HotKey.createHotkey(saveAsCmd, 'ctrl+shift+s', 'RamSaveSceneAs', "Ramses Save Scene As", "Ramses" )

def initializePlugin( obj ):
    plugin = om.MFnPlugin(obj, vendor, version)

    ram.log( "Hi, I'm Ramses, the Rx Asset Management System... I'm loading!" )

    for c in ram.cmds_classes:
        try:
            plugin.registerCommand( c.name, c.createCommand, c.createSyntax )
        except Exception as e:
            print(e)
            ram.log( "Failed to register command: %s\n" % c.name, ram.LogLevel.Critical )

    installHotkeys()

    ram.log( "I'm ready!" )

def uninitializePlugin( obj ):
    plugin = om.MFnPlugin(obj, vendor, version)

    # Rstore hotkeys
    ram.maf.HotKey.restoreSaveSceneHotkey()
    ram.maf.HotKey.restoreOpenSceneHotkey()
    ram.maf.HotKey.restoreSaveSceneAsHotkey()

    for c in reversed( ram.cmds_classes ):
        try:
            plugin.deregisterCommand( c.name )
        except:
            ram.log( "Failed to unregister command: %s\n" % c.name )

    ram.log( "Thanks for playing with me. Much love, See you soon." )
