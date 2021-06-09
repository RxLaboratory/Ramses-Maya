import os

import maya.cmds as cmds # pylint: disable=import-error
from .import_geo import *
from .import_shaders import *
from .utils_items import *
import ramses as ram

ramses = ram.Ramses.instance()

def importer(item, filePaths, step):
    geoFiles = []
    vpShaderFiles = []
    rdrShaderFiles = []
    proxyShadeFiles = []
    proxyGeoFiles = []

    if filePaths[0] == '': # Scan all published files to get the ones corresponding to the pipes

        
        currentFilePath = cmds.file( q=True, sn=True )
        # Get the output pipes from the step being imported
        pipes = getPipes( step, currentFilePath )
        if len(pipes) == 0:
            return

        geo = False
        vpShaders = False
        rdrShaders = False
        proxyShade = False
        proxyGeo = False

        for pipe in pipes:
            for pipeFile in pipe.pipeFiles():
                if pipeFile == GEO_PIPE_FILE:
                    geo = True
                elif pipeFile == VPSHADERS_PIPE_FILE:
                    vpShaders = True
                elif pipeFile == RDRSHADERS_PIPE_FILE:
                    rdrShaders = True
                elif pipeFile == PROXYSHADE_PIPE_FILE:
                    proxyShade = True
                elif pipeFile == PROXYGEO_PIPE_FILE:
                    proxyGeo = True

        # List all files, and get correspondance
        publishFolder = item.publishFolderPath( step )

        if geo:
            geoFiles = GEO_PIPE_FILE.getFiles( publishFolder )
        if vpShaders:
            vpShaderFiles = VPSHADERS_PIPE_FILE.getFiles( publishFolder )
        if rdrShaders:
            rdrShaderFiles = RDRSHADERS_PIPE_FILE.getFiles( publishFolder )
        if proxyShade:
            proxyShadeFiles = PROXYSHADE_PIPE_FILE.getFiles( publishFolder )
        if proxyGeo:
            proxyGeoFiles = PROXYGEO_PIPE_FILE.getFiles( publishFolder )
 
    else: # Sort the selected files
        for file in filePaths:
            if GEO_PIPE_FILE.check(file):
                geoFiles.append( file )
            if VPSHADERS_PIPE_FILE.check(file):
                vpShaderFiles.append( file )
            if RDRSHADERS_PIPE_FILE.check(file):
                rdrShaderFiles.append( file )
            if PROXYSHADE_PIPE_FILE.check(file):
                proxyShadeFiles.append( file )
            if PROXYGEO_PIPE_FILE.check(file):
                proxyGeoFiles.append( file )

    # Import

    # Keep the Geo nodes and the selection to import the shaders on them automatically
    geoNodes = cmds.ls(selection=True, type='transform', long=True)

    if len(geoFiles) > 0:
        ram.log( "I'm importing the geometry." )
        for geoFile in geoFiles:
            geoNodes = geoNodes + importGeo( item, geoFile, step )

    if len(vpShaderFiles) > 0:
        ram.log( "I'm importing the viewport shaders." )
        for vpShaderFile in vpShaderFiles:
            importShaders( item, vpShaderFile, VPSHADERS_PIPE_NAME, geoNodes )

    if len(rdrShaderFiles) > 0:
        ram.log( "I'm importing the render shaders." )
        for rdrShaderFile in rdrShaderFiles:
            importShaders( item, rdrShaderFile, RDRSHADERS_PIPE_NAME, geoNodes )
