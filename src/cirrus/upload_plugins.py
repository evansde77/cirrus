#!/usr/bin/env python
"""
_upload_plugins_

"""

from cirrus.configuration import load_configuration
from pluggage.factory_plugin import PluggagePlugin


class Uploader(PluggagePlugin):
    """
    _Uploader_

    Base class for uploader plugins

    """
    PLUGGAGE_FACTORY_NAME = 'upload'

    def __init__(self):
        super(Uploader, self).__init__()
        self.package_conf = load_configuration()

    def upload(self, opts, build_artifact):
        """
        _upload_

        Override this method to perform the upload.

        :param opts: The argparse opts object from the command
            parser

        :param build_artifact: path to the release tarball to upload

        """
        raise NotImplemented("{}.upload".format(type(self).__name__))
