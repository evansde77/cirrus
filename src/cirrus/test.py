"""
_test_

Command to run available test suites in a package
"""
import sys

from cirrus.invoke_helpers import local
from argparse import ArgumentParser

from cirrus.configuration import load_configuration
from cirrus.build import get_builder_plugin, FACTORY


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
        choices=['nosetests', 'tox', 'pytest'],
        default=None,
        help='Choose test runner framework'
    )
    parser.add_argument(
        '--test-options',
        default='',
        dest='options',
        help='Optional args to pass to test runner'
    )
    parser.add_argument(
        '--builder', '-b',
        help="optional development environment builder to use",
        default=None
    )

    opts = parser.parse_args(argslist)
    return opts


def nose_run(config, opts):
    """
    _nose_test_

    Locally activate vitrualenv and run tests via nose
    """
    where = config.test_where(opts.suite)
    suite_conf = config.test_suite(opts.suite)
    test_opts = suite_conf.get('test_options')
    if opts.options:
        # command line overrides
        test_opts = opts.options

    if opts.builder is None:
        opts.builder = get_builder_plugin()

    builder = FACTORY(opts.builder)
    activate = builder.activate()

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
    if opts.options:
        # command line overrides
        test_opts = opts.options
    tox_command = "tox"
    if tox_ini:
        tox_command += " -c {}".format(tox_ini)
    if test_opts:
        tox_command += " {}".format(test_opts)

    if opts.builder is None:
        opts.builder = get_builder_plugin()

    builder = FACTORY(opts.builder)
    activate = builder.activate()
    local(
        '{0} && {1}'.format(
            activate,
            tox_command
        )
    )


def pytest_run(config, opts):
    """
    activate venv and run pytest
    """
    suite_conf = config.test_suite(opts.suite)
    test_opts = suite_conf.get('test_options')
    where = suite_conf.get('where', 'tests/unit')
    if opts.options:
        # command line overrides
        test_opts = opts.options
    command = "pytest {}".format(where)
    if test_opts:
        command += " {}".format(test_opts)

    if opts.builder is None:
        opts.builder = get_builder_plugin()

    builder = FACTORY(opts.builder)
    activate = builder.activate()
    local(
        '{0} && {1}'.format(
            activate,
            command
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
    if mode == 'pytest':
        pytest_run(config, opts)
        sys.exit(0)


if __name__ == '__main__':
    main()
