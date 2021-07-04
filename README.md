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

## URGENT

SERVER PIPES:

 /!\ Warning: Database Interface says: <br />
<b>Fatal error</b>:  Uncaught PDOException: SQLSTATE[23000]: Integrity constraint violation: 1048 Column 'pipeFileId' cannot be null in C:\xampp\htdocs\ramses\pipes.php:201
Stack trace:
#0 C:\xampp\htdocs\ramses\pipes.php(201): PDOStatement-&gt;execute(Array)
#1 C:\xampp\htdocs\ramses\index.php(78): include('C:\\xampp\\htdocs...')
#2 {main}
  thrown in <b>C:\xampp\htdocs\ramses\pipes.php</b> on line <b>201</b><br />


Pipe list incorrectly retrieved from daemon?


## TODO

- Ramses py module
    - Implement a RamNameManager
- Importer
    - Fix file selection (open) if there's both an ma and mb file
    - autoselect same shot/asset in import dialog
    - Add Auto mode / filters on the import dialog (filter according to the input pipes of the current step)
- Updater
    - Switches for rdr  /vp shaders and geoproxies (in the updater)
    - If there's a selection, update option to filter according to the selection
- Copy to version
    - use thread

- Explications arbo dossier ramses et droits d'accès
- Lister les trucs à faire en début d'année avant l'arrivée des étudiants

### Default addon

- Perf
    - Use threads for copying files

- The default addon checks the pipes to import/export ma or mb, as ref or standard (use the pipeFile shortname)
- Implement an update button for the default addon, using a group + attributes

