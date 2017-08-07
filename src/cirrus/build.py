#!/usr/bin/env python
"""
_build_

Implements the cirrus build command.

This command:
 - creates a virtualenv in the package
 - pip installs requirements.txt for the package into the venv

"""
import sys
from argparse import ArgumentParser
import pluggage.registry

from cirrus.documentation_utils import build_docs
from cirrus.environment import is_anaconda
from cirrus.configuration import load_configuration
from cirrus.logger import get_logger


LOGGER = get_logger()

FACTORY = pluggage.registry.get_factory(
    'builder',
    load_modules=['cirrus.plugins.builders']
)


def get_builder_plugin():
    """
    Get the builder plugin name default.

    If not provided by CLI opt, start with
    user pref in gitconfig,
    Look for hint in cirrus conf or just resort
    to a guess based on what python cirrus is using

    """
    # TODO look up in git config
    config = load_configuration()
    builder = None
    if config.has_gitconfig_param('builder'):
        builder = str(config.get_gitconfig_param('builder'))
    if builder:
        LOGGER.info("Using Builder Plugin from gitconfig: {}".format(builder))
        return builder

    build_config = config.get('build', {})
    builder = build_config.get('builder')
    if builder is not None:
        LOGGER.info("Using Builder Plugin from cirrus.conf: {}".format(builder))
        return builder
    # fall back to old defaults
    if is_anaconda():
        LOGGER.info("Using default CondaPip builder")
        builder = "CondaPip"
    else:
        LOGGER.info("Using default VirtualenvPip builder")
        builder = "VirtualenvPip"
    return builder


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the build command

    : param list argslist: A list of command line arguments
    """
    parser = ArgumentParser(
        description='git cirrus build'
    )
    parser.add_argument('command', nargs='?')
    parser.add_argument(
        '-c',
        '--clean',
        action='store_true',
        help='remove existing virtual environment')

    parser.add_argument(
        '-d',
        '--docs',
        nargs='*',
        help=(
            'generate documentation with Sphinx '
            '(Makefile path must be set in cirrus.conf.'
        )
    )
    parser.add_argument(
        '--builder', '-b',
        help="Builder plugin to use to create dev environment",
        default=None
        )

    parser.add_argument(
        '-u',
        '--upgrade',
        action='store_true',
        default=False,
        help=(
            'Use --upgrade to update the dependencies '
            'in the package requirements'
        )
    )
    parser.add_argument(
        '--extra-requirements',
        nargs="+",
        default=[],
        dest='extras',
        help='extra requirements files to install'
    )

    parser.add_argument(
        '--no-setup-develop',
        dest='nosetupdevelop',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '--python', '-p',
        help='Which python to use to create venv',
        default=None
    )
    build_opts, plugin_opts = parser.parse_known_args(argslist)
    return build_opts, plugin_opts


def plugin_build(opts, extras):
    if opts.builder is None:
        opts.builder = get_builder_plugin()
    LOGGER.info("Using builder: {}".format(opts.builder))
    builder = FACTORY(opts.builder)
    extra_options = builder.process_extra_args(extras)
    options = vars(opts)
    options.update(extra_options)
    builder.create(**options)


def main():
    """
    _main_

    Execute build command
    """
    opts, extras = build_parser(sys.argv)
    plugin_build(opts, extras)
    if opts.docs is not None:
        build_docs(make_opts=opts.docs)


if __name__ == '__main__':
    main()
