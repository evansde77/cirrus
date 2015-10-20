#!/usr/bin/env python
"""
_deploy_plugins_

Plugin helpers to talk to various deployment platforms

"""
from cirrus.logger import get_logger
from cirrus.configuration import load_configuration
from pluggage.errors import FactoryError
from pluggage.factory_plugin import PluggagePlugin
from pluggage.registry import get_factory

LOGGER = get_logger()

# This dict defines which plugin class should handle an ArgumentParser
# subcommand.  Pluggage allows for multiple plugin classes per factory name, but
# here we want a single plugin class to handle a single factory name (or in this
# case, a subcommand)
_REGISTERED_PLUGINS = {'chef': 'ChefServerDeployer'}

# Plugin instance storage
_PLUGINS = {}


def bootstrap_parser(subparser):
    """
    _bootstrap_parser_

    Util to loop through registered plugin instances
    and call their build_parser hooks to add them to
    the CLI suite
    """
    for plugin_factory, plugin_cls in _REGISTERED_PLUGINS.iteritems():
        factory = get_factory(plugin_factory)
        try:
            instance = factory(plugin_cls)
        except FactoryError:
            LOGGER.warn('Could not load plugin "{}"'.format(plugin_cls))
            continue

        deployer_command = subparser.add_parser(plugin_factory)
        instance.build_parser(deployer_command)

        # Store the plugin instance with its command name as the key
        _PLUGINS[plugin_factory] = instance


def get_plugin(plugin_name):
    """
    _get_plugin_

    Helper to get the plugin instance based on the name
    """
    return _PLUGINS.get(plugin_name)


class DeployerBase(object):

    def __init__(self):
        self.package_conf = load_configuration()

    def deploy(self, options):
        """
        _deploy_

        :param options: Instance of argparse namespace containing
        the command line options values

        """
        raise NotImplementedError(
            "{0}.deploy not implemented".format(type(self).__name__)
        )

    def build_parser(self, command_parser):
        """
        _build_parser_

        Hook for the plugin to build out its commandline tool
        suite.

        command_parser is the argparse parser instance for the plugin
        to add its extensions to
        """
        raise NotImplementedError(
            "{0}.build_parser not implemented".format(type(self).__name__)
        )


class ChefServerDeployer(DeployerBase, PluggagePlugin):
    """
    _ChefServerDeployer_

    Implement a chef deployment plugin.

    This assumes your deployment process looks something like:

    1. Bump the package version in an env/role/node for some attribute
       to the current version of this python package
    2. Run pre-chef-client commands on the specified nodes
    3. Run chef-client on the specified nodes
    4. Run post-chef-client commands on the specified nodes

    This plugin runs chef-client serially and is more suited to
    a few nodes (eg a CI or integ system) rather than a full
    scale deployment across many nodes

    """

    PLUGGAGE_FACTORY_NAME = 'chef'

    def deploy(self, opts):
        """
        _deploy_

        Implement deployment via chef server.

        """
        LOGGER.info('Chef deployment running...')
        LOGGER.info(opts)

    def build_parser(self, command_parser):
        """
        _build_parser_

        construct chef plugin cli options

        """
        command_parser.add_argument(
            '--environment', '-e',
            dest='environment',
            default=None,
            help='Chef environment to edit'
        )
        command_parser.add_argument(
            '--role', '-r',
            dest='role',
            default=None,
            help='Chef role to edit'
            )
        command_parser.add_argument(
            '--node', '-n',
            dest='node',
            default=None,
            help='Chef node to edit'
            )
        command_parser.add_argument(
            '--data-bag', '-d',
            dest='data_bag',
            default=None,
            help='Chef data_bag to edit'
            )
        command_parser.add_argument(
            '--attribute', '-a',
            dest='attribute',
            required=True,
            help=(
                'Version attribute to be bumped as '
                'name1.name2.attribute style'
            )
        )
        command_parser.add_argument(
            '--chef-repo',
            dest='chef_repo',
            help=(
                'Location of chef-repo to update '
                'environment files, if desired'
            )
        )
        command_parser.add_argument(
            '--nodes-list',
            dest='node_list',
            help='list of nodes to execute chef-client on',
            nargs='+'
        )
