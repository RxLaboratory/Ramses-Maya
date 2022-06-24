# -*- coding: utf-8 -*-
"""The entry point for replacing items"""

import yaml
import os
from maya import cmds # pylint: disable=import-error
import ramses
import dumaf
from .utils_attributes import list_ramses_nodes
from .utils_options import get_option
from .update_manager import update
from .ui_import import ImportSettingsDialog
from .import_manager import get_import_group, get_import_namespace, import_file

def replacer(item, file_path, step, edit_import_settings):
    """Runs a few checks and replaces selected nodes with the ones from the filepath"""

    # Get options
    import_options = {}
    import_options_str = step.importSettings()
    if import_options_str != "":
        import_options = yaml.safe_load( import_options_str )

    if edit_import_settings or import_options_str == "":
        import_dialog = ImportSettingsDialog()
        import_dialog.set_options(import_options)
        if step:
            import_dialog.set_incoming_step_name(step.shortName())
        if not import_dialog.exec_():
            return
        import_options = import_dialog.get_options()

    ramses.log("I'm replacing the selected nodes with " + str(item))

    # Keep the list of selected Ramses nodes (the selection changes when importing)
    original_nodes = list_ramses_nodes(selected_only=True)

    # Check if we're getting shaders
    file_name = os.path.basename(file_path)
    file_name = os.path.splitext(file_name)[0]

    # Prepare scene to get its new stuff
    item_group = get_import_group(item)
    item_namespace = get_import_namespace(item)

    lock_transform = False
    lock_transform = get_option("lock_transformations", import_options, True)
    as_reference = get_option("as_reference", import_options, False)

    for original_node in original_nodes:
        new_nodes = import_file(file_path, as_reference, lock_transform, item, item_namespace, item_group, step)
        update(original_node, new_nodes)
        original_node = dumaf.Node(original_node)
        original_node.remove()
