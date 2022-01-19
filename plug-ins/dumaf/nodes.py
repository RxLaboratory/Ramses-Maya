# -*- coding: utf-8 -*-

# Functions to handle nodes.

import re
import maya.cmds as cmds # pylint: disable=import-error
from .paths import Path

class Node():

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

    @staticmethod
    def check( node, deleteIfEmpty = True, typesToKeep=() ):
        """Deletes extra shapes from the node, and optionnaly remove it if empty/not in one of given types"""
        
        if not cmds.objExists(node):
            return False
        
        # The shape(s) of this node
        shapes = cmds.listRelatives(node,s=True,f=True)

        if shapes is None:
            # No shapes, no child: empty group to remove
            if not Node.hasChildren(node) and deleteIfEmpty:
                cmds.delete(node)
                # Finished
                return False
            return True

        if len(typesToKeep) == 0: return True

        # Check type
        shapeType = cmds.nodeType( shapes[0] )
        if not shapeType in typesToKeep:
            cmds.delete(shapes[0])
            if not Node.hasChildren(node) and deleteIfEmpty:
                cmds.delete(node)
                # Finished
                return False
            
        return True

    @staticmethod
    def deleteHistory( node ):
        # The shape(s) of this node
        shapes = cmds.listRelatives(node,s=True,f=True)
        if shapes is None: return
        for shape in shapes:
            cmds.delete(shape, constructionHistory=True)

    @staticmethod
    def removeExtraShapes( node ):
        # The shape(s) of this node
        shapes = cmds.listRelatives(node,s=True,f=True)
        if shapes is None: return
        # Remove supplementary shapes
        # (Maya may store more than a single shape in transform nodes because of the dependency graph)
        if len(shapes) > 1:
            cmds.delete(shapes[1:])

    @staticmethod
    def centerPivot( transformNode ):
        cmds.move(0, 0, 0, transformNode + ".rotatePivot", absolute=True)
        cmds.move(0, 0, 0, transformNode + ".scalePivot", absolute=True)

    @staticmethod
    def freezeTransform(transformNode):
        try:
            cmds.makeIdentity(transformNode, apply=True, t=1, r=1, s=1, n=0)
        except RuntimeError:
            return
        Node.centerPivot(transformNode)

    @staticmethod
    def renameShapes( node ):
        # The shape(s) of this node
        shapes = cmds.listRelatives(node,s=True,f=True)
        if shapes is None: return
        for shape in shapes:
            cmds.rename(shape, Path.baseName(node) + 'Shape')  

    @staticmethod
    def createRootCtrl( node, ctrlName ):
        # Get the bounding box
        boundingBox = cmds.exactWorldBoundingBox( node )
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
        # Parent the node
        node = Node.parent(node, controller)
        return (node, controller)

    @staticmethod
    def delete( node ):
        """Deletes a node, even if it's in a reference or contains a reference.
        Warning: This will import the reference!"""
        children = cmds.listRelatives( node, ad=True, type='transform')
        if children:
            for child in children:
                if cmds.referenceQuery( child, isNodeReferenced=True):
                    refFile = cmds.referenceQuery( child, filename=True)
                    # import
                    cmds.file( refFile, importReference = True)
        cmds.delete( node )

    @staticmethod
    def hasChildren(node):
        return cmds.listRelatives(node, c=True, f=True, type='transform') is not None

    @staticmethod
    def parent( child, parent, r=False):
        """Fixed Parenting for Maya: returns a proper path instead of just the node name,
        and keeps the path absolute if arguments are absolute."""
        try:
            if parent != '|':
                child = cmds.parent( child, parent, relative=r )[0]
            else:
                child = cmds.parent(child, world=True)[0]
                return '|' + child
        except: # if the child is already parent to this parent
            return child
        # If maya returned a (relative?) path, we need to get the node name
        # (-> sometimes a path is returned, sometimes just the node name, depending on the fact
        # that the node name is unique in the scene or not)
        # Note that what Maya returns is never absolute (never starts with '|')
        child = Path.baseName( child, True)
        # Prepend again the parent path
        child = parent + '|' + child
        return child

    @staticmethod
    def isTransform( node ):
        return cmds.nodeType(node) == 'transform'

    @staticmethod
    def lockTransform( transformNode, l=True, recursive=False ):
        if recursive:
            nodes = cmds.listRelatives(transformNode, ad=True, f=True, type='transform')
            if nodes is None: nodes = []
            nodes.append( transformNode )
            for node in nodes: Node.lockTransform(node, l, False)
        if not Node.isTransform( transformNode ) :
            return
        for a in ['.tx','.ty','.tz','.rx','.ry','.rz','.sx','.sy','.sz']:
            cmds.setAttr(transformNode + a, lock=l )
            
    @staticmethod
    def hasAttr( node, attr):
        return cmds.attributeQuery( attr, n=node, exists=True )

    @staticmethod
    def isVisible(node):
        if Node.hasAttr( node, 'visibility' ):
            return cmds.getAttr(node + '.v') == 1
        return True

    @staticmethod
    def lockVisibility( node, l=True ):
        if not cmds.attributeQuery( 'visibility', n=node, exists=True ): return
        cmds.setAttr(node+'.visibility',lock=l)

    @staticmethod
    def lockHiddenVisibility():
        for node in cmds.ls(long=True):
            if Node.isHidden(node): Node.lockVisibility( node, True )

    @staticmethod
    def snap( nodeFrom, nodeTo):
        prevParent = cmds.listRelatives(nodeFrom, p = True, f = True)
        if prevParent is not None:
            prevParent = prevParent[0]
        nodeFrom = Node.parent( nodeFrom, nodeTo, True )

        if prevParent is not None:
            nodeFrom = Node.parent( nodeFrom, prevParent )
            return nodeFrom
        
        nodeFrom = Node.parent( nodeFrom, '|' )
        return nodeFrom

    @staticmethod
    def isHidden( node ):
        if not cmds.attributeQuery( 'visibility', n=node, exists=True ):
            return False
        return cmds.getAttr(node + '.visibility') == 0

    @staticmethod
    def getCreateGroup( groupName, parentNode=None ):
        groupName = groupName.replace(' ', '_')
        # Check if exists
        if parentNode is None:
            if not groupName.startswith('|'):
                groupName = '|' + groupName
            if cmds.objExists(groupName) and Node.isGroup(groupName):
                return groupName
        else:
            # Get parentNode full path
            parentNode = cmds.ls(parentNode, long=True)[0]
            c = cmds.listRelatives(parentNode, children=True, type='transform')
            if c is not None:
                # May end with a number
                reStr = '^' + re.escape(groupName) + '\\d*$'
                regex = re.compile(reStr)
                for cn in c:
                    if re.match( regex, cn ):
                        return parentNode + '|' + cn
        # Create the group
        n = cmds.group( name= groupName, em=True )
        if not n.startswith('|'):
            n = '|' + n
        if parentNode is not None:
            n = Node.parent( n, parentNode)
        return n

    @staticmethod
    def isGroup(node):
        # A group is a transform node
        if cmds.objectType(node) != 'transform':
            return False
        # And it does not have any child shape
        return cmds.listRelatives(node,s=True,f=True) is None

    @staticmethod
    def hasParent(node):
        return cmds.listRelatives(node, p=True, f=True) is not None

    @staticmethod
    def moveToZero(node):
        Node.lockTransform( node, False )
        cmds.setAttr(node + '.tx',0)
        cmds.setAttr(node + '.ty',0)
        cmds.setAttr(node + '.tz',0)

    @staticmethod
    def removeEmptyGroups(node=None):
        nodes = ()
        
        if node is None:
            nodes = cmds.ls(type='transform')
        else:
            nodes = cmds.listRelatives(node, ad=True, f=True, type='transform')

        if nodes is None:
            return

        for node in nodes:
            if not Node.isGroup(node):
                continue
            if not Node.hasChildren(node):
                cmds.delete(node)

    @staticmethod
    def select(nodes):
        cmds.select(cl=True)
        for n in nodes:
            try:
                cmds.select(n, noExpand=True, add=True)
            except:
                pass
