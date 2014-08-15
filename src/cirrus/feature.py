'''
_feature_

Command to create a new feature branch off of the develop branch
'''
import os
import sys
from argparse import ArgumentParser

from cirrus.configuration import load_configuration
from cirrus.git_tools import checkout_and_pull, branch, push
from cirrus.github_tools import create_pull_request
from cirrus.logger import get_logger

LOGGER = get_logger()


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
    new_command.add_argument('name', nargs='+')
    new_command.add_argument(
        '--push',
        help='include this to push new feature to remote',
        action='store_true')

    pr_command = subparsers.add_parser('pull-request')
    pr_command.add_argument('-t', '--title', dest='title', required=True)
    pr_command.add_argument('-b', '--body', dest='body', required=True)
    pr_command.add_argument(
        '-n',
        '--notify',
        help='users you would like to be notified',
        required=False)

    opts = parser.parse_args(argslist)
    return opts


def new_feature_branch(opts):
    """
    _new_feature_branch_

    Checks out branch, creates new branch 'name', optionally
    pushes new branch to remote
    """
    config = load_configuration()
    repo_dir = os.getcwd()
    checkout_and_pull(
        repo_dir,
        config.gitflow_branch_name())
    LOGGER.info("Checked out and pulled {0}".format(
        config.gitflow_branch_name()))
    branch_name = ''.join((config.gitflow_feature_prefix(), opts.name[0]))
    branch(repo_dir,
           branch_name,
           config.gitflow_branch_name())
    LOGGER.info("Created branch {0}".format(branch_name))
    if opts.push:
        push(repo_dir)
        LOGGER.info("Branch {0} pushed to remote".format(branch_name))


def new_pr(opts):
    """
    _new_pr_

    Creates a pull request
    """
    repo_dir = os.getcwd()
    pr_body = '{0} \n{1}'.format(opts.notify, opts.body)
    pr_info = {
        'title': opts.title,
        'body': pr_body}
    pr_url = create_pull_request(repo_dir, pr_info)
    LOGGER.info("Created PR {0}".format(pr_url))


def main():
    """
    _main_

    Execute feature command
    """
    opts = build_parser(sys.argv)
    if opts.command == 'new':
        new_feature_branch(opts)
    if opts.command == 'pull-request':
        new_pr(opts)
    else:
        exit(1)


if __name__ == '__main__':
    main()
