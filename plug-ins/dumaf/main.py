# -*- coding: utf-8 -*-

import sys, tempfile, re, os
import maya.cmds as cmds # pylint: disable=import-error
import maya.api.OpenMaya as om # pylint: disable=import-error
from PySide2.QtWidgets import ( # pylint: disable=import-error disable=no-name-in-module
    QApplication
)

def createNameCommand( name, annotation, pyCommand):
    # Because the 'sourceType' parameter of cmds.nameCommand is broken, we first need to create a runtime command to run our python code...

    # There is no way to edit a runtime command so we need to check if it
    # exists and then remove it if it does.
    if cmds.runTimeCommand(name, q=True, exists=True):
        cmds.runTimeCommand(name, e=True, delete=True)
    # Now, re-create it
    cmds.runTimeCommand(
        name, 
        ann=annotation, 
        category='User', 
        command=pyCommand, 
        commandLanguage='python'
        )

    # Create the command
    nc = cmds.nameCommand( name, ann=annotation, command=name)

    return nc

def restoreOpenSceneHotkey():
    # We need to re-create a nameCommand, because Maya...
    command = cmds.nameCommand( annotation="OpenSceneNameCommand", command='OpenScene' )
    cmds.hotkey(keyShortcut='o', ctrlModifier = True, name=command)
    cmds.savePrefs(hotkeys=True)

def restoreSaveSceneAsHotkey():
    # We need to re-create a nameCommand, because Maya...
    command = cmds.nameCommand( annotation="SaveSceneAsNameCommand", command='SaveSceneAs' )
    cmds.hotkey(keyShortcut='s', ctrlModifier = True, shiftModifier=True, name=command)
    cmds.savePrefs(hotkeys=True)

def restoreSaveSceneHotkey():
    # We need to re-create a nameCommand, because Maya...
    command = cmds.nameCommand( annotation="SaveSceneNameCommand", command='SaveScene' )
    cmds.hotkey(keyShortcut='s', ctrlModifier = True, name=command)
    cmds.savePrefs(hotkeys=True)

def deleteNode( node ):
    """Deletes a node, even if it's in a reference or contains a reference.
    Warning: This will import the reference!"""
    children = cmds.listRelatives( node, ad=True, type='transform')
    if children:
        for child in children:
            if cmds.referenceQuery( child, isNodeReferenced=True):
                refFile = cmds.referenceQuery( child, filename=True)
                # import
                cmds.file( refFile, importReference = True)
    cmds.delete( node )

def createRootCtrl( node, ctrlName ):
    # Get the bounding box
    boundingBox = cmds.exactWorldBoundingBox( node )
    xmax = boundingBox[3]
    xmin = boundingBox[0]
    zmax = boundingBox[5]
    zmin = boundingBox[2]
    # Get the 2D Projection on the floor (XZ) lengths
    boundingWidth = xmax - xmin
    boundingLength = zmax - zmin
    # Compute a margin relative to mean of these lengths
    margin = ( boundingWidth + boundingLength ) / 2.0
    # Make it small
    margin = margin / 20.0
    # Create a shape using this margin and coordinates
    cv1 = ( xmin - margin, 0, zmin - margin)
    cv2 = ( xmax + margin, 0, zmin - margin)
    cv3 = ( xmax + margin, 0, zmax + margin)
    cv4 = ( xmin - margin, 0, zmax + margin)
    cv5 = cv1
    controller = cmds.curve( d=1, p=[cv1, cv2, cv3, cv4, cv5], k=(0,1,2,3,4), name=ctrlName)
    # Parent the node
    node = parentNodeTo(node, controller)
    return (node, controller)

