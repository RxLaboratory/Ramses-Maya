import os
import zipfile
from rxbuilder.utils import (
    wipe,
    replace_in_file,
    zip_dir,
    read_version
)
from rxbuilder.py import (
    build_folder
)
from _config import (
    REPO_PATH,
    BUILD_PATH,
    SRC_PATH,
)

VERSION = read_version(REPO_PATH)
MOD_PATH = os.path.join( BUILD_PATH, 'ramses-maya' )

def build():
    if not os.path.isdir(MOD_PATH):
        os.makedirs(MOD_PATH)

    build_folder(
        SRC_PATH,
        MOD_PATH
    )

    # Update metadata
    mod_file = os.path.join(
        MOD_PATH,
        'Ramses.mod'
    )

    replace_in_file( {
        '#version#': VERSION,
        '#modpath#': 'D:\\Path\\To\\Ramses-Maya'
    }, mod_file)

    config_file = os.path.join(
        MOD_PATH, 'plug-ins', 'ramses_maya', 'constants.py'
    )
    replace_in_file( {
        '#version#': VERSION,
    }, config_file)

def zip_module():
    zip_file = os.path.join(
        BUILD_PATH,
        'ramses-maya_' + VERSION + '.zip'
    )
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as z:
        zip_dir(MOD_PATH, z)

if __name__ == '__main__':
    wipe(BUILD_PATH)
    build()
    zip_module()
