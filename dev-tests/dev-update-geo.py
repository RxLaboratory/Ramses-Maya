import os, re

from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module disable=import-error
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QCheckBox,
    QPushButton,
    QAbstractItemView,
)

from PySide2.QtCore import ( # pylint: disable=no-name-in-module disable=import-error
    Slot,
    Qt,
)

import maya.cmds as cmds # pylint: disable=import-error
from dumaf import getMayaWindow # pylint: disable=import-error
import dumaf as maf # pylint: disable=import-error
import ramses as ram # pylint: disable=import-error

class RamsesAttribute():
    MANAGED = 'ramsesManaged'
    STEP = 'ramsesStep'
    ITEM = 'ramsesItem'
    ASSET_GROUP = 'ramsesAssetGroup'
    ITEM_TYPE = 'ramsesItemType'
    GEO_FILE = 'ramsesGeoFilePath'
    GEO_TIME = 'ramsesGeoTimeStamp'
    SHADING_TYPE = 'ramsesShadingType'
    SHADING_FILE = 'ramsesShadingFilePath'
    SHADING_TIME = 'ramsesShadingTimeStamp'
    DT_TYPES = ('string')
    AT_TYPES = ('long', 'bool')

def setRamsesAttr( node, attr, value, t):
    # Add if not already there
    if attr not in cmds.listAttr(node):
        if t in RamsesAttribute.DT_TYPES:
            cmds.addAttr( node, ln= attr, dt=t)
        else:
            cmds.addAttr( node, ln=attr, at=t)
    # Unlock
    cmds.setAttr( node + '.' + attr, lock=False )
    # Set
    if t in RamsesAttribute.DT_TYPES:
        cmds.setAttr( node + '.' + attr, value, type=t)
    else:
        cmds.setAttr( node + '.' + attr, value )    
    # Lock
    cmds.setAttr( node + '.' + attr, lock=True )

def getRamsesAttr( node, attr):
    if attr not in cmds.listAttr(node):
        return None
    return cmds.getAttr(node + '.' + attr)

def setRamsesManaged(node, managed=True):
    setRamsesAttr( node, RamsesAttribute.MANAGED, True, 'bool' )

def isRamsesManaged(node):
    return getRamsesAttr( node, RamsesAttribute.MANAGED )

def listRamsesNodes():
    # Scan all transform nodes
    transformNodes = cmds.ls(type='transform', long=True)
    nodes = []

    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Scanning Scene for Ramses Nodes")
    progressDialog.setMaximum(len(nodes))

    for node in transformNodes:
        progressDialog.increment()
        if isRamsesManaged(node):
            nodes.append(node)

    progressDialog.hide()
    return nodes

def snapNodeTo( nodeFrom, nodeTo):
    prevParent = cmds.listRelatives(nodeFrom, p = True, f = True)
    if prevParent is not None:
        prevParent = prevParent[0]
    nodeFrom = cmds.parent( nodeFrom, nodeTo, relative = True )[0] 
    # Maya, the absolute path please...
    nodeFrom = nodeTo + '|' + nodeFrom

    if prevParent is not None:
        nodeFrom = cmds.parent( nodeFrom, prevParent )[0]
        # Maya, the absolute path please...
        return prevParent + '|' + nodeFrom
    
    nodeFrom = cmds.parent( nodeFrom, world=True)[0]
    # Maya, the absolute path please...
    return '|' + nodeFrom

