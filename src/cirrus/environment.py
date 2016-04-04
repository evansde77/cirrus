#!/usr/bin/env python
"""
_environment_

Utils to get the cirrus environment settings

"""

import os
import cirrus
import inspect
import posixpath


def cirrus_home():
    """
    _cirrus_home_

    Get the CIRRUS_HOME variable, which points to the
    installation location

    """
    if os.environ.get('CIRRUS_HOME') is not None:
        return os.environ['CIRRUS_HOME']
    
    home = inspect.getsourcefile(cirrus)
    # from the cirrus init py in the venv, we need to
    # move up 5 dirs to get the install directory
    for i in range(6): 
        home = os.path.dirname(home)
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
