#!/usr/bin/env python
"""
default

Default credential management that gets things from
your .gitconfig.

"""
import os
import gitconfig
from cirrus.creds_plugin import CredsPlugin


class Default(CredsPlugin):
    """
    Default

    Get credentials from the users ~/.gitconfig file

    """
    PLUGGAGE_OBJECT_NAME = 'default'

    def __init__(self, gitconfig_file=None):
        self.gitconfig_file = gitconfig_file
        super(Default, self).__init__()

    def load(self):
        """
        load - override load hook to read the users .gitconfig file
        """
        if self.gitconfig_file is None:
            self.gitconfig_file = os.path.join(os.environ['HOME'], '.gitconfig')
        self.config = gitconfig.config(self.gitconfig_file)

    def github_credentials(self):
        github_user = self.config.get('cirrus', 'github-user')
        github_token = self.config.get('cirrus', 'github-token')
        return {
            'github_user': github_user,
            'github_token': github_token
        }

    def pypi_credentials(self):
        pypi_user = self.config.get('cirrus', 'pypi-user')
        pypi_token = self.config.get('cirrus', 'pypi-token')
        return {
            'username': pypi_user,
            'token': pypi_token
        }

    def ssh_credentials(self):
        pypi_ssh_user = self.config.get('cirrus', 'ssh-user')
        pypi_key = self.config.get('cirrus', 'ssh-key')
        return {
            'ssh_username': pypi_ssh_user,
            'ssh_key': pypi_key
        }

    def buildserver_credentials(self):
        """

        """
        return {
            'buildserver-user': self.config.get('cirrus', 'buildserver-user'),
            'buildserver-token': self.config.get('cirrus', 'buildserver-token')
        }

    def chef_credentials(self):
        """

        """
        return {
            'chef_server': self.config.get('cirrus', 'chef-server'),
            'chef_username': self.config.get('cirrus', 'chef-username'),
            'chef_keyfile': self.config.get('cirrus', 'chef-keyfile'),
            'chef_client_user': self.config.get('cirrus', 'chef-client-user'),
            'chef_client_keyfile': self.config.get('cirrus', 'chef-client-keyfile')
        }

    def dockerhub_credentials(self):
        return {
            'username': self.config.get('cirrus', 'docker_login_username'),
            'email': self.config.get('cirrus', 'docker_login_email'),
            'password': self.config.get('cirrus', 'docker_login_password')
        }
