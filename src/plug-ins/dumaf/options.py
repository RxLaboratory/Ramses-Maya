# -*- coding: utf-8 -*-
"""Functions to handle maya options (optionVar)."""

import maya.cmds as cmds # pylint: disable=import-error

def get( optionName, defaultVal=None):
    """Gets an option value or return the default if not found"""
    if not cmds.optionVar(exists=optionName):
        return defaultVal
    return cmds.optionVar(q=optionName)

def save( optionName, val):
    """Sets a value in the options"""
    if isinstance(val, int):
        cmds.optionVar(intValue=(optionName, val))
    elif isinstance(val, float):
        cmds.optionVar(floatValue=(optionName, val))
    else:
        cmds.optionVar(stringValue=(optionName, val))
