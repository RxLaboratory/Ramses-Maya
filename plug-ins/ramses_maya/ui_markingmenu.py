import maya.cmds as cmds

MENU_NAME = "RamsesMarkingMenu"

class RamsesMarkingMenu():
    """The main class, which encapsulates everything we need to build and rebuild our marking menu. All
    that is done in the constructor, so all we need to do in order to build/update our marking menu is
    to initialize this class.
    """

    def __init__(self):
        self._removeOld()
        self._build()

    def _build(self):
        """Creates the marking menu context and calls the _buildMarkingMenu() method to populate it with all items."""
        menu = cmds.popupMenu(MENU_NAME, mm=1, b=2, aob=1, ctl=1, alt=1, sh=0, p="viewPanes", pmo=1, pmc=self._buildMarkingMenu)

    def _removeOld(self):
        """Checks if there is a marking menu with the given name and if so deletes it to prepare for creating a new one.
        We do this in order to be able to easily update our marking menus."""
        if cmds.popupMenu(MENU_NAME, ex=1):
            cmds.deleteUI(MENU_NAME)

    def _buildMarkingMenu(self, menu, parent):
        """This is where all the elements of the marking menu are built."""

        # Radial positioned
        cmds.menuItem(p=menu, l="Open", rp="N", c="import maya.cmds as cmds\ncmds.ramOpen()", i="ramopen.png")
        cmds.menuItem(p=menu, l="Replace", rp="E", c="import maya.cmds as cmds\ncmds.ramOpen(r=True)", i="ramreplace.png")
        cmds.menuItem(p=menu, l="Preview", rp="W", c="import maya.cmds as cmds\ncmds.ramPreview()", i="rampreview.png")
        cmds.menuItem(p=menu, l="Import", rp="NE", c="import maya.cmds as cmds\ncmds.ramOpen(i=True)", i="ramimport.png")
        cmds.menuItem(p=menu, l="Publish", rp="S", c="import maya.cmds as cmds\ncmds.ramSaveVersion( updateStatus=True )", i="ramstatus.png")
        cmds.menuItem(p=menu, l="Incremental Save", rp="SW", c="import maya.cmds as cmds\ncmds.ramSaveVersion( updateStatus=False )", i="ramsaveincremental.png")
        #cmds.menuItem(p=menu, l="Publish Settings", rp="SW", c="import maya.cmds as cmds\ncmds.ramPublishSettings( )", i="rampublishsettings.png")

        # List
        cmds.menuItem(p=menu, l="Ramses App", c="import maya.cmds as cmds\ncmds.ramOpenRamses()", i="ramses.png")
        cmds.menuItem(p=menu, divider=True)
        cmds.menuItem(p=menu, l="Save", c="import maya.cmds as cmds\ncmds.ramSave()", i="ramsave.png")
        cmds.menuItem(p=menu, l="Add Comment", c="import maya.cmds as cmds\ncmds.ramSave( sc=True )", i="ramcomment.png")
        cmds.menuItem(p=menu, l="Incremental Save", c="import maya.cmds as cmds\ncmds.ramSaveVersion( updateStatus=False )", i="ramsaveincremental.png")
        cmds.menuItem(p=menu, l="Set Status", c="import maya.cmds as cmds\ncmds.ramSaveVersion( updateStatus=True )", i="ramstatus.png")
        cmds.menuItem(p=menu, divider=True)
        cmds.menuItem(p=menu, l="Thumbnail / Playblast", c="import maya.cmds as cmds\ncmds.ramPreview()", i="rampreview.png")
        cmds.menuItem(p=menu, divider=True)
        cmds.menuItem(p=menu, l="Save As", c="import maya.cmds as cmds\ncmds.ramSaveAs()", i="ramsaveas.png")
        cmds.menuItem(p=menu, l="Save as template", c="import maya.cmds as cmds\ncmds.ramPublishTemplate()", i="ramtemplate.png")
        cmds.menuItem(p=menu, divider=True)
        cmds.menuItem(p=menu, l="Setup Scene", c="import maya.cmds as cmds\ncmds.ramSetupScene()", i="ramsetupscene.png")
        cmds.menuItem(p=menu, l="Open item", c="import maya.cmds as cmds\ncmds.ramOpen()", i="ramopen.png")
        cmds.menuItem(p=menu, l="Import item", c="import maya.cmds as cmds\ncmds.ramOpen(i=True)", i="ramimport.png")
        cmds.menuItem(p=menu, l="Replace item", c="import maya.cmds as cmds\ncmds.ramOpen(r=True)", i="ramreplace.png")
        cmds.menuItem(p=menu, l="Update", c="import maya.cmds as cmds\ncmds.ramUpdate()", i="ramupdate.png")
        cmds.menuItem(p=menu, l="Restore version", c="import maya.cmds as cmds\ncmds.ramRetrieveVersion()", i="ramretrieve.png")
        cmds.menuItem(p=menu, divider=True)
        cmds.menuItem(p=menu, l="Publish Settings", c="import maya.cmds as cmds\ncmds.ramPublishSettings()", i="rampublishsettings.png")
        cmds.menuItem(p=menu, l="Settings", c="import maya.cmds as cmds\ncmds.ramSettings()", i="ramsettings.png")
