import os
import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .ui_publish_mod import PublishModDialog
from .utils_shaders import exportShaders

def publishMod(item, filePath, step):

    # Checks
    if step != 'MOD':
        return

    # Show dialog
    publishModDialog = PublishModDialog( maf.getMayaWindow() )
    if not publishModDialog.exec_():
        return

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Publishing geometry")

    # Options
    removeHidden = publishModDialog.removeHidden()
    removeLocators = publishModDialog.removeLocators()
    renameShapes = publishModDialog.renameShapes()
    onlyRootGroups = publishModDialog.onlyRootGroups()
    noFreeze = publishModDialog.noFreeze()
    noFreezeCaseSensitive = publishModDialog.noFreezeCaseSensitive()

    tempFile = maf.cleanScene()

    # We need to use alembic
    if maf.safeLoadPlugin("AbcExport"):
        ram.log("I have loaded the Alembic Export plugin, needed for the current task.")

    # For all nodes in the publish set
    nodes = ()
    try:
        nodes = cmds.sets( 'Ramses_Publish', nodesOnly=True, q=True )
    except ValueError:
        ram.log("Nothing to publish! The asset you need to publish must be listed in a 'Ramses_Publish' set.")
        cmds.inViewMessage( msg='Nothing to publish! The asset you need to publish must be listed in a <hl>Ramses_Pulbish</hl> set.', pos='midCenter', fade=True )
        return

    numNodes = len(nodes)
    progressDialog.setMaximum(numNodes + 2)
    progressDialog.setText("Preparing")
    progressDialog.increment()
    
    if nodes is None or numNodes == 0:
        ram.log("The 'Ramses_Publish' set is empty, there's nothing to publish!")
        cmds.inViewMessage( msg="The <hl>Ramses_Publish</hl> set is empty, there's nothing to publish!", pos='midCenter', fade=True )
        return

    # Prepare options
    # Freeze transform & center pivot
    if not noFreezeCaseSensitive:
        noFreeze = noFreeze.lower()
    # noFreeze contains a comma-separated list
    noFreeze = noFreeze.replace(' ','')
    noFreeze = noFreeze.split(',')

    # Item info
    fileInfo = ram.RamFileManager.decomposeRamsesFilePath( filePath )
    if fileInfo is None:
        ram.log(ram.Log.MalformedName, ram.LogLevel.Fatal)
        cmds.inViewMessage( msg=ram.Log.MalformedName, pos='midCenter', fade=True )
        cmds.error( ram.Log.MalformedName )
        return
    version = item.latestVersion( fileInfo['resource'], '', step )
    versionFilePath = item.latestVersionFilePath( fileInfo['resource'], '', step )

    publishFolder = item.publishFolderPath( step )
    if publishFolder == '':
        ram.log("I can't find the publish folder for this item, maybe it does not respect the ramses naming scheme or it is out of place.", ram.LogLevel.Fatal)
        cmds.inViewMessage( msg="Can't find the publish folder for this scene, sorry. Check its name and location.", pos='midCenter', fade=True )
        cmds.error( "Can't find publish folder." )
        return
    ram.log( "I'm publishing in " + publishFolder )

    # Let's count how many objects are published
    publishedNodes = []

    for node in nodes:
        progressDialog.setText("Publishing: " + node)
        progressDialog.increment()

        if onlyRootGroups:
            # MOD to publish must be in a group
            # The node must be a root
            if maf.hasParent(node):
                continue
            # It must be a group
            if not maf.isGroup(node):
                continue 
            # It must have children to publish
            if not maf.hasChildren(node):
                continue

        # Absolute path to be sure
        # node = '|' + node

        # Get all children
        childNodes = cmds.listRelatives( node, ad=True, f=True, type='transform')
        if childNodes is None:
            childNodes = []
        childNodes.append(node)

        # Empty group, nothing to do
        if childNodes is None and maf.isGroup(node):
            cmds.delete(node)
            continue

        maf.moveToZero(node)

        # Clean (remove what we don't want to publish)
        for childNode in childNodes:

            # Remove hidden
            if removeHidden and cmds.getAttr(childNode + '.v') == 0:
                cmds.delete(childNode)
                continue

            # The shape(s) of this child
            shapes = cmds.listRelatives(childNode,s=True,f=True)

            if shapes is None:
                # No shapes, no child: empty group to remove
                if not maf.hasChildren(childNode):
                    cmds.delete(childNode)
                # Nothing else to check for groups
                continue

            # Remove supplementary shapes
            # (Maya may store more than a single shape in transform nodes because of the dependency graph)
            if len(shapes) > 1:
                cmds.delete(shapes[1:])

            # The single remaining shape for this child
            shape = shapes[0]

            # Check type
            shapeType = cmds.nodeType( shape )
            typesToKeep = ['mesh']
            if not removeLocators:
                typesToKeep.append('locator')
                
            if shapeType not in typesToKeep:
                cmds.delete(shape)
                if not maf.hasChildren( childNode ):
                    cmds.delete(childNode)
                continue

            # Delete history
            cmds.delete(shape, constructionHistory=True)

            # Rename shapes after transform nodes
            if renameShapes:
                cmds.rename(shape, childNode.split('|')[-1] + 'Shape')

            # Freeze transform & center pivot
            freeze = True
            childName = childNode.lower()
            for no in noFreeze:
                if no in childName:
                    freeze = False
                    break
            if freeze and shapeType == 'mesh':
                maf.freezeTransform(childNode)            

        # Last steps
        nodeName = node.split('|')[-1]

        # Remove remaining empty groups
        maf.removeEmptyGroups(node)

        # Create a root controller
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
        controller = cmds.curve( d=1, p=[cv1, cv2, cv3, cv4, cv5], k=(0,1,2,3,4), name=nodeName + '_root')
        # Parent the node
        cmds.parent(node, controller)

        # Save and create Abc
        # Generate file path
        abcFileInfo = fileInfo.copy()
        # extension
        abcFileInfo['extension'] = 'abc'
        # resource
        if abcFileInfo['resource'] != '':
            abcFileInfo['resource'] = abcFileInfo['resource'] + '-' + nodeName
        else:
            abcFileInfo['resource'] = nodeName
        # path
        abcFilePath = ram.RamFileManager.buildPath((
            publishFolder,
            ram.RamFileManager.composeRamsesFileName( abcFileInfo )
        ))
        # Save
        abcOptions = ' '.join([
            '-frameRange 1 1',
            '-autoSubd', # Crease info
            '-uvWrite',
            '-worldSpace',
            '-writeUVSets',
            '-dataFormat hdf',
            '-root |' + controller,
            '-file ' + abcFilePath
        ])
        cmds.AbcExport(j=abcOptions)
        # Update Ramses Metadata (version)
        ram.RamMetaDataManager.setVersionFilePath( abcFilePath, versionFilePath )
        ram.RamMetaDataManager.setVersion( abcFilePath, version )

        # Export viewport shaders
        shaderFilePath = exportShaders(node, 'vp', publishFolder, fileInfo.copy(), abcFilePath)
        # Update Ramses Metadata (version)
        ram.RamMetaDataManager.setVersionFilePath( shaderFilePath, versionFilePath )
        ram.RamMetaDataManager.setVersion( shaderFilePath, version )

        publishedNodes.append(node)

    progressDialog.setText( "Cleaning" )
    progressDialog.increment()

    # remove all nodes not children or parent of publishedNodes
    allTransformNodes = cmds.ls(transforms=True, long=True)
    allPublishedNodes = []
    for publishedNode in publishedNodes:
        # Children
        published = cmds.listRelatives(publishedNode, ad=True, f=True, type='transform')
        if published is not None:
            allPublishedNodes = allPublishedNodes + published
        # Parents
        published = cmds.listRelatives(publishedNode, ap=True, f=True, type='transform')
        if published is not None:
            allPublishedNodes = allPublishedNodes + published
        # And Self
        published = cmds.ls(publishedNode, transforms=True, long=True)
        if published is not None:
            allPublishedNodes = allPublishedNodes + published
    for transformNode in allTransformNodes:
        if transformNode in allPublishedNodes:
            continue
        if transformNode in maf.nonDeletableObjects:
            continue
        cmds.delete(transformNode)

    # Clean scene:
    # Remove empty groups from the scene
    maf.removeEmptyGroups()

    # Copy published scene to publish
    sceneFileInfo = fileInfo.copy()
    sceneFileInfo['extension'] = 'mb'
    # resource
    if sceneFileInfo['resource'] != '':
        sceneFileInfo['resource'] = sceneFileInfo['resource'] + '-CleanPub'
    else:
        sceneFileInfo['resource'] = 'CleanPub'
    # path
    sceneFilePath = ram.RamFileManager.buildPath((
        publishFolder,
        ram.RamFileManager.composeRamsesFileName( sceneFileInfo )
    ))
    # Save
    cmds.file( rename=sceneFilePath )
    cmds.file( save=True, options="v=1;" )
    # Update Ramses Metadata (version)
    ram.RamMetaDataManager.setVersionFilePath( sceneFilePath, versionFilePath )
    ram.RamMetaDataManager.setVersion( sceneFilePath, version )

    # Re-Open initial scene
    cmds.file(filePath,o=True,f=True)

    # Remove temp file
    if os.path.isfile(tempFile):
        os.remove(tempFile)

    ram.log("I've published these assets:")
    for publishedNode in publishedNodes:
        ram.log(" > " + publishedNode)
    cmds.inViewMessage(  msg="Assets published: <hl>" + '</hl>,<hl>'.join(publishedNodes) + "</hl>.", pos='midCenter', fade=True )

    progressDialog.hide()

if __name__ == "__main__":
    currentScene = cmds.file( q=True, sn=True )
    item = ram.RamItem.fromPath(currentScene)
    publishMod(item, currentScene, ram.RamStep('MOD', 'MOD') )