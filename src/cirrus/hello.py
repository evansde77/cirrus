#!/usr/bin/env python
"""
_hello_

simple Hello World cirrus command example
"""
import sys
from cirrus import __version__
import cirrus.environment as env


def main():
    """
    print details of cirrus environment

    """
    hello_msg = (
        "\nHello from cirrus: {0}\n".format(__version__),
        "CIRRUS_HOME is {0}\n".format(env.cirrus_home()),
        "VIRTUALENV_HOME is {0}\n".format(env.virtualenv_home()),
        "Cirrus Python is {0}\n".format(sys.executable),
    )
    print(''.join(hello_msg))
