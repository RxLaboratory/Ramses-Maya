from .publish_mod import publishMod
from .import_mod import importMod
from .update import updateRamsesItems
import ramses as ram

ramses = ram.Ramses.instance()

# Register publish scripts
ramses.publishScripts.append(publishMod)

# Register import scripts
ramses.importScripts.append(importMod)

# Register user scripts
ramses.userScripts['update'] = updateRamsesItems