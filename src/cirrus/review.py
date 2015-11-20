#!/usr/bin/env python
"""
_review_

Tools for working with and reviewing PRs on GitHub,
including ability to set a specific status context for a branch
to allow for confirmation of reviews for code compliance etc

"""

from argparse import ArgumentParser


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the release command

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
        '--plus-one', '-p',
        type=bool,
        default=False,
        dest='plus_one',
        help='Add a plus-one status'
    )
    review_command.add_argument(
        '--plus-one-context', '-c',
        default='+1',
        dest='plus_one_context',
        help='Github context string to use as +1 tag'
    )


def list_prs(opts):
    pass


def get_pr(opts):
    pass


def review_pr(opts):
    pass



def main():
    opts = build_parser(sys.argv)
    if opts.command == 'list':
        list_prs(opts)
    if opts.command == 'review':
        review_pr(opts)
    if opts.command == 'details':
        get_pr(opts)



if __name__ == '__main__':

    main()