#!/usr/bin/env python
"""
_review_

Tools for working with and reviewing PRs on GitHub,
including ability to set a specific status context for a branch
to allow for confirmation of reviews for code compliance etc

"""
import os
import sys
import pprint

from argparse import ArgumentParser
from cirrus.github_tools import GitHubContext


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the review command

    """
    parser = ArgumentParser(
        description='git cirrus review command'
    )
    parser.add_argument('command', nargs='?')

    subparsers = parser.add_subparsers(dest='command')
    list_command = subparsers.add_parser('list')
    list_command.add_argument(
        '--user', '-u',
        type=str,
        default=None,
        dest='user',
        help='Filter by username'
    )

    detail_command = subparsers.add_parser('details')
    detail_command.add_argument(
        '--id', '-i',
        required=True,
        type=int,
        dest='id',
        help='ID of pull request'
    )

    review_command = subparsers.add_parser('review')
    review_command.add_argument(
        '--id', '-i',
        required=True,
        type=int,
        dest='id',
        help='ID of pull request to review'
    )
    review_command.add_argument(
        '--comment', '-m',
        type=str,
        required=True,
        dest='comment',
        help='Review comment text'
    )
    review_command.add_argument(
        '--plus-one', '-p',
        type=bool,
        default=False,
        dest='plus_one',
        help='Add a plus-one status'
    )
    review_command.add_argument(
        '--plus-one-context',
        default='+1',
        dest='plus_one_context',
        help='Github context string to use as +1 tag'
    )
    plusone_command = subparsers.add_parser('plusone')
    plusone_command.add_argument(
        '--id', '-i',
        required=True,
        type=int,
        dest='id',
        help='ID of pull request to approve/+1'
    )
    plusone_command.add_argument(
        '--plus-one-context', '-c',
        default='+1',
        dest='plus_one_context',
        help='Github context string to use as +1 tag'
    )
    opts = parser.parse_args(argslist)
    return opts


def list_prs(opts):
    """
    _list_prs_

    Print a summary of all open PRs for this repo
    optionally filtered by user

    """
    repo_dir = os.getcwd()
    with GitHubContext(repo_dir) as ghc:
        print "  ID,  User, Title"
        for pr in ghc.pull_requests(user=opts.user):
            print pr['number'], pr['user']['login'], pr['title']


def get_pr(opts):
    """
    _get_pr_

    Print the details of the pr specified by the CLI opts

    """
    repo_dir = os.getcwd()
    with GitHubContext(repo_dir) as ghc:
        pr_data = ghc.pull_request_details(opts.id)
        pprint.pprint(pr_data, indent=2)


def review_pr(opts):
    """
    _review_pr_

    Add a review comment to a PR, and optionally set the
    plus one context status
    """
    repo_dir = os.getcwd()
    with GitHubContext(repo_dir) as ghc:
        ghc.review_pull_request(
            opts.id,
            opts.comment,
            opts.plus_one,
            opts.plus_one_context
        )


def plusone_pr(opts):
    """
    _plusone_pr_

    Set the +1 context status for the PR
    """
    repo_dir = os.getcwd()
    with GitHubContext(repo_dir) as ghc:
        ghc.plus_one_pull_request(
            pr_id=opts.id,
            context=opts.plus_one_context
        )


def main():
    """
    _main_

    call appropriate function based on command line opts
    """
    opts = build_parser(sys.argv)
    if opts.command == 'list':
        list_prs(opts)
    if opts.command == 'review':
        review_pr(opts)
    if opts.command == 'details':
        get_pr(opts)
    if opts.command == 'plusone':
        plusone_pr(opts)


if __name__ == '__main__':
    main()
