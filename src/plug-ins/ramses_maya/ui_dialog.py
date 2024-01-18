# -*- coding: utf-8 -*-
"""
The default Dialog
"""

import os
import yaml
from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module,import-error
    QDialog,
    QMenuBar,
    QVBoxLayout,
    QFileDialog,
    QApplication
)
from PySide2.QtGui import (  # pylint: disable=no-name-in-module
    QKeySequence,
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot
)
from ramses_maya.utils import (
    open_help,
    about_ramses,
    open_api_reference
)
from ramses_maya.ui_about import AboutDialog
from dumaf.utils import checkUpdate
from ramses_maya.utils import donate

class Dialog(QDialog):
    """
    The default Dialog
    """

    def __init__(self, parent=None): # pylint: disable=useless-super-delegation
        super(Dialog, self).__init__(parent)

        # <-- Setup -->
        self.__dialog_setup_ui()
        self.__dialog_setup_menu()
        self.__dialog_connect_events()
        self.__preset_folder = ""

    # <== PRIVATE METHODS ==>

    def __dialog_setup_menu(self):
        self.edit_menu = self.__ui_menu_bar.addMenu("Edit")

        help_menu = self.__ui_menu_bar.addMenu("Help")
        self.__help_action = help_menu.addAction("Ramses Maya Add-on help...")
        self.__about_ramses_action = help_menu.addAction("Ramses general help...")
        self.__api_reference_action = help_menu.addAction("Ramses API reference...")
        help_menu.addSeparator()
        self.__update_action = help_menu.addAction("Check for update")
        self.__donate_action = help_menu.addAction("Donate...")
        help_menu.addSeparator()
        self.__about_qt_action = help_menu.addAction("About Qt...")
        self.__about_action = help_menu.addAction("About...")
        self.__help_action.setShortcut(QKeySequence("F1"))

    def __dialog_setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(6,0,6,6)
        self.main_layout.setSpacing(6)
        self.setLayout(self.main_layout)

        self.__ui_menu_bar = QMenuBar()
        self.main_layout.addWidget(self.__ui_menu_bar)

        self.__ui_about_dialog = AboutDialog(self)

    def __dialog_connect_events(self):
        # menu
        self.__help_action.triggered.connect( open_help )
        self.__about_ramses_action.triggered.connect( about_ramses )
        self.__api_reference_action.triggered.connect( open_api_reference )
        self.__update_action.triggered.connect( self.check_update )
        self.__about_qt_action.triggered.connect( self.show_about_qt )
        self.__about_action.triggered.connect( self.show_about )
        self.__donate_action.triggered.connect( donate )

    # <== PROTECTED METHODS ==>

    def _dialog_add_preset_actions(self):
        self.__save_preset_action = self.edit_menu.addAction("Save preset...")
        self.__load_preset_action = self.edit_menu.addAction("Load preset...")
        self.__save_preset_action.setShortcut(QKeySequence("Ctrl+S"))
        self.__load_preset_action.setShortcut(QKeySequence("Ctrl+O"))
        self.__load_preset_action.triggered.connect( self.load_preset )
        self.__save_preset_action.triggered.connect( self.save_preset )

    # <== PUBLIC METHODS ==>

    @Slot()
    def show_about(self):
        """Shows the about dialog for the module"""
        self.__ui_about_dialog.exec_()

    @Slot()
    def show_about_qt(self):
        """Shows the about dialog for the module"""
        QApplication.aboutQt()

    def load_preset_file(self, file_path):
        """Loads a preset file"""
        if not os.path.isfile(file_path):
            return

        with open(file_path, 'r', encoding='utf-8') as preset_file:
            options = yaml.safe_load(preset_file.read())
            if options:
                self.set_options(options)

    def set_options(self, options):
        """Loads the options. This is a virtual method"""
        pass

    def get_options(self):
        """Returns the options as a dict. This is a virtual method"""
        pass

    @Slot()
    def load_preset(self):
        """Prompts the user to select a preset file to load"""
        open_file = QFileDialog.getOpenFileName(self, "OPen publish settings preset...", self.__preset_folder, "Yaml (*.yml *.yaml)")[0]
        if open_file != "":
            self.load_preset_file(open_file)

    @Slot()
    def save_preset(self):
        """Saves the current options as a preset file"""
        save_file = QFileDialog.getSaveFileName(self, "Save current publish settings as preset...", self.__preset_folder, "Yaml (*.yml *.yaml)")[0]
        if save_file != "":
            options = self.get_options()
            with open(save_file, "w", encoding='utf-8') as preset_file:
                yaml.dump(options, preset_file)

        self.set_preset_folder()

    def set_preset_folder(self, folder_path=""):
        """Sets the default folder for loading/saving presets"""

        if folder_path != "" and os.path.isdir(folder_path):
            self.__preset_folder = folder_path

        # List files in the folder
        preset_files = []

        for file_name in os.listdir(self.__preset_folder):
            ext = os.path.splitext(file_name)[1].lower()
            if ext == ".yaml" or ext == ".yml":
                preset_files.append(self.__preset_folder + file_name)

        self.update_preset_files(preset_files)

    def update_preset_files(self, preset_files):
        """Loads the preset files.
        This is a virtual function."""
        pass

    def get_preset(self):
        """Returns the current options as a string"""
        options = self.get_options()
        return yaml.dump(options)

    def check_update(self):
        """Checks if an update is available"""
        from ramses_maya import TOOL_NAME, VERSION, IS_PRERELEASE
        checkUpdate( TOOL_NAME, VERSION, discreet=False, preRelease=IS_PRERELEASE )

if __name__ == "__main__":
    d = Dialog()
    d.exec_()
