# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .ui_publish_geo import PublishGeoDialog
from .utils_shaders import exportShaders
from .utils_nodes import getPublishNodes
from .utils_attributes import * # pylint: disable=import-error
from .utils_constants import * # pylint: disable=import-error
from .utils_general import * # pylint: disable=import-error
from .utils_items import * # pylint: disable=import-error

def publishSet(item, step, publishFileInfo):

    # Options
    # Show dialog
    publishGeoDialog = PublishGeoDialog( maf.ui.getMayaWindow() )
    if not publishGeoDialog.exec_():
        return

    removeHidden = publishGeoDialog.removeHidden()
    removeLocators = publishGeoDialog.removeLocators()
    renameShapes = publishGeoDialog.renameShapes()
    noFreeze = publishGeoDialog.noFreeze()
    noFreezeCaseSensitive = publishGeoDialog.noFreezeCaseSensitive()
    keepCurves = publishGeoDialog.curves()
    keepSurfaces = publishGeoDialog.surfaces()
    keepAnimation = publishGeoDialog.animation()
    keepAnimatedDeformers = publishGeoDialog.animatedDeformers()
    # Prepare options
    # Freeze transform & center pivot
    if not noFreezeCaseSensitive:
        noFreeze = noFreeze.lower()
    # noFreeze contains a comma-separated list
    noFreeze = noFreeze.replace(' ','')
    noFreeze = noFreeze.split(',')

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Publishing set")

    tempData = maf.scene.createTempScene()
    maf.references.importAll()
    maf.namespaces.removeAll()
    if not keepAnimation: maf.animation.removeAll()
    
    nodes = getPublishNodes()

    if len(nodes) == 0:
        endProcess(tempData, progressDialog)
        return

    numNodes = len(nodes)
    progressDialog.setMaximum(numNodes + 2)
    progressDialog.setText("Preparing")
    progressDialog.increment()

    # Publish folder
    ram.log( "I'm publishing the sets in " + os.path.dirname( publishFileInfo.filePath() ) )

    # File extension
    extension = getExtension( step, SET_STEP, SET_PIPE_FILE, ['ma','mb'], 'mb' )

    # Publish each set (reversed because we may remove some of them)
    for node in reversed(nodes):
        progressDialog.setText("Publishing: " + node)
        progressDialog.increment()

        # Get children
        children = cmds.listRelatives(node, ad=True, f=True, type='transform')

        # If there's no child and just an empty group, nothing to publish
        if children is None and maf.nodes.isGroup( node ):
            cmds.delete(node)
            continue

        # Move the node we're publishing to zero
        maf.nodes.moveToZero( node )

        # Clean all children (reversed because we may remove some of them)
        for child in reversed(children):
            
            # Remove hidden
            if removeHidden and maf.nodes.isHidden( child ):
                cmds.delete( child )
                continue