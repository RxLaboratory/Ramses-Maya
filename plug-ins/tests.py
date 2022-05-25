"""
The Rx Asset Management System (Ramses) Maya Plugin.
This is a file for running tests and should not be used in production.
"""

import sys
from ramses_maya import ui_publish, utils_nodes

publish_nodes = utils_nodes.get_publish_nodes()
if len(publish_nodes) == 0:
    sys.exit()
publish_dialog = ui_publish.PublishDialog()
publish_dialog.load_nodes(publish_nodes)
ok = publish_dialog.exec_()
print(ok)
