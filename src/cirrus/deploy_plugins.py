#!/usr/bin/env python
"""
_deploy_plugins_

Plugin helpers to talk to various deployment platforms

"""
from cirrus.logger import get_logger
from cirrus.configuration import load_configuration


LOGGER = get_logger()
_PLUGINS = {}


def bootstrap_parser(subparser):
    """
    _bootstrap_parser_

    Util to loop through registered plugin instances
    and call their build_parser hooks to add them to
    the CLI suite

    """
    for plugin, instance in _PLUGINS.iteritems():
        deployer_command = subparser.add_parser(plugin)
        instance.build_parser(deployer_command)


def get_plugin(plugin_name):
    """
    _get_plugin_

    Helper to get the plugin instance based on the name
    """
    return _PLUGINS.get(plugin_name)


class DeployerRegistry(type):
    """
    _DeployerRegistry_

    metaclass to register plugin subclasses with plugins registry

    """
    def __init__(cls, name, bases, dct):
        pname = getattr(cls, 'plugin_name')
        if name != "DeployerPlugin":
            assert (pname is not None)
        if pname not in _PLUGINS:
            _PLUGINS[pname] = cls()
        else:
            raise RuntimeError(
                "Duplicate plugin name: {0}".format(pname)
            )
        super(DeployerRegistry, cls).__init__(name, bases, dct)


class DeployerPlugin(object):
    """
    _DeployerPlugin_

    Base class for Deployer plugins.

    Plugin implementations should inherit this,
    override the plugin_name attribute (this will be exposed
        as the command name in the CLI, for example plugin_name="womp"
        will make the plugin available via git cirrus deploy womp )

    The build_parser method sets up the CLI argparse options for the plugin
    The deploy method consumes the options namespace from the parser
    and then executes whatever code it needs to perform the deployment action

    Registry with the plugin framework is handled via the metaclass

    The base class provides some helpers to get at the package
    and user configuration to allow for config access and customisation


    """
    __metaclass__ = DeployerRegistry
    plugin_name = None

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


class ChefServerDeployer(DeployerPlugin):
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
    plugin_name = 'chef'

    def deploy(self, **kwargs):
        """
        _deploy_

        Implement deployment via chef server.

        """
        pass

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
