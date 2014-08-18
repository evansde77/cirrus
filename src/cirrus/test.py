'''
_test_

Command to run available test suites in a package
'''
import os
import posixpath
import sys
from fabric.operations import local

from cirrus.configuration import load_configuration


def main():
    """
    _main_

    Execute test command
    """
    config = load_configuration()

    local('. ./{0}/bin/activate && nosetests -w {1}'.format(
        config.test_venv_name(),
        config.test_where()))


if __name__ == '__main__':
    main()
