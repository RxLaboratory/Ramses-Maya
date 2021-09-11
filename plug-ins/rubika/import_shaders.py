# -*- coding: utf-8 -*-

from .utils_shaders import referenceShaders
from .utils_attributes import * # pylint: disable=import-error

def importShaders( item, filePath, mode, step, nodes=[] ):
    # Import shaders
    shaderNodes = referenceShaders(nodes, mode, filePath, item.shortName())
    for node in shaderNodes:
        setImportAttributes( node, item, step, filePath )