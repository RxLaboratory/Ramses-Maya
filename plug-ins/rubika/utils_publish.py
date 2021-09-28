# -*- coding: utf-8 -*-

from os import pipe
import ramses as ram
import dumaf as maf
import maya.cmds as cmds # pylint: disable=import-error

def setExportMetaData( filePath, pipeType, publishFileInfo ):
    pipeType = pipeType.split('-')[-1]
    ram.RamMetaDataManager.setPipeType( filePath, pipeType )
    ram.RamMetaDataManager.setVersion( filePath, publishFileInfo.version )
    ram.RamMetaDataManager.setState( filePath, publishFileInfo.state )
    ram.RamMetaDataManager.setResource( filePath, publishFileInfo.resource )

def getPublishFilePath( publishFileInfo, extension, pipeName='Published' ):
    sceneInfo = publishFileInfo.copy()
    sceneInfo.version = -1
    sceneInfo.state = ''
    sceneInfo.extension = extension
    if sceneInfo.resource != '': sceneInfo.resource = sceneInfo.resource + '-'
    sceneInfo.resource = sceneInfo.resource + pipeName

    return sceneInfo.filePath()

def publishNodesAsMayaScene( publishFileInfo, nodes, pipeName='Published', extension='mb' ):

    filePath = getPublishFilePath( publishFileInfo, extension, pipeName )

    # Clean scene:
    # Remove empty groups from the scene
    maf.Node.removeEmptyGroups()

    # Select the nodes to publish
    # in a loop just to try to select them all
    replace = True
    for n in nodes:
        try:
            cmds.select(n, noExpand=True, r=replace)
            replace = False
        except:
            pass
    # Save file
    cmds.file( rename=filePath )
    cmds.file( exportSelected=True, options="v=1;" )
    cmds.select(cl=True)

    # Set metadata
    setExportMetaData( filePath, pipeName, publishFileInfo )

    return filePath

def publishNodeAsABC( publishFileInfo, node, pipeName, timeRange=(1,1), frameStep=1, filterEuler=False ):

    if maf.Plugin.load("AbcExport"):
        ram.log("I have loaded the Alembic Export plugin, needed for the current task.")

    nodeName = maf.Path.baseName( node )
    nodeName = nodeName.replace('_root_', '').replace(pipeName, '')
    filePath = getPublishFilePath( publishFileInfo, 'abc', nodeName + '-' + pipeName )

    eulerFilter = ''
    if filterEuler: eulerFilter = '-eulerFilter'

    # Build the ABC command
    abcOptions = ' '.join([
        '-frameRange ' + str(timeRange[0]) + ' ' + str(timeRange[1]),
        eulerFilter,
        '-step ' + str(frameStep),
        '-autoSubd', # crease
        '-uvWrite',
        '-writeUVSets',
        '-worldSpace',
        '-writeVisibility',
        '-dataFormat hdf',
        '-renderableOnly',
        '-root ' + node,
        '-file "' + filePath + '"',
    ])

    ram.log("These are the alembic options:\n" + abcOptions, ram.LogLevel.Debug)

    # Export
    cmds.AbcExport(j=abcOptions)

    # Update Ramses Metadata (version)
    setExportMetaData( filePath, pipeName, publishFileInfo )

    return filePath
