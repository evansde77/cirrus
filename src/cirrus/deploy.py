#!/usr/bin/env python
"""
_deploy_

cirrus deployment command.

Essentially a thin wrapper for the deploy_plugins
module and its constituent bits

"""
import pluggage.registry
from argparse import ArgumentParser
from cirrus.logger import get_logger
from cirrus.configuration import load_configuration


LOGGER = get_logger()


def get_plugin(plugin_name):
    """
    _get_plugin_

    Get the deploy plugin requested from the factory
    """
    factory = pluggage.registry.get_factory(
        'deploy',
        load_modules=['cirrus.plugins.deployers']
    )
    return factory(plugin_name)


def build_parser():
    """
    _build_parser_

    Set up command line parser for the deploy command

    """
    parser = ArgumentParser(
        description='git cirrus deploy command'
    )
    parser.add_argument(
        '--plugin', '-p', dest='plugin', default=None,
        help="Name of deployment plugin to load"
        )
    opts, _ = parser.parse_known_args()
    return opts


def main():
    """
    _main_

    Look up the plugin to be invoked for deployment, via the CLI or cirrus config
    for this package, and then invoke the deployer plugin

    """
    initial_opts = build_parser()
    pname = initial_opts.plugin
    if initial_opts.plugin is None:
        config = load_configuration()
        try:
            pname = config.get_param('deploy', 'plugin', None)
        except KeyError:
            pname = None
    if pname is None:
        msg = "No Plugin specified with --plugin or in cirrus.conf for deploy"
        raise RuntimeError(msg)

    plugin = get_plugin(pname)
    plugin.build_parser()
    opts = plugin.parser.parse_args()
    plugin.deploy(opts)


if __name__ == '__main__':
    main()
