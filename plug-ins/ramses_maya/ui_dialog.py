# -*- coding: utf-8 -*-
"""
The default Dialog
"""

from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module,import-error
    QDialog,
    QMenuBar,
    QVBoxLayout
)
from PySide2.QtGui import (  # pylint: disable=no-name-in-module
    QKeySequence,
)
from .utils import (
    open_help,
    about_ramses,
    open_api_reference
)

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

    # <== PRIVATE METHODS ==>

    def __dialog_setup_menu(self):
        self.edit_menu = self.__ui_menu_bar.addMenu("Edit")

        help_menu = self.__ui_menu_bar.addMenu("Help")
        self.__help_action = help_menu.addAction("Ramses Maya Add-on help...")
        self.__about_ramses_action = help_menu.addAction("Ramses general help...")
        self.__api_reference_action = help_menu.addAction("Ramses API reference...")
        self.__help_action.setShortcut(QKeySequence("F1"))

    def __dialog_setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(6,0,6,6)
        self.main_layout.setSpacing(6)
        self.setLayout(self.main_layout)

        self.__ui_menu_bar = QMenuBar()
        self.main_layout.addWidget(self.__ui_menu_bar)

    def __dialog_connect_events(self):
        # menu
        self.__help_action.triggered.connect( open_help )
        self.__about_ramses_action.triggered.connect( about_ramses )
        self.__api_reference_action.triggered.connect( open_api_reference )
