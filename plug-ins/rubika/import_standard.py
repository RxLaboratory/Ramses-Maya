# -*- coding: utf-8 -*-

import re, os
import maya.cmds as cmds # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
from .utils_attributes import * # pylint: disable=import-error
from .utils_import import *

def importStandard( item, filePath, step):
    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Importing scene...")
    progressDialog.setMaximum(2)
    progressDialog.increment()

    nodes = importFile( item, filePath, step, progressDialog)

    progressDialog.close()

    return nodes