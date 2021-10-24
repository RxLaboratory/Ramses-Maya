# -*- coding: utf-8 -*-

import re, os
import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_attributes import * # pylint: disable=import-error
from .utils_import import *

def importRig( item, rigFile, step):
    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Referencing Rig...")
    progressDialog.setMaximum(2)

    rootNodes = importFile( item, rigFile, step, progressDialog, reference=True, lockTransform=False )

    progressDialog.close()

    return rootNodes