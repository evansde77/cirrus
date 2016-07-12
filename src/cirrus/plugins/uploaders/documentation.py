#!/usr/bin/env python
"""
_documentation_

Uploader plugin that uses fabric to do a remote put

"""
from fabric.operations import put
from cirrus.fabric_helpers import FabricHelper
from cirrus.logger import get_logger
from cirrus.upload_plugins import Uploader


LOGGER = get_logger()


class Documentation(Uploader):
    PLUGGAGE_OBJECT_NAME = 'file_server'

    def upload(self, opts, doc_artifact):
        """
        upload docs to a remote server via fabric over ssh.

        .. note:: This only uploads the doc artifact to the server. If
            desired, the artifact must be manually unpacked on the server.

        Requires the following cirrus.conf section:
        [doc]
        upload_method = file_server
        file_server_upload_path = /path/to/upload/dir

        Requires the following .gitconfig options in the [cirrus] section:
        file-server = [file server url]
        file-server-username = username
        file-server-keyfile = /path/to/keyfile

        file-server may also be specified on the command line

        """
        file_server_conf = self.package_conf.credentials.file_server_credentials()
        file_server_username = file_server_conf['file_server_username']
        file_server_keyfile = file_server_conf['file_server_keyfile']

        if opts.file_server:
            file_server = opts.file_server
        else:
            file_server = file_server_conf['file_server']

        doc_dir = doc_conf['file_server_upload_path']
        LOGGER.info("Uploading {0} to {1}".format(doc_artifact, file_server))
        with FabricHelper(file_server, file_server_username, file_server_keyfile):
            # fabric put the file onto the file server
            put(doc_artifact, doc_dir, use_sudo=opts.fs_sudo)
