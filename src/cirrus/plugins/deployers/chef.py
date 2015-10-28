#!/usr/bin/env python
"""
_chef_

Chef deployer plugin

"""
from cirrus.logger import get_logger
from cirrus.deploy_plugins import Deployer


LOGGER = get_logger()


class ChefServerDeployer(Deployer):
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

    PLUGGAGE_OBJECT_NAME = 'chef'

    def deploy(self, opts):
        """
        _deploy_

        Implement deployment via chef server.

        """
        LOGGER.info('Chef deployment running...')
        LOGGER.info(opts)

    def build_parser(self):
        """
        _build_parser_

        construct chef plugin cli options

        """
        self.parser.add_argument(
            '--environment', '-e',
            dest='environment',
            default=None,
            help='Chef environment to edit'
        )
        self.parser.add_argument(
            '--role', '-r',
            dest='role',
            default=None,
            help='Chef role to edit'
            )
        self.parser.add_argument(
            '--node', '-n',
            dest='node',
            default=None,
            help='Chef node to edit'
            )
        self.parser.add_argument(
            '--data-bag', '-d',
            dest='data_bag',
            default=None,
            help='Chef data_bag to edit'
            )
        self.parser.add_argument(
            '--attribute', '-a',
            dest='attribute',
            required=True,
            help=(
                'Version attribute to be bumped as '
                'name1.name2.attribute style'
            )
        )
        self.parser.add_argument(
            '--chef-repo',
            dest='chef_repo',
            help=(
                'Location of chef-repo to update '
                'environment files, if desired'
            )
        )
        self.parser.add_argument(
            '--nodes-list',
            dest='node_list',
            help='list of nodes to execute chef-client on',
            nargs='+'
        )
