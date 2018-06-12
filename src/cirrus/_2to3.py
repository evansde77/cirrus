#!/usr/bin/env python
"""
_2to3.py

Python 2 and 3 compatibility tweaks

"""

import sys
import contextlib


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
    from StringIO import StringIO

    get_raw_input = raw_input
    from urlparse import urlparse

    def unicode_(s):
        return unicode(s)

    @contextlib.contextmanager
    def redirect_stdout(target):
        original = sys.stdout
        sys.stdout = target
        yield
        sys.stdout = original

else:
    import configparser as ConfigParser
    import builtins
    get_raw_input = input
    from urllib.parse import urlparse
    from io import StringIO
    from contextlib import redirect_stdout

    def unicode_(s):
        return str(s)


def to_str(s):
    return s.decode(ENCODING) if hasattr(s, 'decode') else s
