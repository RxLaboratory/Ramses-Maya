# -*- coding: utf-8 -*-
"""A ComboBox for displaying RamObjects"""

try:
    from PySide2 import QtWidgets as qw
    from PySide2 import QtGui as qg
    from PySide2 import QtCore as qc
except:  # pylint: disable=bare-except
    from PySide6 import QtWidgets as qw
    from PySide6 import QtGui as qg
    from PySide6 import QtCore as qc

import ramses as ram
RAMSES = ram.Ramses.instance()

class RamObjectBox( qw.QComboBox ):
    """A ComboBox for displaying RamObjects"""
    def __init__(self, parent = None):
        super(RamObjectBox,self).__init__(parent)
        self.currentIndexChanged.connect( self.indexChanged )

    @qc.Slot()
    def indexChanged(self, i):
        """Sets the color of the box"""
        color = qg.QColor( 93, 93, 93 )
        pal = self.palette()

        obj = self.itemData(i)
        if obj:
            colorName = self.itemData(i).colorName()
            color = qg.QColor( colorName )

        # adjust Lightness
        if color.lightness() > 120:
            color.setHsl( color.hue(), color.saturation(), 120)

        pal.setColor(QPalette.Button, color)
        self.setPalette(pal)

    def setObject(self, ramObject):
        """Sets the current ramobject"""
        i = 0
        while i < self.count():
            if self.itemData( i ) == ramObject:
                self.setCurrentIndex( i )
                return
            i = i+1

    def getObject(self):
        """Gets the current ramobject"""
        return self.itemData( self.currentIndex() )
