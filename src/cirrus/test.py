'''
_test_

Command to run available test suites in a package
'''
import os
import sys

from cirrus.invoke_helpers import local
from argparse import ArgumentParser

from cirrus.configuration import load_configuration
from cirrus.environment import repo_directory, is_anaconda


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


def activate_command(venv_path):
    if is_anaconda():
        command = "source {}/bin/activate {}".format(venv_path, venv_path)
    else:
        command = ". {}/bin/activate".format(venv_path)
    return command


def nose_run(config, opts):
    """
    _nose_test_

    Locally activate vitrualenv and run tests via nose
    """
    where = config.test_where(opts.suite)
    suite_conf = config.test_suite(opts.suite)
    test_opts = suite_conf.get('test_options')
    venv_path = os.path.join(repo_directory(), config.venv_name())
    if opts.options:
        # command line overrides
        test_opts = opts.options
    activate = activate_command(venv_path)

    local(
        '{0} && nosetests -w {1} {2}'.format(
            activate,
            where,
            test_opts if test_opts else ""
        )
    )


def tox_run(config, opts):
    """
    tox test

    activate venv and run tox test suite

    """
    suite_conf = config.test_suite(opts.suite)
    tox_ini = suite_conf.get('tox_ini')
    test_opts = suite_conf.get('test_options')
    venv_path = os.path.join(repo_directory(), config.venv_name())
    if opts.options:
        # command line overrides
        test_opts = opts.options
    tox_command = "tox"
    if tox_ini:
        tox_command += " -c {}".format(tox_ini)
    if test_opts:
        tox_command += " {}".format(test_opts)
    activate = activate_command(venv_path)
    local(
        '{0} && {1}'.format(
            activate,
            tox_command
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
