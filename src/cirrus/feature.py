'''
_feature_

Command to create a new feature branch off of the develop branch
'''
import os
from argparse import ArgumentParser

from cirrus.configuration import load_configuration
from cirrus.git_tools import checkout_and_pull, branch, push
from cirrus.github_tools import create_pull_request


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
    new_command.add_argument('name', required=True)
    new_command.add_argument('--push', action='store_true')

    pr_command = subparsers.add_parser('pull-request')
    pr_command.add_argument('--title', required=True)
    pr_command.add_argument('--body', required=True)
    pr_command.add_argument('--notify', required=False)

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
        push(repo_dir)


def new_pr(opts):
    config = load_configuration()
    repo_dir = os.getcwd()
    pr_body = '{0} \n{1}'.format(opts.notify, opts.body)
    pr_info = {
        'title': opts.title,
        'body': pr_body}
    create_pull_request(
        repo_dir,
        config.organisation_name(),
        pr_info)


def main(argslist):
    """
    _main_

    Execute feature command
    """
    opts = build_parser(argslist)
    if opts.command == 'new':
        new_feature_branch(opts)
    if opts.command == 'pull-request':
        new_pr(opts)
    else:
        exit(1)
