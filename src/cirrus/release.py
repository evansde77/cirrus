#!/usr/bin/env python
"""
_release_

Implement git cirrus release command


"""

from argparse import ArgumentParser

def highlander(iterable):
    """check only single True value in iterable"""
    # There Can Be Only One!!!
    i = iter(iterable)
    return any(i) and not any(i)


def build_parser(argslist):
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



    publish_command = subparsers.add_parser('publish')

    opts = parser.parse_args(argslist)
    return opts


def new_release(opts):
    """
    _new_release_
    """
    print opts

    if not highlander( [opts.major, opts.minor, opts.micro]):
        msg = "Can only specify one of --major, --minor or --micro"
        raise RuntimeError(msg)

def publish_release(opts):
    """
    _publish_release_
    """
    print opts


def main(argslist):

    opts = build_parser(argslist)
    if opts.command == 'new':
        new_release(opts)

    if opts.command == 'publish':
        publish_release(opts)





if __name__ == '__main__':
    main(['new', '--micro'])
    main(['publish'])
