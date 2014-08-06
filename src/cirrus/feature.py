'''
_feature_

Command to create a new feature branch off of the develop branch
'''
import os
from argparse import ArgumentParser

from cirrus.configuration import load_configuration
from cirrus.git_tools import checkout_and_pull, branch, push


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the release command

    """
    parser = ArgumentParser(
        description='git cirrus feature command'
    )
    parser.add_argument('command', nargs='?')

    subparsers = parser.add_subparsers(dest='command')
    new_command = subparsers.add_parser('new')
    new_command.add_argument(dest='name', required=True)
    new_command.add_argument('--push', dest='push', action='store_true')

    opts = parser.parse_args(argslist)
    return opts


def new_feature_branch(opts):
    config = load_configuration()
    repo_dir = os.getcwd()
    checkout_and_pull(
        repo_dir,
        config.gitflow_branch_name())
    branch(repo_dir,
           ''.join((config.gitflow_feature_prefix(), opts.name)),
           config.gitflow_branch_name())
    if opts.push:
        print opts.push
        push(repo_dir)


def main(argslist):
    """
    _main_

    Execute feature command
    """
    opts = build_parser(argslist)
    if opts.command == 'new':
        new_feature_branch(opts)
    else:
        exit(1)
