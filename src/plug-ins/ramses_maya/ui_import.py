# -*- coding: utf-8 -*-
"""UI for opening/importing/replacing items"""

import os
from functools import cmp_to_key

try:
    from PySide2 import QtWidgets as qw
    from PySide2 import QtCore as qc
    QAction = qw.QAction
except:  # pylint: disable=bare-except
    from PySide6 import QtWidgets as qw
    from PySide6 import QtGui as qg
    from PySide6 import QtCore as qc
    QAction = qg.QAction

import yaml
import ramses as ram
from ramses_maya.ui_object_combobox import RamObjectBox
from ramses_maya.ui_dialog import Dialog
from ramses_maya.utils_options import (
    load_bool_preset,
    get_option
)
from ramses_maya.utils import IMPORT_PRESETS_PATH

RAMSES = ram.Ramses.instance()
SETTINGS = ram.RamSettings.instance()

class ImportDialog( Dialog ):
    """The main open/import/replace dialog"""
    # <== CONSTRUCTOR ==>

    def __init__(self, parent=None):
        super(ImportDialog,self).__init__(parent)

        self.__setup_ui()
        self.__setup_menu()
        self.__load_projects()
        self.__connect_events()

    # <== PRIVATE METHODS ==>

    def __setup_ui(self):
        """Creates the dialog UI"""

        checkableButtonCSS = """
            qw.QPushButton {
                background-color: rgba(0,0,0,0);
                border:none;
                padding: 5px;
                color: #eeeeee;
            }
            qw.QPushButton:hover {
                background-color: #707070;
            }
            qw.QPushButton:checked {
                background-color: #2b2b2b;
            }"""

        self.setWindowTitle( "Open / Import Item" )

        self.setMinimumWidth(1000)

        mainLayout = qw.QVBoxLayout()
        mainLayout.setSpacing(3)
        self.main_layout.addLayout(mainLayout)

        midLayout = qw.QHBoxLayout()
        midLayout.setSpacing(3)

        topLayout = qw.QFormLayout()
        topLayout.setFieldGrowthPolicy( qw.QFormLayout.AllNonFixedFieldsGrow )
        topLayout.setSpacing(3)

        topLayout.addRow(qw.QLabel("Info:"))

        self.projectBox = RamObjectBox()
        topLayout.addRow( "Project:", self.projectBox )

        self.typeWidget = qw.QWidget()
        typeLayout = qw.QVBoxLayout()
        typeLayout.setContentsMargins(0,0,0,0)
        typeLayout.setSpacing(3)
        self.recentButton = qw.QRadioButton()
        self.recentButton.setText("Recent")
        typeLayout.addWidget(self.recentButton)
        self.assetButton = qw.QRadioButton()
        self.assetButton.setText("Asset")
        typeLayout.addWidget(self.assetButton)
        self.shotButton = qw.QRadioButton()
        self.shotButton.setText("Shot")
        typeLayout.addWidget(self.shotButton)
        self.templateButton = qw.QRadioButton()
        self.templateButton.setText("Template")
        typeLayout.addWidget(self.templateButton)
        self.typeWidget.setLayout(typeLayout)
        self.typeWidget.setEnabled(False)
        self.recentButton.setChecked(True)
        topLayout.addRow( "Type:", self.typeWidget )

        self.actionWidget = qw.QWidget()
        actionLayout = qw.QVBoxLayout()
        actionLayout.setContentsMargins(0,0,0,0)
        actionLayout.setSpacing(3)
        self.openButton = qw.QRadioButton()
        self.openButton.setText("Open item")
        self.openButton.setChecked(True)
        actionLayout.addWidget(self.openButton)
        self.importButton = qw.QRadioButton()
        self.importButton.setText("Import item")
        actionLayout.addWidget(self.importButton)
        self.replaceButton = qw.QRadioButton()
        self.replaceButton.setText("Replace selected items")
        actionLayout.addWidget(self.replaceButton)
        self.actionWidget.setLayout(actionLayout)
        topLayout.addRow( "Action:", self.actionWidget )

        self.optionsWidget = qw.QWidget()
        optionsLayout = qw.QVBoxLayout(self.optionsWidget)
        optionsLayout.setContentsMargins(0,0,0,0)
        optionsLayout.setSpacing(3)
        self.__show_import_options = qw.QCheckBox("Edit import options")
        optionsLayout.addWidget(self.__show_import_options)
        topLayout.addRow( "Settings:", self.optionsWidget )

        midLayout.addLayout( topLayout )

        self.itemWidget = qw.QWidget()
        midLayout.addWidget(self.itemWidget)
        itemLayout = qw.QVBoxLayout(self.itemWidget)
        itemLayout.setSpacing(3)
        itemLayout.setContentsMargins(0,0,0,0)
        self.itemLabel = qw.QLabel("Item")
        itemLayout.addWidget(self.itemLabel)
        self.groupBox = RamObjectBox()
        itemLayout.addWidget(self.groupBox)
        self.itemSearchField = qw.QLineEdit()
        self.itemSearchField.setPlaceholderText('Search...')
        self.itemSearchField.setClearButtonEnabled(True)
        itemLayout.addWidget(self.itemSearchField)
        self.itemList = qw.QListWidget()
        itemLayout.addWidget(self.itemList)

        self.stepWidget = qw.QWidget()
        midLayout.addWidget(self.stepWidget)
        stepLayout = qw.QVBoxLayout(self.stepWidget)
        stepLayout.setSpacing(3)
        stepLayout.setContentsMargins(0,0,0,0)
        stepLabel = qw.QLabel("Step:")
        stepLayout.addWidget(stepLabel)
        self.stepList = qw.QListWidget()
        stepLayout.addWidget(self.stepList)

        self.resourcesWidget = qw.QWidget()
        midLayout.addWidget(self.resourcesWidget)
        resourcesLayout = qw.QVBoxLayout(self.resourcesWidget)
        resourcesLayout.setSpacing(3)
        resourcesLayout.setContentsMargins(0,0,0,0)
        self.resourcesLabel = qw.QLabel("Resource:")
        resourcesLayout.addWidget(self.resourcesLabel)
        self.resourceList = qw.QListWidget()
        resourcesLayout.addWidget(self.resourceList)

        self.versionsWidget = qw.QWidget()
        midLayout.addWidget(self.versionsWidget)
        versionsLayout = qw.QVBoxLayout(self.versionsWidget)
        versionsLayout.setSpacing(3)
        versionsLayout.setContentsMargins(0,0,0,0)
        self.versionsLabel = qw.QLabel("Version:")
        versionsLayout.addWidget(self.versionsLabel)
        self.publishVersionBox = qw.QComboBox()
        versionsLayout.addWidget(self.publishVersionBox)
        self.publishVersionBox.setVisible(False)
        self.versionSearchField = qw.QLineEdit()
        self.versionSearchField.setPlaceholderText('Search...')
        self.versionSearchField.setClearButtonEnabled(True)
        versionsLayout.addWidget(self.versionSearchField)
        self.versionList = qw.QListWidget()
        versionsLayout.addWidget(self.versionList)

        mainLayout.addLayout( midLayout )

        buttonsLayout = qw.QHBoxLayout()
        buttonsLayout.setSpacing(2)
        self._openButton = qw.QPushButton("Open")
        buttonsLayout.addWidget( self._openButton )
        self._importButton = qw.QPushButton("Import")
        self._importButton.hide()
        buttonsLayout.addWidget( self._importButton )
        self._replaceButton = qw.QPushButton("Replace")
        self._replaceButton.hide()
        buttonsLayout.addWidget( self._replaceButton )
        self._cancelButton = qw.QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        self._openButton.setEnabled(False)
        self._replaceButton.setEnabled(False)
        self._importButton.setEnabled(False)

        mainLayout.addLayout( buttonsLayout )

        self.__type_changed()

    def __setup_menu(self):
        by_version = SETTINGS.userSettings.get('sort_publish_by_version', True)
        asc = SETTINGS.userSettings.get('sort_publish_ascending', False)

        self.sort_menu = self.edit_menu.addMenu("Sort published versions")

        self.sort_publish_by_version = QAction("By version", self)
        self.sort_publish_by_version.setCheckable(True)
        self.sort_publish_by_version.setChecked( by_version )
        self.sort_menu.addAction(self.sort_publish_by_version)

        self.sort_publish_by_resource = QAction("By resource", self)
        self.sort_publish_by_resource.setCheckable(True)
        self.sort_publish_by_resource.setChecked( not by_version )
        self.sort_publish_by_resource.setParent(self)
        self.sort_menu.addAction(self.sort_publish_by_resource)

        self.sort_menu.addSeparator()

        self.sort_publish_asc = QAction("Ascending", self)
        self.sort_publish_asc.setCheckable(True)
        self.sort_publish_asc.setChecked( asc )
        self.sort_menu.addAction(self.sort_publish_asc)

        self.sort_publish_desc = QAction("Descending", self)
        self.sort_publish_desc.setCheckable(True)
        self.sort_publish_desc.setChecked(not asc )
        self.sort_menu.addAction(self.sort_publish_desc)

    def __connect_events(self):
        self.projectBox.currentIndexChanged.connect( self.__project_changed )

        self.recentButton.clicked.connect( self.__recent_button_clicked )
        self.assetButton.clicked.connect( self.__asset_button_clicked )
        self.shotButton.clicked.connect( self.__shot_button_clicked )
        self.templateButton.clicked.connect( self.__template_button_clicked )
        self.recentButton.clicked.connect( self.__type_changed )
        self.assetButton.clicked.connect( self.__type_changed )
        self.shotButton.clicked.connect( self.__type_changed )
        self.templateButton.clicked.connect( self.__type_changed )

        self.openButton.clicked.connect( self.__open_button_clicked )
        self.importButton.clicked.connect( self.__import_button_clicked )
        self.replaceButton.clicked.connect( self.__replace_button_clicked )
        self.openButton.clicked.connect( self.__action_changed )
        self.importButton.clicked.connect( self.__action_changed )
        self.replaceButton.clicked.connect( self.__action_changed )

        self._cancelButton.clicked.connect( self.reject )
        self._openButton.clicked.connect( self.accept )
        self._importButton.clicked.connect( self.__import )
        self._replaceButton.clicked.connect( self.__replace )
        self.itemList.currentRowChanged.connect( self.__update_resources )
        self.stepList.currentRowChanged.connect( self.__update_resources )
        self.resourceList.currentRowChanged.connect( self.__resource_changed )
        self.versionList.currentRowChanged.connect( self.__version_changed )
        self.groupBox.currentIndexChanged.connect( self.__update_items )
        self.itemSearchField.textChanged.connect( self.__search_item )
        self.versionSearchField.textChanged.connect( self.__search_version )
        self.publishVersionBox.currentIndexChanged.connect( self.__update_published_files )

        self.sort_publish_by_version.toggled.connect( self.__change_sort_publish_by_version )
        self.sort_publish_by_resource.toggled.connect( self.__change_sort_publish_by_resource )
        self.sort_publish_asc.toggled.connect( self.__change_sort_publish_asc )
        self.sort_publish_desc.toggled.connect( self.__change_sort_publish_desc )

    @qc.Slot()
    def __change_sort_publish_by_version(self, checked):
        self.sort_publish_by_version.setChecked( checked )
        self.sort_publish_by_resource.setChecked( not checked )
        SETTINGS.userSettings['sort_publish_by_version'] = checked
        SETTINGS.save()
        self.__update_resources()

    @qc.Slot()
    def __change_sort_publish_by_resource(self, checked):
        self.sort_publish_by_version.setChecked( not checked )
        self.sort_publish_by_resource.setChecked( checked )
        SETTINGS.userSettings['sort_publish_by_version'] = not checked
        SETTINGS.save()
        self.__update_resources()

    @qc.Slot()
    def __change_sort_publish_asc(self, checked):
        self.sort_publish_asc.setChecked( checked )
        self.sort_publish_desc.setChecked( not checked )
        SETTINGS.userSettings['sort_publish_ascending'] = checked
        SETTINGS.save()
        self.__update_resources()

    @qc.Slot()
    def __change_sort_publish_desc(self, checked):
        self.sort_publish_asc.setChecked( not checked )
        self.sort_publish_desc.setChecked( checked )
        SETTINGS.userSettings['sort_publish_ascending'] = not checked
        SETTINGS.save()
        self.__update_resources()

    @qc.Slot()
    def __recent_button_clicked(self):
        self.recentButton.setChecked(True)
        self.assetButton.setChecked(False)
        self.shotButton.setChecked(False)
        self.templateButton.setChecked(False)

    @qc.Slot()
    def __asset_button_clicked(self):
        self.recentButton.setChecked(False)
        self.assetButton.setChecked(True)
        self.shotButton.setChecked(False)
        self.templateButton.setChecked(False)

    @qc.Slot()
    def __shot_button_clicked(self):
        self.recentButton.setChecked(False)
        self.assetButton.setChecked(False)
        self.shotButton.setChecked(True)
        self.templateButton.setChecked(False)

    @qc.Slot()
    def __template_button_clicked(self):
        self.recentButton.setChecked(False)
        self.assetButton.setChecked(False)
        self.shotButton.setChecked(False)
        self.templateButton.setChecked(True)

    @qc.Slot()
    def __open_button_clicked(self):
        self.openButton.setChecked(True)
        self.importButton.setChecked(False)
        self.replaceButton.setChecked(False)
        self.__show_import_options.setEnabled(False)
        self.__show_import_options.setChecked(False)

    @qc.Slot()
    def __import_button_clicked(self):
        self.openButton.setChecked(False)
        self.importButton.setChecked(True)
        self.replaceButton.setChecked(False)
        self.__show_import_options.setEnabled(True)

    @qc.Slot()
    def __replace_button_clicked(self):
        self.openButton.setChecked(False)
        self.importButton.setChecked(False)
        self.replaceButton.setChecked(True)
        self.__show_import_options.setEnabled(True)

    def __load_projects(self):
        # Load projects
        projects = RAMSES.projects()
        self.projectBox.clear()

        if projects is None:
            self.assetButton.setChecked(False)
            self.shotButton.setChecked(False)
            self.templateButton.setChecked(False)
            return

        for project in RAMSES.projects():
            self.projectBox.addItem(str(project), project)

        self.projectBox.setCurrentIndex(-1)

    @qc.Slot()
    def __project_changed(self, index):
        self.assetButton.setChecked(False)
        self.shotButton.setChecked(False)
        self.templateButton.setChecked(False)
        self.typeWidget.setEnabled(index != -1)
        if index == -1:
            return

    @qc.Slot()
    def __type_changed( self ):
        recent = self.recentButton.isChecked()
        shot = self.shotButton.isChecked()
        asset = self.assetButton.isChecked()
        template = self.templateButton.isChecked()

        # adjust UI
        if shot or asset:
            self.itemWidget.show()
            self.stepWidget.show()
            self.versionsWidget.show()
            self.importButton.setEnabled(True)
            self.replaceButton.setEnabled(True)
            if asset:
                self.itemLabel.setText("Asset:")
            else:
                self.itemLabel.setText("Shot:")
        elif recent:
            self.itemWidget.hide()
            self.stepWidget.hide()
            self.versionsWidget.hide()
            self.openButton.setChecked(True)
            self.__open_button_clicked()
            self.importButton.setEnabled(False)
            self.replaceButton.setEnabled(False)
        else:
            self.itemWidget.hide()
            self.stepWidget.show()
            self.versionsWidget.show()
            self.importButton.setEnabled(True)
            self.replaceButton.setEnabled(True)

        # reinit lists
        self.itemList.clear()
        self.stepList.clear()
        self.resourceList.clear()
        self.versionList.clear()
        self.groupBox.clear()

        if not shot and not asset and not template and not recent:
            return

        if recent:
            # Load recent files
            self.__update_resources()

        project = self.projectBox.currentData()
        if not project:
            return

        steps = ()

        # Load asset groups and asset steps
        if asset:
            groups = project.assetGroups()
            self.groupBox.blockSignals(True)
            self.groupBox.addItem("All", "")
            # Add groups
            for group in groups:
                self.groupBox.addItem(group.name(), group)
            self.groupBox.setCurrentIndex(0)
            self.groupBox.blockSignals(False)
            self.__update_items()
            steps = project.steps( ram.StepType.ASSET_PRODUCTION )
        # Load sequences, shots and shot steps
        elif shot:
            groups = project.sequences()
            self.groupBox.blockSignals(True)
            self.groupBox.addItem("All", "")
            # Add sequences
            for group in groups:
                self.groupBox.addItem(group.name(), group)
            self.groupBox.setCurrentIndex(0)
            self.groupBox.blockSignals(False)
            steps = project.steps( ram.StepType.SHOT_PRODUCTION )
        # Load steps for templates
        elif template:
            steps = project.steps()

        # Populate steps
        for step in steps:
            n = str(step)
            item = qw.QListWidgetItem( n )
            item.setData( qc.Qt.UserRole, step )
            self.stepList.addItem( item )

    @qc.Slot()
    def __update_items(self):

        project = self.projectBox.currentData()
        if not project:
            return

        items = ()
        if self.shotButton.isChecked():
            items = project.shots( sequence = self.groupBox.currentData() )
        elif self.assetButton.isChecked():
            items = project.assets( self.groupBox.currentData() )
        else: return

        self.itemList.clear()
        for item in items:
            n = str(item)
            listItem = qw.QListWidgetItem( n )
            listItem.setData( qc.Qt.UserRole, item )
            self.itemList.addItem( listItem )

    @qc.Slot()
    def __search_item(self, text):
        text = text.lower()
        for i in range(0, self.itemList.count()):
            item = self.itemList.item(i)
            item.setHidden(
                text != '' and text not in item.text().lower()
                )

    @qc.Slot()
    def __search_version(self, text):
        text = text.lower()
        for i in range(0, self.versionList.count()):
            item = self.versionList.item(i)
            item.setHidden(
                text != '' and text not in item.text().lower()
                )

    @qc.Slot()
    def __action_changed(self):
        if self.openButton.isChecked():
            self._importButton.hide()
            self._replaceButton.hide()
            self._openButton.show()
            self.versionsLabel.setText("Version:")
            self.versionList.setSelectionMode(qw.QAbstractItemView.SingleSelection)
            self.publishVersionBox.setVisible(False)
            self.resourcesWidget.show()
        else: # Import or replace
            if self.replaceButton.isChecked():
                self._replaceButton.show()
                self._importButton.hide()
                self.versionList.setSelectionMode(qw.QAbstractItemView.SingleSelection)
            else:
                self._replaceButton.hide()
                self._importButton.show()
                self.versionList.setSelectionMode(qw.QAbstractItemView.ExtendedSelection)
            self._openButton.hide()
            self.versionsLabel.setText("File:")
            self.publishVersionBox.setVisible(True)
            self.resourcesWidget.hide()
        self.__update_resources()
        self.__resource_changed( self.resourceList.currentRow() )

    @qc.Slot()
    def __update_resources(self):

        def listTemplateResources(step):
            folder = step.templatesFolderPath()
            if folder == '':
                return

            for f in os.listdir( folder ):
                # Template must be a folder
                fPath = ram.RamFileManager.buildPath((
                    folder,
                    f
                ))
                if not os.path.isdir(fPath):
                    continue

                nm = ram.RamFileInfo()
                if not nm.setFileName( f ):
                    continue

                if nm.project != step.projectShortName():
                    continue

                if nm.step != step.shortName():
                    continue

                for t in os.listdir( fPath ):
                    # Resource must be a file
                    resource = ram.RamFileManager.buildPath((
                        fPath,
                        t
                    ))
                    if not os.path.isfile(resource):
                        continue

                    if not nm.setFileName( t ):
                        continue

                    res = nm.resource

                    if nm.isRestoredVersion:
                        if res != '':
                            res = res + " | "
                        res = res + "v" + str(nm.restoredVersion) + " (restored)"

                    if res == "":
                        res = "Main (" + nm.extension + ")"

                    item = qw.QListWidgetItem( nm.shortName + " | " + res )
                    item.setData( qc.Qt.UserRole, resource )
                    item.setToolTip(os.path.basename(t))
                    self.resourceList.addItem( item )

        self._openButton.setEnabled(False)

        self.resourceList.clear()
        self.versionList.clear()

        if self.recentButton.isChecked():
            recent_files = SETTINGS.recentFiles
            for file in reversed(recent_files):
                if not os.path.isfile(file):
                    recent_files.remove(file)
                    continue
                item = ram.RamItem.fromPath(file)
                if not item:
                    it = qw.QListWidgetItem( os.path.basename(file) )
                    it.setData( qc.Qt.UserRole, file )
                    self.resourceList.insertItem(0, it)
                    continue

                nm = ram.RamFileInfo()
                nm.setFilePath(file)

                res = nm.resource

                if nm.isRestoredVersion:
                    if res != '':
                        res = res + " | "
                    res = res + "v" + str(nm.restoredVersion) + " (restored)"

                itemName = ""
                if nm.project != "":
                    itemName = nm.project + " | "
                itemName = itemName + str(item)
                if nm.step != "":
                    itemName = itemName + " | " + nm.step
                if res != "":
                    itemName = itemName + " | " + res

                it = qw.QListWidgetItem( itemName )
                it.setData( qc.Qt.UserRole, file )
                it.setToolTip( os.path.basename(file) )
                self.resourceList.insertItem(0, it)
            return

        stepItem = self.stepList.currentItem()
        if not stepItem:
            return
        step = stepItem.data(qc.Qt.UserRole)

        currentItem = self.getItem()

        # If open, list resources in wip folder
        if self.openButton.isChecked():
            # Shots and Assets
            if self.assetButton.isChecked() or self.shotButton.isChecked():
                if not currentItem:
                    return
                # List resources
                resources = currentItem.stepFilePaths( step )

                for resource in resources:
                    nm = ram.RamFileInfo()
                    nm.setFilePath(resource)
                    if nm.project == '':
                        continue

                    res = nm.resource

                    if nm.isRestoredVersion:
                        if res != '':
                            res = res + " | "
                        res = res + "v" + str(nm.restoredVersion) + " (restored)"

                    if res == "":
                        res = "Main (" + nm.extension + ")"
                        self._openButton.setEnabled(True)

                    item = qw.QListWidgetItem( res )
                    item.setData( qc.Qt.UserRole, resource )
                    item.setToolTip( os.path.basename(resource) )
                    self.resourceList.addItem( item )

            # Templates
            else:
                # List resources
                listTemplateResources(step)

        # If import asset or shot, list all subfolders
        elif self.assetButton.isChecked() or self.shotButton.isChecked():
            self.__list_published_versions()
        # If import template, list resources
        else:
            listTemplateResources(step)

    @qc.Slot()
    def __list_published_versions(self):
        self.publishVersionBox.clear()
        folders = []
        currentItem = self.getItem()
        if not currentItem:
            return
        step = self.getStep()
        if not step:
            return
        folders = currentItem.publishedVersionFolderPaths( step )

        sorted_folders = folders
        if self.sort_publish_by_version.isChecked():
            sorted_folders = sorted(folders, key=cmp_to_key(publish_sorter))
        if self.sort_publish_desc.isChecked():
            sorted_folders = reversed(sorted_folders)

        for f in sorted_folders:
            folderName = os.path.basename( f )
            folderName = folderName.split("_")
            title = ""

            # Test length to know what we've got
            if len(folderName) == 3: # resource, version, state
                title = folderName[0] + " | v" + folderName[1] + " | " + folderName[2]
            elif len(folderName) < 3: # version (state)
                # naming could be faulty
                try:
                    n = int(folderName[0])
                except ValueError:
                    n = 0
                if n != 0:
                    title = "v" + " | ".join(folderName)
            else:
                title = " | ".join(folderName)

            self.publishVersionBox.addItem(title, f)
            self.__update_published_files()

    @qc.Slot()
    def __update_published_files(self):
        self.versionList.clear()
        # List available files
        folder = self.publishVersionBox.currentData()
        files = ram.RamFileManager.getRamsesFiles( folder )
        for f in files:
            nm = ram.RamFileInfo()
            fileName = os.path.basename(f)
            if not nm.setFileName(fileName):
                continue
            resource = nm.resource
            if resource == "":
                resource = "/ scene_backup /"
            title = resource + " (" + nm.extension + ")"
            item = qw.QListWidgetItem( title )
            item.setData(qc.Qt.UserRole, f)
            item.setToolTip(fileName)
            self.versionList.addItem(item)

    @qc.Slot()
    def __resource_changed(self, row):

        # Import, list publish files for templates
        if self.importButton.isChecked():
            if self.assetButton.isChecked() or self.shotButton.isChecked():
                return
            self.__list_published_versions()
            return

        if self.replaceButton.isChecked():
            return

        # Open, list versions
        if row < 0:
            self._openButton.setEnabled(False)
        else:
            self._openButton.setEnabled(True)

        if self.recentButton.isChecked():
            return

        self.versionList.clear()

        currentItem = self.getItem()
        if not currentItem:
            return

        # List versions
        versionFiles = ()
        versionFiles = currentItem.versionFilePaths( self.getResource(), self.getStep() )

        if len(versionFiles) == 0:
            return

        versionFiles.reverse()    

        # Add current
        item = qw.QListWidgetItem("Current version")
        item.setData(qc.Qt.UserRole, versionFiles[0])
        self.versionList.addItem(item)

        # Add other versions
        for v in versionFiles:
            fileName = os.path.basename( v )
            nm = ram.RamFileInfo()
            if not nm.setFileName( fileName ):
                continue
            comment = ram.RamMetaDataManager.getComment( v )
            itemText = nm.state + ' | ' + str( nm.version )
            if comment != "":
                itemText = itemText + ' | ' + comment
            item = qw.QListWidgetItem( itemText )
            item.setData(qc.Qt.UserRole, v)
            self.versionList.addItem(item)

    @qc.Slot()
    def __version_changed(self, row):
        self._importButton.setEnabled(row >= 0)
        self._replaceButton.setEnabled(row >= 0)

    @qc.Slot()
    def __import(self):
        self.done(2)

    @qc.Slot()
    def __replace(self):
        self.done(3)

    # <== PUBLIC METHODS ==>

    def setMode(self, mode="open"):
        """Sets the mode of the window, either open, import or replace"""
        if mode == "import":
            self.__import_button_clicked()
        elif mode == "replace":
            self.__replace_button_clicked()
        else:
            self.__open_button_clicked()
        self.__action_changed()

    def setProject(self, project):
        """Sets the selected project"""
        if project is None:
            self.projectBox.setCurrentIndex(-1)
            return
        for i in range(self.projectBox.count()):
            testProject = self.projectBox.itemData(i)
            if not testProject:
                continue
            if testProject == project:
                self.projectBox.setCurrentIndex(i)
                return

        self.projectBox.addItem( str(project), project )
        self.projectBox.setCurrentIndex( self.projectBox.count() - 1)

    def setType( self, itemType):
        """Sets the type of item (asset, shot, template)"""
        if itemType == ram.ItemType.ASSET:
            self.assetButton.setChecked(True)
        elif itemType == ram.ItemType.SHOT:
            self.shotButton.setChecked(True)
        self.__type_changed()

    def setItem(self, itemShortName ):
        """Selects a specific item"""
        self.groupBox.setCurrentIndex(0)
        for i in range( 0, self.itemList.count()):
            listItem = self.itemList.item(i)
            if listItem.data(qc.Qt.UserRole).shortName() == itemShortName:
                self.itemList.setCurrentItem(listItem)
                self.__update_resources()
                return

    def setStep(self, stepShortName):
        """Selects a specific step"""
        for i in range(0, self.stepList.count()):
            listItem = self.stepList.item(i)
            if listItem.data(qc.Qt.UserRole).shortName() == stepShortName:
                self.stepList.setCurrentItem(listItem)
                self.__update_resources()
                return

    def getProject(self):
        """Returns the selected project"""
        return self.projectBox.currentData()

    def getItem(self):
        """Returns the Item (RamAsset, RamShot or RamItem if template) currently selected."""

        # if it's an asset or a shot, get from itemList
        if self.shotButton.isChecked() or self.assetButton.isChecked():
            item = self.itemList.currentItem()
            if not item:
                return None
            return item.data(qc.Qt.UserRole)

        # if it's a template, gets a virtual item from the path of the selected resource (or version if import)
        item = self.resourceList.currentItem()
        if not item:
            return None
        return ram.RamItem.fromPath( item.data(qc.Qt.UserRole), True )

    def getStep(self):
        """Returns the selected step"""
        item = self.stepList.currentItem()
        if not item:
            return None
        return item.data(qc.Qt.UserRole)

    def getResource(self):
        """Returns the selected resource string if any"""
        item = self.resourceList.currentItem()
        if not item:
            return ""

        nm = ram.RamFileInfo()
        nm.setFilePath( item.data(qc.Qt.UserRole) )
        return nm.resource

    def getFile(self):
        """Returns the selected file"""
        # return the selected version if it's not  the current
        rowForCurrent = -1
        if self.openButton.isChecked(): rowForCurrent = 0
        if self.versionList.currentRow() > rowForCurrent:
            return self.versionList.currentItem().data(qc.Qt.UserRole)

        # no version selected, return the resource file
        # We can't import if no version file selected
        if self.importButton.isChecked(): return ""

        # return the selected resource if any
        item = self.resourceList.currentItem()
        if item:
            return item.data(qc.Qt.UserRole)

        # If it's an asset or a shot which is selected, return the default (no resource)
        if self.assetButton.isChecked() or self.shotButton.isChecked():

            currentItem = self.getItem()
            if not currentItem: return ""
            step = self.getStep()
            if not step: return ""

            file = currentItem.stepFilePath("", "ma", step) # Try MA first
            if file != "": return file
            file = currentItem.stepFilePath("", "mb", step) # or MB
            return file

    def getFiles(self):
        """Returns the selected files"""
        if self.versionList.count() == 0:
            return ()

        # De-select the item 0, which is basically "no version"
        if self.openButton.isChecked():
            self.versionList.item(0).setSelected(False)
        items = self.versionList.selectedItems()
        if len(items) == 0:
            return self.getFile()

        files = []
        for item in items:
            files.append( item.data(qc.Qt.UserRole) )
        return files

    def show_import_options(self):
        """Tells if the import options must be shown first"""
        return self.__show_import_options.isChecked()

