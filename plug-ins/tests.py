"""
The Rx Asset Management System (Ramses) Maya Plugin.
This is a file for running tests and should not be used in production.
"""

import ramses
import ramses_maya as ram
import dumaf as maf

maf.mayapy.reset_script_session( ram.utils.PLUGIN_PATH )

ram.importer(ramses.RamItem("item", "an asset"), "", ramses.RamStep("STEP", "a step"), False)