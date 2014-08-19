'''
_test_

Command to run available test suites in a package
'''
import sys
from fabric.operations import local

from cirrus.configuration import load_configuration


def nose_test(location):
    """
    _nose_test_

    Locally activate vitrualenv and run tests
    """
    config = load_configuration()
    local('. ./{0}/bin/activate && nosetests -w {1}'.format(
        config.venv_name(),
        config.test_where(location)))


def main():
    """
    _main_

    Execute test command
    """
    if len(sys.argv) > 2 and sys.argv[1] != '--suite':
        exit(1)  # only '--suite' is allowed as an option
    elif len(sys.argv) > 2:  # suite has been specified
        nose_test(sys.argv[2])
    else:  # use default
        nose_test('default')

if __name__ == '__main__':
    main()
