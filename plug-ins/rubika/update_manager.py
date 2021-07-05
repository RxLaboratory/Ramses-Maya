# -*- coding: utf-8 -*-

from .ui_update import UpdateDialog
from .utils_attributes import * # pylint: disable=import-error
import dumaf as maf

from .update_geo import updateGeo

def updateRamsesItems():
    updateDialog = UpdateDialog(maf.getMayaWindow())
    result = updateDialog.exec_() 
    if result == 0:
        return
    nodes = []
    if result == 1:
        nodes = updateDialog.getAllNodes()
    else:
        nodes = updateDialog.getSelectedNodes()

    for node in nodes:
        geoFile = getRamsesAttr(node, RamsesAttribute.GEO_FILE)
        if geoFile:
            updateGeo( node )
