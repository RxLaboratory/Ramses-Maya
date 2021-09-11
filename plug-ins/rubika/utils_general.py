# -*- coding: utf-8 -*-

import os
import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram

def endProcess(tempData, progressDialog):
    # Re-Open initial scene
    cmds.file(tempData[1],o=True,f=True)

    # Remove temp file
    if os.path.isfile(tempData[0]):
        os.remove(tempData[0])

    if progressDialog:
        progressDialog.hide()

