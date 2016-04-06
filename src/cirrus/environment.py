#!/usr/bin/env python
"""
_environment_

Utils to get the cirrus environment settings

"""

import os
import cirrus
import inspect
import posixpath
import subprocess


#
# number of subdirectories from cirrus/__init__.py
# when installed in a venv under CIRRUS_HOME location
NUMBER_OF_SUBDIRS = 6


def repo_directory():
    """
    helper method that extracts the current git repo directory
    using a callout to git rev-parse.
    If in a repo, this returns the path to the top level dir,
    if not, it returns None
    """
    command = ['git', 'rev-parse', '--show-toplevel']
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    outp, err = process.communicate()
    if process.returncode:
        return None
    return outp.strip()


def cirrus_home():
    """
    _cirrus_home_

    Get the CIRRUS_HOME variable, which points to the
    installation location

    """
    if os.environ.get('CIRRUS_HOME') is not None:
        return os.environ['CIRRUS_HOME']
    home = inspect.getsourcefile(cirrus)
    if ('lib' in home) and ('site-packages' in home):
        # we are in a pip installed virtualenv site-packages
        # from the cirrus init py in the venv, we need to
        # move up 5 dirs to get the install directory
        for _ in range(NUMBER_OF_SUBDIRS):
            home = os.path.dirname(home)
    else:
        # we are in a local git repo
        #
        home = repo_directory()
        if home is None:
            msg = "Unable to determine cirrus install location"
            raise RuntimeError(msg)
    os.environ['CIRRUS_HOME'] = home
    return home


def virtualenv_home():
    """
    _virtualenv_home_

    Build the path to the cirrus virtualenv location.
    Allows override by VIRTUALENV_HOME env var

    """
    if os.environ.get('VIRTUALENV_HOME') is not None:
        return os.environ['VIRTUALENV_HOME']
    home = cirrus_home()
    venv = posixpath.join(home, 'venv')
    return venv
