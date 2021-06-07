import maya.cmds as cmds # pylint: disable=import-error

class RamsesAttribute():
    MANAGED = 'ramsesManaged'
    GEO_FILE = 'ramsesGeoFilePath'
    GEO_TIME = 'ramsesGeoTimeStamp'
    SHADING_TYPE = 'ramsesShadingType'
    SHADING_FILE = 'ramsesShadingFilePath'
    SHADING_TIME = 'ramsesShadingTimeStamp'
    DT_TYPES = ('string')
    AT_TYPES = ('long', 'bool')

def setRamsesAttr( node, attr, value, t):
    # Add if not already there
    if attr not in cmds.listAttr(node):
        if t in RamsesAttribute.DT_TYPES:
            cmds.addAttr( node, ln= attr, dt=t)
        else:
            cmds.addAttr( node, ln=attr, at=t)
    # Unlock
    cmds.setAttr( node + '.' + attr, lock=False )
    # Set
    if t in RamsesAttribute.DT_TYPES:
        cmds.setAttr( node + '.' + attr, value, type=t)
    else:
        cmds.setAttr( node + '.' + attr, value )    
    # Lock
    cmds.setAttr( node + '.' + attr, lock=True )

def setRamsesManaged(node, managed=True):
    setRamsesAttr( node, RamsesAttribute.MANAGED, True, 'bool' )