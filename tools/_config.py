import os
from pathlib import Path
from rxbuilder.utils import normpath

VERSION = '1.0.0-Beta'

REPO_PATH = normpath(Path(__file__).parent.parent.resolve())
BUILD_PATH = os.path.join(REPO_PATH, 'build')
SRC_PATH = os.path.join(REPO_PATH, 'src')