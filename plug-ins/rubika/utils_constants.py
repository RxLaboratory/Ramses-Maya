import ramses as ram

# This file contains the default configuration of the Supinfocom-Rubika pipeline
# These values are used to select the right importers/exporters depending on the pipes given by the Ramses Daemon
# The default Steps are also used in case the Daemon is not available.

# FileTypes to be used

ABC_FILE = ram.RamFileType( "Alembic", 'abc', ['.abc'] )
MB_FILE = ram.RamFileType( "Maya Binary", 'mb',  ['.mb'] )
MA_FILE = ram.RamFileType( "Maya ASCII", 'ma', ['.ma'] )
ASS_FILE = ram.RamFileType( "Arnold Source File", 'ass', ['.ass'] )

# Pipe Names

GEO_PIPE_NAME = 'Geometry'
VPSHADERS_PIPE_NAME = 'vpShaders'
RDRSHADERS_PIPE_NAME = 'rdrShaders'
PROXYSHADE_PIPE_NAME = 'proxyShade'
PROXYGEO_PIPE_NAME = 'proxyGeo'
RIG_PIPE_NAME = 'Rig'
SET_PIPE_NAME = LAYOUT_PIPE_NAME = 'Layout' # Layout and Set are the same

# PipeFiles

GEO_PIPE_FILE = ram.RamPipeFile( GEO_PIPE_NAME, ABC_FILE, "" )
VPSHADERS_PIPE_FILE = ram.RamPipeFile( VPSHADERS_PIPE_NAME, MB_FILE, "" )
RDRSHADERS_PIPE_FILE = ram.RamPipeFile( RDRSHADERS_PIPE_NAME, MB_FILE, "" )
PROXYSHADE_PIPE_FILE = ram.RamPipeFile( PROXYSHADE_PIPE_NAME, ASS_FILE, "" )
PROXYGEO_PIPE_FILE = ram.RamPipeFile( PROXYGEO_PIPE_NAME, ABC_FILE, "" )
RIG_PIPE_FILE = ram.RamPipeFile( RIG_PIPE_NAME, MA_FILE, "" )
SET_PIPE_FILE = LAYOUT_PIPE_FILE = ram.RamPipeFile( LAYOUT_PIPE_NAME, MB_FILE, "" )

PIPE_FILES = [
    GEO_PIPE_FILE,
    VPSHADERS_PIPE_FILE,
    RDRSHADERS_PIPE_FILE,
    PROXYSHADE_PIPE_FILE,
    PROXYGEO_PIPE_FILE,
    RIG_PIPE_FILE,
    LAYOUT_PIPE_FILE,
]

# Default Steps

MOD_STEP = ram.RamStep( "Modeling", 'MOD', '', ram.StepType.ASSET_PRODUCTION )
SHADE_STEP = ram.RamStep( "Shading", 'SHADE', '', ram.StepType.ASSET_PRODUCTION )
RIG_STEP = ram.RamStep("Rigging", 'RIG', '', ram.StepType.ASSET_PRODUCTION )
LAY_STEP = ram.RamStep("Layout", 'LAY', '', ram.StepType.ASSET_PRODUCTION )
SET_STEP = ram.RamStep("Set Dressing", 'SET', '', ram.StepType.ASSET_PRODUCTION )

# Setting default Pipes. Don't do that! It is BAD to set a private attribute.
# Unless you know what you're doing.
MOD_STEP._outputPipes = [ 
    ram.RamPipe( '', 'MOD', [ GEO_PIPE_FILE, VPSHADERS_PIPE_FILE, PROXYGEO_PIPE_FILE ] ),
]

SHADE_STEP._outputPipes = [
    ram.RamPipe( '', 'SHADE', [ RDRSHADERS_PIPE_FILE, PROXYSHADE_PIPE_FILE, PROXYGEO_PIPE_FILE ] ),
]

RIG_STEP._outputPipes = [
    ram.RamPipe( '', 'RIG', [ RIG_PIPE_FILE, VPSHADERS_PIPE_FILE ] ),
]

LAY_STEP._outputPipes = [
    ram.RamPipe( '', 'LAY', [ LAYOUT_PIPE_FILE ] ),
]

SET_STEP._outputPipes = [
    ram.RamPipe( '', 'LAY', [ SET_PIPE_FILE ] ),
]