# -*- coding: utf-8 -*-
"""Some general utilitary stuff"""

import os

try:
    from PySide2 import QtGui as qg
    from PySide2 import QtCore as qc
except:  # pylint: disable=bare-except
    from PySide6 import QtGui as qg
    from PySide6 import QtCore as qc

from maya import cmds # pylint: disable=import-error
import dumaf as maf

# Some paths we need
MODULE_PATH = os.path.dirname(os.path.realpath(__file__))
PLUGIN_PATH = os.path.dirname(MODULE_PATH)
ICON_PATH = os.path.dirname(PLUGIN_PATH) + "/icons/"
PUBLISH_PRESETS_PATH = os.path.dirname(PLUGIN_PATH) + "/publish_presets/"
IMPORT_PRESETS_PATH = os.path.dirname(PLUGIN_PATH) + "/import_presets/"

def icon(name):
    """Gets qg.QIcon for an icon from its name (without extension)"""
    return qg.QIcon(ICON_PATH + name + ".png")

@qc.Slot()
def open_help():
    """Opens the online help for the addon"""
    qg.QDesktopServices.openUrl( qc.QUrl( "https://ramses.rxlab.guide/components/addons/maya" ) )

@qc.Slot()
def about_ramses():
    """Opens the web page about Ramses"""
    qg.QDesktopServices.openUrl( qc.QUrl( "https://rxlaboratory.org/tools/ramses" ) )

@qc.Slot()
def donate():
    """Opens the donation page"""
    qg.QDesktopServices.openUrl( qc.QUrl( "http://donate.rxlab.info" ) )

@qc.Slot()
def open_api_reference():
    """Opens the online API reference"""
    qg.QDesktopServices.openUrl( qc.QUrl( "https://ramses.rxlab.guide/dev/add-ons-reference/" ) )

def end_process(temp_data, progress_dialog):
    """Ends a process on the scene (closes and removes the temp file)"""

    # Re-Open initial scene
    cmds.file(temp_data[1],o=True,f=True)

    # Remove temp file
    if os.path.isfile(temp_data[0]):
        os.remove(temp_data[0])

    if progress_dialog:
        progress_dialog.hide()

def getVideoPlayer():
    """Gets the video player to use when playblasting"""
    default = os.path.dirname( cmds.pluginInfo('Ramses', query=True, path=True) )
    default = default + '/../bin/ffplay.exe'
    current = maf.options.get('dublast.videoPlayer', default)
    if current == "":
        current = default
    return current
