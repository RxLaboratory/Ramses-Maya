# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=import-error

class Animation():
    
    @staticmethod
    def removeAll():
        keys = cmds.ls(type='animCurveTL') + cmds.ls(type='animCurveTA') + cmds.ls(type='animCurveTU')
        for key in keys:
            try:
                cmds.delete(key)
            except:
                pass