class ImportSettingsDialog( Dialog ):
    """
    The Dialog to edit import settings
    """

    # <== CONSTRUCTOR ==>

    def __init__(self, parent=None): # pylint: disable=useless-super-delegation
        super(ImportSettingsDialog, self).__init__(parent)
        # <-- Setup -->
        self.__settings_widgets = []
        self.__setup_ui()
        #self._dialog_add_preset_actions()
        self.__connect_events()
        #self.set_preset_folder(IMPORT_PRESETS_PATH)
        #self.__ui_preset_box.setCurrentIndex(-1)
        self.__formats = []

    # <== PRIVATE METHODS ==>

    def __setup_ui(self):
        self.setWindowTitle("Import items")

        uber_layout = qw.QHBoxLayout()
        uber_layout.setSpacing(3)
        self.main_layout.addLayout(uber_layout)

        self.__ui_files_box = qw.QListWidget()
        self.__ui_files_box.setMaximumWidth( 150 )
        #uber_layout.addWidget(self.__ui_files_box)

        self.__ui_stacked_layout = qw.QStackedLayout()
        uber_layout.addLayout(self.__ui_stacked_layout)

        #preset_widget = qw.QWidget()
        #preset_layout = qw.QFormLayout(preset_widget)
        #preset_layout.setFormAlignment(qc.Qt.AlignHCenter | qc.Qt.AlignTop)
        #preset_layout.setSpacing(3)

        #self.__ui_preset_box = qw.QComboBox()
        #preset_layout.addRow("Preset:", self.__ui_preset_box)

        #self.__ui_stacked_layout.addWidget(preset_widget)

        # <-- BOTTOM BUTTONS -->

        buttons_layout = qw.QHBoxLayout()
        buttons_layout.setSpacing(2)
        self.main_layout.addLayout(buttons_layout)

        self.__ui_import_button = qw.QPushButton("Import")
        buttons_layout.addWidget( self.__ui_import_button )
        self.__ui_cancel_button = qw.QPushButton("Cancel")
        buttons_layout.addWidget( self.__ui_cancel_button )

    def __connect_events(self):
        self.__ui_files_box.currentRowChanged.connect( self.__ui_stacked_layout.setCurrentIndex )
        #self.__ui_preset_box.currentIndexChanged.connect( self.__ui_preset_box_current_changed )
        self.__ui_import_button.clicked.connect( self.accept )
        self.__ui_cancel_button.clicked.connect( self.reject )

    # <== PRIVATE SLOTS ==>

    @qc.Slot(int)
    def __ui_preset_box_current_changed(self, index):
        if index < 0:
            return
        file_path = self.__ui_preset_box.itemData(index, qc.Qt.UserRole)
        self.load_preset_file( file_path )

    # <== PRIVATE METHODS ==>

    def __add_file(self, file_dict):
        # Add entry
        fmt = file_dict["format"]
        if fmt == "*" or fmt == "":
            # if already there, ignore
            if fmt == "":
                fmt = "*"
            if fmt in self.__formats:
                return
            self.__formats.append(fmt)
            self.__ui_files_box.addItem("Format: Default (*)")
        else:
            if fmt in self.__formats:
                return
            self.__formats.append(fmt)
            self.__ui_files_box.addItem("Format: " + fmt)
        # Add widget
        widget = ImportSettingsWidget( self )
        self.__ui_stacked_layout.addWidget(widget)
        self.__settings_widgets.append(widget)
        widget.set_options(file_dict)

    # <== PUBLIC METHODS ==>

    def update_preset_files(self, preset_files):
        """Loads the preset files."""
        """if len(preset_files) > 0:
            self.__ui_preset_box.clear()
            for preset_file in preset_files:
                name = os.path.basename(preset_file)
                name = os.path.splitext(name)[0]
                self.__ui_preset_box.addItem(name, preset_file)"""

    def get_options(self):
        """Gets the import options as a dict"""

        options = { }
        formats = []
        for w in self.__settings_widgets:
            formats.append( w.get_options() )

        options['formats'] = formats
        return options

    def set_options(self, options):
        """Loads options from a preset"""
        self.__ui_files_box.clear()
        if self.__settings_widgets:
            for w in self.__settings_widgets:
                self.__ui_stacked_layout.removeWidget(w)
        self.__settings_widgets = []

        # Add Presets
        #self.__ui_files_box.addItem("Select: Preset")

        if not "formats" in options:
            return

        has_default = False
        for f in options['formats']:
            if f['format'] != "*":
                continue
            self.__add_file(f)
            has_default = True

        if not has_default:
            # Add default
            default =  {
                "format": "*"
            }
            self.__add_file(default)

