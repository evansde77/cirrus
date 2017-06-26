#!/usr/bin/env python
"""
_2to3.py

Python 2 and 3 compatibility tweaks

"""

import sys

PY2 = sys.version_info[0] < 3
ENCODING = 'utf-8'
NONETYPE = type(None)

# pylint: disable=undefined-variable
STRTYPE = basestring if PY2 else str

# pylint: disable=undefined-variable
UNITYPE = unicode if PY2 else str

# pylint: disable=undefined-variable
LONGTYPE = long if PY2 else int


def python3_todo(*args, **kwargs):
    """
    placeholder for alt implementations and workaround
    during port
    """
    raise NotImplemented("Python3 port in progress...")


if PY2:
    import ConfigParser
    import __builtin__ as builtins
    get_raw_input = raw_input

    def unicode_(s):
        return unicode(s)

else:
    import configparser as ConfigParser
    import builtins
    get_raw_input = input

    def unicode_(s):
        return str(s)


def to_str(s):
    return s.decode(ENCODING) if hasattr(s, 'decode') else s
