# Ramses-Maya
 The Rx Asset Management System (Ramses) Maya Plugin

## Install

- [Download](https://github.com/Rainbox-dev/Ramses-Maya/archive/refs/heads/main.zip) and unzip the module
- (while the add-on is in development, you also need to manually include the [*ramses*](https://github.com/Rainbox-dev/Ramses-Py) python module in the plug-ins folder)
- Edit `Ramses.mod` with a text editor, and replace the path in the first line with the path where you've unzipped the module.
- Copy `Ramses.mod` in one of your modules paths  
    e.g. `C:\Users\User\Documents\Maya\modules`.  
    You may need to create the *modules* folder if it does not exist yet
- Restart *Maya*.

## TODO

### Default addon

- save preview
  - set view options, and
  - thumbnail using `cmds.refresh(cv=True, fe = "jpg", fn = 'D:/SWAP/TEMP/----test.png')`
  - options to add:
  - Add HUD
  - Restore to previous settings