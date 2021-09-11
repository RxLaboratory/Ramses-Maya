# -*- coding: utf-8 -*-

import ramses as ram # pylint: disable=import-error
import maya.cmds as cmds # pylint: disable=import-error
from .utils_constants import  *
from .ui_pipes import PipeDialog
import dumaf as maf
import ramses as ram

ramses = ram.Ramses.instance()

def getPipeExtension( pipe, pipes, defaultExtension):
    for p in pipes:
        if pipe != p: continue
        fileType = p.fileType()
        if fileType is None: continue
        exts = fileType.extensions()
        if len(exts) == 0: continue
        ext = exts[0]
        if ext.starswith('.'): return ext[1:]
        return ext
    return defaultExtension

def getExtension( step, defaultStep, defaultPipeFile, pipeFiles, filters, defaultExtension ):
    # Get the extension from the pipe (ma or mb)
    pipes = step.outputPipes()
    if len(pipes) == 0:
        pipes = defaultStep.outputPipes()

    for pipe in pipes:
        for pipeFile in pipe.pipeFiles():
            exts = pipeFile.fileType().extensions()
            if len(exts) == 0:
                continue
            ext = exts[0]
            if ext.startswith('.'):
                ext  = ext[1:]
            if ext.lower() in filters:
                return getPipeExtension( defaultPipeFile, pipeFiles, ext)

    # Get default
    ext = defaultPipeFile.fileType().extensions()[0]

    if ext.startswith('.'):
        ext  = ext[1:]
    if ext in filters:
        return getPipeExtension( defaultPipeFile, pipeFiles, ext)

    return getPipeExtension( defaultPipeFile, pipeFiles, defaultExtension)

def getPublishFolder( item, step):
    publishFolder = item.publishFolderPath( step )
    if publishFolder == '':
        ram.log("I can't find the publish folder for this item, maybe it does not respect the ramses naming scheme or it is out of place.", ram.LogLevel.Fatal)
        cmds.inViewMessage( msg="Can't find the publish folder for this scene, sorry. Check its name and location.", pos='midCenter', fade=True )
        cmds.error( "Can't find publish folder." )
        return ''
    return publishFolder

def getPipes( step, currentSceneFilePath = '', mode='Publish' ):
    ps = step.outputPipes()
    
    pipes = []
    
    # Keep only pipes with pipefiles
    for p in ps:
        if len(p.pipeFiles()) != 0: pipes.append(p)

    if len( pipes ) == 0:
        for s in STEPS:
            if s == step:
                print(s)
                pipes = s.outputPipes()
                print(pipes)
                break
    
    if len( pipes ) == 0: # Let's ask!
        pipeDialog = PipeDialog( maf.UI.getMayaWindow(), mode )
        if pipeDialog.exec_():
            pipes = pipeDialog.getPipes()
        return pipes

    if currentSceneFilePath == '':
        return pipes

    scenePipes = []

    # Get the current step if possible
    currentStepShortName = ''
    saveFilePath = ram.RamFileManager.getSaveFilePath( currentSceneFilePath )

    if saveFilePath != '':
        nm = ram.RamFileInfo()
        nm.setFilePath( saveFilePath )
        if nm.project != '':
            currentProject = ramses.project( nm.project )
            if currentProject is None:
                currentProject = ramses.currentProject()
            else:
                ramses.setCurrentProject( currentProject )
            if currentProject is not None:
                currentStep = currentProject.step( nm.step )
                currentStepShortName = currentStep.shortName()

    # Check the pipes
    for pipe in pipes:
        if pipe.inputStepShortName() == currentStepShortName or currentStepShortName == '' or pipe.inputStepShortName() == '':
            scenePipes.append(pipe)

    return scenePipes