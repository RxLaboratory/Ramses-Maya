# -*- coding: utf-8 -*-

import os

import maya.cmds as cmds # pylint: disable=import-error
from .import_geo import *
from .import_shaders import *
from .import_rig import *
from .import_standard import *
from .import_anim import *
from .utils_items import *
import ramses as ram

ramses = ram.Ramses.instance()

def importer(item, filePaths, step):
    geoFiles = []
    geoRefFiles = []
    vpShaderFiles = []
    rdrShaderFiles = []
    proxyShadeFiles = []
    proxyGeoFiles = []
    proxyGeoRefFiles = []
    rigFiles = []
    setFiles = []
    setRefFiles = []
    standardFiles = []
    standardRefFiles = []
    animFiles = []
    animRefFiles = []

    if filePaths[0] == '': # Scan all published files to get the ones corresponding to the pipes

        currentFilePath = cmds.file( q=True, sn=True )
        # Get the output pipes from the step being imported
        pipes = getPipes( step, currentFilePath, 'Import' )
        if len(pipes) == 0:
            return

        geo = False
        geoRef = False
        vpShaders = False
        rdrShaders = False
        proxyShade = False
        proxyGeo = False
        proxyGeoRef = False
        rig = False
        sets = False
        setsRef = False
        standard = False
        standardRef = False
        anim = False
        animRef = False

        for pipe in pipes:
            for pipeFile in pipe.pipeFiles():
                if pipeFile == GEO_PIPE_FILE:
                    geo = True
                elif pipeFile == GEOREF_PIPE_FILE:
                    geoRef = True
                elif pipeFile == VPSHADERS_PIPE_FILE:
                    vpShaders = True
                elif pipeFile == RDRSHADERS_PIPE_FILE:
                    rdrShaders = True
                elif pipeFile == PROXYSHADE_PIPE_FILE:
                    proxyShade = True
                elif pipeFile == PROXYGEO_PIPE_FILE:
                    proxyGeo = True
                elif pipeFile == PROXYGEOREF_PIPE_FILE:
                    proxyGeoRef = True
                elif pipeFile == RIG_PIPE_FILE:
                    rig = True
                elif pipeFile == SET_PIPE_FILE:
                    sets = True
                elif pipeFile == SETREF_PIPE_FILE:
                    setsRef = True
                elif pipeFile == STANDARD_PIPE_FILE:
                    standard = True
                elif pipeFile == STANDARDREF_PIPE_FILE:
                    standardRef = True
                elif pipeFile == ANIM_PIPE_FILE:
                    anim = True
                elif pipeFile == ANIMREF_PIPE_FILE:
                    animRef = True

        # List all files, and get correspondance
        publishFolder = item.publishFolderPath( step )

        if geo:
            geoFiles = GEO_PIPE_FILE.getFiles( publishFolder )
        if geoRef:
            geoRefFiles = GEOREF_PIPE_FILE.getFiles( publishFolder )
        if vpShaders:
            vpShaderFiles = VPSHADERS_PIPE_FILE.getFiles( publishFolder )
        if rdrShaders:
            rdrShaderFiles = RDRSHADERS_PIPE_FILE.getFiles( publishFolder )
        if proxyShade:
            proxyShadeFiles = PROXYSHADE_PIPE_FILE.getFiles( publishFolder )
        if proxyGeo:
            proxyGeoFiles = PROXYGEO_PIPE_FILE.getFiles( publishFolder )
        if proxyGeoRef:
            proxyGeoRefFiles = PROXYGEOREF_PIPE_FILE.getFiles( publishFolder )
        if rig:
            rigFiles = RIG_PIPE_FILE.getFiles( publishFolder )
        if sets:
            setFiles = SET_PIPE_FILE.getFiles( publishFolder )
        if setsRef:
            setRefFiles = SETREF_PIPE_FILE.getFiles( publishFolder )
        if standard:
            standardFiles = STANDARD_PIPE_FILE.getFiles( publishFolder )
        if standardRef:
            standardRefFiles = STANDARDREF_PIPE_FILE.getFiles( publishFolder )
        if anim:
            animFiles = ANIM_PIPE_FILE.getFiles( publishFolder )
        if animRef:
            animRefFiles = ANIMREF_PIPE_FILE.getFiles( publishFolder )
 
    else: # Sort the selected files
        for file in filePaths:
            if GEO_PIPE_FILE.check(file):
                geoFiles.append( file )
            elif GEOREF_PIPE_FILE.check(file):
                geoRefFiles.append( file )
            elif VPSHADERS_PIPE_FILE.check(file):
                vpShaderFiles.append( file )
            elif RDRSHADERS_PIPE_FILE.check(file):
                rdrShaderFiles.append( file )
            elif PROXYSHADE_PIPE_FILE.check(file):
                proxyShadeFiles.append( file )
            elif PROXYGEO_PIPE_FILE.check(file):
                proxyGeoFiles.append( file )
            elif PROXYGEOREF_PIPE_FILE.check(file):
                proxyGeoRefFiles.append( file )
            elif RIG_PIPE_FILE.check( file ):
                rigFiles.append( file )
            elif SET_PIPE_FILE.check( file ):
                setFiles.append( file )
            elif SETREF_PIPE_FILE.check( file ):
                setRefFiles.append( file )
            elif ANIM_PIPE_FILE.check( file ):
                animFiles.append( file )
            elif ANIMREF_PIPE_FILE.check( file ):
                animRefFiles.append( file )
            elif STANDARD_PIPE_FILE.check( file ):
                standardFiles.append( file )
            elif STANDARDREF_PIPE_FILE.check( file ):
                standardRefFiles.append( file )
            elif MA_FILE.check(file) or MB_FILE.check(file) or ABC_FILE.check(file):
                standardFiles.append(file)

    # Import

    # Keep the Geo nodes and the selection to import the shaders on them automatically
    geoNodes = cmds.ls(selection=True, type='transform', long=True)

    if len(geoFiles) > 0:
        ram.log( "I'm importing the geometry." )
        for geoFile in geoFiles:
            geoNodes = geoNodes + importGeo( item, geoFile, step )

    if len(geoRefFiles) > 0:
        ram.log( "I'm referencing the geometry." )
        for geoRefFile in geoRefFiles:
            geoNodes = geoNodes + importGeo( item, geoRefFile, step, ref=True )

    if len(proxyGeoFiles):
        ram.log( "I'm importing the proxy geometry." )
        for geoFile in proxyGeoFiles:
            geoNodes = geoNodes + importGeo( item, geoFile, step )

    if len(proxyGeoRefFiles):
        ram.log( "I'm referencing the proxy geometry." )
        for geoFile in proxyGeoRefFiles:
            geoNodes = geoNodes + importGeo( item, geoFile, step, ref=True )
    
    if len(setFiles) > 0:
        ram.log( "I'm importing the set." )
        for setFile in setFiles:
            geoNodes = geoNodes + importGeo( item, setFile, step )

    if len(setRefFiles) > 0:
        ram.log( "I'm referencing the set." )
        for setFile in setRefFiles:
            geoNodes = geoNodes + importGeo( item, setFile, step, ref=True )

    if len(rigFiles) > 0:
        ram.log( "I'm referencing the rig." )
        for rigFile in rigFiles:
            geoNodes = geoNodes + importRig( item, rigFile, step)

    if len(animFiles) > 0:
        ram.log( "I'm importing the animation.")
        for animFile in animFiles:
            geoNodes = geoNodes + importAnim(item, animFile, step)

    if len(animRefFiles) > 0:
        ram.log( "I'm referencing the animation.")
        for animFile in animRefFiles:
            geoNodes = geoNodes + importAnim(item, animFile, step, ref=True)

    if len(vpShaderFiles) > 0:
        ram.log( "I'm importing the viewport shaders." )
        for vpShaderFile in vpShaderFiles:
            importShaders( item, vpShaderFile, VPSHADERS_PIPE_NAME, step, geoNodes )

    if len(rdrShaderFiles) > 0:
        ram.log( "I'm importing the render shaders." )
        for rdrShaderFile in rdrShaderFiles:
            importShaders( item, rdrShaderFile, RDRSHADERS_PIPE_NAME, step, geoNodes )

    if len(standardFiles) > 0:
        ram.log( "I'm importing " + item.shortName() )
        for standardFile in standardFiles:
            importStandard( item, standardFile, step )

    if len(standardRefFiles) > 0:
        ram.log( "I'm importing " + item.shortName() )
        for standardFile in standardRefFiles:
            importStandard( item, standardRefFiles, step, ref=True )