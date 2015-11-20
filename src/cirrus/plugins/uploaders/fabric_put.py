#!/usr/bin/env python
"""
_fabric_put_

Uploader plugin that uses fabric to do a remote put

"""
from fabric.operations import put
from cirrus.fabric_helpers import FabricHelper
from cirrus.logger import get_logger
from cirrus.upload_plugins import Uploader
from cirrus.configuration import get_pypi_auth


LOGGER = get_logger()


class Pypi(Uploader):
    PLUGGAGE_OBJECT_NAME = 'fabric'

    def upload(self, opts, build_artifact):
        """
        upload to pypi via fabric over ssh
        """
        pypi_conf = self.package_conf.pypi_config()
        pypi_auth = get_pypi_auth()
        if opts.pypi_url:
            pypi_url = opts.pypi_url
        else:
            pypi_url = pypi_conf['pypi_url']

        if pypi_auth['ssh_username'] is not None:
            pypi_user = pypi_auth['ssh_username']
        else:
            pypi_user = pypi_auth['username']

        package_dir = pypi_conf['pypi_upload_path']
        LOGGER.info("Uploading {0} to {1}".format(build_artifact, pypi_url))
        with FabricHelper(pypi_url, pypi_user, pypi_auth['ssh_key']):
            # fabric put the file onto the pypi server
            put(build_artifact, package_dir, use_sudo=opts.pypi_sudo)
