#!/usr/bin/env python
"""
_docs_

Implement git cirrus docs command
"""
import sys
from argparse import ArgumentParser
from cirrus.configuration import load_configuration
from cirrus.documentation_utils import (
    build_docs,
    build_doc_artifact,
    publish_documentation)


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the docs command
    """
    parser = ArgumentParser(description='git cirrus docs command')
    parser.add_argument('command', nargs='?')

    subparsers = parser.add_subparsers(dest='command')
    build_command = subparsers.add_parser(
        'build',
        help='Build Sphinx documentation')
    build_command.add_argument(
        '--make',
        nargs='*',
        help=('generate documentation with Sphinx (Makefile path must be set '
              'in cirrus.conf) and create an artifact. Argument list is used '
              'to run the Sphinx make command. Default: clean html'))
    build_command.set_defaults(make=[])

    subparsers.add_parser(
        'pack',
        help='Package documentation as a tarball')

    publish_command = subparsers.add_parser(
        'publish',
        help='Publish documentation as specified in cirrus.conf')
    publish_command.add_argument(
        '--test',
        action='store_true',
        help='test only, do not actually publish documentation'
    )
    publish_command.set_defaults(test=False)

    opts = parser.parse_args(argslist)
    return opts


def main():
    opts = build_parser(sys.argv)
    if opts.command == 'build':
        build_docs(make_opts=opts.make)

    if opts.command == 'pack':
        build_doc_artifact()

    if opts.command == 'publish':
        publish_documentation(opts)


if __name__ == '__main__':
    main()
