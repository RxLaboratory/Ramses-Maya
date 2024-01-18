import os
import zipfile
from .file_deploy import deploy as deploy_files
from .py_build import get_py_build_path
from .environment import Environment
from .utils import (
    get_deploy_path,
    zip_dir,
    get_project_name
)
E = Environment.instance()   

def deploy_mod(path, name, version):
    deploy_path = get_deploy_path(name)

    if not os.path.isdir(deploy_path):
        os.makedirs(deploy_path)

    zip_file = os.path.join(deploy_path, os.path.basename(path) + version + '.zip')
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zip:
        zip_dir(path, zip)

def deploy(name="Python"):
    print("> Deploying Python...")

    deploy_files()

    version = ""
    if 'meta' in E.ENV:
        version = E.ENV['meta'].get('version', '')
        if version != '':
            version = '_' + version

    build_path = get_py_build_path(name)

    print(">> Deploying Modules...")
    for mod in E.ENV['py']:
        mod_build_path = os.path.join(
            build_path,
            mod.get("name", "")
        )
        print(">>> From: " + mod_build_path)
        deploy_mod(mod_build_path, name, version)