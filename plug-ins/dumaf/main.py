import sys, tempfile, re
import maya.cmds as cmds # pylint: disable=import-error
import maya.api.OpenMaya as om # pylint: disable=import-error
from PySide2.QtWidgets import ( # pylint: disable=import-error disable=no-name-in-module
    QApplication
)

def getNodesInSet( setName ):
    # Create a list and add the set
    selectionList = om.MSelectionList()
    try:
        selectionList.add( setName )
    except:
        return []
    # Get the node for the set and create a FnSet
    node = selectionList.getDependNode( 0 )
    set = om.MFnSet(node)
    # Get all members of the set
    publishNodes = set.getMembers( True )
    publishPaths = []
    # An iterator to get all dagPaths
    iterator = om.MItSelectionList(publishNodes)
    while not iterator.isDone():
        dagPath = iterator.getDagPath()
        publishPaths.append( dagPath.fullPathName() )
        iterator.next()
    return publishPaths

def cleanNode( node, deleteIfEmpty = True, typesToKeep = ('mesh'), renameShapes = True, freezeTranform = True ):

    # The shape(s) of this node
    shapes = cmds.listRelatives(node,s=True,f=True)

    if shapes is None:
        # No shapes, no child: empty group to remove
        if not hasChildren(node) and deleteIfEmpty:
            cmds.delete(node)
        # Finished
        return False

    # Remove supplementary shapes
    # (Maya may store more than a single shape in transform nodes because of the dependency graph)
    if len(shapes) > 1:
        cmds.delete(shapes[1:])

    # The single remaining shape for this child
    shape = shapes[0]

    # Check type
    shapeType = cmds.nodeType( shape )
        
    if shapeType not in typesToKeep:
        cmds.delete(shape)
        if not hasChildren( node ) and deleteIfEmpty:
            cmds.delete( node )
            return False
    else:
        # Delete history
        cmds.delete(shape, constructionHistory=True)

        # Rename shapes after transform nodes
        if renameShapes:
            cmds.rename(shape, node.split('|')[-1] + 'Shape')

        # Freeze transform & center pivot
        if freezeTranform and shapeType == 'mesh':
            freezeTransform(node)

def snapNodeTo( nodeFrom, nodeTo):
    prevParent = cmds.listRelatives(nodeFrom, p = True, f = True)
    if prevParent is not None:
        prevParent = prevParent[0]
    nodeFrom = cmds.parent( nodeFrom, nodeTo, relative = True )[0] 
    # Maya, the absolute path please...
    nodeFrom = nodeTo + '|' + nodeFrom

    if prevParent is not None:
        nodeFrom = cmds.parent( nodeFrom, prevParent )[0]
        # Maya, the absolute path please...
        return prevParent + '|' + nodeFrom
    
    nodeFrom = cmds.parent( nodeFrom, world=True)[0]
    # Maya, the absolute path please...
    return '|' + nodeFrom

def lockTransform( transformNode ):
    if cmds.nodeType(transformNode) != 'transform':
        return
    for a in ['.tx','.ty','.tz','.rx','.ry','.rz','.sx','.sy','.sz']:
        cmds.setAttr(transformNode + a, lock=True )

def getNodeBaseName( node, keepNameSpace = False ):
    nodeName = node.split('|')[-1]
    if not keepNameSpace:
        nodeName = nodeName.split(':')[-1]
    return nodeName

def getNodeAbsolutePath( nodeName ):
    n = cmds.ls(nodeName, long=True)
    if n is not None:
        return n[0]
    return nodeName

def getCreateGroup( groupName, parentNode=None ):
    # Check if exists
    if parentNode is None:
        if groupName[0] != '|':
            groupName = '|' + groupName
        if cmds.objExists(groupName) and isGroup(groupName):
            return groupName
    else:
        # Get parentNode full path
        parentNode = cmds.ls(parentNode, long=True)[0]
        c = cmds.listRelatives(parentNode, children=True, type='transform')
        if c is not None:
            # May end with a number
            reStr = '^' + re.escape(groupName) + '\\d*$'
            regex = re.compile(reStr)
            for cn in c:
                if re.match( regex, cn ):
                    return parentNode + '|' + cn
    # Create the group
    n = cmds.group( name= groupName, em=True )
    if parentNode is not None:
        n = cmds.parent( n, parentNode )[0]
        n = parentNode + '|' + n
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

