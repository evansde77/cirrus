#!/usr/bin/env python
"""
package

Implementation for the package command that handles helping set up and
manipulate packages for use with cirrus.

Commands:

package init - Initialise a new repo with a basic cirrus.conf file
  add the appropriate setup, manifest and requirements files

package sublime-project - Assistant to set up a sublime project for a cirrus
  managed package, including build rules for the local venv

"""
import sys
import os
from argparse import ArgumentParser


def build_parser(argslist):
    """
    build CLI parser and process args
    """
    parser = ArgumentParser(
        description='git cirrus package command'
    )
    parser.add_argument('command', nargs='?')

    subparsers = parser.add_subparsers(dest='command')
    init_command = subparsers.add_parser('init')
    init_command.add_argument(
        '--repo', '-r',
        dest='repo',
        default=os.getcwd()
    )

    subl_command = subparsers.add_parser('sublime-project')
    subl_command.add_argument(
        '--project-name', '-p',
        dest='project',
        help='Name of project, defaults to name of cirrus package',
        default=None
    )
    subl_command.add_argument(
        '--include-nose',
        help='Include a nosetests build rule',
        dest='include_nose',
        default=False,
        action='store_true'
    )
    subl_command.add_argument(
        '--python-path',
        nargs='+',
        help='extra directories in package to add to pythonpath in sublime project',
        dest='pythonpath',
        default=list()
    )

    opts = parser.parse_args(argslist)
    return opts


def init_package(opts):
    """
    initialise a repo with a basic cirrus setup
    """


def subl_project(opts):
    """
    create a sublime project file for a repo
    """




def main():
    """
    main cli response handler
    """
    opts = build_parser(sys.argv)

    if opts.command == 'init':
        init_package(opts)


if __name__ == '__main__':
    main()
