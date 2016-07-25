#!/usr/bin/env python
"""
_doc_file_server_

Publisher plugin that uses fabric to do a remote put

"""
from fabric.operations import put
from cirrus.fabric_helpers import FabricHelper
from cirrus.logger import get_logger
from cirrus.publish_plugins import Publisher


LOGGER = get_logger()


class Documentation(Publisher):
    PLUGGAGE_OBJECT_NAME = 'doc_file_server'

    def publish(self, doc_artifact):
        """
        publish docs to a remote server via fabric over ssh.

        .. note:: This only uploads the doc artifact to the server. If
            desired, the artifact must be manually unpacked on the server.

        Requires the following cirrus.conf sections:
        [doc]
        publisher = doc_file_server

        [doc_file_server]
        doc_file_server_url = http://localhost:8080
        doc_file_server_upload_path = /path/to/upload/dir
        doc_file_server_sudo = [True | False]

        .. note:: file_server_sudo is optional for False because it defaults
            to False.

        Requires the following .gitconfig options in the [cirrus] section:
        file-server-username = username
        file-server-keyfile = /path/to/keyfile

        """
        fs_creds = self.package_conf.credentials.file_server_credentials()
        fs_username = fs_creds['file_server_username']
        fs_keyfile = fs_creds['file_server_keyfile']

        try:
            fs_config = self.package_conf['doc_file_server']
            fs_url = fs_config['doc_file_server_url']
            fs_upload_path = fs_config['doc_file_server_upload_path']
        except KeyError as err:
            msg = (
                'cirrus.conf [doc_file_server] section is missing or '
                'incomplete. Error: {}'
                '\nPlease see below for an example.\n'
                '\n [doc_file_server]'
                '\n doc_file_server_url = http://localhost:8080'
                '\n doc_file_server_upload_path = /path/to/upload/dir'
                '\n doc_file_server_sudo = [True | False]'.format(err)
            )
            raise RuntimeError(msg)

        # need to check for True as a string because ConfigParser always
        # stores values internally as strings
        use_sudo = False
        if fs_config.get('doc_file_server_sudo', 'False').lower() == 'true':
            use_sudo = True

        LOGGER.info("Uploading {0} to {1}".format(doc_artifact, fs_url))
        with FabricHelper(fs_url, fs_username, fs_keyfile):
            # fabric put the file onto the file server
            put(doc_artifact, fs_upload_path, use_sudo=use_sudo)
