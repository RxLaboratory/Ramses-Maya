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

## NOTES / DOC

### INFO / HELP

Le but est de garder une certaine souplesse dans le pipe (pour évolutions/cas particuliers)

Il s'adaptera en fonction des paramètres et surtout de la config du pipe dans l'appli ramses: 

Chaque pipe contient des types de fichiers auxquels on donne un ID. Ces IDs sont reconnus par l'addon :

- "GeoPipe": Geométrie (doit être un .abc, .ma ou .mb)
- "vpShaPipe": viewport shaders (doit être un .mb -> .ma à implémenter)
- "rdrShaPipe": render shaders (doit être un .mb -> .ma à implémenter)
- "pShaPipe": proxy shaders (doit être un .ass)
- "pGeoPipe": proxy geometrie (doit être un .abc, .ma ou .mb)
- "RigPipe": rig (doit être un .ma ou .mb)
- "SetPipe": set (doit être un .ma ou .mb) peut contenir des geos updatable. pour éviter l'update des changements de placement de certaiuns objts lors de l'update du layout, les sortir de la hiérarchie du layout
- "AnimPipe": anim (doit être un abc)

-> lors de la publication/importation, l'addon fait ce qu'il faut en fonction de cette info (.abc, .mb, etc)

Si il ne trouve pas cette info, il se basera sur l'ID des steps :

- MOD - Modelisation (-> publie Geo, proxyGeo et vpShader)
- SHADE - Shading (-> publie rdrShader et proxyShade et proxyGeo)
- RIG - Rigging (-> publie Rig)
- SET
- LAY
- LIGHT
- ANIM
- VFX

Si on n'est pas sur un step connu, il affiche une liste des types pris en charge

Ramses sait ce qu'il doit publier grâce à des sets dans la scène :

- "Ramses_Publish" contient les nodes "root" à publier
- "Ramses_Proxy" contient les nodes "root" des proxies (si shaders, des meshs auxquels les shaders sont appliqués)
- "Ramses_DelOnPublish" contient les nodes à supprimer avant publication

### Ramses

- [x] *WIP* à chaque step, il y a un fichier de travail template vide, ramses le renomme et le place à la création de l'asset/shot

### Grouper les assets
- [x] CHARACTERS (chars)
- [x] PROPS
- [x] ITEMS (assets)
- [x] SETS (correspond aux publish stages)
-> Asset groups dans Ramses
et possibilité d'en ajouter

### Les Steps

#### Asset steps

- [x] Mode
  - [x] Publish abc
  - [x] Publish vp shaders .mb
  - [x] Publish proxy geo .abc
- [x] Setup
  - [x] Import modé
  - [x] Update modé
  - [x] Publish .ma ou .mb
- [x] Shading
  - [x] Import modé
  - [x] Update modé
  - [x] Publish .mb
  - [x] Publish proxy: .abc, .ass
- [x] Set Dressing
  - [x] Import modé
  - [x] Publish .mb

#### Shots steps

- [x] Layout
  - [x] Import rig, sets, geo
  - [x] Publish .mb
  - [x] Publish .abc (gpu cache)
- [x] Animation
  - [x] Import rig
  - [x] Import/update abc du layout
  - [x] Import/update les props
  - [x] Publish .abc (sans oublier la caméra)
  - [ ] Ajouter optionnellement l'anim des crease
- [x] FX, Rien pour l'instant
- [x] Lighting
  - [x] Import/update Le layout, vire tout ce qui a été baké/publish en abc (l'anim)
  - [x] Import/update les abc
  - [x] Import/update les shaders et les assigne : depuis les items et depuis les charas, etc
  - [ ] Publish Rendu exr
- [ ] Compositing
  - [ ] Import/update les exr, eventuelle prépare un arbre, etc
  - [ ] Publish Rendu exr ou png
