import sys

from argparse import ArgumentParser

from cirrus.release.new import new_release, make_new_version
from cirrus.release.status import show_release_status
from cirrus.release.merge import merge_release, cleanup_release
from cirrus.release.upload import upload_release
from cirrus.release.build import build_release
from cirrus.release.status import release_status


def build_parser(argslist):
    """
    _build_parser_

    Set up command line parser for the release command

    """
    parser = ArgumentParser(
        description='git cirrus release command'
    )
    parser.add_argument('command', nargs='?')

    subparsers = parser.add_subparsers(dest='command')
    new_command = subparsers.add_parser('new')
    new_command.add_argument(
        '--micro',
        action='store_true',
        dest='micro'
    )
    new_command.add_argument(
        '--minor',
        action='store_true',
        dest='minor'
    )
    new_command.add_argument(
        '--major',
        action='store_true',
        dest='major'
    )
    new_command.add_argument(
        '--nightly',
        action='store_true',
        dest='nightly',
        default=False
    )
    new_command.add_argument(
        '--skip-existing',
        default=False,
        action='store_true',
        help='Increment past any existing, unmerged release branches'
    )
    new_command.add_argument(
        '--bump',
        nargs=2,
        action='append',
        help='package versions to update in requirements.txt, eg --bump argparse 1.2.1 --bump womp 9.9.9'
    )
    new_command.add_argument(
        '--no-remote',
        action='store_true',
        default=False,
        help="dont push release branch to remote"
    )

    # borrow --micro/minor/major options from "new" command.
    subparsers.add_parser('trigger', parents=[new_command], add_help=False)
    new_version_command = subparsers.add_parser('new-version', parents=[new_command], add_help=False)

    cleanup_command = subparsers.add_parser(
        'cleanup'
    )
    cleanup_command.add_argument(
        '--version', '-v',
        help='version to cleanup, defaults to current release',
        default=None
    )
    cleanup_command.add_argument(
        '--no-remote',
        help='Do not remove remote branch if set',
        default=False,
        action='store_true'
    )

    subparsers.add_parser('build')

    status_command = subparsers.add_parser('status')
    status_command.add_argument(
        '--release',
        help='check status of the provided release, defaults to current branch',
        default=None
    )

    merge_command = subparsers.add_parser('merge')
    merge_command.add_argument(
        '--wait-on-ci',
        action='store_true',
        dest='wait_on_ci',
        default=False,
        help='Wait for GH CI status to be success before uploading'
    )
    merge_command.add_argument(
        '--context-string',
        default=None,
        dest='github_context_string',
        help='Update the github context string provided when pushed'
    )

    merge_command.add_argument(
        '--develop-context-string',
        default=None,
        dest='github_develop_context_string',
        help='Update the github context string for develop branch provided when pushed'
    )
    merge_command.add_argument(
        '--master-context-string',
        default=None,
        dest='github_master_context_string',
        help='Update the github context string for master branch provided when pushed'
    )

    merge_command.add_argument(
        '--cleanup',
        action='store_true',
        dest='cleanup',
        help='Clean up release branch after merging'
    )
    merge_command.add_argument(
        '--skip-master',
        action='store_true',
        dest='skip_master',
        default=False,
        help='Skip the master merge and push'
    )
    merge_command.add_argument(
        '--skip-develop',
        action='store_true',
        dest='skip_develop',
        default=False,
        help='Skip the develop merge and push'
    )
    merge_command.add_argument(
        '--log-status',
        action='store_true',
        dest='log_status',
        default=False,
        help='log all status values for branches during command'
    )
    merge_command.add_argument(
        '--no-remote',
        help='Do not remove remote branch if set',
        default=False,
        action='store_true'
    )

    upload_command = subparsers.add_parser('upload')
    upload_command.add_argument(
        '--test',
        action='store_true',
        dest='test',
        help='test only, do not actually push or upload'
    )
    upload_command.add_argument(
        '--plugin',
        dest='plugin',
        default='pypi',
        help='Uploader plugin to use'
    )
    upload_command.add_argument(
        '--pypi-url', '-r',
        action='store',
        dest='pypi_url',
        help='upload to specified pypi url'
    )
    upload_command.add_argument(
        '--pypi-sudo',
        action='store_true',
        dest='pypi_sudo',
        help='use sudo to upload build artifact to pypi'
    )
    upload_command.add_argument(
        '--no-pypi-sudo',
        action='store_false',
        dest='pypi_sudo',
        help='do not use sudo to upload build artifact to pypi'
    )
    upload_command.set_defaults(pypi_sudo=True)

    opts = parser.parse_args(argslist)
    return opts


def main():
    opts = build_parser(sys.argv)
    if opts.command == 'new':
        new_release(opts)

    if opts.command == 'new-version':
        make_new_version(opts)

    if opts.command == 'status':
        show_release_status(opts)

    if opts.command == 'trigger':
        trigger_release(opts)

    if opts.command == 'merge':
        merge_release(opts)

    if opts.command == 'upload':
        upload_release(opts)

    if opts.command == 'build':
        build_release(opts)

    if opts.command == 'cleanup':
        cleanup_release(opts)


