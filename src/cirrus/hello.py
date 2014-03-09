#!/usr/bin/env python
"""
_hello_

simple Hello World cirrus command example
"""
import os
import sys
import cirrus.environment as env

def main():
    print "hello from cirrus"
    print "CIRRUS_HOME is {0}".format(env.cirrus_home())
    print "VIRTUALENV_HOME is {0}".format(env.virtualenv_home())
    print "Cirrus Python is {0}".format(sys.executable)
