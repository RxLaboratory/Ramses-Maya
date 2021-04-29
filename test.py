import maya.cmds as cmds  # pylint: disable=import-error

try:
    cmds.unloadPlugin("ram_cmds.py")
except:
    print("Ramses can not be unloaded.")
    
cmds.loadPlugin("ram_cmds.py")

cmds.ramOpenRamses()