from .publish_mod import publishMod
import ramses as ram

ramses = ram.Ramses.instance()

# Register publish scripts
ramses.publishScripts.append(publishMod)