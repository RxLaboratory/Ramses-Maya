# Ramses-Maya SR - The Ramses-Maya Plugin, Supinfocom-Rubika Flavor

 The Rx Asset Management System (Ramses) Maya Plugin, extended for the Supinfocom-Rubika production pipeline.

## Install

- [Download](https://github.com/Rainbox-dev/Ramses-Maya/archive/refs/heads/main.zip) and unzip the module
- (while the add-on is in development, you also need to manually include the [*ramses*](https://github.com/Rainbox-dev/Ramses-Py) python module in the plug-ins folder)
- Edit `Ramses.mod` with a text editor, and replace the path in the first line with the path where you've unzipped the module.
- Copy `Ramses.mod` in one of your modules paths  
    e.g. `C:\Users\User\Documents\Maya\modules`.  
    You may need to create the *modules* folder if it does not exist yet
- Restart *Maya*.

## TODO

- Fix file selection if there's both an ma and mb file
- Switches for rdr/vp shaders and geoproxies/shaderproxies (in the updater or importer)
- Add Auto mode / filters on the import dialog (filter according to the input pipes of the current step)
- Generate preview (playblast or thumbnail and later render)
- Generate preview option on new status
- If there's a selection, update option to filter according to the selection
- Implement  a 'Ramses_IgnoreUpdate' Set (which move the asset to the item folder before updating, and removes same asset if any from the updated nodes)

### Default addon

- The default addon checks the pipes to import/export ma or mb, as ref or standard (use the pipeFile shortname)
- Implement an update button for the default addon, using a group + attributes

## NOTES / DOC

### INFO / HELP

Le but est de garder une certaine souplesse dans le pipe (pour évolutions/cas particuliers)

Il s'adaptera en fonction des paramètres et surtout de la config du pipe dans l'appli ramses: 

Chaque pipe contient des types de fichiers auxquels on donne un ID. Ces IDs sont reconnus par l'addon :

- "Geo" (doit être un .abc -> .ma ou .mb à implémenter)
- "vpShader" (doit être un .mb -> .ma à implémenter)
- "rdrShader" (doit être un .mb -> .ma à implémenter)
- "proxyShade" (doit être un .ass)
- "proxyGeo" (doit être un .abc -> .ma ou .mb à implémenter)
- "Rig" (doit être un .ma ou .mb)
- "Anim"

-> lors de la publication/importation, l'addon fait ce qu'il faut en fonction de cette info (.abc, .mb, etc)

Si il ne trouve pas cette info, il se basera sur l'ID des steps :

- MOD - Modelisation (-> publie Geo, proxyGeo et vpShader)
- SHADE - Shading (-> publie rdrShader et proxyShade et proxyGeo)
- RIG - Rigging (-> publie Rig)

Si on n'est pas sur un step connu, il affiche une liste des types pris en charge

Ramses sait ce qu'il doit publier grâce à des sets dans la scène :

- "Ramses_Publish" contient les nodes "root" à publier
- "Ramses_Proxy" contient les nodes "root" des proxies (si shaders, des meshs auxquels les shaders sont appliqués)
- "Ramses_DelOnPublish" contient les nodes à supprimer avant publication

### Ramses

- [ ] *WIP* à chaque step, il y a un fichier de travail template vide, ramses le renomme et le place à la création de l'asset/shot

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
- [ ] Set Dressing
  - [ ] Import modé
  - [ ] Publish .mb (same way as rig)

#### Shots steps

- [ ] Layout
  - [ ] Import rig, sets, geo
  - [ ] Publish .mb
  - [ ] Publish .abc (gpu cache)
- [ ] Animation
  - [x] Import rig
  - [ ] Import/update abc du layout
  - [x] Import/update les props
  - [ ] Publish .abc (sans oublier la caméra)
  - [ ] Ajouter optionnellement l'anim des crease
- [x] FX, Rien pour l'instant
- [ ] Lighting
  - [ ] Import/update Le layout, vire tout ce qui a été baké/publish en abc
  - [ ] Import/update les abc
  - [x] Import/update les shaders et les assigne : depuis les items et depuis les charas, etc
  - [ ] Publish Rendu exr
- [ ] Compositing
  - [ ] Import/update les exr, eventuelle prépare un arbre, etc
  - [ ] Publish Rendu exr ou png

### Questions

- Les shaders sont en référence, pas de souci ?
- Dans pipou, la modé est importée en référence pour le shading, un intérêt ?