# -*- coding: utf-8 -*-

from .publish_geo import *
from .publish_set import *
from .publish_shaders import *
from .publish_standard import *
from .publish_anim import *
from .utils_constants import *
from .utils_items import *
from .publish_rig import *
from .utils_nodes import *
import ramses as ram

def publisher(item, step, publishFileInfo):

    ram.log("Publishing " + str(item) + " for " + str(step) + " in:\n" + os.path.dirname( publishFileInfo.filePath()), ram.LogLevel.Info)

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
    rig = False
    sets = False
    standard = False
    anim = False

    pipeFiles = []

    for pipe in pipes:
        for pipeFile in pipe.pipeFiles():
            pipeFiles.append(pipeFile)
            if pipeFile == GEO_PIPE_FILE or pipeFile == GEOREF_PIPE_FILE:
                geo = True
            elif pipeFile == VPSHADERS_PIPE_FILE:
                vpShaders = True
            elif pipeFile == RDRSHADERS_PIPE_FILE:
                rdrShaders = True
            elif pipeFile == PROXYSHADE_PIPE_FILE:
                proxyShade = True
            elif pipeFile == PROXYGEO_PIPE_FILE or pipeFile == PROXYGEOREF_PIPE_FILE:
                proxyGeo = True
            elif pipeFile == RIG_PIPE_FILE:
                rig = True
            elif pipeFile == SET_PIPE_FILE or pipeFile == SETREF_PIPE_FILE:
                sets = True
            elif pipeFile == STANDARD_PIPE_FILE or pipeFile == STANDARDREF_PIPE_FILE:
                standard = True
            elif pipeFile == ANIM_PIPE_FILE or  pipeFile == ANIMREF_PIPE_FILE:
                anim = True

    # We're deleting everything in the "Ramses_DelOnPublish" set
    cmds.delete( getDelOnPubNodes() )

    vpShadersPublished = False
    rdrShadersPublished = False

    if geo: # If we publish the geometry, we may publish shaders and proxy geo with the same function
        ram.log( "I'm publishing the geometry (and maybe some shading and proxies...)." )
        if vpShaders:
            vpShadersPublished = True
            publishGeo( item, step, publishFileInfo, pipeFiles )
        elif rdrShaders:
            rdrShadersPublished = True
            publishGeo( item, step, publishFileInfo, pipeFiles )
        else:
            publishGeo( item, step, publishFileInfo, pipeFiles )

    if rig: # The rig may also publish the vp shaders
        vpShadersPublished = vpShaders
        publishRig( item, step, publishFileInfo, pipeFiles, vpShaders )

    if vpShaders and not vpShadersPublished:
        ram.log( "I'm publishing the viewport shaders." )
        publishShaders( item, step, publishFileInfo, VPSHADERS_PIPE_NAME )
    
    if rdrShaders and not rdrShadersPublished:
        ram.log( "I'm publishing the render shaders." )
        publishShaders( item, step, publishFileInfo, RDRSHADERS_PIPE_NAME )
    
    if proxyGeo and not geo:
        ram.log( "I'm publishing the geo proxies." )
        publishGeo( item, step, publishFileInfo, pipeFiles )

    if proxyShade:
        ram.log( "I'm publishing the shading proxies." )
        publishProxyShaders(item, step, publishFileInfo )

    if sets:
        ram.log( "I'm publishing the set." )
        publishSet(item, step, publishFileInfo, pipeFiles)

    if standard:
        ram.log( "Publishing Maya Binary." )
        publishStandard( item, step, publishFileInfo, pipeFiles )
    
    if anim:
        ram.log( "Publishing animation." )
        publishAnim( item, step, publishFileInfo, pipeFiles )