#!/usr/bin/env python
"""
conda related helpers

"""
import os
import subprocess

from cirrus._2to3 import to_str


def which_conda():
    try:
        outp = subprocess.check_output(['which', 'conda'])
    except Exception:
        return None
    return to_str(outp).strip()


def pyenv_shims():
    try:
        outp = subprocess.check_output(['pyenv', 'shims'])
    except Exception:
        return []
    shims = to_str(outp)
    shims = shims.split()
    return shims


def pyenv_which_conda():
    try:
        outp = subprocess.check_output(['which', 'pyenv', 'conda'])
    except Exception:
        return None
    return to_str(outp).strip()


def conda_is_pyenv():
    return which_conda() in pyenv_shims()


def conda_setup_script(conda_bin):
    """given conda bin path, return the conda.sh script location"""
    bin_dir = os.path.dirname(conda_bin)
    pkg_dir = os.path.dirname(bin_dir)
    conda_sh = os.path.join(pkg_dir, 'etc', 'profile.d', 'conda.sh')
    return conda_sh


def find_conda_setup_script():
    conda = which_conda()
    if conda is None:
        return None

    if conda_is_pyenv():
        conda = pyenv_which_conda()

    return conda_setup_script(conda)


def conda_version():
    """get the installed version of conda, return None if not installed"""
    try:
        outp = subprocess.check_output(['conda', '-V'])
    except Exception:
        return None
    outp = to_str(outp)
    vers = outp.replace('conda', '').strip()
    split = vers.split('.', 2)
    return {
        'major': int(split[0]),
        'minor': int(split[1]),
        'micro': int(split[2]),
    }


def is_anaconda_5():
    """
    anaconda 5 has conda version 4.4.0 or greater... obviously :/

    """
    vers = conda_version()
    if not vers:
        return False
    ma = vers['major'] >= 4
    mi = vers['minor'] >= 4
    return ma and mi
