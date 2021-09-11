# -*- coding: utf-8 -*-

import os
import maya.cmds as cmds # pylint: disable=import-error
import dumaf as maf
import ramses as ram # pylint: disable=import-error
from .utils_attributes import * # pylint: disable=import-error
from .utils_constants import *
from .utils_general import *
from .utils_publish import *

# mode is either VPSHADERS_PIPE_NAME or RDRSHADERS_PIPE_NAME
def exportShaders(node, publishFileInfo, mode = ''): 
    # List all nodes containing shaders
    nodes = cmds.listRelatives(node, ad=True, f=True, type='mesh')
    # If there are Yeti nodes
    try:
        nodes = nodes + cmds.listRelatives(node, ad=True, f=True, type='pgYetiMaya')
    except:
        pass

    # Prepare the data info we're exporting
    allShadingEngines = []

    # Get shading info
    for meshNode in nodes:
        nodeHistory = cmds.listHistory( meshNode, f=True )
        shadingEngines = cmds.listConnections( nodeHistory, type='shadingEngine')
        shadingEngine = 'initialShadingGroup'

        # Get the name from parent (transform node for this mesh)
        objectName = cmds.listRelatives(meshNode, p=True)[0]
        # Remove namespace if any
        objectName = objectName.split(':')[-1]

        if shadingEngines is not None:
            for shadingEngine in shadingEngines:

                # Get the first surface shader to rename the engine
                surfaceShaders = cmds.listConnections(shadingEngine + '.surfaceShader')
                if surfaceShaders is not None:
                    surfaceShader = surfaceShaders[0]
                    surfaceShaderName = surfaceShader.split(':')[-1]
                    # Remove all what's before the first '_'
                    i = surfaceShaderName.find('_')
                    if i >= 0:
                        surfaceShaderName = surfaceShaderName[i+1:]
                    # And rename
                    if shadingEngine != 'initialShadingGroup':
                        shadingEngine = cmds.rename( shadingEngine, surfaceShaderName)
            
                    # List the objects this engine is shading
                    setRamsesManaged( shadingEngine )
                    objectNames = getRamsesAttr( shadingEngine, RamsesAttribute.SHADED_OBJECTS )
                    if objectNames is None:
                        objectNames = ''
                    else:
                        objectNames = objectNames + ','
                    objectNames = objectNames + objectName
                    setRamsesAttr( shadingEngine, RamsesAttribute.SHADED_OBJECTS, objectNames, 'string')
        
        allShadingEngines.append(shadingEngine)

    # Select and export shadingEngines
    nodeName = maf.Path.baseName( node )
    savePath = publishNodesAsMayaScene( publishFileInfo, allShadingEngines, nodeName + '-' + mode, 'mb')
       
    return savePath

# mode is either VPSHADERS_PIPE_NAME or RDRSHADERS_PIPE_NAME
def referenceShaders(nodes, mode, filePath, itemShortName=''):
    
    # If already referenced, get the existing reference and clean it
    shaderNodes = []
    isAlreadyReferenced = False
    try:
        shaderNodes = cmds.referenceQuery( filePath, nodes=True )
        isAlreadyReferenced = True
    except:
        pass

    if not isAlreadyReferenced:
        # Reference the shader file
        shaderNodes = cmds.file(filePath,r=True,mergeNamespacesOnClash=True,namespace=itemShortName, returnNewNodes = True)

    if shaderNodes is None or len(shaderNodes) == 0:
        ram.log( "I did not find any shader to import, sorry." )
        return []

    for node in nodes:
        # For all mesh
        meshes = cmds.listRelatives( node, ad=True, type='mesh', f=True)
        if meshes is None:
            ram.log("I can't find any geometry to apply the shaders, sorry.")
            return

        found = False

        for mesh in meshes:
            # Get the transform node (which has the name we're looking for)
            transformNode = cmds.listRelatives(mesh, p=True, type='transform')[0]
            nodeName = maf.Path.baseName( transformNode )
            # Apply
            cmds.select(mesh, r=True)
            for shaderNode in shaderNodes:
                shadedObjects = getRamsesAttr( shaderNode, RamsesAttribute.SHADED_OBJECTS )
                if shadedObjects is None:
                    continue
                shadedObjects = shadedObjects.split(',')

                if nodeName in shadedObjects:
                    found = True
                    cmds.sets(e=True, forceElement = shaderNode)

        cmds.select(clear=True)

        if found:
            # Shading Data
            setRamsesManaged( node )
            setRamsesAttr( node, RamsesAttribute.SHADING_TYPE, mode, 'string')

    return shaderNodes
