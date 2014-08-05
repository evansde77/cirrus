'''
_feature_

Command to create a new feature branch off of the develop branch
'''
import os
from argparse import ArgumentParser

from cirrus.configuration import load_configuration
from cirrus.git_tools import checkout_and_pull, branch, commit_files


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
    new_command.add_argument(
        '--name',
        dest='name',
        required=True
    )

    push_command = subparsers.add_parser('push')
    push_command.add_argument(
        '-m',
        dest='c_msg',
        help='Commit Message',
        required=True)
    push_command.add_argument(
        '--add',
        dest='c_files',
        help="list of files separated by ','",
        required=True)

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


def push_feature(opts):
    repo_dir = os.getcwd()
    commit_files(repo_dir, opts.c_msg, opts.c_files.split(','))


def main(argslist):
    """
    _main_

    Execute feature command
    """
    opts = build_parser(argslist)
    if opts.command == 'new':
        new_feature_branch(opts)
    if opts.command == 'push':
        push_feature(opts)
    else:
        exit(1)
