import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error

def getPublishNodes():
    try:
        nodes = cmds.sets( 'Ramses_Publish', nodesOnly=True, q=True )
    except ValueError:
        ram.log("Nothing to publish! The asset you need to publish must be listed in a 'Ramses_Publish' set.")
        cmds.inViewMessage( msg='Nothing to publish! The asset you need to publish must be listed in a <hl>Ramses_Pulbish</hl> set.', pos='midCenter', fade=True )
        return ()

    if nodes is None or len(nodes) == 0:
        ram.log("The 'Ramses_Publish' set is empty, there's nothing to publish!")
        cmds.inViewMessage( msg="The <hl>Ramses_Publish</hl> set is empty, there's nothing to publish!", pos='midCenter', fade=True )
        return ()

    return nodes