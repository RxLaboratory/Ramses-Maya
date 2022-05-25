# -*- coding: utf-8 -*-
"""
The UI for publishing scenes
"""

from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module,import-error
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QStackedLayout,
    QWidget,
    QFormLayout,
    QCheckBox,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
    QStyledItemDelegate,
    QPushButton,
    QLabel,
    QTextEdit,
    QComboBox,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot,
    Qt,
)
from maya import cmds # pylint: disable=import-error
import yaml
from dumaf import DuMaNode

# NOTE
# formats to implement: abc, ma, mb, ma shaders, mb shaders, ass

class NoEditDelegate(QStyledItemDelegate):
    """
    A delegate to be able to edit only the second column of the Nodes tree view
    """
    def __init__(self, parent=None): # pylint: disable=useless-super-delegation
        super(NoEditDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index): # pylint: disable=unused-argument,invalid-name
        """Overrides QStyledItemDelegate.createEditor"""
        return 0

class PublishDialog(QMainWindow):
    """
    The Main Dialog to publish the scene
    """
    def __init__(self, parent=None): # pylint: disable=useless-super-delegation
        super(PublishDialog, self).__init__(parent)
        self.__setup_ui()
        self.__setup_menu()
        self.__connect_events()
        self.__update_preset()

    # <== PRIVATE METHODS ==>

    def __setup_menu(self):
        edit_menu = self.menuBar().addMenu("Edit")
        self.__save_preset_action = edit_menu.addAction("Save preset...")
        self.__load_preset_action = edit_menu.addAction("Load preset...")

        help_menu = self.menuBar().addMenu("Help")
        self.__help_action = help_menu.addAction("Ramses Maya Add-on help...")

    def __setup_ui(self):
        self.setWindowFlag(Qt.Dialog)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle("Publish scene")
        self.setMinimumWidth( 700 )

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        #mainWidget.setLayout( mainLayout )
        main_layout.setContentsMargins(6,6,6,6)
        main_layout.setSpacing(12)

        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)
        content_layout.setSpacing(3)

        self.__ui_sections_box = QListWidget()
        self.__ui_sections_box.addItem("Select: Format")
        self.__ui_sections_box.addItem("Select: Nodes")
        self.__ui_sections_box.addItem("Pre-Publish: Settings")
        self.__ui_sections_box.addItem("Publish: Maya scene")
        self.__ui_sections_box.addItem("Publish: Maya scene - shaders")
        self.__ui_sections_box.addItem("Publish: Alembic")
        self.__ui_sections_box.item(4).setHidden(True)
        self.__ui_sections_box.item(5).setHidden(True)
        self.__ui_sections_box.setMaximumWidth( 150 )
        content_layout.addWidget(self.__ui_sections_box)

        self.__ui_stacked_layout = QStackedLayout()
        content_layout.addLayout(self.__ui_stacked_layout)

        # <-- PRESET -->

        preset_widget = QWidget()
        preset_layout = QVBoxLayout(preset_widget)
        preset_layout.setSpacing(3)
        preset_layout.setContentsMargins(3,3,3,3)
        content_layout.addWidget(preset_widget)

        preset_label = QLabel("You can use this preset in Ramses to set\nthe current settings as defaults for pipes or steps.")
        preset_layout.addWidget(preset_label)
        self.__ui_preset_edit = QTextEdit()
        self.__ui_preset_edit.setReadOnly(True)
        preset_layout.addWidget(self.__ui_preset_edit)

        # <-- GENERAL -->

        general_widget = QWidget()
        self.__ui_stacked_layout.addWidget(general_widget)
        general_layout = QFormLayout(general_widget)
        general_layout.setSpacing(3)

        self.__ui_built_in_preset = QComboBox()
        self.__ui_built_in_preset.addItem("None")
        self.__ui_built_in_preset.addItem("Simple.mb")
        self.__ui_built_in_preset.addItem("Geometry.abc")
        self.__ui_built_in_preset.addItem("Rig.ma")
        self.__ui_built_in_preset.addItem("Animation.abc")
        self.__ui_built_in_preset.addItem("Shaders.mb")
        general_layout.addRow("Built-in preset:", self.__ui_built_in_preset)

        format_widget = QWidget()
        format_layout = QVBoxLayout(format_widget)
        format_layout.setSpacing(3)
        format_layout.setContentsMargins(3,3,3,3)
        general_layout.addRow("Format:", format_widget)

        self.__ui_maya_scene_box = QCheckBox("Maya scene (ma/mb)")
        self.__ui_maya_scene_box.setChecked(True)
        format_layout.addWidget(self.__ui_maya_scene_box)
        self.__ui_maya_shaders_box = QCheckBox("Maya scene, shaders only (ma/mb)")
        format_layout.addWidget(self.__ui_maya_shaders_box)
        self.__ui_alembic_box = QCheckBox("Alembic (abc)")
        format_layout.addWidget(self.__ui_alembic_box)
        self.__ui_arnold_scene_source_box = QCheckBox("Arnold scene source (ass)")
        format_layout.addWidget(self.__ui_arnold_scene_source_box)

        # <-- Nodes -->

        nodes_widget = QWidget()
        nodes_layout = QVBoxLayout(nodes_widget)
        nodes_layout.setContentsMargins(0,0,0,0)
        nodes_layout.setSpacing(3)
        self.__ui_stacked_layout.addWidget( nodes_widget )

        self.__ui_nodes_tree = QTreeWidget()
        self.__ui_nodes_tree.setHeaderLabels(("Node", "Publish name"))
        self.__ui_nodes_tree.setSelectionMode(QAbstractItemView.MultiSelection)
        self.__ui_nodes_tree.setItemDelegateForColumn(0, NoEditDelegate())
        nodes_layout.addWidget(self.__ui_nodes_tree)

        nodes_buttons_layout = QHBoxLayout()
        nodes_buttons_layout.setSpacing(3)
        nodes_layout.addLayout(nodes_buttons_layout)
        self.__ui_select_no_nodes = QPushButton("Select none")
        nodes_buttons_layout.addWidget( self.__ui_select_no_nodes )
        self.__ui_select_all_nodes = QPushButton("Select all")
        nodes_buttons_layout.addWidget( self.__ui_select_all_nodes )

        # <-- PRE-PUBLISH -->

        pre_publish_widget = QWidget()
        pre_publish_vlayout = QVBoxLayout(pre_publish_widget)
        pre_publish_vlayout.setSpacing(3)
        self.__ui_stacked_layout.addWidget( pre_publish_widget )

        pre_publish_layout = QFormLayout()
        pre_publish_layout.setSpacing(3)
        pre_publish_vlayout.addLayout(pre_publish_layout)

        self.__ui_import_references_box = QCheckBox("Import references")
        self.__ui_import_references_box.setChecked(True)
        pre_publish_layout.addRow("Clean:", self.__ui_import_references_box)

        self.__ui_remove_namespaces_box = QCheckBox("Remove namespaces")
        self.__ui_remove_namespaces_box.setChecked(True)
        pre_publish_layout.addRow("", self.__ui_remove_namespaces_box)

        self.__ui_remove_hidden_nodes_box = QCheckBox("Remove hidden nodes")
        self.__ui_remove_hidden_nodes_box.setChecked(True)
        pre_publish_layout.addRow("", self.__ui_remove_hidden_nodes_box)

        self.__ui_delete_history_box = QCheckBox("Delete node history")
        self.__ui_delete_history_box.setChecked(True)
        pre_publish_layout.addRow("", self.__ui_delete_history_box)

        self.__ui_remove_extra_shapes_box = QCheckBox("Remove extra shapes")
        self.__ui_remove_extra_shapes_box.setChecked(True)
        pre_publish_layout.addRow("", self.__ui_remove_extra_shapes_box)

        self.__ui_remove_animation_box = QCheckBox("Remove animation")
        self.__ui_remove_animation_box.setChecked(True)
        pre_publish_layout.addRow("", self.__ui_remove_animation_box)

        self.__ui_types_box = QComboBox()
        self.__ui_types_box.addItem("Keep", "keep")
        self.__ui_types_box.addItem("Remove", "remove")
        self.__ui_types_box.setCurrentIndex(1)
        pre_publish_layout.addRow("Types:", self.__ui_types_box)

        self.__ui_types_edit = QTextEdit()
        self.__ui_types_edit.setPlainText("locator\nbezierCurve\nnurbsCurve\nnurbsSurface")
        self.__ui_types_edit.setMaximumHeight(100)
        pre_publish_layout.addRow("", self.__ui_types_edit)

        self.__ui_freeze_transform_box = QCheckBox("")
        self.__ui_freeze_transform_box.setChecked(True)
        pre_publish_layout.addRow("Freeze transformations", self.__ui_freeze_transform_box)

        self.__ui_freeze_white_list_widget = QWidget()
        freeze_white_list_layout = QVBoxLayout(self.__ui_freeze_white_list_widget)
        freeze_white_list_layout.setContentsMargins(0,0,0,0)
        freeze_white_list_layout.setSpacing(3)
        freeze_white_list_label = QLabel("Ignore names containing:")
        freeze_white_list_layout.addWidget(freeze_white_list_label)
        self.__ui_freeze_white_list_edit = QLineEdit("_eye_, _eyes_")
        freeze_white_list_layout.addWidget( self.__ui_freeze_white_list_edit )
        self.__ui_freeze_white_list_case_box = QCheckBox("Case sensitive")
        freeze_white_list_layout.addWidget(self.__ui_freeze_white_list_case_box )
        pre_publish_layout.addRow("", self.__ui_freeze_white_list_widget)

        # <-- Maya Scene -->

        maya_widget = QWidget()
        maya_vlayout = QVBoxLayout(maya_widget)
        maya_vlayout.setSpacing(3)
        self.__ui_stacked_layout.addWidget( maya_widget )

        maya_layout = QFormLayout()
        maya_layout.setSpacing(3)
        maya_vlayout.addLayout(maya_layout)

        self.__ui_maya_format_box = QComboBox()
        self.__ui_maya_format_box.addItem("Maya Binary (mb)", "mb")
        self.__ui_maya_format_box.addItem("Maya ASCII (ma)", "ma")
        maya_layout.addRow("Format:", self.__ui_maya_format_box )

        self.__ui_maya_hidden_nodes_box = QCheckBox("Lock visibility")
        self.__ui_maya_hidden_nodes_box.setChecked(True)
        maya_layout.addRow("Hidden nodes:", self.__ui_maya_hidden_nodes_box)

        self.__ui_maya_hide_joints_box = QComboBox()
        self.__ui_maya_hide_joints_box.addItem("Disable draw", "disable")
        self.__ui_maya_hide_joints_box.addItem("Hide", "hide")
        self.__ui_maya_hide_joints_box.addItem("Hide and lock visibility", "lock")
        self.__ui_maya_hide_joints_box.addItem("Keep", "keep")
        maya_layout.addRow("Joints:", self.__ui_maya_hide_joints_box)

        # <-- Maya Shaders -->

        shaders_widget = QWidget()
        shaders_vlayout = QVBoxLayout(shaders_widget)
        shaders_vlayout.setSpacing(3)
        self.__ui_stacked_layout.addWidget( shaders_widget )
        shaders_layout = QFormLayout()
        shaders_layout.setSpacing(3)
        shaders_vlayout.addLayout(shaders_layout)

        self.__ui_shaders_format_box = QComboBox()
        self.__ui_shaders_format_box.addItem("Maya Binary (mb)", "mb")
        self.__ui_shaders_format_box.addItem("Maya ASCII (ma)", "ma")
        shaders_layout.addRow("Format:", self.__ui_shaders_format_box )

        # <-- Alembic -->

        alembic_widget = QWidget()
        alembic_vlayout = QVBoxLayout(alembic_widget)
        alembic_vlayout.setSpacing(3)
        self.__ui_stacked_layout.addWidget( alembic_widget )
        alembic_layout = QFormLayout()
        alembic_layout.setSpacing(3)
        alembic_vlayout.addLayout(alembic_layout)

        self.__ui_alembic_renderable_box = QCheckBox("Renderable only")
        self.__ui_alembic_renderable_box.setChecked(True)
        alembic_layout.addRow("Export:", self.__ui_alembic_renderable_box)

        self.__ui_alembic_frames_widget = QWidget()
        frame_range_layout = QHBoxLayout(self.__ui_alembic_frames_widget)
        frame_range_layout.setContentsMargins(0,0,0,0)
        frame_range_layout.setSpacing(3)
        self.__ui_alembic_frame_start_box = QSpinBox()
        self.__ui_alembic_frame_start_box.setMinimum(-10000)
        self.__ui_alembic_frame_start_box.setMaximum(10000)
        in_frame = int(cmds.playbackOptions(q=True,ast=True))
        frame_range_layout.addWidget( self.__ui_alembic_frame_start_box)
        self.__ui_alembic_frame_start_box.setValue( in_frame )
        self.__ui_alembic_frame_end_box = QSpinBox()
        self.__ui_alembic_frame_end_box.setMinimum(-10000)
        self.__ui_alembic_frame_end_box.setMaximum(10000)
        out_frame = int(cmds.playbackOptions(q=True,aet=True))
        self.__ui_alembic_frame_end_box.setValue(out_frame)
        frame_range_layout.addWidget( self.__ui_alembic_frame_end_box)
        alembic_layout.addRow("Frame range:", self.__ui_alembic_frames_widget)

        self.__ui_alembic_handles_widget = QWidget()
        handles_layout = QHBoxLayout(self.__ui_alembic_handles_widget)
        handles_layout.setContentsMargins(0,0,0,0)
        handles_layout.setSpacing(3)
        self.__ui_alembic_handle_start_box = QSpinBox()
        self.__ui_alembic_handle_start_box.setMinimum(0)
        self.__ui_alembic_handle_start_box.setMaximum(10000)
        self.__ui_alembic_handle_start_box.setPrefix("-")
        handles_layout.addWidget( self.__ui_alembic_handle_start_box)
        self.__ui_alembic_handle_start_box.setValue( 0 )
        self.__ui_alembic_handle_end_box = QSpinBox()
        self.__ui_alembic_handle_end_box.setMinimum(0)
        self.__ui_alembic_handle_end_box.setMaximum(10000)
        self.__ui_alembic_handle_end_box.setPrefix("+")
        handles_layout.addWidget( self.__ui_alembic_handle_end_box)
        alembic_layout.addRow("Handles:", self.__ui_alembic_handles_widget)
       
        self.__ui_alembic_frame_step_box = QDoubleSpinBox()
        self.__ui_alembic_frame_step_box.setMinimum(0.1)
        self.__ui_alembic_frame_step_box.setMaximum( 100 )
        self.__ui_alembic_frame_step_box.setDecimals(1)
        self.__ui_alembic_frame_step_box.setValue(1.0)
        alembic_layout.addRow("Frame step:", self.__ui_alembic_frame_step_box)
        
        self.__ui_alembic_filter_euler_box = QCheckBox("Filter Euler rotations")
        self.__ui_alembic_filter_euler_box.setChecked(True)
        alembic_layout.addRow("", self.__ui_alembic_filter_euler_box)

    def __connect_events(self):
        self.__ui_sections_box.currentRowChanged.connect( self.__ui_sections_box_row_changed )
        # format
        self.__ui_maya_scene_box.clicked.connect( self.__ui_maya_scene_box_clicked )
        self.__ui_maya_shaders_box.clicked.connect( self.__ui_maya_shaders_box_clicked )
        self.__ui_alembic_box.clicked.connect( self.__ui_alembic_box_clicked )
        self.__ui_arnold_scene_source_box.clicked.connect( self.__ui_arnold_scene_source_box_clicked )
        # general
        self.__ui_import_references_box.clicked.connect( self.__update_preset )
        self.__ui_remove_namespaces_box.clicked.connect( self.__update_preset )
        self.__ui_remove_animation_box.clicked.connect( self.__update_preset )
        self.__ui_remove_hidden_nodes_box.clicked.connect( self.__update_preset )
        self.__ui_delete_history_box.clicked.connect( self.__update_preset )
        self.__ui_remove_extra_shapes_box.clicked.connect( self.__update_preset )
        self.__ui_freeze_transform_box.clicked.connect( self.__update_preset )
        self.__ui_freeze_white_list_edit.textEdited.connect( self.__update_preset )
        self.__ui_freeze_white_list_case_box.clicked.connect( self.__update_preset )
        self.__ui_types_box.currentIndexChanged.connect( self.__update_preset )
        self.__ui_types_edit.textChanged.connect( self.__update_preset )
        # nodes
        self.__ui_select_no_nodes.clicked.connect( self.__ui_nodes_tree.clearSelection )
        self.__ui_select_all_nodes.clicked.connect( self.__ui_nodes_tree.selectAll )
        # maya
        self.__ui_maya_format_box.currentIndexChanged.connect( self.__update_preset )
        self.__ui_maya_hide_joints_box.currentIndexChanged.connect( self.__update_preset )
        self.__ui_maya_hidden_nodes_box.clicked.connect( self.__update_preset )
        # maya shaders
        self.__ui_shaders_format_box.currentIndexChanged.connect( self.__update_preset )
        # alembic
        self.__ui_alembic_renderable_box.clicked.connect( self.__update_preset )
        self.__ui_alembic_frame_start_box.valueChanged.connect( self.__update_preset )
        self.__ui_alembic_frame_end_box.valueChanged.connect( self.__update_preset )
        self.__ui_alembic_handle_start_box.valueChanged.connect( self.__update_preset )
        self.__ui_alembic_handle_end_box.valueChanged.connect( self.__update_preset )
        self.__ui_alembic_frame_step_box.valueChanged.connect( self.__update_preset )
        self.__ui_alembic_filter_euler_box.clicked.connect( self.__update_preset )

    # <== PRIVATE SLOTS ==>

    @Slot(int)
    def __ui_sections_box_row_changed(self, row):
        self.__ui_stacked_layout.setCurrentIndex(row)

    @Slot(bool)
    def __ui_maya_scene_box_clicked(self, checked):
        item = self.__ui_sections_box.item(3)
        item.setHidden(not checked)
        self.__update_preset()

    @Slot(bool)
    def __ui_maya_shaders_box_clicked(self, checked):
        item = self.__ui_sections_box.item(4)
        item.setHidden(not checked)
        self.__update_preset()

    @Slot(bool)
    def __ui_alembic_box_clicked(self, checked):
        item = self.__ui_sections_box.item(5)
        item.setHidden(not checked)
        self.__update_preset()

    @Slot(bool)
    def __ui_arnold_scene_source_box_clicked(self, checked):
        #item = self.__ui_sections_box.item(5)
        #item.setHidden(not checked)
        self.__update_preset()

    @Slot()
    def __update_preset(self):
        # Main options
        options = self.get_options()
        options_str = yaml.dump(options)
        self.__ui_preset_edit.setText(options_str)

    # <== PUBLIC SLOTS ==>

    def get_options(self):
        """Gets the publish options as a dict"""

        options = {}
        options["import_references"] = self.__ui_import_references_box.isChecked()
        options["remove_namespaces"] = self.__ui_remove_namespaces_box.isChecked()
        options["remove_animation"] = self.__ui_remove_animation_box.isChecked()
        options["remove_hidden_nodes"] = self.__ui_remove_hidden_nodes_box.isChecked()
        options["delete_history"] = self.__ui_delete_history_box.isChecked()
        options["remove_extra_shapes"] = self.__ui_remove_extra_shapes_box.isChecked()
        options["types_mode"] = self.__ui_types_box.currentData(Qt.UserRole)

        types_str = self.__ui_types_edit.toPlainText()
        if types_str != "":
            types_arr = types_str.split("\n")
            options["types"] = []
            for type_str in types_arr:
                type_str = type_str.replace(" ", "")
                type_str = type_str.replace("\r", "")
                options["types"].append(type_str)

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

        return options

    def get_maya_options(self):
        """Gets the options for maya as a dict, or None if not set to publish a maya scene"""
        if not self.__ui_maya_scene_box.isChecked():
            return None

        options = {}
        maya = {}

        maya["lock_hidden_nodes"] = self.__ui_maya_hidden_nodes_box.isChecked()
        maya["joints"] = self.__ui_maya_hide_joints_box.currentData(Qt.UserRole)
                 
        options[ self.__ui_maya_format_box.currentData(Qt.UserRole) ] = maya
        
        return options

    def get_shaders_options(self):
        """Gets the options for maya shaders as a dict, or None if not set to publish a maya scene"""
        if not self.__ui_maya_shaders_box.isChecked():
            return None

        options = {}
        maya = {}

        maya["only_shaders"] = True
        
        options[ self.__ui_shaders_format_box.currentData(Qt.UserRole) ] = maya
        return options

    def get_alembic_options(self):
        """Gets the options for alembic as a dict, or None if not set to publish an alembic file"""
        if not self.__ui_alembic_box.isChecked():
            return None

        options = {}
        abc = {}

        abc["renderable_only"] = self.__ui_alembic_renderable_box.isChecked()
        if not self.__ui_remove_animation_box.isChecked():
            abc["animation"] = {}
            abc["animation"]["in"] = self.__ui_alembic_frame_start_box.value()
            abc["animation"]["out"] = self.__ui_alembic_frame_end_box.value()
            abc["animation"]["handle_in"] = self.__ui_alembic_handle_start_box.value()
            abc["animation"]["handle_out"] = self.__ui_alembic_handle_end_box.value()
            abc["animation"]["frame_step"] = self.__ui_alembic_frame_step_box.value()
            self.__ui_alembic_frames_widget.setEnabled(True)
            self.__ui_alembic_handles_widget.setEnabled(True)
            self.__ui_alembic_frame_step_box.setEnabled(True)
        else:
            self.__ui_alembic_frames_widget.setEnabled(False)
            self.__ui_alembic_handles_widget.setEnabled(False)
            self.__ui_alembic_frame_step_box.setEnabled(False)

        abc["filter_euler_rotations"] = self.__ui_alembic_filter_euler_box.isChecked()
 
        options[ "abc" ] = abc
        return options

    def get_ass_options(self):
        """Gets the options for arnold scene source as a dict, or None if not set to publish an ass file"""
        if not self.__ui_arnold_scene_source_box.isChecked():
            return None

        options = "ass"
        return options

    def load_nodes(self, nodes):
        """Gets the nodes to be published and populates the nodes tree view"""
        self.__ui_nodes_tree.clear()
        for node in nodes:
            node = DuMaNode(node)
            item = QTreeWidgetItem(self.__ui_nodes_tree)
            item.setText(0, node.name())
            item.setText(1, node.name().replace("_", " "))
            item.setSelected(True)
            item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setData(0, Qt.UserRole, node)
            self.__ui_nodes_tree.addTopLevelItem(item)

if __name__ == '__main__':
    #app = QApplication(sys.argv)
    publish_dialog = PublishDialog()
    publish_dialog.show()
    #sys.exit(app.exec_())
