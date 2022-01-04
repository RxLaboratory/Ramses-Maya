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

"""A wrapper class for maya nodes"""

import re
import maya.cmds as cmds  # pylint: disable=import-error

class DuMaNode():
    """A wrapper class for maya nodes"""

    nonDeletableObjects = [
        '|frontShape',
        '|front',
        '|perspShape',
        '|persp',
        '|sideShape',
        '|side',
        '|topShape',
        '|top',
        'initialShadingGroup',
        'initialParticleSE',
        'lambert1',
        'standardSurface1',
        'particleCloud1',
    ]

    # <== Constructor ==>

    def __init__(self, nodePath):

        if isinstance(nodePath, DuMaNode):
            # Copy constructor

            # Get the uuid
            self.__uuid = nodePath.uuid()
        else:
            # Get the uuid
            # For some reason, Maya returns the short names if queried with uuid,
            # We need to get the full paths first...
            nPath = cmds.ls(nodePath, long=True)
            if len(nPath) > 0:
                self.__uuid = cmds.ls(nPath, uuid=True)[0]
            else:
                raise ValueError("Sorry, the node '" + nodePath + "' doesn't exist.")

    # <== Static ==>

    @staticmethod
    def getDuMaNodes(nodePathsOrUuids):
        """Returns a list of DuMaNodes"""
        if nodePathsOrUuids is None:
            return []
        nodes = []
        for nodePath in nodePathsOrUuids:
            nodes.append(DuMaNode(nodePath))
        return nodes

    @staticmethod
    def getCreateGroup(groupName, parentNode=None):
        """Gets or create a group with the groupName in the parentNode"""
        groupName = groupName.replace(' ', '_')
        # Check if exists
        if parentNode is None:
            if not groupName.startswith('|'):
                groupName = '|' + groupName
            if cmds.objExists(groupName):
                groupNode = DuMaNode(groupName)
                if groupNode.isGroup():
                    return groupNode
        else:
            parentNode = DuMaNode(parentNode)
            childNodes = parentNode.children(recursive=False, transformOnly=True)
            if len(childNodes) > 0:
                # May end with a number
                reStr = '^' + re.escape(groupName) + '\\d*$'
                regex = re.compile(reStr)
                for childNode in childNodes:
                    childName = childNode.name()
                    if re.match( regex, childName ):
                        return childNode
        # Create the group
        groupPath = cmds.group( name= groupName, em=True )
        if not groupPath.startswith('|'):
            groupPath = '|' + groupPath
        groupNode = DuMaNode(groupPath)
        groupNode.parentTo(parentNode)
        return groupNode

    @staticmethod
    def getEmptyGroups(parentNode=None):
        """Gets all empty groups children of the parent node or in the scene"""
        nodes = ()
        emptyGroups = []

        if parentNode is None:
            nodes = cmds.ls(type='transform')
            nodes = DuMaNode.getDuMaNodes(nodes)
        else:
            parentNode = DuMaNode(parentNode)
            nodes = parentNode.children(transformOnly=True)

        for testNode in nodes:
            if not testNode.isGroup():
                continue
            if not testNode.hasChildren():
                emptyGroups.append(testNode)
        return emptyGroups


    @staticmethod
    def removeEmptyGroups(parentNode=None):
        """Removes all empty groups from the scene or the given parent node"""
        emptyGroups = DuMaNode.getEmptyGroups(parentNode)
        while len(emptyGroups) > 0:
            for group in emptyGroups:
                group.remove()
            emptyGroups = DuMaNode.getEmptyGroups(parentNode)

    # <== Public ==>

    def name(self, keepNameSpace = False):
        """Returns the name of the node"""
        if not self.exists():
            return ''
        nodePath = self.path()
        nodeName = nodePath.split('|')[-1]
        if not keepNameSpace:
            nodeName = nodeName.split(':')[-1]
        return nodeName

    def checkType(self, deleteIfEmpty=True, typesToKeep=()):
        """Checks if the node contains one of the given types.
        If not, the node is removed, and optionally if it is empty.
        Note: extra shapes will be removed.
        Returns False if the node is removed."""

        if not self.exists:
            return False

        self.removeExtraShapes()

        shapeType = self.shapeType()

        # no shape, remove if it is empty
        if shapeType == '':
            if not self.hasChildren() and deleteIfEmpty:
                self.remove()
                return False

        # if we keep everything
        if len(typesToKeep) == 0:
            return True

        # Check type
        if not shapeType in typesToKeep:
            self.removeShape()
            # If it is empty, remove
            if not self.hasChildren() and deleteIfEmpty:
                self.remove()
                return False

        return True

    def children(self, recursive=True, transformOnly=False):
        """Gets the children of this node"""
        if not self.exists():
            return []
        children = []
        nodePath = self.path()
        if transformOnly:
            children = cmds.listRelatives(
                nodePath,
                ad=recursive,
                type='transform'
            )
        else:
            children = cmds.listRelatives(
                nodePath,
                ad=recursive
            )
        if children is None:
            return []
        return DuMaNode.getDuMaNodes(children)

    def createRootController(self, ctrlName):
        """Creates and returns a curve to be used as a controller for this node"""
        if not self.exists():
            return None
        nodePath = self.path()
        # Get the bounding box
        boundingBox = cmds.exactWorldBoundingBox( nodePath )
        xmax = boundingBox[3]
        xmin = boundingBox[0]
        zmax = boundingBox[5]
        zmin = boundingBox[2]
        # Get the 2D Projection on the floor (XZ) lengths
        boundingWidth = xmax - xmin
        boundingLength = zmax - zmin
        # Compute a margin relative to mean of these lengths
        margin = ( boundingWidth + boundingLength ) / 2.0
        # Make it small
        margin = margin / 20.0
        # Create a shape using this margin and coordinates
        cv1 = ( xmin - margin, 0, zmin - margin)
        cv2 = ( xmax + margin, 0, zmin - margin)
        cv3 = ( xmax + margin, 0, zmax + margin)
        cv4 = ( xmin - margin, 0, zmax + margin)
        cv5 = cv1
        controller = cmds.curve( d=1, p=[cv1, cv2, cv3, cv4, cv5], k=(0,1,2,3,4), name=ctrlName)
        controller = DuMaNode(controller)
        # Parent the node
        self.parentTo(controller)
        return controller

    def deleteHistory(self):
        """Deletes the construction history of the node"""
        if not self.exists():
            return

        shapes = self.shapes()
        for shape in shapes:
            shape.deleteHistory()

        nodePath = self.path()
        cmds.delete(nodePath, constructionHistory=True)

    def exists(self):
        """Checks if this node still exists in the scene"""
        nodePath = self.path()
        if nodePath == '':
            return False
        return cmds.objExists(nodePath)

    def freezeTransform(self):
        """Resets the transformation matrix to 0"""
        if not self.exists():
            return

        # Works only from transform nodes
        if not self.isTransform():
            return

        nodePath = self.path()
        cmds.move(0, 0, 0, nodePath + ".rotatePivot", absolute=True)
        cmds.move(0, 0, 0, nodePath + ".scalePivot", absolute=True)
        cmds.makeIdentity(nodePath, apply=True, t=1, r=1, s=1, n=0)

    def getAttr(self, attribute):
        """Gets the value of the Maya attribute"""
        if not self.exists():
            return None
        if not self.hasAttr(attribute):
            return None

        nodePath = self.path()
        return cmds.getAttr(nodePath + '.' + attribute)

    def hasChildren(self):
        """Checks if the nodes has any children"""
        if not self.exists():
            return False
        return len(self.children(transformOnly=True)) != 0

    def hasParent(self):
        """Checks if the node has a parent"""
        if not self.exists():
            return False
        return cmds.listRelatives(self.path(), p=True, f=True) is not None

    def hasAttr(self, attribute):
        """Checks if the nodes has the given Maya attribute"""
        if not self.exists():
            return False
        nodePath = self.path()
        return cmds.attributeQuery(attribute, n=nodePath, exists=True)

    def importReference(self):
        """Imports the reference file is this node is part of a reference"""
        if not self.exists():
            return
        if not self.isReferenced():
            return

        refFile = self.referenceFile()
        cmds.file(refFile, importReference=True)

    def isGroup(self):
        """Check if the node is a group (does not have any shape)"""
        if not self.exists():
            return False
        # A group is a transform node
        if not self.isTransform():
            return False
        # And it does not have any child shape
        nodePath = self.path()
        return cmds.listRelatives(nodePath, s=True, f=True) is None

    def isHidden(self):
        """Checks if the node is hidden.
        Note that if it does not have a visibility attribute,
        this function returns False"""
        if not self.exists():
            return False
        if not self.hasAttr('visibility'):
            return False
        return self.getAttr('visibility') == 0

    def isReferenced(self):
        """Checks if this node is part of a reference"""
        if not self.exists():
            return False
        nodePath = self.path()
        return cmds.referenceQuery(nodePath, isNodeReferenced=True)

    def isTransform(self):
        """Checks if this is a transform node"""
        if not self.exists():
            return False
        return cmds.nodeType(self.path()) == 'transform'

    def isVisible(self):
        """Checks if the node is visible.
        Note that if it does not have a visibility attribute,
        this function returns True"""
        if not self.exists():
            return False
        return not self.isHidden()

    def lockTransform(self, lockNode=True, lockChildren=False):
        """Locks all transformation of the node"""
        if not self.exists():
            return
        # This is not a transform node
        if not self.isTransform():
            return
        if lockChildren:
            children = self.children(transformOnly=True)
            for child in children:
                child.lockTransform(lockNode)

        nodePath = self.path()
        for attr in ['.tx', '.ty', '.tz', '.rx', '.ry', '.rz', '.sx', '.sy', '.sz']:
            cmds.setAttr(nodePath + attr, lock=lockNode)

    def lockVisibility(self, lockNode=True, lockChildren=False):
        """Locks the visibility of the node"""
        if not self.exists():
            return

        if lockChildren:
            children = self.children(transformOnly=True)
            for child in children:
                child.lockVisibility(lockNode)

        nodePath = self.path()
        if not cmds.attributeQuery('visibility', n=nodePath, exists=True):
            return
        cmds.setAttr(nodePath + '.visibility', lock=lockNode)

    def moveToZero(self):
        """Moves the node to the [0,0,0] coordinate (translation)"""
        if not self.exists():
            return
        # Unlock transform to be able to move
        self.lockTransform(False)
        nodePath = self.path()
        cmds.setAttr(nodePath + '.tx', 0)
        cmds.setAttr(nodePath + '.ty', 0)
        cmds.setAttr(nodePath + '.tz', 0)

    def parent(self):
        """Gets the parent node"""
        if not self.exists():
            return None

        nodePath = self.path()
        prnt = cmds.listRelatives(nodePath, p=True, f=True)

        if prnt is not None:
            return DuMaNode(prnt[0])

        return None

    def parentTo(self, parent, rel=False):
        """Parents the node to the parent"""
        if not self.exists():
            return

        nodePath = self.path()

        toWorld = False
        if parent is None:
            toWorld = True
        elif parent == '|':
            toWorld = True

        try:
            if toWorld:
                cmds.parent(nodePath, world=True)
            else:
                parent = DuMaNode(parent)
                parentPath = parent.path()
                cmds.parent(nodePath, parentPath, relative=rel)
        except Exception:
            pass

    def path(self):
        """Returns the full path for the node"""
        paths = cmds.ls(self.__uuid, long=True)
        if len(paths) == 0:
            return ''
        return paths[0]

    def referenceFile(self):
        """Gets the source file of the reference if this node is part of a reference"""
        if not self.exists():
            return

        if not self.isReferenced:
            return None

        nodePath = self.path()
        return cmds.referenceQuery(nodePath, filename=True)

    def remove(self):
        """Deletes the node from the scene,
        even if it's in a reference or contains a reference.
        Warning: this will import the reference!"""
        if not self.exists():
            return

        children = self.children(transformOnly=True)
        for child in children:
            child.importReference()
        nodePath = self.path()
        cmds.delete(nodePath)

    def removeShape(self):
        """Removes the shape from this node"""
        if not self.exists():
            return
        self.removeExtraShapes()
        shape = self.shape()
        if shape is not None:
            shape.remove()

    def removeExtraShapes(self):
        """Removes all extra shapes from this node"""
        if not self.exists():
            return
        # The shape(s) of this node
        shapes = self.shapes()
        # Remove supplementary shapes
        # (Maya may store more than a single shape in transform nodes
        # because of the dependency graph)
        if len(shapes) > 1:
            for shape in shapes[1:]:
                shape.remove()

    def renameShapes(self):
        """Automatically renames the shapes after the transform node name"""
        if not self.exists():
            return
        nodePath = self.path()
        # list all shapes
        shapes = cmds.listRelatives(nodePath,s=True,f=True)
        if shapes is None:
            return

        for shape in shapes:
            cmds.rename(shape, self.name() + 'Shape')

    def select(self):
        """Adds the node to the current selection"""
        if not self.exists():
            return
        cmds.select(self.path(), add=True)

    def shapes(self):
        """Gets all the shapes of this node"""
        if not self.exists():
            return []
        nodePath = self.path()
        # The shapes of this node
        shapePaths = cmds.listRelatives(nodePath,s=True,f=True)
        return DuMaNode.getDuMaNodes(shapePaths)

    def shape(self):
        """Gets the main shape of this node"""
        if not self.exists():
            return []
        shapes = self.shapes()
        if len(shapes) == 0:
            return None
        return shapes[0]

    def snap(self, targetNode):
        """Moves the node to the target.
        The current translation value is kept (offset from current parent is kept)"""
        if not self.exists():
            return

        # Keep the current parent
        parent = self.parent()

        # Parent with snap
        self.parentTo(targetNode, True)

        # Reparent
        self.parentTo(parent)

    def shapeType(self):
        """Checks the type of the shape of this node"""
        if not self.exists():
            return ''
        shape = self.shape()
        if shape is None:
            return ''
        shapePath = shape.path()
        return cmds.nodeType(shapePath)

    def unParent(self):
        """Unparents (= parents to the world) the node"""
        if not self.exists():
            return
        self.parentTo('|')

    def uuid(self):
        """Returns the uuid of this node"""
        return self.__uuid


if __name__ == '__main__':
    # A test node
    node = DuMaNode('pCube1')

    print(node.path())
    print(node.deleteHistory())
