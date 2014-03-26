#!/usr/bin/env python
"""
_prestage_

Command to pull in remote github repos and install them
into the virtualenv

Looks at the prestage section of the cirrus config and expects entries
of the form:
carburetor=github.com/cloudant/carburetor.git

And for each of those will git clone the repo locally and
pip install it into the virtualenv

If requirements.txt contains an absolute requirement for the named package
Eg:
carburetor==0.1.2
then it will check out that tag in the local repo clone prior to installing


"""
import os
import shutil
import subprocess

from pip.req import parse_requirements

from cirrus.configuration import load_configuration
from cirrus.configuration import get_github_auth


def git_clone_repo(repo_url, dirname, tag=None):
    """
    _git_clone_repo_

    Get a local clone of the repo so that we can install
    it locally via pip -e into the virtualenv
    """
    gh_user, gh_tok = get_github_auth()
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    clone_url = 'https://{0}:{1}@{2}'.format(gh_user, gh_tok, repo_url)
    clone_comm = 'git clone {0} {1}'.format(clone_url, dirname)
    subprocess.check_call(clone_comm, shell=True)
    if tag is not None:
        comm = 'cd {0} && git checkout {1}'.format(dirname, tag)
        subprocess.check_call(comm, shell=True)


def install_from_repo(venv, local_repo):
    """
    _install_from_repo_

    install package from a local clone of the repo into the virtualenv

    """
    command = ". {0} && pip install -e {1}".format(venv, local_repo)
    subprocess.check_call(command, shell=True)


def main():
    """
    _main_

    Execute prestage command:
    - look into cirrus conf for requirements to be prestaged
    - look for matching version requirement in requirements.txt
    - clone each repo locally
    - pip install -e the repo into the virtualenv

    """
    working_dir = os.getcwd()
    repo_cache = os.path.join(working_dir, 'prestage')
    if not os.path.exists(repo_cache):
        os.makedirs(repo_cache)
    config = load_configuration()
    prestage_params = config.get('prestage', {})
    build_params = config.get('build', {})
    venv_name = build_params.get('virtualenv_name', 'venv')
    reqs_name = build_params.get('requirements_file', 'requirements.txt')
    venv_path = os.path.join(working_dir, venv_name)
    venv_command = os.path.join(venv_path, 'bin', 'activate')

    reqs = {}
    # TODO: this only supports explicit == version reqs right now
    # make this more flexible
    for req in parse_requirements(reqs_name):
        if req.req is not None:
            versions = [ x for x in req.absolute_versions]
            if len(versions) > 0:
                reqs[req.name] = versions[0]

    # prestage section contains a map of package name: repo
    for req, repo in prestage_params.iteritems():
        msg = "Prestaging repo for requirement {req} from {repo}"
        tag = reqs.get(req)
        if tag is not None:
            msg += " with tag {tag}"
        msg.format(req=req, repo=repo, tag=tag)
        print msg
        local_repo = os.path.join(repo_cache, req)
        git_clone_repo(repo, local_repo, tag=reqs.get(req))
        install_from_repo(venv_command, local_repo)


if __name__ == '__main__':
    main()