"""
The Rx Asset Management System (Ramses) Maya Plugin.
This is a file for running tests and should not be used in production.
"""

import ramses
import ramses_maya as ram
import dumaf as maf

node = maf.Node("truc")
print(node.is_empty())
node.remove_empty(True)