#!/usr/bin/env python
"""
keyring module plugin

"""
import keyring
from cirrus.creds_plugin import CredsPlugin


class Keyring(CredsPlugin):
    """
    Keyring

    Get credentials from the platform's keyring implementation
    Eg: Keychain on OSX
    See https://pypi.python.org/pypi/keyring for more details

    """
    PLUGGAGE_OBJECT_NAME = 'keyring'

    def __init__(self):
        self.keyring = None
        self.section = "cirrus"
        super(Keyring, self).__init__()

    def load(self):
        """
        load current keyring object
        """
        self.keyring = keyring.get_keyring()

    def github_credentials(self):
        github_user = self.keyring.get_password(self.section, 'github-user')
        github_token = self.keyring.get_password(self.section, 'github-token')
        return {
            'github_user': github_user,
            'github_token': github_token
        }

    def set_github_credentials(self, username, token):
        self.keyring.set_password(self.section, 'github-user', username)
        self.keyring.set_password(self.section, 'github-token', token)

    def pypi_credentials(self):
        pypi_user = self.keyring.get_password(self.section, 'pypi-user')
        pypi_token = self.keyring.get_password(self.section, 'pypi-token')
        return {
            'username': pypi_user,
            'token': pypi_token
        }

    def set_pypi_credentials(self, username, token):
        self.keyring.set_password(self.section, 'pypi-user', username)
        self.keyring.set_password(self.section, 'pypi-token', token)

    def ssh_credentials(self):
        pypi_ssh_user = self.keyring.get_password(self.section, 'ssh-user')
        pypi_key = self.keyring.get_password(self.section, 'ssh-key')
        return {
            'ssh_username': pypi_ssh_user,
            'ssh_key': pypi_key
        }

    def set_ssh_credentials(self, user, keyfile):
        self.keyring.set_password(self.section, 'ssh-user', user)
        self.keyring.set_password(self.section, 'ssh-key', keyfile)

    def buildserver_credentials(self):
        """

        """
        return {
            'buildserver-user': self.keyring.get_password(self.section, 'buildserver-user'),
            'buildserver-token': self.keyring.get_password(self.section, 'buildserver-token')
        }

    def set_buildserver_credentials(self, user, token):
        self.keyring.set_password(self.section, 'buildserver-user', user)
        self.keyring.set_password(self.section, 'buildserver-token', token)

    def chef_credentials(self):
        """

        """
        return {
            'chef_server': self.keyring.get_password(self.section, 'chef-server'),
            'chef_username': self.keyring.get_password(self.section, 'chef-username'),
            'chef_keyfile': self.keyring.get_password(self.section, 'chef-keyfile'),
            'chef_client_user': self.keyring.get_password(self.section, 'chef-client-user'),
            'chef_client_keyfile': self.keyring.get_password(self.section, 'chef-client-keyfile')
        }

    def set_chef_credentials(self, server, username, keyfile, client_user=None, client_key=None):
        if client_user is None:
            client_user = username
        if client_key is None:
            client_key = keyfile
        self.keyring.set_password(self.section, 'chef-server', server)
        self.keyring.set_password(self.section, 'chef-username', username)
        self.keyring.set_password(self.section, 'chef-keyfile', keyfile)
        self.keyring.set_password(self.section, 'chef-client-user', client_user)
        self.keyring.set_password(self.section, 'chef-client-keyfile', client_key)

    def dockerhub_credentials(self):
        return {
            'username': self.keyring.get_password(self.section, 'docker_login_username'),
            'email': self.keyring.get_password(self.section, 'docker_login_email'),
            'password': self.keyring.get_password(self.section, 'docker_login_password')
        }

    def set_dockerhub_credentials(self, email, user, password):
        self.keyring.set_password(self.section, 'docker_login_username', user)
        self.keyring.set_password(self.section, 'docker_login_email', email)
        self.keyring.set_password(self.section, 'docker_login_password', password)

    def file_server_credentials(self):
        return {
            'file_server_username': self.keyring.get_password(self.section, 'file-server-username'),
            'file_server_keyfile': self.keyring.get_password(self.section, 'file-server-keyfile')
        }

    def set_file_server_credentials(self, username, keyfile):
        self.keyring.set_password(self.section, 'file-server-username', username)
        self.keyring.set_password(self.section, 'file-server-keyfile', keyfile)
