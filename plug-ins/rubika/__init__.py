from .publish import publishSorter
from .import_mod import importMod
from .update import updateRamsesItems
import ramses as ram

ramses = ram.Ramses.instance()

# Register publish scripts
ramses.publishScripts.append(publishSorter)

# Register import scripts
ramses.importScripts.append(importMod)

# Register user scripts
ramses.userScripts['update'] = updateRamsesItems