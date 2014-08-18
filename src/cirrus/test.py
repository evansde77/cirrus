'''
_test_

Command to run available test suits in a package
'''
import nose
import sys
from argparse import ArgumentParser


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the release command

    """
    parser = ArgumentParser(
        description='git cirrus test command'
    )
    parser.add_argument('command', nargs='+')

    opts = parser.parse_args(argslist)
    return opts


def main():
    """
    _main_

    Execute test command
    """
    opts = build_parser(sys.argv)
    if opts.args[0].startswith('--suit'):
        suit = opts.args[0].lstrip('--suit=')
        nose.run(suit)
    else:
        nose.run()


if __name__ == '__main__':
    main()
