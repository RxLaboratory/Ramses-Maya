# -*- coding: utf-8 -*-
"""
The UI for publishing scenes
"""

import os


try:
    from PySide2 import QtWidgets as qw
    from PySide2 import QtCore as qc
except:  # pylint: disable=bare-except
    from PySide6 import QtWidgets as qw
    from PySide6 import QtCore as qc

import yaml
from dumaf import Node
from .utils import (
    PUBLISH_PRESETS_PATH,
)
from .ui_dialog import Dialog
from .utils_options import (
    load_bool_preset,
    load_enum_preset,
    load_number_preset
)
from .ui_stepComboBox import StepComboBox

# NOTE
# formats to implement: abc, ma, mb, ma shaders, mb shaders, ass

class NoEditDelegate(qw.QStyledItemDelegate):
    """
    A delegate to be able to edit only the second column of the Nodes tree view
    """
    def __init__(self, parent=None): # pylint: disable=useless-super-delegation
        super(NoEditDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index): # pylint: disable=unused-argument,invalid-name
        """Overrides qw.QStyledItemDelegate.createEditor"""
        return 0

class PublishDialog(Dialog):
    """
    The Main Dialog to publish the scene
    """
    # <== CONSTRUCTOR ==>

    def __init__(self, parent=None): # pylint: disable=useless-super-delegation
        super(PublishDialog, self).__init__(parent)
        # <-- Setup -->
        self.__setup_ui()
        self._dialog_add_preset_actions()
        self.__connect_events()
        self.set_preset_folder(PUBLISH_PRESETS_PATH)
        self.__ui_preset_box.setCurrentIndex(-1)
        self.__update_preset()

    # <== PRIVATE METHODS ==>

    def __setup_ui(self):
        self.setWindowTitle("Publish scene")
        self.setMinimumWidth( 700 )

        content_layout = qw.QHBoxLayout()
        self.main_layout.addLayout(content_layout)
        content_layout.setSpacing(3)

        self.__ui_sections_box = qw.QListWidget()
        self.__ui_sections_box.addItem("Select: Format")
        self.__ui_sections_box.addItem("Select: Nodes")
        self.__ui_sections_box.addItem("Pre-Publish: Settings")
        self.__ui_sections_box.addItem("Publish: Maya scene")
        self.__ui_sections_box.addItem("Publish: Maya scene - shaders")
        self.__ui_sections_box.addItem("Publish: Alembic")
        self.__ui_sections_box.addItem("Publish: OBJ")
        self.__ui_sections_box.item(4).setHidden(True)
        self.__ui_sections_box.item(5).setHidden(True)
        self.__ui_sections_box.item(6).setHidden(True)
        self.__ui_sections_box.setMaximumWidth( 150 )
        content_layout.addWidget(self.__ui_sections_box)

        self.__ui_stacked_layout = qw.QStackedLayout()
        content_layout.addLayout(self.__ui_stacked_layout)

        # <-- PRESET -->

        preset_widget = qw.QWidget()
        preset_layout = qw.QVBoxLayout(preset_widget)
        preset_layout.setSpacing(3)
        preset_layout.setContentsMargins(3,3,3,3)
        content_layout.addWidget(preset_widget)

        preset_label = qw.QLabel("You can use this preset in Ramses to set\nthe current settings as default settings for steps.")
        preset_layout.addWidget(preset_label)
        self.__ui_preset_edit = qw.QTextEdit()
        self.__ui_preset_edit.setReadOnly(True)
        preset_layout.addWidget(self.__ui_preset_edit)

        # <-- BOTTOM BUTTONS -->
        buttons_layout = qw.QHBoxLayout()
        buttons_layout.setSpacing(2)
        self.main_layout.addLayout(buttons_layout)

        self.__ui_publish_button = qw.QPushButton("Publish Scene")
        buttons_layout.addWidget( self.__ui_publish_button )
        self.__ui_cancel_button = qw.QPushButton("Cancel")
        buttons_layout.addWidget( self.__ui_cancel_button )

        # <-- GENERAL -->

        general_widget = qw.QWidget()
        self.__ui_stacked_layout.addWidget(general_widget)
        general_layout = qw.QFormLayout(general_widget)
        general_layout.setFormAlignment(qc.Qt.AlignHCenter | qc.Qt.AlignTop)
        general_layout.setSpacing(3)

        self.__ui_step_box = StepComboBox()
        self.__ui_step_label = qw.QLabel("Step:")
        self.__ui_step_box.hide()
        self.__ui_step_label.hide()
        general_layout.addRow(self.__ui_step_label, self.__ui_step_box)

        self.__ui_preset_box = qw.QComboBox()
        general_layout.addRow("Preset:", self.__ui_preset_box)

        format_widget = qw.QWidget()
        format_layout = qw.QVBoxLayout(format_widget)
        format_layout.setSpacing(3)
        format_layout.setContentsMargins(3,3,3,3)
        general_layout.addRow("Format:", format_widget)

        self.__ui_maya_scene_box = qw.QCheckBox("Maya scene (ma/mb)")
        self.__ui_maya_scene_box.setChecked(True)
        format_layout.addWidget(self.__ui_maya_scene_box)
        self.__ui_maya_shaders_box = qw.QCheckBox("Maya scene, shaders only (ma/mb)")
        format_layout.addWidget(self.__ui_maya_shaders_box)
        self.__ui_alembic_box = qw.QCheckBox("Alembic (abc)")
        format_layout.addWidget(self.__ui_alembic_box)
        self.__ui_arnold_scene_source_box = qw.QCheckBox("Arnold scene source (ass)")
        format_layout.addWidget(self.__ui_arnold_scene_source_box)
        self.__ui_obj_box = qw.QCheckBox("OBJ")
        format_layout.addWidget(self.__ui_obj_box)

        # <-- Nodes -->

        nodes_widget = qw.QWidget()
        nodes_layout = qw.QVBoxLayout(nodes_widget)
        nodes_layout.setContentsMargins(0,0,0,0)
        nodes_layout.setSpacing(3)
        self.__ui_stacked_layout.addWidget( nodes_widget )

        self.__ui_nodes_tree = qw.QTreeWidget()
        self.__ui_nodes_tree.setHeaderLabels(("Node", "Publish name"))
        self.__ui_nodes_tree.setSelectionMode(qw.QAbstractItemView.MultiSelection)
        self.__ui_nodes_tree.setItemDelegateForColumn(0, NoEditDelegate())
        nodes_layout.addWidget(self.__ui_nodes_tree)

        nodes_buttons_layout = qw.QHBoxLayout()
        nodes_buttons_layout.setSpacing(3)
        nodes_layout.addLayout(nodes_buttons_layout)
        self.__ui_select_no_nodes = qw.QPushButton("Select none")
        nodes_buttons_layout.addWidget( self.__ui_select_no_nodes )
        self.__ui_select_all_nodes = qw.QPushButton("Select all")
        nodes_buttons_layout.addWidget( self.__ui_select_all_nodes )

        # <-- PRE-PUBLISH -->

        pre_publish_widget = qw.QWidget()
        pre_publish_vlayout = qw.QVBoxLayout(pre_publish_widget)
        pre_publish_vlayout.setSpacing(3)
        self.__ui_stacked_layout.addWidget( pre_publish_widget )

        pre_publish_layout = qw.QFormLayout()
        pre_publish_layout.setSpacing(3)
        pre_publish_layout.setFormAlignment(qc.Qt.AlignHCenter | qc.Qt.AlignTop)
        pre_publish_vlayout.addLayout(pre_publish_layout)

        self.__ui_import_references_box = qw.QCheckBox("Import references")
        pre_publish_layout.addRow("Clean:", self.__ui_import_references_box)

        self.__ui_remove_namespaces_box = qw.QCheckBox("Remove namespaces")
        pre_publish_layout.addRow("", self.__ui_remove_namespaces_box)

        self.__ui_remove_hidden_nodes_box = qw.QCheckBox("Remove hidden nodes")
        pre_publish_layout.addRow("", self.__ui_remove_hidden_nodes_box)

        self.__ui_delete_history_box = qw.QCheckBox("Delete node history")
        pre_publish_layout.addRow("", self.__ui_delete_history_box)

        self.__ui_remove_extra_shapes_box = qw.QCheckBox("Remove extra shapes")
        pre_publish_layout.addRow("", self.__ui_remove_extra_shapes_box)

        self.__ui_remove_empty_groups_box = qw.QCheckBox("Remove empty groups")
        pre_publish_layout.addRow("", self.__ui_remove_empty_groups_box)

        self.__ui_remove_animation_box = qw.QCheckBox("Remove animation")
        pre_publish_layout.addRow("", self.__ui_remove_animation_box)

        self.__ui_types_box = qw.QComboBox()
        self.__ui_types_box.addItem("Keep", "keep")
        self.__ui_types_box.addItem("Remove", "remove")
        pre_publish_layout.addRow("Types:", self.__ui_types_box)

        self.__ui_types_edit = qw.QTextEdit()
        self.__ui_types_edit.setPlainText("locator\nbezierCurve\nnurbsCurve\nnurbsSurface")
        self.__ui_types_edit.setMaximumHeight(100)
        pre_publish_layout.addRow("", self.__ui_types_edit)

        self.__ui_freeze_transform_box = qw.QCheckBox("")
        pre_publish_layout.addRow("Freeze transformations", self.__ui_freeze_transform_box)

        self.__ui_freeze_white_list_widget = qw.QWidget()
        freeze_white_list_layout = qw.QVBoxLayout(self.__ui_freeze_white_list_widget)
        freeze_white_list_layout.setContentsMargins(0,0,0,0)
        freeze_white_list_layout.setSpacing(3)
        freeze_white_list_label = qw.QLabel("Ignore names containing:")
        freeze_white_list_layout.addWidget(freeze_white_list_label)
        self.__ui_freeze_white_list_edit = qw.QLineEdit("_eye_, _eyes_")
        freeze_white_list_layout.addWidget( self.__ui_freeze_white_list_edit )
        self.__ui_freeze_white_list_case_box = qw.QCheckBox("Case sensitive")
        freeze_white_list_layout.addWidget(self.__ui_freeze_white_list_case_box )
        pre_publish_layout.addRow("", self.__ui_freeze_white_list_widget)

        # <-- Maya Scene -->

        maya_widget = qw.QWidget()
        maya_vlayout = qw.QVBoxLayout(maya_widget)
        maya_vlayout.setSpacing(3)
        self.__ui_stacked_layout.addWidget( maya_widget )

        maya_layout = qw.QFormLayout()
        maya_layout.setSpacing(3)
        maya_layout.setFormAlignment(qc.Qt.AlignHCenter | qc.Qt.AlignTop)
        maya_vlayout.addLayout(maya_layout)

        self.__ui_maya_format_box = qw.QComboBox()
        self.__ui_maya_format_box.addItem("Maya Binary (mb)", "mb")
        self.__ui_maya_format_box.addItem("Maya ASCII (ma)", "ma")
        maya_layout.addRow("Format:", self.__ui_maya_format_box )

        self.__ui_maya_hidden_nodes_box = qw.QCheckBox("Lock visibility")
        maya_layout.addRow("Hidden nodes:", self.__ui_maya_hidden_nodes_box)

        self.__ui_maya_lock_transform_box = qw.QCheckBox("Lock transformations")
        maya_layout.addRow("Node transform:", self.__ui_maya_lock_transform_box)

        self.__ui_maya_hide_joints_box = qw.QComboBox()
        self.__ui_maya_hide_joints_box.addItem("Disable draw", "disable")
        self.__ui_maya_hide_joints_box.addItem("Hide", "hide")
        self.__ui_maya_hide_joints_box.addItem("Hide and lock visibility", "lock")
        self.__ui_maya_hide_joints_box.addItem("Keep", "keep")
        maya_layout.addRow("Joints:", self.__ui_maya_hide_joints_box)

        # <-- Maya Shaders -->

        shaders_widget = qw.QWidget()
        shaders_vlayout = qw.QVBoxLayout(shaders_widget)
        shaders_vlayout.setSpacing(3)
        self.__ui_stacked_layout.addWidget( shaders_widget )
        shaders_layout = qw.QFormLayout()
        shaders_layout.setFormAlignment(qc.Qt.AlignHCenter | qc.Qt.AlignTop)
        shaders_layout.setSpacing(3)
        shaders_vlayout.addLayout(shaders_layout)

        self.__ui_shaders_format_box = qw.QComboBox()
        self.__ui_shaders_format_box.addItem("Maya Binary (mb)", "mb")
        self.__ui_shaders_format_box.addItem("Maya ASCII (ma)", "ma")
        shaders_layout.addRow("Format:", self.__ui_shaders_format_box )

        # <-- Alembic -->

        alembic_widget = qw.QWidget()
        alembic_vlayout = qw.QVBoxLayout(alembic_widget)
        alembic_vlayout.setSpacing(3)
        self.__ui_stacked_layout.addWidget( alembic_widget )
        alembic_layout = qw.QFormLayout()
        alembic_layout.setFormAlignment(qc.Qt.AlignHCenter | qc.Qt.AlignTop)
        alembic_layout.setSpacing(3)
        alembic_vlayout.addLayout(alembic_layout)

        self.__ui_alembic_renderable_box = qw.QCheckBox("Renderable only")
        alembic_layout.addRow("Export:", self.__ui_alembic_renderable_box)

        self.__ui_alembic_worldSpace_box = qw.QCheckBox("World space")
        alembic_layout.addRow("", self.__ui_alembic_worldSpace_box)

        self.__ui_alembic_handles_widget = qw.QWidget()
        handles_layout = qw.QHBoxLayout(self.__ui_alembic_handles_widget)
        handles_layout.setContentsMargins(0,0,0,0)
        handles_layout.setSpacing(3)
        self.__ui_alembic_handle_start_box = qw.QSpinBox()
        self.__ui_alembic_handle_start_box.setMinimum(0)
        self.__ui_alembic_handle_start_box.setMaximum(10000)
        self.__ui_alembic_handle_start_box.setPrefix("-")
        handles_layout.addWidget( self.__ui_alembic_handle_start_box)
        self.__ui_alembic_handle_start_box.setValue( 0 )
        self.__ui_alembic_handle_end_box = qw.QSpinBox()
        self.__ui_alembic_handle_end_box.setMinimum(0)
        self.__ui_alembic_handle_end_box.setMaximum(10000)
        self.__ui_alembic_handle_end_box.setPrefix("+")
        handles_layout.addWidget( self.__ui_alembic_handle_end_box)
        alembic_layout.addRow("Handles:", self.__ui_alembic_handles_widget)

        self.__ui_alembic_frame_step_box = qw.QDoubleSpinBox()
        self.__ui_alembic_frame_step_box.setMinimum(0.1)
        self.__ui_alembic_frame_step_box.setMaximum( 100 )
        self.__ui_alembic_frame_step_box.setDecimals(1)
        alembic_layout.addRow("Frame step:", self.__ui_alembic_frame_step_box)

        self.__ui_alembic_filter_euler_box = qw.QCheckBox("Filter Euler rotations")
        alembic_layout.addRow("Rotations:", self.__ui_alembic_filter_euler_box)

        self.__ui_abc_custom_attr_box = qw.QCheckBox("Automatically add all custom/extra attributes")
        alembic_layout.addRow("Custom Attributes:", self.__ui_abc_custom_attr_box)

        self.__ui_abc_attr_edit = qw.QTextEdit()
        self.__ui_abc_attr_edit.setPlaceholderText("Add all the attributes with these exact names.\nOne attribute per line.")
        self.__ui_abc_attr_edit.setMaximumHeight(100)
        alembic_layout.addRow("Attributes:", self.__ui_abc_attr_edit)

        self.__ui_abc_prefix_edit = qw.QTextEdit()
        self.__ui_abc_prefix_edit.setPlaceholderText("Add all the attributes with these prefix in their names.\nOne prefix per line.")
        self.__ui_abc_prefix_edit.setMaximumHeight(100)
        alembic_layout.addRow("Attributes prefix:", self.__ui_abc_prefix_edit)

        # <-- OBJ -->

        obj_widget = qw.QWidget()
        obj_vlayout = qw.QVBoxLayout(obj_widget)
        obj_vlayout.setSpacing(3)
        self.__ui_stacked_layout.addWidget( obj_widget )
        obj_layout = qw.QFormLayout()
        obj_layout.setFormAlignment(qc.Qt.AlignHCenter | qc.Qt.AlignTop)
        obj_layout.setSpacing(3)
        obj_vlayout.addLayout(obj_layout)

        self.__ui_obj_mtl_box = qw.QCheckBox("Materials (.mtl)")
        obj_layout.addRow("Export:", self.__ui_obj_mtl_box)

    def __connect_events(self):
        self.__ui_sections_box.currentRowChanged.connect( self.__ui_stacked_layout.setCurrentIndex )
        self.__ui_publish_button.clicked.connect( self.__ui_publish_button_clicked )
        self.__ui_cancel_button.clicked.connect( self.__ui_cancel_button_clicked )
        # format
        self.__ui_step_box.currentIndexChanged.connect( self.__ui_step_box_changed )
        self.__ui_maya_scene_box.toggled.connect( self.__ui_maya_scene_box_clicked )
        self.__ui_maya_shaders_box.toggled.connect( self.__ui_maya_shaders_box_clicked )
        self.__ui_alembic_box.toggled.connect( self.__ui_alembic_box_clicked )
        self.__ui_arnold_scene_source_box.toggled.connect( self.__ui_arnold_scene_source_box_clicked )
        self.__ui_obj_box.toggled.connect( self.__ui_obj_box_clicked )
        self.__ui_preset_box.currentIndexChanged.connect( self.__ui_preset_box_current_changed )
        # general
        self.__ui_import_references_box.toggled.connect( self.__update_preset )
        self.__ui_remove_namespaces_box.toggled.connect( self.__update_preset )
        self.__ui_remove_animation_box.toggled.connect( self.__update_preset )
        self.__ui_remove_hidden_nodes_box.toggled.connect( self.__update_preset )
        self.__ui_delete_history_box.toggled.connect( self.__update_preset )
        self.__ui_remove_extra_shapes_box.toggled.connect( self.__update_preset )
        self.__ui_freeze_transform_box.toggled.connect( self.__update_preset )
        self.__ui_freeze_white_list_edit.textEdited.connect( self.__update_preset )
        self.__ui_freeze_white_list_case_box.toggled.connect( self.__update_preset )
        self.__ui_types_box.currentIndexChanged.connect( self.__update_preset )
        self.__ui_types_edit.textChanged.connect( self.__update_preset )
        self.__ui_remove_empty_groups_box.toggled.connect( self.__update_preset )
        # nodes
        self.__ui_select_no_nodes.clicked.connect( self.__ui_nodes_tree.clearSelection )
        self.__ui_select_all_nodes.clicked.connect( self.__ui_nodes_tree.selectAll )
        # maya
        self.__ui_maya_format_box.currentIndexChanged.connect( self.__update_preset )
        self.__ui_maya_hide_joints_box.currentIndexChanged.connect( self.__update_preset )
        self.__ui_maya_lock_transform_box.toggled.connect( self.__update_preset )
        self.__ui_maya_hidden_nodes_box.toggled.connect( self.__update_preset )
        # maya shaders
        self.__ui_shaders_format_box.currentIndexChanged.connect( self.__update_preset )
        # alembic
        self.__ui_alembic_renderable_box.toggled.connect( self.__update_preset )
        self.__ui_alembic_worldSpace_box.toggled.connect( self.__update_preset )
        self.__ui_alembic_handle_start_box.valueChanged.connect( self.__update_preset )
        self.__ui_alembic_handle_end_box.valueChanged.connect( self.__update_preset )
        self.__ui_alembic_frame_step_box.valueChanged.connect( self.__update_preset )
        self.__ui_alembic_filter_euler_box.toggled.connect( self.__update_preset )
        self.__ui_abc_custom_attr_box.toggled.connect( self.__update_preset )
        self.__ui_abc_attr_edit.textChanged.connect( self.__update_preset )
        self.__ui_abc_prefix_edit.textChanged.connect( self.__update_preset )

    def __set_maya_defaults(self, frmt="mb"):
        self.__ui_maya_scene_box.setChecked(True)
        # Default maya options
        if frmt == "mb":
            self.__ui_maya_format_box.setCurrentIndex(0)
        else:
            self.__ui_maya_format_box.setCurrentIndex(1)
        self.__ui_maya_hide_joints_box.setCurrentIndex(0)
        self.__ui_maya_lock_transform_box.setChecked(False)
        self.__ui_maya_hidden_nodes_box.setChecked(True)

    def __set_alembic_defaults(self):
        self.__ui_alembic_box.setChecked(True)
        self.__ui_alembic_renderable_box.setChecked(True)
        self.__ui_alembic_worldSpace_box.setChecked(True)
        self.__ui_alembic_handle_start_box.setValue(0)
        self.__ui_alembic_handle_end_box.setValue(0)
        self.__ui_alembic_frame_step_box.setValue(1)
        self.__ui_alembic_filter_euler_box.setChecked(True)
        self.__ui_abc_attr_edit.setText("")
        self.__ui_abc_prefix_edit.setText("")
        self.__ui_abc_custom_attr_box.setChecked(False)

    def __set_obj_defaults(self):
        self.__ui_obj_mtl_box.setChecked(True)

    # <== PRIVATE SLOTS ==>

    @qc.Slot()
    def __ui_publish_button_clicked(self):
        self.accept()

    @qc.Slot()
    def __ui_cancel_button_clicked(self):
        self.reject()

    @qc.Slot(bool)
    def __ui_maya_scene_box_clicked(self, checked):
        item = self.__ui_sections_box.item(3)
        item.setHidden(not checked)
        if checked:
            self.__set_maya_defaults()
        self.__update_preset()

    @qc.Slot(bool)
    def __ui_maya_shaders_box_clicked(self, checked):
        item = self.__ui_sections_box.item(4)
        item.setHidden(not checked)
        self.__update_preset()

    @qc.Slot(bool)
    def __ui_alembic_box_clicked(self, checked):
        item = self.__ui_sections_box.item(5)
        item.setHidden(not checked)
        if checked:
            self.__set_alembic_defaults()
        self.__update_preset()

    @qc.Slot()
    def __ui_arnold_scene_source_box_clicked(self):
        #item = self.__ui_sections_box.item(5)
        #item.setHidden(not checked)
        self.__update_preset()

    @qc.Slot()
    def __ui_obj_box_clicked(self, checked):
        item = self.__ui_sections_box.item(6)
        item.setHidden(not checked)
        if checked:
            self.__set_obj_defaults()
        self.__update_preset()

    @qc.Slot(int)
    def __ui_preset_box_current_changed(self, index):
        if index < 0:
            return
        file_path = self.__ui_preset_box.itemData(index, qc.Qt.UserRole)
        self.load_preset_file( file_path )

    @qc.Slot()
    def __update_preset(self):
        # Main options
        options = self.get_options()
        options_str = yaml.dump(options)
        self.__ui_preset_edit.setText(options_str)

    @qc.Slot()
    def __ui_step_box_changed(self):
        current_step = self.__ui_step_box.current_step()
        if current_step is None:
            self.__ui_publish_button.setText("Save settings")
            self.__ui_publish_button.setEnabled(False)
        else:
            self.__ui_publish_button.setText("Save settings for: " + current_step.name())
            self.__ui_publish_button.setEnabled(True)
            # Load step options
            options = current_step.publishSettings()
            if options != "":
                options = yaml.safe_load( options )
                self.set_options(options)

    # <== PUBLIC ==>

    def get_options(self):
        """Gets the publish options as a dict"""

        options = {}
        options["import_references"] = self.__ui_import_references_box.isChecked()
        options["remove_namespaces"] = self.__ui_remove_namespaces_box.isChecked()
        options["remove_animation"] = self.__ui_remove_animation_box.isChecked()
        options["remove_hidden_nodes"] = self.__ui_remove_hidden_nodes_box.isChecked()
        options["delete_history"] = self.__ui_delete_history_box.isChecked()
        options["remove_extra_shapes"] = self.__ui_remove_extra_shapes_box.isChecked()
        options["remove_empty_groups"] = self.__ui_remove_empty_groups_box.isChecked()

        types_str = self.__ui_types_edit.toPlainText()
        if types_str != "":
            options["types"] = {}
            options["types"]["mode"] = self.__ui_types_box.currentData(qc.Qt.UserRole)
            types_arr = types_str.split("\n")
            options["types"]["list"] = []
            for type_str in types_arr:
                type_str = type_str.replace(" ", "")
                type_str = type_str.replace("\r", "")
                options["types"]["list"].append(type_str)

        if self.__ui_freeze_transform_box.isChecked():
            self.__ui_freeze_white_list_widget.setEnabled(True)
            options["freeze_transform"] = {}
            options["freeze_transform"]["case_sensitive"] = self.__ui_freeze_white_list_case_box.isChecked()
            # Get freeze transform whitelist
            no_freeze = self.__ui_freeze_white_list_edit.text()
            no_freeze = no_freeze.replace(' ','')
            no_freeze = no_freeze.split(',')
            if not (len(no_freeze) == 1 and no_freeze[0] == ""):
                options["freeze_transform"]["whitelist"] = no_freeze
        else:
            self.__ui_freeze_white_list_widget.setEnabled(False)

        options["formats"] = []

        maya_options = self.get_maya_options()
        if maya_options:
            options["formats"].append( maya_options )

        shaders_options = self.get_shaders_options()
        if shaders_options:
            options["formats"].append( shaders_options )

        abc_options = self.get_alembic_options()
        if abc_options:
            options["formats"].append( abc_options )

        ass_options = self.get_ass_options()
        if ass_options:
            options["formats"].append( ass_options )

        obj_options = self.get_obj_options()
        if obj_options:
            options["formats"].append( obj_options )

        return options

    def get_maya_options(self):
        """Gets the options for maya as a dict, or None if not set to publish a maya scene"""
        if not self.__ui_maya_scene_box.isChecked():
            return None

        options = {}
        maya = {}

        maya["lock_hidden_nodes"] = self.__ui_maya_hidden_nodes_box.isChecked()
        maya["lock_transformations"] = self.__ui_maya_lock_transform_box.isChecked()
        maya["joints"] = self.__ui_maya_hide_joints_box.currentData(qc.Qt.UserRole)
                 
        options[ self.__ui_maya_format_box.currentData(qc.Qt.UserRole) ] = maya
        
        return options

    def get_shaders_options(self):
        """Gets the options for maya shaders as a dict, or None if not set to publish a maya scene"""
        if not self.__ui_maya_shaders_box.isChecked():
            return None

        options = {}
        maya = {}

        maya["only_shaders"] = True
        
        options[ self.__ui_shaders_format_box.currentData(qc.Qt.UserRole) ] = maya
        return options

    def get_alembic_options(self):
        """Gets the options for alembic as a dict, or None if not set to publish an alembic file"""
        if not self.__ui_alembic_box.isChecked():
            return None

        options = {}
        abc = {}

        abc["renderable_only"] = self.__ui_alembic_renderable_box.isChecked()
        abc["world_space"] = self.__ui_alembic_worldSpace_box.isChecked()
        if not self.__ui_remove_animation_box.isChecked():
            abc["animation"] = {}
            abc["animation"]["handle_in"] = self.__ui_alembic_handle_start_box.value()
            abc["animation"]["handle_out"] = self.__ui_alembic_handle_end_box.value()
            abc["animation"]["frame_step"] = self.__ui_alembic_frame_step_box.value()
            self.__ui_alembic_handles_widget.setEnabled(True)
            self.__ui_alembic_frame_step_box.setEnabled(True)
        else:
            self.__ui_alembic_handles_widget.setEnabled(False)
            self.__ui_alembic_frame_step_box.setEnabled(False)

        abc["filter_euler_rotations"] = self.__ui_alembic_filter_euler_box.isChecked()

        abc["add_extra_attributes"] = self.__ui_abc_custom_attr_box.isChecked()
        abc["attributes"] = self.__ui_abc_attr_edit.toPlainText().split("\n")
        abc["attributes_prefix"] = self.__ui_abc_prefix_edit.toPlainText().split("\n")

        options[ "abc" ] = abc
        return options

    def get_ass_options(self):
        """Gets the options for arnold scene source as a dict, or None if not set to publish an ass file"""
        if not self.__ui_arnold_scene_source_box.isChecked():
            return None

        options = "ass"
        return options

    def get_obj_options(self):
        """Gets the options for obj as a dict, or None if not set to publish an obj file"""
        if not self.__ui_obj_box.isChecked():
            return None

        options = {}
        obj = {}

        obj["materials"] = self.__ui_obj_mtl_box.isChecked()
        options["obj"] = obj
        return options

    def load_nodes(self, nodes):
        """Gets the nodes to be published and populates the nodes tree view"""
        self.__ui_nodes_tree.clear()
        for node in nodes:
            maNode = Node(node)
            item = qw.QTreeWidgetItem(self.__ui_nodes_tree)
            item.setText(0, maNode.name())
            item.setText(1, maNode.name().replace("_", " "))
            item.setSelected(True)
            item.setFlags(qc.Qt.ItemIsEditable | qc.Qt.ItemIsEnabled | qc.Qt.ItemIsSelectable)
            item.setData(0, qc.Qt.UserRole, maNode)
            self.__ui_nodes_tree.addTopLevelItem(item)

    def update_preset_files(self, preset_files):
        """Loads the preset files."""
        if len(preset_files) > 0:
            self.__ui_preset_box.clear()
            for preset_file in preset_files:
                name = os.path.basename(preset_file)
                name = os.path.splitext(name)[0]
                self.__ui_preset_box.addItem(name, preset_file)

    def set_options(self, options):
        """Loads options from a preset"""

        # General
        if "freeze_transform" in options:
            self.__ui_freeze_transform_box.setChecked(True)
            load_bool_preset( "case_sensitive", options["freeze_transform"], self.__ui_freeze_white_list_case_box, False )
            if "whitelist" in options["freeze_transform"]:
                whitelist = ", ".join(options["freeze_transform"]["whitelist"])
                self.__ui_freeze_white_list_edit.setText(whitelist)
            else:
                self.__ui_freeze_white_list_edit.setText("")
        else:
            self.__ui_freeze_transform_box.setChecked(False)

        if "types" in options:
            if "list" in options["types"]:
                types_str = "\n".join(options["types"]["list"])
                self.__ui_types_edit.setPlainText(types_str)
                load_enum_preset( "mode", options["types"], self.__ui_types_box, "remove" )
        else:
            self.__ui_types_edit.setPlainText("")

        load_bool_preset( "delete_history", options, self.__ui_delete_history_box, False )
        load_bool_preset( "import_references", options, self.__ui_import_references_box, True )
        load_bool_preset( "remove_animation", options, self.__ui_remove_animation_box, False )
        load_bool_preset( "remove_extra_shapes", options, self.__ui_remove_extra_shapes_box, True )
        load_bool_preset( "remove_hidden_nodes", options, self.__ui_remove_hidden_nodes_box, True )
        load_bool_preset( "remove_namespaces", options, self.__ui_remove_namespaces_box, True )
        load_bool_preset( "remove_empty_groups", options, self.__ui_remove_empty_groups_box, True )

        # Formats
        # Uncheck all
        self.__ui_maya_scene_box.setChecked(False)
        self.__ui_maya_shaders_box.setChecked(False)
        self.__ui_alembic_box.setChecked(False)
        self.__ui_arnold_scene_source_box.setChecked(False)
        self.__ui_obj_box.setChecked(False)

        if "formats" in options:
            for frmt in options["formats"]:

                # <-- MAYA -->

                if frmt == "mb" or frmt == "ma":
                    self.__set_maya_defaults(frmt)

                elif "mb" in frmt or "ma" in frmt:
                    shaders = False

                    mbin = "mb" in frmt
                    if mbin:
                        frmt = frmt["mb"]
                    else:
                        frmt = frmt["ma"]

                    if "only_shaders" in frmt: 
                        shaders = frmt["only_shaders"]
                    if shaders:
                        self.__ui_maya_shaders_box.setChecked(True)
                        if mbin:
                            self.__ui_shaders_format_box.setCurrentIndex(0)
                        else:
                            self.__ui_shaders_format_box.setCurrentIndex(1)
                        continue

                    self.__set_maya_defaults(frmt)

                    if mbin:
                        self.__ui_maya_format_box.setCurrentIndex(0)
                    else:
                        self.__ui_maya_format_box.setCurrentIndex(1)

                    load_bool_preset( "lock_hidden_nodes", frmt, self.__ui_maya_hidden_nodes_box, True )
                    load_bool_preset( "lock_transformations", frmt, self.__ui_maya_lock_transform_box, False )
                    load_enum_preset( "joints", frmt, self.__ui_maya_hide_joints_box, "disable" )

                # <-- ALEMBIC -->

                elif frmt == "abc":
                    self.__set_alembic_defaults()

                elif "abc" in frmt:
                    self.__set_alembic_defaults()
                    frmt = frmt["abc"]
                    load_bool_preset( "filter_euler_rotations", frmt, self.__ui_alembic_filter_euler_box, True)
                    load_bool_preset( "renderable_only", frmt, self.__ui_alembic_filter_euler_box, True)
                    load_bool_preset( "world_space", frmt, self.__ui_alembic_worldSpace_box, True)
                    if "animation" in frmt:
                        anim = frmt["animation"]
                        load_number_preset( "frame_step", anim, self.__ui_alembic_frame_step_box, 1)
                        load_number_preset( "handle_in", anim, self.__ui_alembic_handle_start_box, 1)
                        load_number_preset( "handle_out", anim, self.__ui_alembic_handle_end_box, 1)
                    load_bool_preset("add_extra_attributes", frmt, self.__ui_abc_custom_attr_box, False)
                    if "attributes" in frmt:
                        attrs_str = "\n".join(frmt["attributes"])
                        self.__ui_abc_attr_edit.setPlainText(attrs_str)
                    if "attributes_prefix" in frmt:
                        pref_str = "\n".join(frmt["attributes_prefix"])
                        self.__ui_abc_prefix_edit.setPlainText(pref_str)

                # <-- ASS -->

                elif frmt == "ass" or "ass" in frmt:
                    self.__ui_arnold_scene_source_box.setChecked(True)

                # <-- OBJ -->

                elif frmt == "obj":
                    self.__set_obj_defaults()

                elif "obj" in frmt:
                    self.__set_obj_defaults()
                    frmt = frmt["obj"]
                    load_bool_preset( "materials", frmt, self.__ui_obj_mtl_box)
        else:
            self.__set_maya_defaults()

    def get_nodes(self):
        """"Returns a list of tuples (node, publish name)"""
        nodes = []
        for item in self.__ui_nodes_tree.selectedItems():
            nodes.append((item.data(0, qc.Qt.UserRole), item.text(1)))
        return nodes

    def set_steps(self, steps):
        """Sets the steps"""
        self.__ui_step_box.set_steps(steps)
        # Show the row
        self.__ui_step_label.show()
        self.__ui_step_box.show()

    def get_step(self):
        return self.__ui_step_box.current_step()

    def set_step(self, step):
        self.__ui_step_box.set_step(step)
