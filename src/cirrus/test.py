'''
_test_

Command to run available test suites in a package
'''
import nose
import os
import posixpath
import sys
from argparse import ArgumentParser

from cirrus.configuration import load_configuration


def main():
    """
    _main_

    Execute test command
    """
    config = load_configuration()
    opts = sys.argv[1]
    current_dir = os.getcwd()
    print "current_dir: {0}".format(current_dir)
    print opts
    if opts=='suite':
        pkg = posixpath.join(current_dir, config.test_where())
        nose_args = '-w {0}'.format(pkg)
        print 'nose_args: {0}'.format(nose_args)
        arguments = ['test.py', pkg]
        print "Got some args: {0}".format(nose.run(argv=arguments))
    else:
        print "No args here: {0}".format(nose.run())


if __name__ == '__main__':
    main()
