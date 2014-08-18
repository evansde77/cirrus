'''
_test_

Command to run available test suites in a package
'''
import nose
import sys
from argparse import ArgumentParser

from cirrus.configuration import load_configuration


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the release command

    """
    parser = ArgumentParser(
        description='git cirrus test command'
    )
    subparsers = parser.add_argument('command', nargs='+')
    subparsers.add_command('--suite')

    opts = parser.parse_args(argslist)
    return opts


def main():
    """
    _main_

    Execute test command
    """
    config = load_configuration()
    opts = build_parser(sys.argv)
    if opts.suite:
        suite = config.nose_args()
        nose.run(suite)
    else:
        nose.run()


if __name__ == '__main__':
    main()
