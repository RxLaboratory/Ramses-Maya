# -*- coding: utf-8 -*-

# Functions to create and edit "name commands" and hotkeys.

import maya.cmds as cmds # pylint: disable=import-error

class NameCmd():
    
    @staticmethod
    def createNameCommand( name, annotation, pyCommand):
        # Because the 'sourceType' parameter of cmds.nameCommand is broken, we first need to create a runtime command to run our python code...

        # There is no way to edit a runtime command so we need to check if it
        # exists and then remove it if it does.
        if cmds.runTimeCommand(name, q=True, exists=True):
            cmds.runTimeCommand(name, e=True, delete=True)
        # Now, re-create it
        cmds.runTimeCommand(
            name, 
            ann=annotation, 
            category='User', 
            command=pyCommand, 
            commandLanguage='python'
            )

        # Create the command
        nc = cmds.nameCommand( name, ann=annotation, command=name)

        return nc

    @staticmethod
    def restoreOpenSceneHotkey():
        # We need to re-create a nameCommand, because Maya...
        command = cmds.nameCommand( annotation="OpenSceneNameCommand", command='OpenScene' )
        cmds.hotkey(keyShortcut='o', ctrlModifier = True, name=command)
        cmds.savePrefs(hotkeys=True)

    @staticmethod
    def restoreSaveSceneAsHotkey():
        # We need to re-create a nameCommand, because Maya...
        command = cmds.nameCommand( annotation="SaveSceneAsNameCommand", command='SaveSceneAs' )
        cmds.hotkey(keyShortcut='s', ctrlModifier = True, shiftModifier=True, name=command)
        cmds.savePrefs(hotkeys=True)

    @staticmethod
    def restoreSaveSceneHotkey():
        # We need to re-create a nameCommand, because Maya...
        command = cmds.nameCommand( annotation="SaveSceneNameCommand", command='SaveScene' )
        cmds.hotkey(keyShortcut='s', ctrlModifier = True, name=command)
        cmds.savePrefs(hotkeys=True)