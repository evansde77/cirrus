#!/usr/bin/env python
"""
builder plugin

Define the plugin base API for builders
for managing virtualenvs of various flavours

"""
from cirrus.configuration import load_configuration

from pluggage.factory_plugin import PluggagePlugin


class Builder(PluggagePlugin):
    PLUGGAGE_FACTORY_NAME = 'builder'

    def __init__(self):
        super(Builder, self).__init__()
        self.package_conf = load_configuration()

    def create(self, path, **kwargs):
        """
        _create_

        create a new python runtime environment
        at the location provided

        """
        pass

    def clean(self, path, **kwargs):
        """
        _clean_

        remove the specified runtime environment

        """
        pass

    def activate(self):
        """
        return a shell command string to activate the
        runtime environment
        """
        pass