class ImportSettingsWidget( qw.QWidget ):
    """
    The Dialog to edit import settings for a single pipe
    """
    # <== CONSTRUCTOR ==>

    def __init__(self, parent=None): # pylint: disable=useless-super-delegation
        super(ImportSettingsWidget, self).__init__(parent)
        # <-- Setup -->
        self.__setup_ui()
        self.__connect_events()
        self.__format = "*"
        self.__update_preset()

    def __setup_ui(self):
        uber_layout = qw.QHBoxLayout(self)

        # <-- GENERAL -->

        main_layout = qw.QFormLayout()
        main_layout.setFormAlignment(qc.Qt.AlignHCenter | qc.Qt.AlignTop)
        uber_layout.addLayout(main_layout)

        self.__ui_reference_box = qw.QCheckBox("As reference")
        main_layout.addRow("Import:", self.__ui_reference_box )

        self.__ui_reload_reference_box = qw.QCheckBox("Auto-reload reference")
        self.__ui_reload_reference_box.setEnabled(False)
        main_layout.addRow("", self.__ui_reload_reference_box )

        self.__ui_lock_transform_box = qw.QCheckBox("Lock transformations")
        self.__ui_lock_transform_box.setChecked(True)
        main_layout.addRow("", self.__ui_lock_transform_box)

        self.__ui_namespace_box = qw.QCheckBox("Create namespace")
        self.__ui_namespace_box.setChecked(True)
        main_layout.addRow("", self.__ui_namespace_box)

        self.__ui_no_root_shape_box = qw.QCheckBox("Don't add shape")
        self.__ui_no_root_shape_box.setChecked(False)
        main_layout.addRow("Root node:", self.__ui_no_root_shape_box)
    

        self.__ui_apply_shaders_box = qw.QCheckBox("Apply to selected nodes")
        self.__ui_apply_shaders_box.setChecked(True)
        main_layout.addRow("Shaders:", self.__ui_apply_shaders_box)

        # <-- PRESET -->

        preset_widget = qw.QWidget()
        preset_layout = qw.QVBoxLayout(preset_widget)
        preset_layout.setSpacing(3)
        preset_layout.setContentsMargins(3,3,3,3)
        uber_layout.addWidget(preset_widget)

        preset_label = qw.QLabel("You can use this preset in Ramses to set\nthe current settings as default settings for pipes.")
        preset_layout.addWidget(preset_label)
        self.__ui_preset_edit = qw.QTextEdit()
        self.__ui_preset_edit.setReadOnly(True)
        preset_layout.addWidget(self.__ui_preset_edit)

    def __connect_events(self):
        self.__ui_reference_box.toggled.connect( self.__ui_reference_box_clicked )
        self.__ui_lock_transform_box.toggled.connect( self.__update_preset )
        self.__ui_apply_shaders_box.toggled.connect( self.__update_preset )
        self.__ui_no_root_shape_box.toggled.connect( self.__update_preset )
        self.__ui_namespace_box.toggled.connect( self.__update_preset )

    @qc.Slot()
    def __update_preset(self):
        # Main options
        options = self.get_options()
        options_str = yaml.dump(options)
        self.__ui_preset_edit.setText(options_str)

    @qc.Slot(bool)
    def __ui_reference_box_clicked(self, checked):
        self.__ui_lock_transform_box.setDisabled(checked)
        self.__ui_reload_reference_box.setEnabled(checked)
        if checked:
            self.__ui_lock_transform_box.setChecked(False)
        self.__update_preset()

    def get_options(self):
        """Gets the import options as a dict"""

        options = {}
        if self.__format != "":
            options["format"] = self.__format
        
        as_ref = self.__ui_reference_box.isChecked()
        options["as_reference"] = as_ref
        if not as_ref:
            options["autoreload_reference"] = False
            options["lock_transformations"] = self.__ui_lock_transform_box.isChecked()
        else:
            options["lock_transformations"] = False
            options["autoreload_reference"] = self.__ui_reload_reference_box.isChecked()
        
        options["apply_shaders"] = self.__ui_apply_shaders_box.isChecked()

        options["no_root_shape"] = self.__ui_no_root_shape_box.isChecked()

        options["create_namespace"] = self.__ui_namespace_box.isChecked()
        
        return options

    def set_options(self, options):
        """Loads options from a preset"""

        load_bool_preset("lock_transformations", options, self.__ui_lock_transform_box, True)
        load_bool_preset("autoreload_reference", options, self.__ui_reload_reference_box, False)
        load_bool_preset("as_reference", options, self.__ui_reference_box, False)
        load_bool_preset("apply_shaders", options, self.__ui_apply_shaders_box, True)
        load_bool_preset("no_root_shape", options, self.__ui_no_root_shape_box, False)
        load_bool_preset("create_namespace", options, self.__ui_namespace_box, True)

        self.__format = get_option("format", options, "*")

        self.__update_preset()

def publish_sorter(a, b):
    """Sorts published folders"""
    if a == b:
        return 0
    a = a.split(" | ")
    b = b.split(" | ")
    if len(a) != len(b):
        return len(b) - len(a)
    i = 0
    while i < len(a):
        if a[i] < b[i]:
            return -1
        if a[i] > b[i]:
            return 1
    return 0

if __name__ == '__main__':
    dialog = ImportDialog()
    ok = dialog.exec_()
    print(ok)
    if ok == 1:
        print(dialog.getFile())
