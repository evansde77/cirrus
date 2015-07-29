'''
_test_

Command to run available test suites in a package
'''
import sys

from fabric.operations import local
from argparse import ArgumentParser
from nose.tools import nottest

from cirrus.configuration import load_configuration


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the release command

    """
    parser = ArgumentParser(
        description='git cirrus test command'
    )
    parser.add_argument('test', nargs='+')
    parser.add_argument('--suite') 

    opts = parser.parse_args(argslist)
    return opts


@nottest
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
    opts = build_parser(sys.argv)
    if opts.suite is not None:
        nose_test(opts.suite)
    else:
        nose_test('default')


if __name__ == '__main__':
    main()
