from .publish_geo import *
from .publish_shaders import *
import ramses as ram

def publisher(item, filePath, step):
    # Check what needs to be published

    # From pipes first
    pipes = step.outputPipes()
    if len(pipes) > 0:
        geo = False
        vpShaders = False
        rdrShaders = False
        proxyShade = False
        proxyGeo = False

        for pipe in pipes:
            for pipeFile in pipe.pipeFiles():
                pipeType = pipeFile.shortName()
                if pipeType == 'Geometry':
                    geo = True
                elif pipeType == 'vpShaders':
                    vpShaders = True
                elif pipeType == 'rdrShaders':
                    rdrShaders = True
                elif pipeType == 'proxyShade':
                    proxyShade = True
                elif pipeType == 'proxyGeo':
                    proxyGeo = True

        if geo:
            geoMode = ONLY_GEO
            if proxyGeo:
                geoMode = ALL
            ram.log( "I'm publishing the geometry." )
            if vpShaders:
                publishGeo( item, filePath, step, 'vp', geoMode )
            elif rdrShaders:
                publishGeo( item, filePath, step, 'rdr', geoMode )
            else:
                publishGeo( item, filePath, step, '', geoMode )
        else:
            if vpShaders:
                ram.log( "I'm publishing the viewport shaders." )
                publishShaders( item, filePath, step, 'vp' )
            if rdrShaders:
                ram.log( "I'm publishing the render shaders." )
                publishShaders( item, filePath, step, 'rdr' )

        if proxyShade:
            publishProxyShaders(item, filePath, step)
    # From step if we did not find the pipes
    else:
        step = ram.RamObject.getObjectShortName(step)
        if step == 'MOD':
            ram.log( "I'm publishing the Modeling step." )
            publishGeo( item, filePath, step, 'vp')
        elif step == 'SHADE':
            ram.log( "I'm publishing the Shading step." )
            publishGeo( item, filePath, step, 'rdr', ONLY_PROXY)
            publishProxyShaders(item, filePath, step)