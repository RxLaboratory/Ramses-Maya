import sys
import maya.cmds as cmd # pylint: disable=import-error
from PySide2.QtWidgets import ( # pylint: disable=import-error
    QApplication
)

def getCreateGroup( groupName ):
    n = '|' + groupName
    if cmds.objExists(n):
        return n
    cmds.group( name= groupName, em=True )
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
]

def safeLoadPlugin(pluginName):
    ok = cmds.pluginInfo(pluginName, loaded=True, q=True)
    if not ok:
        cmds.loadPlugin(pluginName)
        ram.log("I have loaded the plug-in " + pluginName + ", needed for the current task.")
        
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
    tempFile = ram.RamFileManager.buildPath((
        tempDir,
        fileName
    ))
    cmds.file(rename=tempFile)
    return tempFile

def cleanScene(removeAnimation=True):
    tempFile = createTempScene(name='')

    # Import all references
    for ref in cmds.ls(type='reference'):
        refFile = cmds.referenceQuery(ref, f=True)
        cmds.file(refFile, importReference=True)

    # Clean names
    removeAllNamespaces()

    # No animation in the mod step!
    if removeAnimation:
        removeAllAnimCurves()
    
    return tempFile

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
