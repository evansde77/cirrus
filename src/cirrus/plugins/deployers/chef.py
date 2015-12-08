#!/usr/bin/env python
"""
_chef_

Chef deployer plugin.

Uses defaults from package cirrus conf chef section
and overrides them with some CLI controls.

Example config:

[chef]
query="roles:nodes"
query_attribute=host
query_format_str="{}.cloudant.com"
chef_server=https://chef.my.org
chef_username=steve
chef_keyfile=/path/to/steve.pem
attributes=thing.application.version

"""
import os

from fabric.operations import run
from cirrus.fabric_helpers import FabricHelper
from cirrus.logger import get_logger
from cirrus.deploy_plugins import Deployer
import cirrus.chef_tools as ct
from cirrus.configuration import get_chef_auth


LOGGER = get_logger()


def attr_list(x):
    """
    parser for attribute lists on cli
    """
    if ',' in x:
        return [y for y in x.split(',') if y.strip()]
    else:
        return [x]


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

        args = self._read_cirrus_conf(opts)
        for opt in vars(opts):
            if (opt in args) and (getattr(opts, opt, None) is not None):
                args[opt] = getattr(opts, opt)
        args['version'] = self.package_conf.package_version()
        self._validate_args(args)

        attributes = {
            a: args['version'] for a in args['attributes']
        }

        if args['environment'] is not None:
            ct.update_chef_environment(
                args['chef_server'],
                args['chef_keyfile'],
                args['chef_username'],
                args['environment'],
                attributes,
                chef_repo=args['chef_repo']
            )

        if args['role'] is not None:
            raise NotImplemented("Dave is being lazy")

        nodes = self._find_nodes(args)
        if nodes:
            self.run_chef_client(args, nodes)

    def run_chef_client(self, opts, nodes):
        """
        _run_chef_client_

        Trigger a chef client run on each of the specified nodes

        """
        if opts['chef_client_user'] is None:
            msg = (
                "No chef client user provided, please update your gitconfig"
                " to include  chef-client-user and chef-client-keyfile"
                " in the cirrus section"
            )
            LOGGER.error(msg)
            raise RuntimeError(msg)

        for node in nodes:
            LOGGER.info("Running chef-client on {}".format(node))
            with FabricHelper(node, opts['chef_client_user'], opts['chef_client_keyfile']):
                run('sudo chef-client')

    def _find_nodes(self, args):
        """
        return list of nodes to run chef-client on
        """
        if args['node_list']:
            # CLI provided list wins
            return args['node_list']
        if args['query']:
            nodes = ct.list_nodes(
                args['chef_server'],
                args['chef_keyfile'],
                args['chef_username'],
                args['query'],
                attribute=args['query_attribute'],
                format_str=args['query_format_str']
            )
            return nodes
        return []

    def _read_cirrus_conf(self, opts):
        """
        extract the cirrus conf section for this plugin
        and reconcile against the opts provided.
        """
        chef_auth = get_chef_auth()
        params = [
            'environment',
            'role',
            'node_list',
            'query',
            'query_attribute',
            'query_format_str',
            'chef_repo',
            'chef_server',
            'chef_username',
            'chef_keyfile',
            'attributes'
        ]
        if 'chef' not in self.package_conf:
            result = {
                x: None for x in params
            }
            result.update(chef_auth)
            return result
        result = {
            param: self.package_conf.get_param('chef', param, None)
            for param in params
        }
        result['attributes'] = attr_list(result['attributes'])
        result.update(chef_auth)
        return result

    def _validate_args(self, args):
        """
        preprocess args and complain about stuff
        """
        if args['environment'] is None and args['role'] is None:
            msg = "Must provide role or environment to edit"
            LOGGER.error(msg)
            raise RuntimeError(msg)

        if args['chef_repo'] is not None:
            if not os.path.exists(args['chef_repo']):
                msg = "Chef Repo does not exist: {}".format(args['chef_repo'])
                LOGGER.error(msg)
                raise RuntimeError(msg)

        not_none = [
            'chef_server',
            'chef_username',
            'chef_keyfile',
            'attributes',
            'version'
        ]
        for nn in not_none:
            if args[nn] is None:
                msg = (
                    "Must provide a value for {} on CLI"
                    " or in cirrus.conf chef section"
                ).format(nn)
                LOGGER.error(msg)
                raise RuntimeError(msg)

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
        #TODO: value needs converted to a list
        self.parser.add_argument(
            '--attribute', '-a',
            dest='attributes',
            default=None,
            type=attr_list,
            help=(
                'Version attribute to be bumped as '
                'name1.name2.attribute style, use comma separation '
                'for multiple attrs'
                'Edits are made to override_attributes, '
                'do not prefix with override_attributes'
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
            '--chef-server',
            dest='chef_server',
            help=(
                'URL of chef-server to update '
                'environment, roles etc if desired'
            )
        )
        self.parser.add_argument(
            '--chef-username',
            dest='chef_username',
            help=(
                'chef server username'
            )
        )
        self.parser.add_argument(
            '--chef-keyfile',
            dest='chef_keyfile',
            help=(
                'Path to PEM key to access chef server'
            )
        )
        self.parser.add_argument(
            '--nodes-list',
            dest='node_list',
            help='list of nodes to execute chef-client on',
            nargs='+'
        )
