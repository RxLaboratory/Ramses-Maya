import tempfile

import maya.cmds as cmds # pylint: disable=import-error

import ramses as ram # pylint: disable=import-error

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

def cleanScene(removeAnimation=True):
    # Rename the file because we're going to modify stuff in there
    tempDir = tempfile.gettempdir()
    tempFile = ram.RamFileManager.buildPath((
        tempDir,
        'RamsesWorkingFile.mb'
    ))
    cmds.file(rename=tempFile)

    # Import all references
    for ref in cmds.ls(type='reference'):
        refFile = cmds.referenceQuery(ref, f=True)
        cmds.file(refFile, importReference=True)

    # Clean names
    removeAllNamespaces()

    # No animation in the mod step!
    if removeAnimation:
        removeAllAnimCurves()

def hasParent(node):
    return cmds.listRelatives(node, p=True, f=True) is not None

def hasChildren(node):
    return cmds.listRelatives(node, c=True, f=True) is not None

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

def publishMod(item, filePath, step): # TODO Finish implementation, build UI, Add progress window in Ramses-Maya passed as an arg to the scripts

    # OPTIONS (build UI)
    removeHidden = True
    removeLocators = True
    renameShapes = True

    # Checks
    if step.shortName() != 'MOD':
        return

    cleanScene()

    # We need to use alembic
    safeLoadPlugin("AbcExport")

    # For all nodes in the publish set
    nodes = ()
    try:
        nodes = cmds.sets( 'Ramses_Publish', nodesOnly=True, q=True )
    except ValueError:
        ram.log("Nothing to publish! The asset you need to publish must be listed in a 'Ramses_Publish' set.")
        cmds.inViewMessage( msg='Nothing to publish! The asset you need to publish must be listed in a <hl>Ramses_Pulbish</hl> set.', pos='midCenter', fade=True )
        return
    
    if nodes is None or len(nodes) == 0:
        ram.log("The 'Ramses_Publish' set is empty, there's nothing to publish!")
        cmds.inViewMessage( msg="The <hl>Ramses_Publish</hl> set is empty, there's nothing to publish!", pos='midCenter', fade=True )
        return

    # Let's count how many objects are published
    publishedNodes = []

    for node in nodes:
        # MOD to publish must be in a group
        # The node must be a root
        if hasParent(node):
            continue
        # It must be a group
        if not isGroup(node):
            continue 
        # It must have children to publish
        if not hasChildren(node):
            continue

        # Absolute path to be sure
        node = '|' + node

        moveToZero(node)

        # Get all children
        contentNodes = cmds.listRelatives( node, ad=True, f=True)
        if contentNodes is None:
            cmds.delete(node)
            continue

        # Clean (remove what we don't want to publish)
        for contentNode in contentNodes:
            # Delete history
            cmds.delete(contentNode, constructionHistory=True)

            # Remove hidden
            if removeHidden and cmds.getAttr(contentNode + '.v') == 0:
                cmds.delete(contentNode)
                continue

            # The type
            contentType = cmds.nodeType( contentNode )
            typesToKeep = ['mesh', 'transform']
            if not removeLocators:
                typesToKeep.append('locator')
                
            if contentType not in typesToKeep:
                cmds.delete(contentNode)
                continue

        # Second cleaning step: remove empty transform nodes and clean remaining data
        transformNodes = cmds.listRelatives(node, ad=True, f=True, type='transform')
        if transformNodes is None:
            cmds.delete(node)
            continue

        for transformNode in transformNodes:
            shapes = cmds.listRelatives(transformNode,s=True,f=True)
            children = cmds.listRelatives(transformNode,ad=True,f=True, type='transform')

            # Remove empty transform nodes
            if shapes is None and children is None:
                cmds.delete(transformNode)
                continue

            # Remove supplementary shapes
            # (Maya may store more than a single shape in transform nodes because of the dependency graph)
            if len(shapes) > 1:
                cmds.delete(shapes[1:])

            # Rename shapes after transform nodes
            if renameShapes:
                cmds.rename(shapes[0], transformNode.split('|')[-1] + 'Shape')

            # Freeze transform & center pivot
            # cf pipou line 1032
            # -> Ignore list with object name

            # Create a root controller
            # cf pipou line 1071

            # Export viewport shaders
            # cf pipou line 1066 & funcShaders.exportShaders()
            # Update Ramses Metadata (version)

            # Save and create Abc
            # cf pipou line 1100
            # Update Ramses Metadata (version)

        publishedNodes.append(node)

    # Clean scene: remove all nodes not children of publishedNodes

    # Copy published scene to publish
    # Update Ramses Metadata (version)

    # Re-Open initial scene
    # cf pipou line 1114

    # Remove temp file
    # cf pipou line 1132       

    print('ok')


        
publishMod(None, '', ram.RamStep('MOD','MOD'))