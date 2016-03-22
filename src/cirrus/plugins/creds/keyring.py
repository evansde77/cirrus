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

    def pypi_credentials(self):
        pypi_user = self.keyring.get_password(self.section, 'pypi-user')
        pypi_token = self.keyring.get_password(self.section, 'pypi-token')
        return {
            'username': pypi_user,
            'token': pypi_token
        }

    def ssh_credentials(self):
        pypi_ssh_user = self.keyring.get_password(self.section, 'ssh-user')
        pypi_key = self.keyring.get_password(self.section, 'ssh-key')
        return {
            'ssh_username': pypi_ssh_user,
            'ssh_key': pypi_key
        }

    def buildserver_credentials(self):
        """

        """
        return {
            'buildserver-user': self.keyring.get_password(self.section, 'buildserver-user'),
            'buildserver-token': self.keyring.get_password(self.section, 'buildserver-token')
        }

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

    def dockerhub_credentials(self):
        return {
            'username': self.keyring.get_password(self.section, 'docker_login_username'),
            'email': self.keyring.get_password(self.section, 'docker_login_email'),
            'password': self.keyring.get_password(self.section, 'docker_login_password')
        }
