#!/usr/bin/env python
"""
conda related helpers

"""
import subprocess


def conda_version():
    """get the installed version of conda, return None if not installed"""
    try:
        outp = subprocess.check_output(['conda', '-V'])
    except Exception:
        return None
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
