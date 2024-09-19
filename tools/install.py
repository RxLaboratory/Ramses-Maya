import os
from _config import (
    BUILD_PATH,
    SRC_PATH,
    REPO_PATH
)

# Symlink Ramses-Py and DuPYF
rampy_dest= os.path.join(
    REPO_PATH,
    'src', 'plug-ins', 'ramses'
)
if not os.path.exists(rampy_dest):
    rampy_src = os.path.join(
        REPO_PATH,
        '..', 'Ramses-Py', 'ramses'
    )
    os.symlink(rampy_src, rampy_dest)

dupyf_dest = os.path.join(
    REPO_PATH,
    'src', 'plug-ins', 'dupyf'
)
if not os.path.exists(dupyf_dest):
    dupyf_src = os.path.join(
        REPO_PATH,
        '..', '..', 'Python', 'DuPYF', 'dupyf'
    )
    os.symlink(dupyf_src, dupyf_dest)

# Write the .Mod file

mod_dest = os.path.expanduser("~/Documents/maya/modules/Ramses.mod")
mod_src = os.path.join(REPO_PATH, 'src', 'Ramses.mod')

with open(mod_src, 'r', encoding='utf8') as in_f:
    content = in_f.read()

content = content.replace('#modpath#', os.path.join(REPO_PATH, 'src'))

with open(mod_dest, 'w', encoding='utf8') as out_f:
    out_f.write(content)

print("Ramses Maya installed!")
