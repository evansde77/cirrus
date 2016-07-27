#!/usr/bin/env python
"""
_publish_plugins_

"""

from cirrus.configuration import load_configuration
from pluggage.factory_plugin import PluggagePlugin


class Publisher(PluggagePlugin):
    """
    _Publisher_

    Base class for publisher plugins

    """
    PLUGGAGE_FACTORY_NAME = 'publish'

    def __init__(self):
        super(Publisher, self).__init__()
        self.package_conf = load_configuration()

    def publish(self, doc_artifact):
        """
        _publish_

        Override this method to publish the documentation.

        :param doc_artifact: path to the documentation tarball to publish

        """
        raise NotImplemented("{}.publish".format(type(self).__name__))
