# -*- coding: utf-8 -*-

# ====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# ======================= END GPL LICENSE BLOCK ========================

"""Tools to handle node attributes"""

import maya.cmds as cmds # pylint: disable=import-error

def get_all_extra( root_node_path, recursive=True):
    """List all extra attributes in this node (and its children)"""

    # List this node attributes
    attributes = cmds.listAttr(root_node_path, userDefined=True)
    if attributes is None:
        attributes = set()
    else:
        attributes = set(attributes)

    # Recursion
    if recursive:
        children = cmds.listRelatives(
                root_node_path,
                ad=recursive,
                fullPath=True
            )
        if not children:
            return set(attributes)
        for child in children:
            child_attrs = get_all_extra( child, recursive=False)
            attributes.update(child_attrs)

    return attributes
