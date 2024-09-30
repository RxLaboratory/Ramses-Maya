# -*- coding: utf-8 -*-

# Functions to handle node paths.

import re
import maya.cmds as cmds # pylint: disable=import-error

RE_MAYA_UNAUTHORIZED_CHARS = re.compile('[^a-zA-Z0-9_]')

def baseName( node, keepNameSpace = False ):
    """!
    @brief Gets the name of a node from a DAG path

    Parameters : 
        @param node => The path to the node
        @param keepNameSpace = False => If True, keeps the namespace:: part if any

    """
    nodeName = node.split('|')[-1]
    if not keepNameSpace:
        nodeName = nodeName.split(':')[-1]
    return nodeName

def absolutePath( nodeName ):
    """!
    @brief Gets the absolute path from a (unique) name of an existing node
    
    Parameters : 
        @param nodeName => [description]
    """
    n = cmds.ls(nodeName, long=True)
    if n is not None:
        return n[0]
    return nodeName

def sanitizeName( name ):
    """!
    @brief Replaces unauthorized characters in the name by '_'

    Parameters : 
        @param name => A name for a node in Maya
    """
    return re.sub (
        RE_MAYA_UNAUTHORIZED_CHARS,
        '_',
        name )
