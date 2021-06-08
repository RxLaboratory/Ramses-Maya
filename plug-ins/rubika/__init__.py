from .publish_manager import publisher
from .import_manager import importer
from .update_manager import updateRamsesItems
import ramses as ram

ramses = ram.Ramses.instance()

# Register publish scripts
ramses.publishScripts.append(publisher)

# Register import scripts
ramses.importScripts.append(importer)

# Register user scripts
ramses.userScripts['update'] = updateRamsesItems