"""
The Rx Asset Management System (Ramses) Maya Plugin.
This is a file for running tests and should not be used in production.
"""

from maya import cmds
import ramses
import ramses_maya as ram
import dumaf as maf

RAMSES = ramses.Ramses.instance()

maf.mayapy.reset_script_session( ram.utils.PLUGIN_PATH )

dlg = ram.ui_scene_setup.SceneSetupDialog()
ok = dlg.setItem(ramses.RamShot("Shot 001", "S001"))
if not ok:
    dlg.exec_()
else:
    dlg.create_sets()