# mode is 'vp' for viewport, 'rdr' for rendering
def importShaders(node, mode, filePath, itemShortName=''):
    # Get shader data
    shaderData = ram.RamMetaDataManager.getValue(filePath,'shaderData')
    if shaderData is None:
        ram.log("I can't find any shader for this geometry, sorry.")
        return
    if 'shaderFilePath' not in shaderData:
        ram.log("I can't find any shader for this geometry, sorry.")
        return
    shaderFile = shaderData['shaderFilePath']
    if not os.path.isfile(shaderFile):
        ram.log("I can't find the shader file, sorry. It should be there: " + shaderFile)
        return
    
    # For all mesh
    meshes = cmds.listRelatives( node, ad=True, type='mesh', f=True)
    if meshes is None:
        ram.log("I can't find any geometry to apply the shaders, sorry.")
        return

    # Reinit the shaders on everything (in case we're just reloading the shaders)
    cmds.select(node,r=True)
    cmds.sets(e=True,forceElement='initialShadingGroup')

    # If already referenced, get the existing reference and clean it
    isAlreadyReferenced = False
    try:
        cmds.referenceQuery( shaderFile, namespace=True )
        isAlreadyReferenced = True
    except:
        pass

    if not isAlreadyReferenced:
        # Reference the shader file
        cmds.file(shaderFile,r=True,mergeNamespacesOnClash=True,namespace=itemShortName)

    for mesh in meshes:
        # Get the transform node (which has the name we're looking for)
        transformNode = cmds.listRelatives(mesh, p=True, type='transform')[0]
        nodeName = maf.getNodeBaseName( transformNode )
        if nodeName not in shaderData:
            continue
        meshShaderData = shaderData[nodeName]
        if not meshShaderData['hasShader']:
            continue
        # Apply
        cmds.select(mesh, r=True)
        shader = meshShaderData['shader']
        if shader != 'initialShadingGroup':
            shaderName = itemShortName + ':' + shader
            cmds.sets(e=True, forceElement = shaderName)
        else:
            cmds.sets(e=True,forceElement='initialShadingGroup')
        # Set opaque
        if meshShaderData['opaque']:
            cmds.setAttr(mesh + '.aiOpaque', 1)
        else:
            cmds.setAttr(mesh + '.aiOpaque', 0)

    cmds.select(clear=True)

    # Shading Data
    timestamp = os.path.getmtime( shaderFile )

    setRamsesManaged( node )
    setRamsesAttr( node, RamsesAttribute.SHADING_TYPE, mode, 'string')
    setRamsesAttr( node, RamsesAttribute.SHADING_FILE, shaderFile, 'string')
    setRamsesAttr( node, RamsesAttribute.SHADING_TIME, timestamp, 'long')

def importMod(item, filePath, step):

    # Checks
    if step != 'MOD':
        return

    if item.itemType() != ram.ItemType.ASSET:
        ram.log("Sorry, this is not a valid Asset, I won't import it.")
        return

    # Progress
    progressDialog = maf.ProgressDialog()
    progressDialog.show()
    progressDialog.setText("Importing Geometry")
    progressDialog.setMaximum(2)

    # Get info
    itemShortName = item.shortName()
    itemType = ram.ItemType.ASSET
    assetGroupName = item.group()
    # Get the file timestamp
    timestamp = os.path.getmtime( filePath )
    timestamp = int(timestamp)

    # Get the Asset Group
    assetGroup = 'RamASSETS_' + assetGroupName
    assetGroup = maf.getCreateGroup( assetGroup )

    # Check if the short name is not made only of numbers
    regex = re.compile('^\\d+$')
    if re.match(regex, itemShortName):
        itemShortName = itemType + itemShortName

    # Get the Item Group
    itemGroup = maf.getCreateGroup( itemShortName, assetGroup )

    # Import the file
    progressDialog.setText("Importing file...")
    progressDialog.increment()
    newNodes = cmds.file(filePath,i=True,ignoreVersion=True,mergeNamespacesOnClash=True,returnNewNodes=True,ns=itemShortName)

    # Get the controler, and parent nodes to the group
    progressDialog.setText("Tidying...")
    progressDialog.increment()
    progressDialog.setMaximum( len(newNodes) + 2 )
    rootCtrl = ''
    rootCtrlShape = ''
    for node in newNodes:
        progressDialog.increment()
        # When parenting the root, children won't exist anymore
        if not cmds.objExists(node):
            continue
        # only the root
        if maf.hasParent(node):
            continue
        if not cmds.nodeType(node) == 'transform':
            continue
        # Parent to the item group
        rootCtrl = cmds.parent(node, itemGroup)[0]
        # get the full path please... Maya...
        rootCtrl = itemGroup + '|' + rootCtrl
        if '_root' in node:
            # Get the shape
            nodeShapes = cmds.listRelatives(rootCtrl, shapes=True, f=True, type='nurbsCurve')
            if nodeShapes is None:
                continue
            rootCtrlShape = nodeShapes[0]
            # Adjust root appearance
            cmds.setAttr(rootCtrlShape+'.overrideEnabled', 1)
            cmds.setAttr(rootCtrlShape+'.overrideColor', 18)
            cmds.rename(rootCtrlShape,rootCtrl + 'Shape')

        # Adjust root object
        cmds.setAttr(rootCtrl+'.useOutlinerColor',1)
        cmds.setAttr(rootCtrl+'.outlinerColor',0.392,0.863,1)

        # Store Ramses Data!
        setRamsesManaged( rootCtrl )
        setRamsesAttr( rootCtrl, RamsesAttribute.GEO_FILE, filePath, 'string' )
        setRamsesAttr( rootCtrl, RamsesAttribute.GEO_TIME, timestamp, 'long' )
        setRamsesAttr( rootCtrl, RamsesAttribute.STEP, step, 'string' )
        setRamsesAttr( rootCtrl, RamsesAttribute.ITEM, item.shortName(), 'string' )
        setRamsesAttr( rootCtrl, RamsesAttribute.ITEM_TYPE, itemType, 'string' )
        setRamsesAttr( rootCtrl, RamsesAttribute.ASSET_GROUP, item.group(), 'string' )

        # Lock transform
        children = cmds.listRelatives(rootCtrl, ad=True, f=True, type='transform')
        for child in children:
            maf.lockTransform(child)

        # Import shaders
        importShaders(rootCtrl, 'vp', filePath, itemShortName)
        
    progressDialog.hide()
    return rootCtrl

