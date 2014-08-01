'''
_feature_

Command to create a new feature branch off of the develop branch
'''
import os
import shutil
import subprocess

from cirrus.configuration import load_configuration


def git_checkout_develop(dirname):
    """
    _git_checkout_develop_

    Get the latest develop updates before branching off
    """
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    comm = 'cd {0} && git checkout develop && git pull'.format(dirname)
    subprocess.check_call(comm, shell=True)


def git_branch(feature_name):
    """
    _git_branch_

    Create the new feature branch
    """
    comm = 'git checkout -b feature/{0} develop'.format(feature_name)
    subprocess.check_call(comm, shell=True)


def main():
    """
    _main_

    Execute feature command
    """
    config = load_configuration()
    feature_params = config.get('feature', {})
    local_repo = feature_params['local_repo']
    feature_name = feature_params['name']
    git_checkout_develop(local_repo)
    git_branch(feature_name)
