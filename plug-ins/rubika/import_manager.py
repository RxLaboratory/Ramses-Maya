import os

import maya.cmds as cmds
from .import_geo import importGeo
from .import_shaders import importShaders
import ramses as ram

ramses = ram.Ramses.instance()

def importer(item, filePath, step):
    # Check what needs to be imported

    # Get the output pipes from the step being imported
    pipes = step.outputPipes()
    
    # If we've got all the pipes
    if len(pipes) > 0:
        
        geoPipeFile = None
        vpShadersPipeFile = None
        rdrShadersPipeFile = None

        # Get the current step if possible
        currentStepShortName = ''
        currentFilePath = cmds.file( q=True, sn=True )
        saveFilePath = ram.RamFileManager.getSaveFilePath( currentFilePath )

        if saveFilePath != '':
            saveFileInfo = ram.RamFileManager.decomposeRamsesFilePath( saveFilePath )
            if saveFileInfo is not None:
                currentProject = ramses.project( saveFileInfo['project'] )
                if currentProject is None:
                    currentProject = ramses.currentProject()
                else:
                    ramses.setCurrentProject( currentProject )
                if currentProject is not None:
                    currentStep = currentProject.step( saveFileInfo['step'] )
                    currentStepShortName = currentStep.shortName()

        for pipe in pipes:
            if pipe.inputStepShortName() == currentStepShortName or currentStepShortName == '':
                for pipeFile in pipe.pipeFiles():
                    pipeType = pipeFile.shortName()
                    if pipeType == 'Geometry':
                        geoPipeFile = pipeFile
                    elif pipeType == 'vpShaders':
                        vpShadersPipeFile = pipeFile
                    elif pipeType == 'rdrShaders':
                        rdrShadersPipeFile = pipeFile

        geoFiles = []
        vpShaderFiles = []
        rdrShaderFiles = []

        # Find the files if needed
        if len(filePath) == 0:
            # List all files, and get correspondance
            publishFolder = item.publishFolderPath( step )

            if geoPipeFile:
                geoFiles = geoPipeFile.getFiles( publishFolder )
            if vpShadersPipeFile:
                vpShaderFiles = vpShadersPipeFile.getFiles( publishFolder )
            if rdrShadersPipeFile:
                rdrShaderFiles = rdrShadersPipeFile.getFiles( publishFolder )

        # Keep the Geo nodes and the selection to import the shaders on them automatically
        geoNodes = cmds.ls(selection=True, type='transform', long=True)

        if geoPipeFile:
            ram.log( "I'm importing the geometry." )
            for geoFile in geoFiles:
                geoNodes = geoNodes + importGeo( item, geoFile, step )

        if vpShadersPipeFile:
            ram.log( "I'm importing the viewport shaders." )
            for vpShaderFile in vpShaderFiles:
                importShaders( item, vpShaderFile, 'vp', geoNodes )

        if rdrShadersPipeFile:
            ram.log( "I'm importing the render shaders." )
            for rdrShaderFile in rdrShaderFiles:
                importShaders( item, rdrShaderFile, 'rdr', geoNodes )

    # Use step if we did not find pipes #  TODO if filePath is none -> Refactor also publish : just create the default RamPipeFiles to replace the ones we did not get
    else:
        step = ram.RamObject.getObjectShortName(step)
        if step == 'MOD':
            ram.log( "I'm publishing the Modeling step." )
            importGeo()
        elif step == 'SHADE':
            ram.log( "I'm publishing the Shading step." )
