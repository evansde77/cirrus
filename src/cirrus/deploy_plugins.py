#!/usr/bin/env python
"""
_deploy_plugins_

Plugin helpers to talk to various deployment platforms,
Plugins should subclass the Deployer class, override the
build_parser to handle whatever CLI args they need and
also deploy to do the actual implementation.

Drop plugins in the cirrus.plugins.deployers dir to get them
picked up by the plugin factory

"""
import argparse

from cirrus.configuration import load_configuration
from pluggage.factory_plugin import PluggagePlugin


class Deployer(PluggagePlugin):
    PLUGGAGE_FACTORY_NAME = 'deploy'

    def __init__(self):
        super(Deployer, self).__init__()
        self.package_conf = load_configuration()
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--plugin', '-p', dest='plugin', default=None)

    def deploy(self, options):
        """
        _deploy_

        :param options: Instance of argparse namespace containing
        the command line options values

        """
        raise NotImplementedError(
            "{0}.deploy not implemented".format(type(self).__name__)
        )

    def build_parser(self):
        """
        _build_parser_

        Hook for the plugin to build out its commandline tool
        suite on self.parser.

        The master CLI only uses the --plugin option to select the
        plugin and then passes everything onto that plugin.
        The plugin parser must allow --plugin, hence the addition
        of that arg in the base class

        """
        raise NotImplementedError(
            "{0}.build_parser not implemented".format(type(self).__name__)
        )
