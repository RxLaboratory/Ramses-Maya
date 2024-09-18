# -*- coding: utf-8 -*-
"""
A ComboBox for selecting steps
"""

try:
    from PySide2 import QtWidgets as qw
    from PySide2 import QtCore as qc
except:  # pylint: disable=bare-except
    from PySide6 import QtWidgets as qw
    from PySide6 import QtCore as qc

from ramses import RamStep

class StepComboBox(qw.QComboBox):
    """
    A ComboBox for selecting steps
    """
    # <== CONSTRUCTOR ==>

    def __init__(self, parent=None): # pylint: disable=useless-super-delegation
        super(StepComboBox, self).__init__(parent)

    # <== PUBLIC ==>

    def set_steps(self, steps):
        """Sets the list of steps"""

        self.clear()
        for step in steps:
            self.addItem(str(step), step)

    def current_step(self):
        return self.currentData()

    @qc.Slot()
    def set_step(self, step):
        if isinstance(step, RamStep):
            for i in range(self.count()):
                if self.itemData(i, qc.Qt.UserRole) == step:
                    self.setCurrentIndex(i)
                    return
        else:
            for i in range(self.count()):
                if self.itemData(i, qc.Qt.UserRole).shortName() == step:
                    self.setCurrentIndex(i)
                    return
        return None
