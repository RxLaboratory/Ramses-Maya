# -*- coding: utf-8 -*-
"""Some general utilitary stuff"""

import os
from PySide2.QtGui import ( # pylint: disable=no-name-in-module,import-error
    QIcon,
    QDesktopServices
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot,
    QUrl
)

from ramses import RamSettings
SETTINGS = RamSettings.instance()

# Some paths we need
MODULE_PATH = os.path.dirname(os.path.realpath(__file__))
PLUGIN_PATH = os.path.dirname(MODULE_PATH)
ICON_PATH = os.path.dirname(PLUGIN_PATH) + "/icons/"
PUBLISH_PRESETS_PATH = os.path.dirname(PLUGIN_PATH) + "/publish_presets/"

def icon(name):
    """Gest QIcon for an icon from its name (without extension)"""
    return QIcon(ICON_PATH + name + ".png")

@Slot()
def open_help():
    """Opens the online help for the addon"""
    QDesktopServices.openUrl( QUrl( SETTINGS.addonsHelpUrl ) )

@Slot()
def about_ramses():
    """Opens the web page about Ramses"""
    QDesktopServices.openUrl( QUrl( SETTINGS.generalHelpUrl ) )

@Slot()
def open_api_reference():
    """Opens the online API reference"""
    QDesktopServices.openUrl( QUrl( SETTINGS.apiReferenceUrl ) )