import sys
import maya.api.OpenMaya as om # pylint: disable=import-error
import ramses_maya as ram

def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass

def initializePlugin(obj):
    # Register all commands
    plugin = om.MFnPlugin(obj, ram.vendor, ram.version)

    for c in ram.cmds_classes:
        try:
            plugin.registerCommand( c.name, c.createCommand )
        except:
            sys.stderr.write( "Failed to register command: %s\n" % c.name )

def uninitializePlugin(obj):
    # Register all commands
    plugin = om.MFnPlugin(obj, ram.vendor, ram.version)

    for c in reversed( ram.cmds_classes ):
        try:
            plugin.deregisterCommand( c.name )
        except:
            sys.stderr.write( "Failed to unregister command: %s\n" % c.name )