'''
_feature_

Command to create a new feature branch off of the develop branch
'''
import os
import sys
from argparse import ArgumentParser

from cirrus.configuration import load_configuration
from cirrus.environment import repo_directory
from cirrus.git_tools import checkout_and_pull, branch, push
from cirrus.git_tools import has_unstaged_changes, current_branch
from cirrus.github_tools import create_pull_request
from cirrus.github_tools import GitHubContext
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
        help='Deprecated, use --no-remote instead',
        default=True,
        action='store_true')
    new_command.add_argument(
        '--no-remote',
        help='Do not hit remote if set',
        default=False,
        action='store_true'
    )

    pr_command = subparsers.add_parser('pull-request')
    pr_command.add_argument('-t', '--title', dest='title', required=True)
    pr_command.add_argument('-b', '--body', dest='body', required=True)
    pr_command.add_argument(
        '-n',
        '--notify',
        help='users you would like to be notified',
        required=False)

    short_pr_command = subparsers.add_parser('pr')
    short_pr_command.add_argument('-t', '--title', dest='title', required=True)
    short_pr_command.add_argument('-b', '--body', dest='body', required=True)
    short_pr_command.add_argument(
        '-n',
        '--notify',
        help='users you would like to be notified',
        required=False)

    merge_command = subparsers.add_parser('merge')
    merge_command.add_argument(
        '--no-remote',
        help='Do not hit remote if set',
        default=False,
        action='store_true'
    )

    list_command = subparsers.add_parser('list')

    opts = parser.parse_args(argslist)
    return opts


def new_feature_branch(opts):
    """
    _new_feature_branch_

    Checks out branch, creates new branch 'name', optionally
    pushes new branch to remote
    """
    config = load_configuration()
    repo_dir = repo_directory()
    checkout_and_pull(
        repo_dir,
        config.gitflow_branch_name(),
        pull=not opts.no_remote
    )
    LOGGER.info("Checked out and pulled {0}".format(
        config.gitflow_branch_name()))
    branch_name = ''.join((config.gitflow_feature_prefix(), opts.name[0]))
    branch(repo_dir,
           branch_name,
           config.gitflow_branch_name())
    LOGGER.info("Created branch {0}".format(branch_name))
    if not opts.no_remote:
        push(repo_dir)
        LOGGER.info("Branch {0} pushed to remote".format(branch_name))


def merge_feature_branch(opts):
    """
    merge current feature branch into develop
    """
    config = load_configuration()
    main_branch = config.gitflow_branch_name()
    repo_dir = repo_directory()
    curr_branch = current_branch(repo_dir)
    LOGGER.info("Merging {} into {}".format(curr_branch, main_branch))
    # make sure repo is clean
    if has_unstaged_changes(repo_dir):
        msg = (
            "Error: Unstaged changes are present on the feature branch {}"
            "Please commit them or clean up before proceeding"
        ).format(curr_branch)
        LOGGER.error(msg)
        raise RuntimeError(msg)

    checkout_and_pull(repo_dir,  main_branch, pull=not opts.no_remote)
    with GitHubContext(repo_dir) as ghc:
        ghc.merge_branch(curr_branch)
        if not opts.no_remote:
            ghc.push_branch(main_branch)
            LOGGER.info("Branch {0} pushed to remote".format(main_branch))


def new_pr(opts):
    """
    _new_pr_

    Creates a pull request
    """
    repo_dir = repo_directory()
    #parse notify adding '@' if necessary
    notifiees = []
    if opts.notify is not None:
        notify = opts.notify.split(',')
        for user in notify:
            if not user.startswith('@'):
                tmp = '@{0}'.format(user)
                notifiees.append(tmp)

    pr_body = '{0} \n{1}'.format(' '.join(notifiees), opts.body)
    pr_info = {
        'title': opts.title,
        'body': pr_body}
    pr_url = create_pull_request(repo_dir, pr_info)
    LOGGER.info("Created PR {0}".format(pr_url))


def list_feature_branches(opts):
    """
    list unmerged feature branches
    """
    repo_dir = repo_directory()
    print("unmerged feature branches:")
    with GitHubContext(repo_dir) as ghc:
        for x in ghc.iter_git_feature_branches(merged=False):
            print(x)


def main():
    """
    _main_

    Execute feature command
    """
    opts = build_parser(sys.argv)
    if opts.command == 'new':
        new_feature_branch(opts)
    if opts.command == 'list':
        list_feature_branches(opts)
    if opts.command in ('pull-request', 'pr'):
        new_pr(opts)
    if opts.command == 'merge':
        merge_feature_branch(opts)
    else:
        exit(1)


if __name__ == '__main__':
    main()
