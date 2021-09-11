# Ramses-Maya

The Rx Asset Management System (Ramses) Maya Plugin

- The [Ramses documentation](http://ramses.rxlab.guide) is available on [ramses.rxlab.guide](http://ramses.rxlab.guide).
- The main [Git repository](https://github.com/RxLaboratory/Ramses) for all *Ramses* components, [releases](https://github.com/RxLaboratory/Ramses/releases) and [issues](https://github.com/RxLaboratory/Ramses/issues) is [here](https://github.com/RxLaboratory/Ramses).
- The [developer documentation and all references](http://ramses.rxlab.io) are available on [ramses.rxlab.io](http://ramses.rxlab.io).

## Install

- [Download](https://github.com/Rainbox-dev/Ramses-Maya/archive/refs/heads/main.zip) and unzip the module
- Edit `Ramses.mod` with a text editor, and replace the path in the first line with the path where you've unzipped the module.
- Copy `Ramses.mod` in one of your modules paths  
    e.g. `C:\Users\User\Documents\Maya\modules`.  
    You may need to create the *modules* folder if it does not exist yet
- Restart *Maya*.

## TODO

- Publish:
    - Rig: Error: Non-deletable node
- Import:
    - when importing shaders (reference): override to set ramses attributes
    - getCreateGroup does not return existing group
    - Import anim (and remove rig) issue:
        # #   File "D:/DEV_SRC/RxOT/Ramses/Ramses-Maya/plug-ins\rubika\import_anim.py", line 30, in importAnim
        # #     step = getRamsesAttr(node, RamsesAttribute.STEP)
        # #   File "D:/DEV_SRC/RxOT/Ramses/Ramses-Maya/plug-ins\rubika\utils_attributes.py", line 82, in getRamsesAttr
        # #     if attr not in cmds.listAttr(node):
        # # ValueError: No object matches name: |S001:Main|S001:IS_Rig|S001:IS_Rig_001:Iseult_Root|S001:IS_Rig_001:Iseult_Geo #
    - autoselect same asset/shot as selected in the viewport
    - UI: reload versions if action change
- rebuild update
    - RamItem latestversion not working
    - Check/test updates
    - Rebuild set update
    - option to filter according to selection
    
