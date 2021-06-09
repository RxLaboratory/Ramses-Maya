from .publish_geo import *
from .publish_shaders import *
from .utils_constants import *
from .utils_items import *
import ramses as ram

def publisher(item, filePath, step):
    # Check what needs to be published

    # Get pipes
    pipes = getPipes( step )
    if len(pipes) == 0:
        return
    
    geo = False
    vpShaders = False
    rdrShaders = False
    proxyShade = False
    proxyGeo = False

    for pipe in pipes:
        for pipeFile in pipe.pipeFiles():
            if pipeFile == GEO_PIPE_FILE:
                geo = True
            elif pipeFile == VPSHADERS_PIPE_FILE:
                vpShaders = True
            elif pipeFile == RDRSHADERS_PIPE_FILE:
                rdrShaders = True
            elif pipeFile == PROXYSHADE_PIPE_FILE:
                proxyShade = True
            elif pipeFile == PROXYGEO_PIPE_FILE:
                proxyGeo = True

    if geo: # If we publish the geometry, we may publish shaders and proxy geo with the same function
        geoMode = ONLY_GEO
        if proxyGeo:
            geoMode = ALL

        ram.log( "I'm publishing the geometry (and maybe some shading and proxies...)." )
        if vpShaders:
            publishGeo( item, filePath, step, 'vp', geoMode )
        elif rdrShaders:
            publishGeo( item, filePath, step, 'rdr', geoMode )
        else:
            publishGeo( item, filePath, step, '', geoMode )
    else: # if we did not publish the geometry, we may have to publish the shaders and proxy geo anyway
        if vpShaders:
            ram.log( "I'm publishing the viewport shaders." )
            publishShaders( item, filePath, step, 'vp' )
        if rdrShaders:
            ram.log( "I'm publishing the render shaders." )
            publishShaders( item, filePath, step, 'rdr' )
        if proxyGeo:
            ram.log( "I'm publishing the geo proxies." )
            publishGeo( item, filePath, step, '', ONLY_PROXY )

    if proxyShade:
        publishProxyShaders(item, filePath, step)
