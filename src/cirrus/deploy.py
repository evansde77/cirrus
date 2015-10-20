#!/usr/bin/env python
"""
_deploy_

cirrus deployment command.

Essentially a thin wrapper for the deploy_plugins
module and its constituent bits

"""
from argparse import ArgumentParser
from cirrus.deploy_plugins import bootstrap_parser, get_plugin
from cirrus.logger import get_logger

LOGGER = get_logger()


def build_parser():
    """
    _build_parser_

    Set up command line parser for the deploy command

    """
    parser = ArgumentParser(
        description='git cirrus deploy command'
    )
    subparsers = parser.add_subparsers(dest='command')
    bootstrap_parser(subparsers)
    opts = parser.parse_args()
    return opts


def main():
    opts = build_parser()
    plugin = get_plugin(opts.command)
    plugin.deploy(opts)


if __name__ == '__main__':
    main()
