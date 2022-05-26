"""
The Rx Asset Management System (Ramses) Maya Plugin.
This is a file for running tests and should not be used in production.
"""

import sys
import ramses_maya as ram
from dumaf import mayapy

mayapy.reset_script_session( ram.utils.PLUGIN_PATH )

publish_nodes = ram.utils_nodes.get_publish_nodes()
if len(publish_nodes) == 0:
    sys.exit()
publish_dialog = ram.ui_publish.PublishDialog()
publish_dialog.load_nodes(publish_nodes)
publish_dialog.show()
