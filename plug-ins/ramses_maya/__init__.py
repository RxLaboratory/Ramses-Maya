"""
The Rx Asset Management System (Ramses) Maya Plugin
"""

from ramses import *
import dumaf as maf
from .ram_cmds import cmds_classes
from .publish_manager import publisher

RAMSES = Ramses.instance()

# Register publish scripts
RAMSES.publishScripts.append(publisher)
