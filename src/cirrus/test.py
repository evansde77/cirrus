'''
_test_

Command to run available test suites in a package
'''
import sys

from fabric.operations import local
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
    
    parser.add_argument(
        '--suite',
        help=(
            'test suite configuration to use as defined in the '
            'test-<suite> section of cirrus.conf'
        ),
        default='default'
    )
    parser.add_argument(
        '--mode',
        choices=['nosetests', 'tox'],
        default=None,
        help='Choose test runner framework'
    )
    parser.add_argument(
        '--test-options',
        default='',
        dest='options',
        help='Optional args to pass to test runner'
    )

    opts = parser.parse_args(argslist)
    return opts


def nose_run(config, opts):
    """
    _nose_test_

    Locally activate vitrualenv and run tests via nose
    """
    where = config.test_where(opts.suite)
    local(
        '. ./{0}/bin/activate && nosetests -w {1} {2}'.format(
            config.venv_name(),
            where,
            opts.options
        )
    )


def tox_run(config, opts):
    """
    tox test

    activate venv and run tox test suite

    """
    local(
        '. ./{0}/bin/activate && tox {1}'.format(
            config.venv_name(),
            opts.options
        )
    )


def main():
    """
    _main_

    Execute test command
    """
    opts = build_parser(sys.argv[1:])
    config = load_configuration()
    mode = config.test_mode(opts.suite)
    if opts.mode:
        mode = opts.mode

    # backwards compat: default to nosetests
    if mode is None:
        mode = 'nosetests'

    if mode == 'nosetests':
        nose_run(config, opts)
        sys.exit(0)
    if mode == 'tox':
        tox_run(config, opts)
        sys.exit(0)


if __name__ == '__main__':
    main()