def checkSaveState():
    """Checks if the current scene needs to be saved,
    and asks for the user to save if needed.
    Returns False if the user cancels the operation,
    True if the scene can be safely closed"""
    currentFilePath = cmds.file( q=True, sn=True )
    if cmds.file(q=True, modified=True):
        sceneName = os.path.basename(currentFilePath)
        if sceneName == '':
            sceneName = 'untitled scene'
        result = cmds.confirmDialog( message="Save changes to " + sceneName + "?", button=("Save", "Don't Save", "Cancel") )
        if result == 'Cancel':
            return False
        if result == 'Save':
            cmds.file( save=True, options="v=1;" )
    return True

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

def checkNode( node, deleteIfEmpty = True, typesToKeep=('mesh') ):
    if not cmds.objExists(node):
        return False
    
    # The shape(s) of this node
    shapes = cmds.listRelatives(node,s=True,f=True)

    if shapes is None:
        # No shapes, no child: empty group to remove
        if not hasChildren(node) and deleteIfEmpty:
            cmds.delete(node)
        # Finished
        return False

    shape = shapes[0]

    # Check type
    shapeType = cmds.nodeType( shape )
    if not shapeType in typesToKeep:
        cmds.delete(node)
        return False
        
    return True

def cleanNode( node, deleteIfEmpty = True, renameShapes = True, freezeTranform = True, keepHistory=False ):

    if not cmds.objExists(node):
        return False

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
        
    # Delete history
    if not keepHistory:
        cmds.delete(shape, constructionHistory=True)

    # Freeze transform & center pivot
    if freezeTranform and shapeType == 'mesh':
        freezeTransform(node)

    # Rename shapes after transform nodes
    if renameShapes:
        cmds.rename(shape, getNodeBaseName(node) + 'Shape')   

    return True  

def snapNodeTo( nodeFrom, nodeTo):
    prevParent = cmds.listRelatives(nodeFrom, p = True, f = True)
    if prevParent is not None:
        prevParent = prevParent[0]
    nodeFrom = parentNodeTo( nodeFrom, nodeTo, True )

    if prevParent is not None:
        nodeFrom = parentNodeTo( nodeFrom, prevParent )
        return nodeFrom
    
    nodeFrom = parentNodeTo( nodeFrom, '|' )
    return nodeFrom

def lockTransform( transformNode, l=True ):

    if cmds.nodeType(transformNode) != 'transform':
        return
    for a in ['.tx','.ty','.tz','.rx','.ry','.rz','.sx','.sy','.sz']:
        cmds.setAttr(transformNode + a, lock=l )

def lockVisibility( node, l=True ):
    if not cmds.attributeQuery( 'visibility', n=node, exists=True ): return
    cmds.setAttr(node+'.visibility',lock=l)

def isHidden( node ):
    if not cmds.attributeQuery( 'visibility', n=node, exists=True ):
        return False
    return cmds.getAttr(node + '.visibility') == 0

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
        if not groupName.startswith('|'):
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
    if not n.startswith('|'):
        n = '|' + n
    if parentNode is not None:
        n = parentNodeTo( n, parentNode)
    return n

def parentNodeTo( child, parent, r=False):
    """Fixed Parenting for Maya: returns a proper path instead of just the node name,
    and keeps the path absolute if arguments are absolute."""
    try:
        if parent != '|':
            child = cmds.parent( child, parent, relative=r )[0]
        else:
            child = cmds.parent(child, world=True)[0]
            return '|' + child
    except: # if the child is already parent to this parent
        return child
    # If maya returned a (relative?) path, we need to get the node name
    # (-> sometimes a path is returned, sometimes just the node name, depending on the fact
    # that the node name is unique in the scene or not)
    # Note that what Maya returns is never absolute (never starts with '|')
    child = getNodeBaseName( child, True)
    # Prepend again the parent path
    child = parent + '|' + child
    return child

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
        if isHidden(node): lockVisibility( node, True )

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

def freezeTransform(transformNode):
        lockTransform( transformNode, False )
        cmds.move(0, 0, 0, transformNode + ".rotatePivot", absolute=True)
        cmds.move(0, 0, 0, transformNode + ".scalePivot", absolute=True)
        cmds.makeIdentity(transformNode, apply=True, t=1, r=1, s=1, n=0)
