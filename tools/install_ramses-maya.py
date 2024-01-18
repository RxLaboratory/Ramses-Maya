import os
import _setup_env as ramaya
ramaya.init()
B = ramaya.builder
E = B.ENVIRONMENT

# Symlink Ramses-Py and DuPYF
rampy_dest= os.path.join(
    E.REPO_DIR,
    'src', 'plug-ins', 'ramses'
)
if not os.path.exists(rampy_dest):
    rampy_src = os.path.join(
        E.REPO_DIR,
        '..', 'Ramses-Py'
    )
    os.symlink(rampy_src, rampy_dest)

dupyf_dest = os.path.join(
    E.REPO_DIR,
    'src', 'plug-ins', 'dupyf'
)
if not os.path.exists(dupyf_dest):
    dupyf_src = os.path.join(
        E.REPO_DIR,
        '..', '..', 'Python', 'DuPYF'
    )
    os.symlink(dupyf_src, dupyf_dest)

# Write the .Mod file
    
mod_dest = os.path.expanduser("~/Documents/maya/modules/Ramses.mod")
mod_src = os.path.join(E.REPO_DIR, 'src', 'Ramses.mod')

with open(mod_src, 'r', encoding='utf8') as in_f:
    content = in_f.read()

content = content.replace('#modpath#', os.path.join(E.REPO_DIR, 'src'))

with open(mod_dest, 'w', encoding='utf8') as out_f:
    out_f.write(content)

print("Ramses Maya installed!")