"""
    Automatically updates ALL items in ALL the scenes of a given step
    This is given as an example and SHOULD NOT be used in production,
    Unless you really know what you're doing.
"""

import os
from maya import cmds # pylint: disable=import-error
import ramses as ram

# Set a log file
log_file = "D:/Ramses_auto_update_log.txt"

# Get the Ramses instance
RAMSES = ram.Ramses.instance()

# A simple function to log stuff
def log( msg ):
    """Log to log_file and the console"""
    print("Ramses auto-update: " + msg)
    with open(log_file,"a", encoding='utf8') as f:
        f.write(msg + "\n")

# Everything in a function makes it easier to manipulate
def auto_update( step_id = 'layout' ):
    """The main auto update function."""

    # Get the current project
    project = RAMSES.currentProject()

    # Reinit the log
    with open(log_file, 'w', encoding='utf8') as f:
        f.write("Starting auto-update...\n")

    # If there's no project, can't do nothing!
    if not project:
        log("No current project")
        return

    # Get the step
    step = project.step(step_id)

    # If the step doesn't exist, can't do nothing!
    if not step:
        log("Invalid step (" + step_id + ")")
        return

    # List all the items
    items = []
    if step.stepType() == ram.StepType.SHOT_PRODUCTION:
        items = project.shots()
    elif step.stepType() == ram.StepType.ASSET_PRODUCTION:
        items = project.assets()

    # Nothing to update
    if len(items) == 0:
        log("Empty step, or unsupported step type (pre or post production)")
        return

    # For all items
    # A counter
    i = 0
    for ram_item in items:

        # Open scene (try both ma and mb)
        path = ram_item.stepFilePath(extension="mb",step=step_id)
        if path == "":
            path = ram_item.stepFilePath(extension="ma",step=step_id)
        if path == "":
            continue

        i = i+1
        log("Opening " + str(ram_item))
        log("File: " + path)

        # Maya open command
        cmds.file( path, open=True )
        log("Scene loaded")

        # Use the ramses command to update all imported items
        cmds.ramUpdate( updateAll=True )
        log("Updated!")

        # Save as a new version
        cmds.ramSaveVersion( updateStatus=False )
        log("Saved scene!\n")

    # Finished!
    log("Updated " + str(i) + " scenes.")

# Run the function
# Just change the step id if you wish
auto_update('Rig')
