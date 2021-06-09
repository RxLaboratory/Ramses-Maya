import maya.cmds as cmds # pylint: disable=import-error
from .utils_attributes import *
import ramses as ram # pylint: disable=import-error

def getPublishNodes():
    try:
        nodes = cmds.sets( 'Ramses_Publish', nodesOnly=True, q=True )
    except ValueError:
        ram.log("Nothing to publish! The asset you need to publish must be listed in a 'Ramses_Publish' set.")
        cmds.inViewMessage( msg='Nothing to publish! The asset you need to publish must be listed in a <hl>Ramses_Publish</hl> set.', pos='midCenter', fade=True )
        return []

    if nodes is None or len(nodes) == 0:
        ram.log("The 'Ramses_Publish' set is empty, there's nothing to publish!")
        cmds.inViewMessage( msg="The <hl>Ramses_Publish</hl> set is empty, there's nothing to publish!", pos='midCenter', fade=True )
        return []

    return nodes

def getProxyNodes( showAlert = False ):
    try:
        nodes = cmds.sets( 'Ramses_Proxies', nodesOnly=True, q=True )
    except ValueError:
        if showAlert:
            ram.log("Can't find any proxy! The proxy you need to publish must be listed in a 'Ramses_Proxies' set.")
            cmds.inViewMessage( msg="Can't find any proxy! The proxy you need to publish must be listed in a <hl>Ramses_Proxies</hl> set.", pos='midCenter', fade=True )
        return []

    if nodes is None or len(nodes) == 0:
        if showAlert:
            ram.log("The 'Ramses_Proxies' set is empty.")
            cmds.inViewMessage( msg="The <hl>Ramses_Proxies</hl> set is empty.", pos='midCenter', fade=True )
        return []

    for node in nodes:
        setRamsesAttr( node, RamsesAttribute.IS_PROXY, True, 'bool' )

    return nodes