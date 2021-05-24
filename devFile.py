import sys
sys.path.append(
    'D:/DEV_SRC/RxOT/Ramses/Ramses-Py'
)

import maya.cmds as cmds
import ramses as ram

ramses = ram.Ramses.instance()
settings = ram.RamSettings.instance()

def checkDaemon():
    """Checks if the Daemon is available (if the settings tell we have to work with it)"""
    if settings.online:
        if not ramses.connect():
            cmds.confirmDialog(
                title="No User",
                message="You must log in Ramses first!",
                button=["OK"],
                icon="warning"
                )
            ramses.showClient()
            cmds.error( "User not available: You must log in Ramses first!" )
            return False

    return True

def publishTemplate():
    ram.log("Publishing template...")

    # Check if the Daemon is available if Ramses is set to be used "online"
    if not checkDaemon():
        return

    # If we're online, get the current project and steps
    if settings.online:
        project = ramses.currentProject()

        if project is None:
            cmds.error( "No current project: You must select a project in Ramses first!" )
            return

        print(project.shortName())
    
    # Offline, try to guess the project & step from the current file
    print("offline")

publishTemplate()