from .utils_shaders import referenceShaders

def importShaders( item, filePath, mode, nodes=[] ):
    # Import shaders
    referenceShaders(nodes, mode, filePath, item.shortName())