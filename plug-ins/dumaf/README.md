# DuMAF - Duduf Maya Framework

## Changes

- Created new namespaces
- Renamed `getNodesInSet` to `getNodes`
- Renamed `deleteNode` to `delete`
- Renamed `parentNodeTo` to `parent`
- Renamed `getNodeBaseName` to `baseName`
- Renamed `getNodeAbsolutePath` to `absolutePath`
- Renamed `checkNode` to `check`
- Renamed `snapNodeTo` to `snap`
- Renamed `safeLoadPlugin` to `load`
- Renamed `removeAllNamespaces` to `removeAll`
- Renamed `removeAllAnimCurves` to `removeAll`
- Removed `cleanNode`, and added `removeExtraShapes`, `deleteHistory`, `freezeTrasnform`, `renameShapes`
    - cleanNode was: deleteifempty=True, renameShapes=True, freezeT=True, keepHistory=False
        - deleteIfEmpty
        - removeExtrashapes
        - deletehistory
        - freezeT
        - renameshapes
- `checkNode` was: deleteIfEmpty = True, typesToKeep=('mesh')
    - deleteifempty
    - checktype
- Removed `cleanScene`, and added `createTempScene`, `references.importAll`
    - cleanscene was: removeAnim = True, lockVisibility = False
        - create temp scene
        - import all refs
        - remove namespaces
        - if removeAnim remove anim
        - if lockVibility lock hiddenvisibility

