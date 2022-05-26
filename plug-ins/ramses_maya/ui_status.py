# -*- coding: utf-8 -*-
"""The UI for changing the scene status/publishing"""

from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QLabel,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QComboBox,
    QSlider,
    QSpinBox,
    QTextEdit,
    QPushButton,
    QCheckBox,
)
from PySide2.QtGui import (  # pylint: disable=no-name-in-module
    QColor,
    QPalette,
    )
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot,
    Qt
)

import ramses as ram
RAMSES = ram.Ramses.instance()

class StateBox( QComboBox ):
    """A Combobox to show states, whcih changes color according to the state"""
    def __init__(self, parent = None):
        super(StateBox,self).__init__(parent)

        # Populate states from Ramses
        for state in RAMSES.states():
            self.addItem( state.shortName(), state.color() )

        self.setState( RAMSES.defaultState )
        self.currentIndexChanged.connect( self.indexChanged )

    @Slot()
    def indexChanged(self, i):
        color = self.itemData(i)
        color = QColor.fromRgb( color[0], color[1], color[2] )
        pal = self.palette()
        pal.setColor(QPalette.Button, color)
        self.setPalette(pal)

    def setState(self, state):
        i = 0
        while i < self.count():
            if self.itemText( i ) == state.shortName():
                self.setCurrentIndex( i )
                return
            i = i+1

    def getState(self):
        return RAMSES.state( self.currentText() )

class StatusDialog( QDialog ):
    """The Dialog for editing the status"""

    def __init__(self, parent = None):
        super(StatusDialog,self).__init__(parent)
        self.__setup_ui()
        self.__conect_evenhts()

    def __setup_ui(self):
        self.setWindowTitle( "Incremental Save: Update Status" )
        self.setMinimumWidth( 400 )

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(6,6,6,6)
        main_layout.setSpacing(3)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(3)

        self.__ui_state_box = StateBox()
        top_layout.addWidget( self.__ui_state_box )

        self.__ui_completion_slider = QSlider( Qt.Horizontal )
        self.__ui_completion_slider.setMaximum(100)
        top_layout.addWidget( self.__ui_completion_slider )
        self.__ui_completion_box = QSpinBox( )
        self.__ui_completion_box.setMinimum( 0 )
        self.__ui_completion_box.setMaximum( 100 )
        self.__ui_completion_box.setSuffix( "%" )
        top_layout.addWidget( self.__ui_completion_box )

        main_layout.addLayout( top_layout )

        options_layout = QFormLayout()
        options_layout.setFieldGrowthPolicy( QFormLayout.AllNonFixedFieldsGrow )
        options_layout.setSpacing(3)

        self.__ui_publish_box = QCheckBox("Publish the current scene.")
        options_layout.addRow( "Publication:", self.__ui_publish_box )

        self.__ui_publish_settings_box = QCheckBox("Edit publish settings.")
        self.__ui_publish_settings_box.setEnabled(False)
        options_layout.addRow( "", self.__ui_publish_settings_box )

        self.__ui_preview_box = QCheckBox("Create preview files (thumbnail or playblast).")
        options_layout.addRow( "Preview:", self.__ui_preview_box )

        self.__ui_comment_label = QLabel("Comment:")
        self.__ui_comment_edit = QTextEdit()
        options_layout.addRow( self.__ui_comment_label, self.__ui_comment_edit )

        main_layout.addLayout( options_layout )

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(2)

        self.__ui_save_button = QPushButton("Update Status and Save")
        buttons_layout.addWidget( self.__ui_save_button )
        self.__ui_skip_button = QPushButton("Skip and just Save")
        buttons_layout.addWidget( self.__ui_skip_button )
        self.__ui_cancel_button = QPushButton("Cancel")
        buttons_layout.addWidget( self.__ui_cancel_button )

        main_layout.addLayout( buttons_layout )

        self.setLayout( main_layout )

    def __conect_evenhts(self):
        self.__ui_completion_slider.valueChanged.connect( self.__ui_completion_box.setValue )
        self.__ui_completion_box.valueChanged.connect( self.__ui_completion_slider.setValue )
        self.__ui_state_box.currentTextChanged.connect(self.stateChanged )
        self.__ui_save_button.clicked.connect( self.accept )
        self.__ui_cancel_button.clicked.connect( self.reject )
        self.__ui_skip_button.clicked.connect( self.skip )
        self.__ui_publish_box.clicked[bool].connect( self.__ui_publish_settings_box.setEnabled )

    def stateChanged(self, s):
        state = RAMSES.state( s )
        self.__ui_completion_box.setValue( state.completionRatio() )

    def setStatus( self, status):
        self.__ui_state_box.setState( status.state )
        self.__ui_completion_box.setValue( status.completionRatio )
        self.__ui_comment_edit.setPlainText( status.comment )

    def getState(self):
        return self.__ui_state_box.getState()

    def getCompletionRatio(self):
        return self.__ui_completion_box.value()

    def getComment(self):
        return self.__ui_comment_edit.toPlainText()

    def publish(self):
        """Checks if the scene has to be published"""
        return self.__ui_publish_box.isChecked()

    def edit_publish_settings(self):
        """Checks if the publish settings have to be edited"""
        return self.__ui_publish_settings_box.isChecked()

    def skip(self):
        self.done(2)

    def setOffline(self, offline):
        online = not offline
        self.__ui_completion_slider.setVisible(online)
        self.__ui_completion_box.setVisible(online)
        self.__ui_comment_edit.setVisible(online)
        self.__ui_comment_label.setVisible(online)

    def setPublish(self, pub=True):
        self.__ui_publish_box.setChecked(pub)

    def preview(self):
        return self.__ui_preview_box.isChecked()

if __name__ == '__main__':
    statusDialog = StatusDialog()
    ok = statusDialog.exec_()
    print(ok)
