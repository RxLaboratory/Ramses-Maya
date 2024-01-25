# -*- coding: utf-8 -*-
"""Rendering functions"""

from maya import cmds

def set_renderable_camera(camera):
    """Sets the camera to be the unique renderable camera"""
    cameras = cmds.ls(type='camera')
    for cam in cameras:
        # get the transform node
        cam = cmds.listRelatives(cam, parent=True, f=True, type='transform')[0]
        cmds.setAttr( cam + '.renderable', cam == camera)

def get_renderable_cameras():
    """Lists all renderable cameras"""
    cameras = cmds.ls(type='camera')
    renderableCameras = []
    for camera in cameras:
        # get the transform node
        camera = cmds.listRelatives(camera, parent=True, f=True, type='transform')[0]
        if cmds.getAttr( camera + '.renderable'):
            renderableCameras.append(camera)
    return renderableCameras

def get_persp_cameras():
    """Lists all persp cams"""
    cameras = cmds.ls(type='camera')
    perspCameras = []
    for camera in cameras:
        # get the transform node
        camera = cmds.listRelatives(camera, parent=True, f=True, type='transform')[0]
        if not cmds.camera(camera, orthographic=True, query=True):
            perspCameras.append(camera)
    return perspCameras

def get_ortho_cameras():
    """Lists all ortho cams"""
    cameras = cmds.ls(type='camera')
    orthoCameras = []
    for camera in cameras:
        # get the transform node
        camera = cmds.listRelatives(camera, parent=True, f=True, type='transform')[0]
        if cmds.camera(camera, orthographic=True, query=True):
            orthoCameras.append(camera)
    return orthoCameras

def set_render_resolution(width, height, pixelAspect=1.0):
    '''
    Sets render resolution properly.

    @param width- The width of the resolution.
    @param height- The width of the resolution.
    @param pixelAspect- The pixel aspect to set the defaultResolution to.

    Returns None
    '''
    # Calculates the device aspect since pixel aspect isn't an actual attribute.
    device_aspect = float(width * pixelAspect)/float(height)

    # Set the Lock Device Aspect Ratio. IMPORTANT!
    # If you don't do this it won't work.
    cmds.setAttr("defaultResolution.lockDeviceAspectRatio", 1)

    # Set width, height, and aspect ratio.
    cmds.setAttr("defaultResolution.width", width)
    cmds.setAttr("defaultResolution.height", height)
    cmds.setAttr("defaultResolution.deviceAspectRatio", device_aspect)