nonDeletableObjects = [
    '|frontShape',
    '|front',
    '|perspShape',
    '|persp',
    '|sideShape',
    '|side',
    '|topShape',
    '|top',
    'initialShadingGroup',
    'initialParticleSE',
    'lambert1',
    'standardSurface1',
    'particleCloud1',
]

def safeLoadPlugin(pluginName):
    ok = cmds.pluginInfo(pluginName, loaded=True, q=True)
    if not ok:
        cmds.loadPlugin(pluginName)
        return True
    return False
        
def removeAllNamespaces():
    # Set the current namespace to the root
    cmds.namespace(setNamespace=':')

    # Remove namespaces containing nodes
    nodes = cmds.ls()
    namespaces = []
    for node in nodes:
        if ':' in node:
            nodeNamespaces = node.split(":")[0:-1]
            for nodeNamespace in nodeNamespaces:
                if not nodeNamespace in namespaces:
                    namespaces.append(nodeNamespace)
    for namespace in namespaces:
        try:
            cmds.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)
        except:
            pass

    # Remove remaining namespaces without merging with root
    namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
    for namespace in namespaces:
        try:
            cmds.namespace(removeNamespace=namespace)
        except:
            pass

def removeAllAnimCurves():
    keys = cmds.ls(type='animCurveTL') + cmds.ls(type='animCurveTA') + cmds.ls(type='animCurveTU')
    for key in keys:
        try:
            cmds.delete(key)
        except:
            pass

def createTempScene(name=''):
    # Rename the file because we're going to modify stuff in there
    tempDir = tempfile.gettempdir()
    fileName = 'RamsesWorkingFile' + name + '.mb'
    tempFile = tempDir + '/' + fileName
    cmds.file(rename=tempFile)
    return tempFile

def cleanScene(removeAnimation=True, lockVisibility = False):
    prevFile = cmds.file( q=True, sn=True )
    tempFile = createTempScene(name='')

    # Import all references
    for ref in cmds.ls(type='reference'):
        refFile = cmds.referenceQuery(ref, f=True)
        cmds.file(refFile, importReference=True)

    # Clean names
    removeAllNamespaces()

    # Remove Anim
    if removeAnimation:
        removeAllAnimCurves()
    
    # Lock visibility if hidden
    if lockVisibility:
        lockHiddenVisibility()

    return (tempFile, prevFile)

def lockHiddenVisibility():
    for node in cmds.ls(long=True):
        if not cmds.attributeQuery( 'visibility', n=node, exists=True ):
            continue
        if not cmds.getAttr(node+'.visibility'):
            cmds.setAttr(node+'.visibility',lock=True)

def hasParent(node):
    return cmds.listRelatives(node, p=True, f=True) is not None

def hasChildren(node):
    return cmds.listRelatives(node, c=True, f=True, type='transform') is not None

def isGroup(node):
    # A group is a transform node
    if cmds.objectType(node) != 'transform':
        return False
    # And it does not have any child shape
    return cmds.listRelatives(node,s=True,f=True) is None

def moveToZero(node):
    cmds.setAttr(node + '.tx',0)
    cmds.setAttr(node + '.ty',0)
    cmds.setAttr(node + '.tz',0)

def removeEmptyGroups(node=None):
    remove = True
    while remove:
        nodes = ()
        remove = False
        if node is None:
            nodes = cmds.ls(type='transform')
        else:
            nodes = cmds.listRelatives(node, ad=True, f=True, type='transform')
        if nodes is None:
            return
        for node in nodes:
            if not isGroup(node):
                continue
            if not hasChildren(node):
                cmds.delete(node)
                remove = True

def freezeTransform(shape):
        cmds.move(0, 0, 0, shape + ".rotatePivot", absolute=True)
        cmds.move(0, 0, 0, shape + ".scalePivot", absolute=True)
        cmds.makeIdentity(shape, apply=True, t=1, r=1, s=1, n=0)