class UpdateDialog( QDialog ):

    def __init__(self, parent = None):
        super(UpdateDialog, self).__init__(parent)
        self.__setupUi()
        self.__listItems()
        self.__connectEvents()

    def __setupUi(self):

        self.setWindowTitle("Update Items")

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        self.onlyNewButton = QCheckBox("Show only updated items.")
        self.onlyNewButton.setChecked(True)
        mainLayout.addWidget( self.onlyNewButton )

        self.itemList = QListWidget()
        self.itemList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        mainLayout.addWidget(self.itemList)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)

        self._updateButton = QPushButton("Update All")
        self._updateButton.setEnabled(False)
        buttonsLayout.addWidget( self._updateButton )
        self._updateSelectedButton = QPushButton("Update Selected")
        self._updateSelectedButton.setEnabled(False)
        buttonsLayout.addWidget( self._updateSelectedButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )

        mainLayout.addLayout( buttonsLayout )

        self.setLayout( mainLayout )

    def __connectEvents(self):
        self._updateButton.clicked.connect( self.accept )
        self._cancelButton.clicked.connect( self.reject )
        self.onlyNewButton.clicked.connect( self.showOnlyNew )
        self.itemList.itemSelectionChanged.connect( self.selectionChanged )
        self._updateSelectedButton.clicked.connect( self._updateSelected )

    Slot()
    def _updateSelected(self):
        self.done(2)

    Slot()
    def selectionChanged(self):
        items = self.itemList.selectedItems()
        self._updateSelectedButton.setEnabled(len(items) > 0)

    Slot()
    def showOnlyNew(self, checked = True):
        for i in range(0, self.itemList.count()):
            if not checked:
                self.itemList.item(i).setHidden(False)
            else:
                itemText = self.itemList.item(i).text()
                hidden =  not itemText.startswith('New: ')
                self.itemList.item(i).setHidden(hidden)
                if hidden:
                    self.itemList.item(i).setSelected(False)

    def __listItems(self):
        nodes = listRamsesNodes()
        if len(nodes) == 0:
            self._updateButton.setEnabled(False)
            self._updateSelectedButton.setEnabled(False)
            return
        self._updateButton.setEnabled(True)
        for node in nodes:
            name = getRamsesAttr(node, RamsesAttribute.ITEM )
            step = getRamsesAttr(node, RamsesAttribute.STEP )
            item = QListWidgetItem( self.itemList )
            item.setData(Qt.UserRole, node)
            item.setToolTip(node)
            print(node)
            itemText = name + ' (' + step + ') - ' + node.split(':')[-1]
            # Check timestamp
            geoFile = getRamsesAttr(node, RamsesAttribute.GEO_FILE)
            geoTime = getRamsesAttr(node, RamsesAttribute.GEO_TIME)
            shadingFile = getRamsesAttr(node, RamsesAttribute.SHADING_FILE)
            shadingTime = getRamsesAttr(node, RamsesAttribute.SHADING_TIME)
            updated = False
            if geoFile is not None:
                geoFTimeStamp = os.path.getmtime( geoFile )
                geoFTimeStamp = int(geoFTimeStamp)
                if geoFTimeStamp > geoTime:
                    updated = True
            # Shaders a referenced, they're always up-to-date
            # if shadingFile is not None:
            #     shadingFTimeStamp = os.path.getmtime( shadingFile )
            #     shadingFTimeStamp = int( shadingFTimeStamp )
            #     if shadingFTimeStamp > shadingTime:
            #         updated = True
            if updated:
                itemText = 'New: ' + itemText 
            elif self.onlyNewButton.isChecked():
                item.setHidden(True)
            item.setText(itemText)

    def getAllNodes(self):
        nodes = []
        for i in range(0, self.itemList.count()):
            item = self.itemList.item(i)
            if item.text().startswith('New: '):
                nodes.append( self.itemList.item(i).data(Qt.UserRole) )
        return nodes

    def getSelectedNodes(self):
        nodes = []
        for item in self.itemList.selectedItems():
            nodes.append( item.data(Qt.UserRole) )
        return nodes

