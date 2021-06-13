import ramses as ram

# This file contains the default configuration of the Supinfocom-Rubika pipeline
# These values are used to select the right importers/exporters depending on the pipes given by the Ramses Daemon
# The default Steps are also used in case the Daemon is not available.

# FileTypes to be used in the pipeline

ABC_FILE = ram.RamFileType( "Alembic", 'abc', ['.abc'] )
MB_FILE = ram.RamFileType( "Maya Binary", 'mb',  ['.mb'] )
MA_FILE = ram.RamFileType( "Maya ASCII", 'ma', ['.ma'] )
ASS_FILE = ram.RamFileType( "Arnold Source File", 'ass', ['.ass'] )

# Pipe Names - These are the names to use in the Ramses Pipeline Editor

STANDARDB_PIPE_NAME = 'Standard' # used for layout, lighting, etc non-managed pipes
STANDARDA_PIPE_NAME = 'StandardA' # used for layout, lighting, etc non-managed pipes
GEO_PIPE_NAME = 'Geometry'
VPSHADERS_PIPE_NAME = 'vpShaders'
RDRSHADERS_PIPE_NAME = 'rdrShaders'
PROXYSHADE_PIPE_NAME = 'proxyShade'
PROXYGEO_PIPE_NAME = 'proxyGeo'
RIG_PIPE_NAME = 'Rig'
SET_PIPE_NAME = 'Set'
ANIM_PIPE_NAME = 'Anim'

# PipeFiles - These associate the name with a file type (and a color space, ignored for now)

STANDARDB_PIPE_FILE = ram.RamPipeFile( STANDARDB_PIPE_NAME, MB_FILE, "" )
STANDARDA_PIPE_FILE = ram.RamPipeFile( STANDARDA_PIPE_NAME, MA_FILE, "" )
GEO_PIPE_FILE = ram.RamPipeFile( GEO_PIPE_NAME, ABC_FILE, "" )
VPSHADERS_PIPE_FILE = ram.RamPipeFile( VPSHADERS_PIPE_NAME, MB_FILE, "" )
RDRSHADERS_PIPE_FILE = ram.RamPipeFile( RDRSHADERS_PIPE_NAME, MB_FILE, "" )
PROXYSHADE_PIPE_FILE = ram.RamPipeFile( PROXYSHADE_PIPE_NAME, ASS_FILE, "" )
PROXYGEO_PIPE_FILE = ram.RamPipeFile( PROXYGEO_PIPE_NAME, ABC_FILE, "" )
RIG_PIPE_FILE = ram.RamPipeFile( RIG_PIPE_NAME, MA_FILE, "" )
SET_PIPE_FILE = ram.RamPipeFile( SET_PIPE_NAME, MB_FILE, "" )
ANIM_PIPE_FILE = ram.RamPipeFile( ANIM_PIPE_NAME, ABC_FILE, "" )

PIPE_FILES = ( # All previously configured pipe files have to be listed here
    STANDARDB_PIPE_FILE,
    STANDARDA_PIPE_FILE,
    GEO_PIPE_FILE,
    VPSHADERS_PIPE_FILE,
    RDRSHADERS_PIPE_FILE,
    PROXYSHADE_PIPE_FILE,
    PROXYGEO_PIPE_FILE,
    RIG_PIPE_FILE,
    SET_PIPE_FILE,
    ANIM_PIPE_FILE,
)

# Default Steps - These are the steps to be used when the Daemon/Client Application is not available to give us the pipes we need

MOD_STEP = ram.RamStep( "Modeling", 'MOD', '', ram.StepType.ASSET_PRODUCTION )
SHADE_STEP = ram.RamStep( "Shading", 'SHADE', '', ram.StepType.ASSET_PRODUCTION )
RIG_STEP = ram.RamStep("Rigging", 'RIG', '', ram.StepType.ASSET_PRODUCTION )
SET_STEP = ram.RamStep("Set Dressing", 'SET', '', ram.StepType.ASSET_PRODUCTION )
LAY_STEP = ram.RamStep("Layout", 'LAY', '', ram.StepType.SHOT_PRODUCTION )
LIGHT_STEP = ram.RamStep("Lighting", 'LIGHT', '', ram.StepType.SHOT_PRODUCTION )
ANIM_STEP = ram.RamStep("Animation", 'ANIM', ram.StepType.SHOT_PRODUCTION )
FX_STEP = ram.RamStep("Visual Effects", 'VFX', ram.StepType.SHOT_PRODUCTION )

# Association between the steps and the pipes

# Setting default Pipes.
# Don't do that! It is BAD to set a private attribute.
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
    ram.RamPipe( '', 'LAY', [ STANDARDB_PIPE_FILE ] ),
]

SET_STEP._outputPipes = [
    ram.RamPipe( '', 'LAY', [ SET_PIPE_FILE ] ),
]

LIGHT_STEP._outputPipes = [
    ram.RamPipe( '', 'LAY', [ STANDARDB_PIPE_FILE ] ),
]

ANIM_STEP._outputPipes = [
    ram.RamPipe( '', 'ANIM', [ ANIM_PIPE_FILE ] ),
]

FX_STEP._outputPipes = [
    ram.RamPipe( '', 'VFX', [ ANIM_PIPE_FILE ] ),
]

STEPS = ( # All previously configured steps files have to be listed here
    MOD_STEP,
    SHADE_STEP,
    RIG_STEP,
    SET_STEP,
    LAY_STEP,
    LIGHT_STEP,
    ANIM_STEP,
    FX_STEP,
)