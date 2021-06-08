from .publish_geo import publishGeo
from .publish_shaders import publishShaders
import ramses as ram

def publishSorter(item, filePath, step):
    # Check what needs to be published

    # From pipes first
    pipes = step.outputPipes()
    if len(pipes) > 0:
        geo = False
        vpShaders = False
        rdrShaders = False

        for pipe in pipes:
            for pipeFile in pipe.pipeFiles():
                pipeType = pipeFile.shortName()
                if pipeType == 'Geo':
                    geo = True
                if pipeType == 'vpShaders':
                    vpShaders = True
                if pipeType == 'rdrShaders':
                    rdrShaders = True

        if geo:
            ram.log( "I'm publishing the geometry." )
            if vpShaders:
                publishGeo( item, filePath, step, 'vp' )
            elif rdrShaders:
                publishGeo( item, filePath, step, 'rdr' )
            else:
                publishGeo( item, filePath, step, '' )
        else:
            if vpShaders:
                ram.log( "I'm publishing the viewport shaders." )
                publishShaders( item, filePath, step, 'vp' )
            if rdrShaders:
                ram.log( "I'm publishing the render shaders." )
                publishShaders( item, filePath, step, 'rdr' )

    else:
        step = ram.RamObject.getObjectShortName(step)
        if step == 'MOD':
            ram.log( "I'm publishing the Modeling step." )
            publishGeo( item, filePath, step, 'vp')