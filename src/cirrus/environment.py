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


def repo_directory():
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
    if 'venv' in home and 'site-packages' in home:
        # we are in a pip installed virtualenv site-packages
        # from the cirrus init py in the venv, we need to
        # move up 5 dirs to get the install directory
        for i in range(6): 
            home = os.path.dirname(home)
    else:
        # we are in a local git repo
        #
        home = repo_directory()
        if home is None:
            msg = "Unable to determine cirrus install location"
            raise RuntimeError(msg)
    os.environ['CIRRUS_HOME'] = home
    return os.environ['CIRRUS_HOME']

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
