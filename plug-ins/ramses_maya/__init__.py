"""
The Rx Asset Management System (Ramses) Maya Plugin
"""

from ramses import *
import dumaf as maf
from .ram_cmds import cmds_classes
from .publish_manager import publisher
from .import_manager import importer
from . import utils
from . import ui_publish
from . import ui_import
from . import ui_scene_setup

RAMSES = Ramses.instance()

# Register publish scripts
RAMSES.publishScripts.append(publisher)

# Register import scripts
RAMSES.importScripts.append(importer)