def updateRamsesItems():
    updateDialog = UpdateDialog(getMayaWindow())
    result = updateDialog.exec_() 
    if result == 0:
        return
    nodes = []
    if result == 1:
        nodes = updateDialog.getAllNodes()
    else:
        nodes = updateDialog.getSelectedNodes()

    for node in nodes:
        step = getRamsesAttr(node, RamsesAttribute.STEP)
        if step == 'MOD':
            updateMod( node )

def updateMod( rootCtrl ):
    # We need to use alembic
    if maf.safeLoadPlugin("AbcExport"):
        ram.log("I have loaded the Alembic Export plugin, needed for the current task.")

    # Create a locator to keep current transform
    rootLocator = cmds.spaceLocator(name='_ramsesTempLocator_')
    # Snap!
    rootLocator = snapNodeTo( rootLocator, rootCtrl )

    # We need to transfer the deformers to the new geo
    currentNodes = cmds.listRelatives(rootCtrl, ad = True, f=True)
    if currentNodes is None:
        return
    deformerSets = {}
    for node in currentNodes:
        sets = cmds.listSets(object=node, ets= True, type=2) # Type 2 is for deformers, 1 is for rendering sets
        if sets is not None:
            nodeName = node.split('|')[-1]
            deformerSets[nodeName] = sets

    # Re-Import
    itemShortName = getRamsesAttr( rootCtrl, RamsesAttribute.ITEM )
    assetGroup = getRamsesAttr( rootCtrl, RamsesAttribute.ASSET_GROUP )
    filePath = getRamsesAttr( rootCtrl, RamsesAttribute.GEO_FILE )
    item = ram.RamAsset('', itemShortName, '', assetGroup)
    newRootCtrl = importMod( item, filePath, 'MOD')

    # Move to the locator
    newRootCtrl = snapNodeTo( newRootCtrl, rootLocator )

    # Re-set deformers
    newNodes = cmds.listRelatives( newRootCtrl, ad = True, f = True)
    if newNodes is not None:
        for newNode in newNodes:
            newName = newNode.split('|')[-1]
            if newName in deformerSets:
                cmds.sets( newNode, include=deformerSets[newName])

    # Delete
    cmds.delete( rootCtrl )
    cmds.delete( rootLocator )

updateRamsesItems()