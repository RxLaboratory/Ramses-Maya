# -*- coding: utf-8 -*-

import os
from PySide2.QtGui import ( # pylint: disable=no-name-in-module,import-error
    QIcon
)

# Some paths we need
modPath = os.path.dirname(os.path.realpath(__file__))
pluginPath = os.path.dirname(modPath)
iconPath = os.path.dirname(pluginPath) + "/icons/"

def icon(name):
    return QIcon(iconPath + name + ".png")