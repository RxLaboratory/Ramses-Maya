import ramses_maya as ram
import maya.api.OpenMaya as om # pylint: disable=import-error

vendor = "RxLaboratory"
version = "0.0.1-dev"

def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass

def initializePlugin( obj ):
    plugin = om.MFnPlugin(obj, vendor, version)

    for c in ram.cmds_classes:
        try:
            plugin.registerCommand( c.name, c.createCommand, c.createSyntax )
        except Exception as e:
            print(e)
            ram.log( "Failed to register command: %s\n" % c.name, ram.LogLevel.Critical )

    ram.log( "I'm ready!" )

def uninitializePlugin( obj ):
    plugin = om.MFnPlugin(obj, vendor, version)

    for c in reversed( ram.cmds_classes ):
        try:
            plugin.deregisterCommand( c.name )
        except:
            ram.log( "Failed to unregister command: %s\n" % c.name )

    ram.log( "Thanks for playing with me. Much love, See you soon." )
