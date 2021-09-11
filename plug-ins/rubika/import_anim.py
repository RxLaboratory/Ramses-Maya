# -*- coding: utf-8 -*-

import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_attributes import * # pylint: disable=import-error
from .utils_constants import *
from .ui_import_anim import ImportAnimDialog
from .import_geo import *

def importAnim( item, filePath, step ):
    
    dialog = ImportAnimDialog(maf.UI.getMayaWindow())
    if not dialog.exec_():
        return

    removeRigs = dialog.removeRig()

    # Just import as any Geo
    rootCtrls = importGeo( item, filePath, step )

    if removeRigs:
        newRootCtrls = []
        for rootCtrl in rootCtrls:
            # remove corresponding rig if any (and move the root to the same parent node)
            currentAssetName = rootCtrl.split('|')[-1].split(':')[-1].split('_')[0]
            ramsesNodes = listRamsesNodes()
            for node in ramsesNodes:
                newRootCtrls.append(rootCtrl)
                step = getRamsesAttr(node, RamsesAttribute.STEP)
                if not step: continue
                if step != RIG_STEP.shortName():  continue
                itemName = getRamsesAttr(node, RamsesAttribute.ITEM)
                if not itemName: continue
                if itemName == currentAssetName:
                    # Re-parent
                    p = cmds.listRelatives( node, parent=True, f=True, type='transform')
                    if p is not None: rootCtrl = maf.Node.parent( rootCtrl, p[0] )
                    maf.Node.delete( node )
                newRootCtrls.append(rootCtrl)

    return rootCtrls