# -*- coding: utf-8 -*-

import sys
from PySide2.QtWidgets import ( # pylint: disable=import-error disable=no-name-in-module
    QApplication
)
from .rendering import get_ortho_cameras, get_persp_cameras, get_renderable_cameras
from .paths import baseName

def getMayaWindow():
    app = QApplication.instance() #get the qApp instance if it exists.
    if not app:
        app = QApplication(sys.argv)

    try:
        mayaWin = next(w for w in app.topLevelWidgets() if w.objectName()=='MayaWindow')
        return mayaWin
    except:
        return None

def update_cam_combobox(combobox):
    combobox.clear()

    renderableCameras = get_renderable_cameras()
    perspCameras =  get_persp_cameras()
    orthoCameras = get_ortho_cameras()

    numRenderCam = len(renderableCameras)
    if numRenderCam > 0:
        for camera in renderableCameras:
            cameraName = baseName(camera)
            combobox.addItem( cameraName, camera)
        combobox.insertSeparator( numRenderCam )

    numPerspCam = len( perspCameras )
    if numPerspCam > 0:
        for camera in perspCameras:
            cameraName = baseName(camera)
            combobox.addItem( cameraName, camera)
        combobox.insertSeparator( numRenderCam+numPerspCam+1 )

    for camera in orthoCameras:
        cameraName = baseName(camera)
        combobox.addItem( cameraName, camera)

