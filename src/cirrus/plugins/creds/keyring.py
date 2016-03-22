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
        super(Keyring, self).__init__()
        self.section = "cirrus"
        self.keyring = None

    def load(self):
        """
        """
        self.keyring = keyring.get_keyring()

    def github_credentials(self):
        github_user = self.keyring.get_password('cirrus', 'github-user')
        github_token = self.keyring.get_password('cirrus', 'github-token')
        return {
            'github_user': github_user,
            'github_token': github_token
        }

    def pypi_credentials(self):
        pypi_user = self.keyring.get_password('cirrus', 'pypi-user')
        pypi_token = self.keyring.get_password('cirrus', 'pypi-token')
        return {
            'username': pypi_user,
            'token': pypi_token
        }

    def ssh_credentials(self):
        pypi_ssh_user = self.keyring.get_password('cirrus', 'ssh-user')
        pypi_key = self.keyring.get_password('cirrus', 'ssh-key')
        return {
            'ssh_username': pypi_ssh_user,
            'ssh_key': pypi_key
        }

    def buildserver_credentials(self):
        """

        """
        return {
            'buildserver-user': self.keyring.get_password('cirrus', 'buildserver-user'),
            'buildserver-token': self.keyring.get_password('cirrus', 'buildserver-token')
        }

    def chef_credentials(self):
        """

        """
        return {
            'chef_server': self.keyring.get_password('cirrus', 'chef-server'),
            'chef_username': self.keyring.get_password('cirrus', 'chef-username'),
            'chef_keyfile': self.keyring.get_password('cirrus', 'chef-keyfile'),
            'chef_client_user': self.keyring.get_password('cirrus', 'chef-client-user'),
            'chef_client_keyfile': self.keyring.get_password('cirrus', 'chef-client-keyfile')
        }

    def dockerhub_credentials(self):
        return {
            'username': self.config.get_param('cirrus', 'docker_login_username', None),
            'email': self.config.get_param('cirrus', 'docker_login_email', None),
            'password': self.config.get_param('cirrus', 'docker_login_password', None)
        }
