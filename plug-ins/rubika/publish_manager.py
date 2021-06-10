from .publish_geo import *
from .publish_shaders import *
from .utils_constants import *
from .utils_items import *
from .publish_rig import *
from .utils_nodes import *
import ramses as ram

def publisher(item, filePath, step):
    # Check what needs to be published
    print(step)
    # Get pipes
    pipes = getPipes( step )
    if len(pipes) == 0:
        return
    
    geo = False
    vpShaders = False
    rdrShaders = False
    proxyShade = False
    proxyGeo = False
    rig = False

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
            elif pipeFile == RIG_PIPE_FILE:
                rig = True

    # We're deleting everything which name stats with "delOnPub_"
    cmds.delete( getDelOnPubNodes() )

    vpShadersPublished = False
    rdrShadersPublished = False

    if geo: # If we publish the geometry, we may publish shaders and proxy geo with the same function
        geoMode = ONLY_GEO
        if proxyGeo:
            geoMode = ALL

        ram.log( "I'm publishing the geometry (and maybe some shading and proxies...)." )
        if vpShaders:
            vpShadersPublished = True
            publishGeo( item, filePath, step, VPSHADERS_PIPE_NAME, geoMode )
        elif rdrShaders:
            rdrShadersPublished = True
            publishGeo( item, filePath, step, RDRSHADERS_PIPE_NAME, geoMode )
        else:
            publishGeo( item, filePath, step, '', geoMode )

    if rig: # The rig may also publish the vp shaders
        vpShadersPublished = vpShaders
        publishRig( item, filePath, step, vpShaders )

    if vpShaders and not vpShadersPublished:
        ram.log( "I'm publishing the viewport shaders." )
        publishShaders( item, filePath, step, VPSHADERS_PIPE_NAME )
    if rdrShaders and not rdrShadersPublished:
        ram.log( "I'm publishing the render shaders." )
        publishShaders( item, filePath, step, RDRSHADERS_PIPE_NAME )
    if proxyGeo:
        ram.log( "I'm publishing the geo proxies." )
        publishGeo( item, filePath, step, '', ONLY_PROXY )

    if proxyShade:
        publishProxyShaders(item, filePath, step )
