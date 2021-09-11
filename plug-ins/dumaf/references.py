# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=import-error

class Reference():

    @staticmethod
    def importAll():
        for ref in cmds.ls(type='reference'):
            refFile = cmds.referenceQuery(ref, f=True)
            cmds.file(refFile, importReference=True)