# -*- coding: utf-8 -*-
"""The entry point for replacing items"""

import yaml
import os
from maya import cmds # pylint: disable=import-error
import ramses
import dumaf
from .utils_attributes import list_ramses_nodes, set_import_attributes
from .utils_options import get_option
from .update_manager import update
from .ui_import import ImportSettingsDialog
from .import_manager import get_import_group, get_import_namespace, import_file, get_format_options

def replacer(file_path, item, step, import_options, show_import_options=False):
    """Runs a few checks and replaces selected nodes with the ones from the filepath"""

    extension = os.path.splitext(file_path)[1][1:]

    if show_import_options:
        import_dialog = ImportSettingsDialog()
        if len(import_options['formats']) != 0:
            import_dialog.set_options(import_options)
        else:
            # Set defaults from file paths
            import_options = {}
            formats = []
            if extension != "":
                o = {
                    'format': extension
                }
            formats.append(o)
            import_options['formats'] = formats
            import_dialog.set_options(import_options)

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

    options = get_format_options(file_path, import_options)
    lock_transform = options.get("lock_transformations", "Not set")
    as_reference = options.get("as_reference", "Not set")
    no_root_shape = options.get("no_root_shape", "Not set")

    for original_node in original_nodes:
        # Get the current node settings

        # Make sure the node still exists
        if not cmds.objExists( original_node ):
            continue

        # Get the first child to check the options
        children = cmds.listRelatives( original_node, ad=True, type='transform', fullPath=True)
        if children and len(children) > 0:
            child = children[0]
            # Check if this is a reference, in which case, just replace it,
            # unless the options state otherwise
            if (cmds.referenceQuery(child, isNodeReferenced=True) and
                (as_reference == "Not set" or as_reference == True) ):
                # Get the reference node
                rNode = cmds.referenceQuery( child, referenceNode=True)
                # Reload new file
                cmds.file( file_path, loadReference=rNode )
                # Set new version
                set_import_attributes(original_node, item, step, file_path)
                continue

            # check if transforms are locked
            if lock_transform == "Not set":
                for child in children:
                    child = dumaf.Node(child)
                    if not child.is_transform_locked(recursive=True):
                        lock_transform = False
                        break

        # check if there's a root shape
        if no_root_shape == "Not set":
            ctrl_shape = cmds.listRelatives(original_node, shapes=True, f=True, type='nurbsCurve')
            no_root_shape = False
            if not ctrl_shape:
                no_root_shape = True

        # Clean the options
        if no_root_shape == "Not set":
            no_root_shape = False
        if lock_transform == "Not set":
            lock_transform = True
        if as_reference == "Not set":
            as_reference = False

        new_nodes = import_file(file_path, as_reference, lock_transform, no_root_shape, item, item_namespace, item_group, step, autoreload_reference=False)
        update(original_node, new_nodes)
        original_node = dumaf.Node(original_node)
        original_node.remove()
