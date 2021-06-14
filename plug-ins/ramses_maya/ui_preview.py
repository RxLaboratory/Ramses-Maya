from PySide2.QtWidgets import ( # pylint: disable=no-name-in-module
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QSpinBox,
    QVBoxLayout,
    QFormLayout,
    QWidget,
    QComboBox,
    QLineEdit,
    QPushButton,
    QSlider,
)
from PySide2.QtCore import ( # pylint: disable=no-name-in-module
    Slot,
    Qt
)

import maya.cmds as cmds # pylint: disable=import-error
import maya.mel as mel # pylint: disable=import-error
import dumaf as maf

import ramses as ram
ramses = ram.Ramses.instance()

class PreviewDialog( QDialog ):

    def __init__(self, parent=None):
        super(PreviewDialog, self).__init__(parent)
        self.modelEditor = None
        self.pbWin = 'ramsesPlayblasterWin'
        self.pbLayout = 'ramsesPlayblasterLayout'
        self.modelPanel = 'ramsesPlayblasterPanel'

        self.__setupUi()
        self.__loadCameras()
        self.showRenderer()
        self.__connectEvents()

    def __setupUi(self):
        self.setWindowTitle( "Create preview" )

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(6,6,6,6)
        mainLayout.setSpacing(3)

        topLayout = QFormLayout()
        topLayout.setFieldGrowthPolicy( QFormLayout.AllNonFixedFieldsGrow )
        topLayout.setSpacing(3)

        self.cameraBox = QComboBox()
        topLayout.addRow("Camera:", self.cameraBox)

        sizeWidget = QWidget()
        sizeLayout = QHBoxLayout()
        sizeLayout.setContentsMargins(0,1,0,0)
        sizeLayout.setSpacing(3)
        self.sizeEdit = QSpinBox()
        self.sizeEdit.setMaximum(100)
        self.sizeEdit.setMinimum(10)
        self.sizeEdit.setSuffix(' %')
        self.sizeEdit.setValue(50)
        sizeLayout.addWidget(self.sizeEdit)
        self.sizeSlider = QSlider()
        self.sizeSlider.setOrientation( Qt.Horizontal )
        self.sizeSlider.setMaximum(100)
        self.sizeSlider.setMinimum(10)
        self.sizeSlider.setValue(50)
        sizeLayout.addWidget(self.sizeSlider)
        sizeWidget.setLayout(sizeLayout)
        topLayout.addRow("Size:", sizeWidget)

        renderOptionsWidget = QWidget()
        renderOptionsLayout = QVBoxLayout()
        renderOptionsLayout.setContentsMargins(0,1,0,0)
        renderOptionsLayout.setSpacing(3)
        self.displayAppearenceBox = QComboBox()
        self.displayAppearenceBox.addItem("Smooth Shaded", 'smoothShaded')
        self.displayAppearenceBox.addItem("Flat Shaded", 'flatShaded')
        self.displayAppearenceBox.addItem("Bounding Box", 'boundingBox')
        self.displayAppearenceBox.addItem("Points", 'points')
        self.displayAppearenceBox.addItem("Wireframe", 'wireframe')
        renderOptionsLayout.addWidget(self.displayAppearenceBox)
        self.useLightsBox = QComboBox( )
        self.useLightsBox.addItem( "Default Lighting", 'default' )
        self.useLightsBox.addItem( "Silhouette", 'none' )
        self.useLightsBox.addItem( "Scene Lighting", 'all' )
        renderOptionsLayout.addWidget(self.useLightsBox)
        self.displayTexturesBox = QCheckBox( "Display Textures")
        self.displayTexturesBox.setChecked(True)
        renderOptionsLayout.addWidget(self.displayTexturesBox)
        self.displayShadowsBox = QCheckBox("Display Shadows")
        self.displayShadowsBox.setChecked(True)
        renderOptionsLayout.addWidget(self.displayShadowsBox )
        self.aoBox = QCheckBox("Ambient Occlusion")
        self.aoBox.setChecked(True)
        renderOptionsLayout.addWidget(self.aoBox)
        self.aaBox = QCheckBox("Anti-Aliasing")
        self.aaBox.setChecked(True)
        renderOptionsLayout.addWidget(self.aaBox)
        self.onlyPolyBox = QCheckBox("Only Polygons")
        self.onlyPolyBox.setChecked(True)
        renderOptionsLayout.addWidget(self.onlyPolyBox)
        self.motionTrailBox = QCheckBox("Show Motion Trails")
        renderOptionsLayout.addWidget(self.motionTrailBox)
        renderOptionsWidget.setLayout( renderOptionsLayout )
        topLayout.addRow("Renderer:", renderOptionsWidget)

        self.commentEdit = QLineEdit()
        self.commentEdit.setMaxLength(20)
        topLayout.addRow("Comment:", self.commentEdit)

        mainLayout.addLayout(topLayout)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(2)
        self._playblastButton = QPushButton("Playblast")
        buttonsLayout.addWidget( self._playblastButton )
        self._thumbnailButton = QPushButton("Thumbnail")
        buttonsLayout.addWidget( self._thumbnailButton )
        self._cancelButton = QPushButton("Cancel")
        buttonsLayout.addWidget( self._cancelButton )
        mainLayout.addLayout( buttonsLayout )

        self.setLayout(mainLayout)

    def __connectEvents(self):
        self._playblastButton.clicked.connect( self.__ok )
        self._playblastButton.clicked.connect( self.accept )
        self._thumbnailButton.clicked.connect( self.__ok )
        self._thumbnailButton.clicked.connect( self.__thumbnail )
        self._cancelButton.clicked.connect( self.reject )
        self.rejected.connect(self.hideRenderer)
        self.displayAppearenceBox.currentIndexChanged.connect( self.__updateLightsBox )
        self.displayAppearenceBox.currentIndexChanged.connect( self.__updateRenderer )
        self.useLightsBox.currentIndexChanged.connect( self.__updateRenderer )
        self.displayTexturesBox.clicked.connect( self.__updateRenderer )
        self.motionTrailBox.clicked.connect( self.__updateRenderer )
        self.displayShadowsBox.clicked.connect( self.__updateRenderer )
        self.cameraBox.currentIndexChanged.connect( self.__updateRenderer )
        self.aaBox.clicked.connect( self.__updateRenderer )
        self.aoBox.clicked.connect( self.__updateRenderer )
        self.sizeSlider.valueChanged.connect( self.sizeEdit.setValue )
        self.sizeEdit.valueChanged.connect( self.sizeSlider.setValue )

    def __updateRenderer(self):
        cmds.modelEditor(self.modelEditor,
            camera=self.cameraBox.currentData(), 
            displayAppearance=self.displayAppearenceBox.currentData(),
            displayLights= self.useLightsBox.currentData(),
            displayTextures=self.displayTexturesBox.isChecked(),
            motionTrails=self.motionTrailBox.isChecked(),
            shadows=self.displayShadowsBox.isChecked(),
            edit=True)

        cmds.setAttr('hardwareRenderingGlobals.multiSampleEnable',self.aaBox.isChecked() ) # AA
        cmds.setAttr('hardwareRenderingGlobals.ssaoEnable', self.aoBox.isChecked() ) # AO

    def showRenderer(self):
        # Get/Create window
        if not cmds.window(self.pbWin, exists=True, query=True):
            cmds.window(self.pbWin)
            cmds.paneLayout(self.pbLayout)
        cmds.window(self.pbWin, title= 'Ramses Playblaster', edit=True)

        # Set window size to the renderer size
        # Prepare viewport
        cmds.windowPref(self.pbWin, maximized=True,edit=True)

        # Get/Create new model panel
        if not cmds.modelPanel(self.modelPanel,exists=True,query=True):
            cmds.modelPanel(self.modelPanel)
        cmds.modelPanel(self.modelPanel, parent=self.pbLayout, menuBarVisible=False, edit=True)

        # The model editor with default values
        self.modelEditor = cmds.modelPanel(self.modelPanel, modelEditor=True, query=True)
        # Adjust render setting
        cmds.modelEditor(self.modelEditor, activeView=True, edit=True)
        self.__updateRenderer()
        
        # Adjust cam
        cmds.camera(self.cameraBox.currentData(),e=True,displayFilmGate=False,displayResolution=False,overscan=1.0)
        # Clear selection
        cmds.select(clear=True)

        # Show window
        cmds.showWindow( self.pbWin )

    def __ok(self):
        if self.onlyPolyBox.isChecked():
            cmds.modelEditor(self.modelEditor, e=True, alo=False) # only polys, all off
            cmds.modelEditor(self.modelEditor, e=True, polymeshes=True) # polys
            cmds.modelEditor(self.modelEditor, e=True, motionTrails=self.motionTrailBox.isChecked() )

    Slot()
    def __updateLightsBox(self, index):
        self.useLightsBox.setEnabled( index < 2 )

    Slot()
    def __thumbnail(self):
        self.done(2)

    def __loadCameras(self):
        cameras = cmds.ls(type='camera')
        renderableCameras = []
        perspCameras = []
        orthoCameras = []
        for camera in cameras:
            # get the transform node
            camera = cmds.listRelatives(camera, parent=True, f=True, type='transform')[0]
            if cmds.getAttr( camera + '.renderable'):
                renderableCameras.append(camera)
                continue
            if cmds.camera(camera, orthographic=True, query=True):
                orthoCameras.append(camera)
                continue
            perspCameras.append(camera)
                
        numRenderCam = len(renderableCameras)
        if numRenderCam > 0:
            for camera in renderableCameras:
                cameraName = maf.getNodeBaseName(camera)
                self.cameraBox.addItem( cameraName, camera)
            self.cameraBox.insertSeparator( numRenderCam )
        numPerspCam = len( perspCameras )
        if numPerspCam > 0:
            for camera in perspCameras:
                cameraName = maf.getNodeBaseName(camera)
                self.cameraBox.addItem( cameraName, camera)
            self.cameraBox.insertSeparator( numRenderCam+numPerspCam )

        for camera in orthoCameras:
            cameraName = maf.getNodeBaseName(camera)
            self.cameraBox.addItem( cameraName, camera)
    
    def comment(self):
        return self.commentEdit.text()

    def camera(self):
        return self.cameraBox.currentData()

    def getSize(self):
        return self.sizeEdit.value() / 100.0

    Slot()
    def hideRenderer(self):
        cmds.window( self.pbWin, visible=False, edit=True)

    def setWindowSize(self):
        s = self.getSize()
        w = cmds.getAttr("defaultResolution.width") * s - 4
        h = cmds.getAttr("defaultResolution.height") * s - 23
        cmds.windowPref(self.pbWin, maximized=False, edit=True)
        cmds.window(self.pbWin, width=w, height=h, edit=True)
        cmds.refresh(cv=True)

